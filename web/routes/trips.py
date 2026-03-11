"""
Trip API and page routes.

Thin I/O layer: parse request → call service → return JSON or render template.
No business logic here; all logic lives in the services.
Uses Pydantic for request validation.
"""

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, request, jsonify, url_for, render_template, abort, current_app
from flask_login import login_required, current_user
from pydantic import ValidationError

from web.schemas import (
    AddActivityRequest,
    AddFlightRequest,
    AddHotelRequest,
    CreateTripRequest,
    MoveActivityRequest,
    ReorderActivitiesRequest,
    UpdateDescriptionRequest,
)

from src.services.add_activity import AddActivityService
from src.services.add_flight import AddFlightService
from src.services.add_hotel import AddHotelService
from src.services.create_trip import CreateTripService
from src.services.get_trip import GetTripService
from src.services.join_trip import JoinTripService
from src.services.remove_activity import RemoveActivityService
from src.services.remove_collaborator import RemoveCollaboratorService
from src.services.remove_flight import RemoveFlightService
from src.services.remove_hotel import RemoveHotelService
from src.services.update_trip_description import UpdateTripDescriptionService


def _validation_error_response(exc: ValidationError):
    """Format Pydantic ValidationError as JSON 400 response."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    msg = first.get("msg", str(exc))
    loc = first.get("loc", ())
    field = loc[0] if loc else "body"
    return jsonify({"error": f"{field}: {msg}"}), 400


def _hotel_total(hotel) -> Decimal:
    """Hotel cost is per night; total = cost_per_night * num_nights."""
    nights = max(1, (hotel.check_out_date - hotel.check_in_date).days)
    return hotel.cost_estimate * nights


def _compute_budget_summary(result):
    """Compute spent vs total budget from GetTripResult. Returns dict for JSON/template."""
    trip = result.trip
    total_budget = trip.total_budget()
    # Flight cost is per person; multiply by num_people
    flights_total = sum(f.cost_estimate for f in result.flights) * trip.num_people
    hotels_total = sum(_hotel_total(h) for h in result.hotels)
    activities_total = sum(
        (a.cost_estimate or Decimal("0")) for a in result.activities
    )
    spent = flights_total + hotels_total + activities_total
    return {
        "total_budget": str(total_budget),
        "spent": str(spent),
        "flights_total": str(flights_total),
        "hotels_total": str(hotels_total),
        "activities_total": str(activities_total),
        "remaining": str(total_budget - spent),
        "over_budget": spent > total_budget,
    }


def create_trips_blueprint(
    create_trip_service: CreateTripService,
    get_trip_service: GetTripService,
    join_trip_service: JoinTripService,
    collaborator_repo,
    add_flight_service: AddFlightService,
    add_hotel_service: AddHotelService,
    add_activity_service: AddActivityService,
    remove_collaborator_service: RemoveCollaboratorService,
    leave_trip_service,
    remove_trip_service,
    remove_flight_service: RemoveFlightService,
    remove_hotel_service: RemoveHotelService,
    remove_activity_service: RemoveActivityService,
    reorder_activities_service,
    move_activity_service,
    update_trip_description_service: UpdateTripDescriptionService,
    ai_suggestions_service=None,
) -> Blueprint:
    """Create the trips blueprint with services injected."""
    bp = Blueprint("trips", __name__)

    @bp.route("/api/trips", methods=["POST"])
    @login_required
    def create_trip():
        """Create a trip; body: origin, destination, per_person_budget, num_people, start_date, end_date, activity_preferences. Requires login."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = CreateTripRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        try:
            result = create_trip_service.execute(
                origin=body.origin,
                destination=body.destination,
                per_person_budget=Decimal(str(body.per_person_budget)),
                num_people=body.num_people,
                start_date=body.start_date,
                end_date=body.end_date,
                activity_preferences=body.activity_preferences or "",
                name=body.name or "",
                owner_id=current_user.id,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        # Auto-add creator as traveler (operator)
        from src.domain.trip import Collaborator
        name = (current_user.name or "").strip() or (current_user.email or "").split("@")[0] or "Traveler"
        creator_collab = Collaborator(
            id=None,
            trip_id=result.trip.id,
            name=name,
            budget=result.trip.per_person_budget,
        )
        collaborator_repo.create(creator_collab, user_id=current_user.id)
        # Use BASE_URL if set for reliable links; else use url_for
        base = current_app.config.get("BASE_URL")
        invite_url = (base + "/trip/" + result.trip.invite_code) if base else url_for("trips.trip_page", code=result.trip.invite_code, _external=True)
        return jsonify({
            "trip_id": result.trip.id,
            "invite_code": result.trip.invite_code,
            "invite_url": invite_url,
            "days": [
                {"id": d.id, "date": d.date.isoformat(), "order": d.order}
                for d in result.days
            ],
        }), 201

    @bp.route("/api/trips/<code>/description", methods=["PATCH", "PUT"])
    def update_trip_description(code: str):
        """Update trip description; body: { "description": "..." }."""
        data = request.get_json()
        if data is None:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = UpdateDescriptionRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        result = update_trip_description_service.execute(invite_code=code, description=body.description)
        if result is None:
            return jsonify({"error": "Trip not found"}), 404
        return jsonify({"trip": {"description": result.trip.description}}), 200

    @bp.route("/api/trips/<code>/join", methods=["POST"])
    @login_required
    def join_trip(code: str):
        """Join a trip by invite code. Uses current user's name. Body: { "name" (optional), "budget": number }."""
        data = request.get_json() or {}
        budget_val = data.get("budget")
        if budget_val is None:
            return jsonify({"error": "budget is required"}), 400
        try:
            budget = Decimal(str(budget_val))
        except Exception:
            return jsonify({"error": "budget must be a number"}), 400
        if budget < 0:
            return jsonify({"error": "budget cannot be negative"}), 400
        name = (data.get("name") or "").strip()
        if not name:
            name = (current_user.name or "").strip() or (current_user.email or "").split("@")[0] or "Traveler"
        try:
            result = join_trip_service.execute(
                invite_code=code,
                name=name,
                budget=budget,
                user_id=current_user.id,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({
            "collaborator": {
                "id": result.collaborator.id,
                "trip_id": result.collaborator.trip_id,
                "name": result.collaborator.name,
                "budget": str(result.collaborator.budget),
            },
        }), 201

    @bp.route("/api/trips/<code>/leave", methods=["POST"])
    @login_required
    def leave_trip(code: str):
        """Leave the trip (remove self as collaborator)."""
        try:
            leave_trip_service.execute(invite_code=code, user_id=current_user.id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"left": True}), 200

    @bp.route("/api/trips/<code>", methods=["DELETE"])
    @login_required
    def delete_trip(code: str):
        """Delete the trip. Only trip owner (operator) can delete."""
        from persistence.sqlite.models import TripModel
        trip_model = TripModel.query.filter_by(invite_code=code).first()
        if not trip_model:
            return jsonify({"error": "Trip not found"}), 404
        if trip_model.owner_id != current_user.id:
            return jsonify({"error": "Only the trip operator can delete the trip"}), 403
        try:
            remove_trip_service.execute(code)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"deleted": True}), 200

    @bp.route("/api/trips/<code>/collaborators/<int:collaborator_id>", methods=["DELETE"])
    @login_required
    def delete_collaborator(code: str, collaborator_id: int):
        """Delete a collaborator (trip member) by id. Only trip owner (operator) can remove travelers."""
        from persistence.sqlite.models import TripModel
        trip_model = TripModel.query.filter_by(invite_code=code).first()
        if not trip_model:
            return jsonify({"error": "Trip not found"}), 404
        if trip_model.owner_id != current_user.id:
            return jsonify({"error": "Only the trip operator can remove travelers"}), 403
        try:
            remove_collaborator_service.execute(invite_code=code, collaborator_id=collaborator_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"deleted": True}), 200

    @bp.route("/api/trips/<code>", methods=["GET"])
    def trip_by_code(code: str):
        """Get trip by invite code (JSON API)."""
        result = get_trip_service.execute(code)
        if result is None:
            return jsonify({"error": "Trip not found"}), 404
        return jsonify({
            "trip": {
                "id": result.trip.id,
                "name": result.trip.name,
                "origin": result.trip.origin,
                "destination": result.trip.destination,
                "per_person_budget": str(result.trip.per_person_budget),
                "num_people": result.trip.num_people,
                "start_date": result.trip.start_date.isoformat(),
                "end_date": result.trip.end_date.isoformat(),
                "activity_preferences": result.trip.activity_preferences,
                "invite_code": result.trip.invite_code,
                "description": getattr(result.trip, "description", None),
            },
            "days": [
                {"id": d.id, "date": d.date.isoformat(), "order": d.order}
                for d in result.days
            ],
            "collaborators": [
                {"id": c.id, "name": c.name, "budget": str(c.budget)}
                for c in result.collaborators
            ],
            "flights": [
                {
                    "id": f.id,
                    "origin": f.origin,
                    "destination": f.destination,
                    "departure_date": f.departure_date.isoformat(),
                    "return_date": f.return_date.isoformat(),
                    "cost_estimate": str(f.cost_estimate),
                    "departure_time": f.departure_time,
                }
                for f in result.flights
            ],
            "hotels": [
                {
                    "id": h.id,
                    "name": h.name,
                    "check_in_date": h.check_in_date.isoformat(),
                    "check_out_date": h.check_out_date.isoformat(),
                    "cost_estimate": str(h.cost_estimate),
                }
                for h in result.hotels
            ],
            "activities": [
                {
                    "id": a.id,
                    "day_id": a.day_id,
                    "title": a.title,
                    "time": a.time,
                    "cost_estimate": str(a.cost_estimate) if a.cost_estimate else None,
                    "order": a.order,
                }
                for a in result.activities
            ],
            "budget_summary": _compute_budget_summary(result),
        })

    @bp.route("/api/trips/<code>/flights", methods=["POST"])
    def add_flight(code: str):
        """Add a flight; body: { "origin", "destination", "departure_date", "return_date", "cost_estimate", "departure_time?" }."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = AddFlightRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        try:
            result = add_flight_service.execute(
                invite_code=code,
                origin=body.origin,
                destination=body.destination,
                departure_date=body.departure_date,
                return_date=body.return_date,
                cost_estimate=Decimal(str(body.cost_estimate)),
                departure_time=body.departure_time,
                link=body.link,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        f = result.flight
        return jsonify({
            "flight": {
                "id": f.id,
                "origin": f.origin,
                "destination": f.destination,
                "departure_date": f.departure_date.isoformat(),
                "return_date": f.return_date.isoformat(),
                "cost_estimate": str(f.cost_estimate),
                "departure_time": f.departure_time,
                "link": f.link,
            },
        }), 201

    @bp.route("/api/trips/<code>/flights/<int:flight_id>", methods=["DELETE"])
    def delete_flight(code: str, flight_id: int):
        """Delete a saved flight by id."""
        try:
            remove_flight_service.execute(invite_code=code, flight_id=flight_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"deleted": True}), 200

    @bp.route("/api/trips/<code>/hotels", methods=["POST"])
    def add_hotel(code: str):
        """Add a hotel; body: { "name", "check_in_date", "check_out_date", "cost_estimate" }."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = AddHotelRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        try:
            result = add_hotel_service.execute(
                invite_code=code,
                name=body.name,
                check_in_date=body.check_in_date,
                check_out_date=body.check_out_date,
                cost_estimate=Decimal(str(body.cost_estimate)),
                link=body.link,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        h = result.hotel
        return jsonify({
            "hotel": {
                "id": h.id,
                "name": h.name,
                "check_in_date": h.check_in_date.isoformat(),
                "check_out_date": h.check_out_date.isoformat(),
                "cost_estimate": str(h.cost_estimate),
                "link": h.link,
            },
        }), 201

    @bp.route("/api/trips/<code>/hotels/<int:hotel_id>", methods=["DELETE"])
    def delete_hotel(code: str, hotel_id: int):
        """Delete a saved hotel by id."""
        try:
            remove_hotel_service.execute(invite_code=code, hotel_id=hotel_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"deleted": True}), 200

    @bp.route("/api/trips/<code>/activities", methods=["POST"])
    def add_activity(code: str):
        """Add an activity; body: { "day_id", "title", "time?", "cost_estimate?" }."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = AddActivityRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        result = add_activity_service.execute(
            invite_code=code,
            day_id=body.day_id,
            title=body.title,
            time=body.time,
            cost_estimate=Decimal(str(body.cost_estimate)) if body.cost_estimate is not None else None,
        )
        if result is None:
            return jsonify({"error": "Trip or day not found"}), 404
        a = result.activity
        return jsonify({
            "activity": {
                "id": a.id,
                "day_id": a.day_id,
                "title": a.title,
                "time": a.time,
                "cost_estimate": str(a.cost_estimate) if a.cost_estimate else None,
            },
        }), 201

    @bp.route("/api/trips/<code>/activities/<int:activity_id>", methods=["DELETE"])
    def delete_activity(code: str, activity_id: int):
        """Delete a saved activity by id."""
        try:
            remove_activity_service.execute(invite_code=code, activity_id=activity_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"deleted": True}), 200

    @bp.route("/api/trips/<code>/activities/<int:activity_id>/move", methods=["PATCH", "PUT"])
    def move_activity(code: str, activity_id: int):
        """Move activity to a different day; body: { "day_id": int, "order"?: int }."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = MoveActivityRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        try:
            move_activity_service.execute(
                invite_code=code,
                activity_id=activity_id,
                day_id=body.day_id,
                order=body.order,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"moved": True}), 200

    @bp.route("/api/trips/<code>/activities/reorder", methods=["PATCH", "PUT"])
    def reorder_activities(code: str):
        """Reorder activities; body: { "day_id": int, "activity_ids": [id1, id2, ...] }."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        try:
            body = ReorderActivitiesRequest.model_validate(data)
        except ValidationError as e:
            return _validation_error_response(e)
        try:
            reorder_activities_service.execute(
                invite_code=code,
                day_id=body.day_id,
                activity_ids=body.activity_ids,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"reordered": True}), 200

    @bp.route("/api/trips/<code>/suggestions", methods=["GET"])
    def get_trip_suggestions(code: str):
        """Get AI-generated flight and hotel options. Use ?refresh=1 to fetch fresh from AI."""
        import json
        from persistence.sqlite.suggestion_repository import (
            create_many,
            delete_by_trip_id,
            get_by_trip_id,
            get_voted_suggestion_ids,
        )
        result = get_trip_service.execute(code)
        if result is None:
            return jsonify({"error": "Trip not found"}), 404
        trip = result.trip
        force_refresh = request.args.get("refresh") == "1"
        cached = get_by_trip_id(trip.id) if trip.id else []
        voted_ids = set()
        if current_user.is_authenticated and cached:
            voted_ids = get_voted_suggestion_ids(
                current_user.id, [s.id for s in cached]
            )
        if not force_refresh and cached:
            flights_out = []
            hotels_out = []
            for s in cached:
                d = json.loads(s.data)
                d["id"] = s.id
                d["vote_count"] = s.vote_count or 0
                d["user_has_voted"] = s.id in voted_ids
                if s.suggestion_type == "flight":
                    flights_out.append(d)
                else:
                    hotels_out.append(d)
            return jsonify({"flights": flights_out, "hotels": hotels_out}), 200
        if not ai_suggestions_service or not hasattr(ai_suggestions_service, "get_trip_suggestions"):
            return jsonify({"flights": [], "hotels": []}), 200
        flights, hotels = ai_suggestions_service.get_trip_suggestions(
            origin=trip.origin,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            num_people=trip.num_people,
            total_budget=trip.total_budget(),
        )
        def flight_json(o):
            return {
                "origin": o.origin,
                "destination": o.destination,
                "departure_date": o.departure_date.isoformat(),
                "return_date": o.return_date.isoformat(),
                "cost_estimate": str(o.cost_estimate),
                "description": o.description,
                "airline": o.airline,
                "flight_number": o.flight_number,
                "link": o.link,
                "trip_type": "one_way" if o.departure_date == o.return_date else "roundtrip",
            }
        def hotel_json(h):
            return {
                "name": h.name,
                "check_in_date": h.check_in_date.isoformat(),
                "check_out_date": h.check_out_date.isoformat(),
                "cost_estimate": str(h.cost_estimate),
                "description": h.description,
                "link": getattr(h, "link", None),
            }
        if trip.id and (flights or hotels):
            delete_by_trip_id(trip.id)
            flight_data = [flight_json(o) for o in flights]
            hotel_data = [hotel_json(h) for h in hotels]
            flight_models = create_many(trip.id, "flight", flight_data)
            hotel_models = create_many(trip.id, "hotel", hotel_data)
            flights_out = []
            for m in flight_models:
                d = json.loads(m.data)
                d["id"] = m.id
                d["vote_count"] = 0
                flights_out.append(d)
            hotels_out = []
            for m in hotel_models:
                d = json.loads(m.data)
                d["id"] = m.id
                d["vote_count"] = 0
                hotels_out.append(d)
        else:
            flights_out = [flight_json(o) for o in flights]
            hotels_out = [hotel_json(h) for h in hotels]
        for o in flights_out + hotels_out:
            o["user_has_voted"] = False
        if current_user.is_authenticated:
            all_ids = [o["id"] for o in flights_out + hotels_out if "id" in o]
            if all_ids:
                voted_ids = get_voted_suggestion_ids(current_user.id, all_ids)
                for o in flights_out + hotels_out:
                    if "id" in o:
                        o["user_has_voted"] = o["id"] in voted_ids
        return jsonify({"flights": flights_out, "hotels": hotels_out}), 200

    @bp.route("/api/trips/<code>/suggestions/<int:suggestion_id>/vote", methods=["POST"])
    @login_required
    def vote_suggestion(code: str, suggestion_id: int):
        """Upvote a suggestion (once per user). Returns vote_count and has_voted."""
        from persistence.sqlite.suggestion_repository import get_by_id, increment_vote
        result = get_trip_service.execute(code)
        if result is None:
            return jsonify({"error": "Trip not found"}), 404
        s = get_by_id(suggestion_id)
        if not s or s.trip_id != result.trip.id:
            return jsonify({"error": "Suggestion not found"}), 404
        new_count, did_vote = increment_vote(suggestion_id, current_user.id)
        return jsonify({
            "vote_count": new_count or 0,
            "has_voted": True,
        }), 200

    @bp.route("/api/trips/<code>/suggestions/raw", methods=["GET"])
    def get_trip_suggestions_raw(code: str):
        """Get the raw API response (for debugging)."""
        result = get_trip_service.execute(code)
        if result is None:
            return jsonify({"error": "Trip not found"}), 404
        if not ai_suggestions_service or not hasattr(ai_suggestions_service, "get_trip_suggestions_raw"):
            return jsonify({"raw": "(Mock service - no raw output)"}), 200
        trip = result.trip
        raw = ai_suggestions_service.get_trip_suggestions_raw(
            origin=trip.origin,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            num_people=trip.num_people,
            total_budget=trip.total_budget(),
        )
        return jsonify({"raw": raw}), 200

    @bp.route("/api/trips/<code>/suggestions/activities", methods=["POST"])
    def get_activity_suggestions(code: str):
        """Search for activities; body: { "query": "beach activities", "day_date": "YYYY-MM-DD" }."""
        result = get_trip_service.execute(code)
        if result is None:
            return jsonify({"error": "Trip not found"}), 404
        if not ai_suggestions_service:
            return jsonify({"options": []}), 200
        data = request.get_json() or {}
        query = (data.get("query") or "").strip()
        day_date_str = (data.get("day_date") or "").strip()
        if not query:
            return jsonify({"error": "query is required"}), 400
        try:
            day_date = datetime.strptime(day_date_str, "%Y-%m-%d").date() if day_date_str else result.trip.start_date
        except ValueError:
            day_date = result.trip.start_date
        budget = result.trip.per_person_budget * result.trip.num_people / result.trip.total_days()

        # Append dietary preferences if current_user has them
        final_query = query
        if current_user.is_authenticated and current_user.dietary_prefs:
            final_query += f". User dietary preferences: {current_user.dietary_prefs}"

        opts = ai_suggestions_service.get_activity_suggestions(
            day_date=day_date,
            destination=result.trip.destination,
            preferences=final_query,
            budget_remaining=budget,
        )
        return jsonify({
            "options": [{
                "title": a.title,
                "time": a.time,
                "cost_estimate": str(a.cost_estimate) if a.cost_estimate else None,
                "description": a.description,
            } for a in opts]
        }), 200

    @bp.route("/api/trips/<code>/suggestions/flights", methods=["GET", "POST"])
    def get_flight_suggestions(code: str):
        """Flight options only. GET uses trip defaults; POST uses provided form inputs."""
        r = get_trip_service.execute(code)
        if r is None:
            return jsonify({"error": "Trip not found"}), 404
        if not ai_suggestions_service:
            return jsonify({"options": []}), 200
        if request.method == "POST":
            payload = request.get_json() or {}
            origin = (payload.get("origin") or r.trip.origin).strip()
            destination = (payload.get("destination") or r.trip.destination).strip()
            dep_str = (payload.get("departure_date") or "").strip()
            ret_str = (payload.get("return_date") or "").strip()
            trip_type = (payload.get("trip_type") or "roundtrip").strip()
            try:
                departure_date = datetime.strptime(dep_str, "%Y-%m-%d").date() if dep_str else r.trip.start_date
            except ValueError:
                return jsonify({"error": "departure_date must be YYYY-MM-DD"}), 400
            if trip_type == "one_way":
                return_date = departure_date
            else:
                try:
                    return_date = datetime.strptime(ret_str, "%Y-%m-%d").date() if ret_str else r.trip.end_date
                except ValueError:
                    return jsonify({"error": "return_date must be YYYY-MM-DD"}), 400
            if hasattr(ai_suggestions_service, "get_flight_options_custom"):
                opts = ai_suggestions_service.get_flight_options_custom(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    trip_type=trip_type,
                )
            else:
                opts = ai_suggestions_service.get_flight_options(
                    origin, destination, departure_date, return_date
                )
        else:
            opts = ai_suggestions_service.get_flight_options(
                r.trip.origin, r.trip.destination, r.trip.start_date, r.trip.end_date
            )
        return jsonify({
            "options": [{
                "origin": o.origin, "destination": o.destination,
                "departure_date": o.departure_date.isoformat(),
                "return_date": o.return_date.isoformat(),
                "cost_estimate": str(o.cost_estimate),
                "description": o.description, "airline": o.airline,
                "flight_number": o.flight_number, "link": o.link,
                "trip_type": "one_way" if o.departure_date == o.return_date else "roundtrip",
            } for o in opts]
        }), 200

    @bp.route("/trip/<code>")
    @login_required
    def trip_page(code: str):
        """Serve the trip page (shareable link). Requires login."""
        from persistence.sqlite.models import TripModel
        result = get_trip_service.execute(code)
        if result is None:
            abort(404)
        activities_by_day = {}
        for a in result.activities:
            activities_by_day.setdefault(a.day_id, []).append(a)

        trip_model = TripModel.query.filter_by(invite_code=code).first()
        is_owner = trip_model is not None and trip_model.owner_id == current_user.id

        my_collaborator_id = None
        user_display_name = (current_user.name or "").strip() or (current_user.email or "").split("@")[0] or "Traveler"
        if collaborator_repo and result.trip.id:
            my_collab = collaborator_repo.get_by_trip_id_and_user_id(result.trip.id, current_user.id)
            my_collaborator_id = my_collab.id if my_collab else None

            # Auto-join logic if logged in user is viewing a trip for the first time
            if not is_owner and not my_collaborator_id:
                try:
                    join_trip_service.execute(
                        invite_code=code,
                        user_id=current_user.id,
                        name=user_display_name,
                        budget=result.trip.per_person_budget,
                    )
                    # Refresh data after joining
                    result = get_trip_service.execute(code)
                    my_collab = collaborator_repo.get_by_trip_id_and_user_id(result.trip.id, current_user.id)
                    my_collaborator_id = my_collab.id if my_collab else None
                except Exception as e:
                    # Ignore join errors like already joined (which is handled above anyway)
                    pass

        return render_template(
            "trip.html",
            trip=result.trip,
            days=result.days,
            collaborators=result.collaborators,
            flights=result.flights,
            hotels=result.hotels,
            activities=result.activities,
            activities_by_day=activities_by_day,
            budget_summary=_compute_budget_summary(result),
            invite_url=(current_app.config.get("BASE_URL") + "/trip/" + code) if current_app.config.get("BASE_URL") else url_for("trips.trip_page", code=code, _external=True),
            my_collaborator_id=my_collaborator_id,
            user_display_name=user_display_name,
            is_owner=is_owner,
        )

    @bp.route("/trip/<code>/itinerary")
    @login_required
    def trip_itinerary(code: str):
        """Serve the printable trip itinerary page. Requires login."""
        result = get_trip_service.execute(code)
        if result is None:
            abort(404)
        activities_by_day = {}
        for a in result.activities:
            activities_by_day.setdefault(a.day_id, []).append(a)
        return render_template(
            "itinerary.html",
            trip=result.trip,
            days=result.days,
            collaborators=result.collaborators,
            flights=result.flights,
            hotels=result.hotels,
            activities_by_day=activities_by_day,
            budget_summary=_compute_budget_summary(result),
        )

    return bp
