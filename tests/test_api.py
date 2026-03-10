"""
API integration tests.

Uses Flask test client against in-memory SQLite. No real OpenAI calls (mock AI).
"""

import pytest
from datetime import date


def test_health(client):
    """Health endpoint returns ok."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"


def test_create_trip_requires_login(client):
    """POST /api/trips without login redirects to login page."""
    r = client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "MIA",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
            "name": "Beach Trip",
        },
        content_type="application/json",
    )
    # Flask-Login redirects unauthenticated users to login
    assert r.status_code in (302, 401)
    if r.status_code == 302:
        assert "/login" in r.headers.get("Location", "")


def test_create_trip(auth_client):
    """POST /api/trips creates a trip and returns invite URL (when logged in)."""
    r = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "MIA",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
            "name": "Beach Trip",
        },
        content_type="application/json",
    )
    assert r.status_code == 201
    data = r.get_json()
    assert "trip_id" in data
    assert "invite_code" in data
    assert "invite_url" in data
    assert len(data["invite_code"]) >= 6
    assert len(data["days"]) == 5  # 10th through 14th


def test_create_trip_invalid_date_format(auth_client):
    """Create trip with invalid date format returns 400 (Pydantic validation)."""
    r = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "MIA",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "06/10/2025",  # wrong format
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
        },
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_create_trip_missing_origin(auth_client):
    """Create trip without origin returns 400."""
    r = auth_client.post(
        "/api/trips",
        json={
            "destination": "MIA",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
        },
        content_type="application/json",
    )
    assert r.status_code == 400
    assert "origin" in r.get_json().get("error", "").lower()


def test_get_trip_not_found(client):
    """GET /api/trips/BADCODE returns 404."""
    r = client.get("/api/trips/BADCODE")
    assert r.status_code == 404


def test_create_and_get_trip(auth_client):
    """Create trip then fetch by invite code."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "LAX",
            "destination": "Tokyo",
            "per_person_budget": 1200,
            "num_people": 1,
            "start_date": "2025-07-01",
            "end_date": "2025-07-07",
            "activity_preferences": "culture",
            "name": "Japan",
        },
        content_type="application/json",
    )
    assert create.status_code == 201
    code = create.get_json()["invite_code"]

    r = auth_client.get(f"/api/trips/{code}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["trip"]["origin"] == "LAX"
    assert data["trip"]["destination"] == "Tokyo"
    assert data["trip"]["name"] == "Japan"
    assert data["trip"]["invite_code"] == code
    assert len(data["days"]) == 7
    assert len(data["collaborators"]) == 1  # Creator auto-added as traveler
    assert data["flights"] == []
    assert data["hotels"] == []
    assert data["activities"] == []


def test_join_trip(auth_client):
    """Create trip, join as collaborator."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Boston",
            "per_person_budget": 200,
            "num_people": 2,
            "start_date": "2025-08-01",
            "end_date": "2025-08-03",
            "activity_preferences": "",
            "name": "Boston",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]

    join = auth_client.post(
        f"/api/trips/{code}/join",
        json={"name": "Alice", "budget": 250},
        content_type="application/json",
    )
    assert join.status_code == 201
    collab = join.get_json()["collaborator"]
    assert collab["name"] == "Alice"
    assert collab["budget"] == "250.00"

    trip = auth_client.get(f"/api/trips/{code}").get_json()
    assert len(trip["collaborators"]) == 2  # Creator + Alice
    alice = next(c for c in trip["collaborators"] if c["name"] == "Alice")
    assert alice["budget"] == "250.00"


def test_add_flight(auth_client):
    """Create trip, add flight."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "JFK",
            "destination": "LHR",
            "per_person_budget": 1000,
            "num_people": 1,
            "start_date": "2025-09-01",
            "end_date": "2025-09-10",
            "activity_preferences": "",
            "name": "London",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]

    add = auth_client.post(
        f"/api/trips/{code}/flights",
        json={
            "origin": "JFK",
            "destination": "LHR",
            "departure_date": "2025-09-01",
            "return_date": "2025-09-10",
            "cost_estimate": 650,
        },
        content_type="application/json",
    )
    assert add.status_code == 201
    flight = add.get_json()["flight"]
    assert flight["origin"] == "JFK"
    assert flight["cost_estimate"] == "650.00"

    trip = auth_client.get(f"/api/trips/{code}").get_json()
    assert len(trip["flights"]) == 1
    assert trip["flights"][0]["cost_estimate"] == "650.00"


def test_add_hotel(auth_client):
    """Create trip, add hotel."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 800,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]

    add = auth_client.post(
        f"/api/trips/{code}/hotels",
        json={
            "name": "Beach Resort",
            "check_in_date": "2025-06-10",
            "check_out_date": "2025-06-14",
            "cost_estimate": 1200,
        },
        content_type="application/json",
    )
    assert add.status_code == 201
    hotel = add.get_json()["hotel"]
    assert hotel["name"] == "Beach Resort"
    assert hotel["cost_estimate"] == "1200.00"


def test_add_activity(auth_client):
    """Create trip, add activity to a day."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 500,
            "num_people": 1,
            "start_date": "2025-06-10",
            "end_date": "2025-06-12",
            "activity_preferences": "",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]
    day_id = create.get_json()["days"][0]["id"]

    add = auth_client.post(
        f"/api/trips/{code}/activities",
        json={
            "day_id": day_id,
            "title": "Beach volleyball",
            "time": "14:00",
            "cost_estimate": 0,
        },
        content_type="application/json",
    )
    assert add.status_code == 201
    activity = add.get_json()["activity"]
    assert activity["title"] == "Beach volleyball"
    assert activity["day_id"] == day_id


def test_delete_trip(auth_client):
    """Operator can delete a trip; non-owner gets 403."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Boston",
            "per_person_budget": 200,
            "num_people": 1,
            "start_date": "2025-08-01",
            "end_date": "2025-08-02",
            "activity_preferences": "",
            "name": "Boston",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]

    r = auth_client.delete(f"/api/trips/{code}")
    assert r.status_code == 200
    assert r.get_json()["deleted"] is True

    r2 = auth_client.get(f"/api/trips/{code}")
    assert r2.status_code == 404


def test_delete_collaborator(auth_client):
    """Operator removes a traveler; creator stays as traveler."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Boston",
            "per_person_budget": 200,
            "num_people": 1,
            "start_date": "2025-08-01",
            "end_date": "2025-08-02",
            "activity_preferences": "",
            "name": "Boston",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]
    auth_client.post(
        f"/api/trips/{code}/join",
        json={"name": "Bob", "budget": 150},
        content_type="application/json",
    )
    trip = auth_client.get(f"/api/trips/{code}").get_json()
    bob_id = next(c["id"] for c in trip["collaborators"] if c["name"] == "Bob")

    r = auth_client.delete(f"/api/trips/{code}/collaborators/{bob_id}")
    assert r.status_code == 200

    trip2 = auth_client.get(f"/api/trips/{code}").get_json()
    assert len(trip2["collaborators"]) == 1  # Creator remains


def test_move_activity_to_different_day(auth_client):
    """Move an activity from one day to another."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 500,
            "num_people": 1,
            "start_date": "2025-06-10",
            "end_date": "2025-06-12",
            "activity_preferences": "",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]
    days = create.get_json()["days"]
    day1_id, day2_id = days[0]["id"], days[1]["id"]
    a = auth_client.post(
        f"/api/trips/{code}/activities",
        json={"day_id": day1_id, "title": "Day 1 activity"},
        content_type="application/json",
    ).get_json()["activity"]
    r = auth_client.patch(
        f"/api/trips/{code}/activities/{a['id']}/move",
        json={"day_id": day2_id, "order": 0},
        content_type="application/json",
    )
    assert r.status_code == 200
    trip = auth_client.get(f"/api/trips/{code}").get_json()
    acts = trip["activities"]
    assert len(acts) == 1
    assert acts[0]["day_id"] == day2_id
    assert acts[0]["title"] == "Day 1 activity"


def test_reorder_activities(auth_client):
    """Reorder activities within a day."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 500,
            "num_people": 1,
            "start_date": "2025-06-10",
            "end_date": "2025-06-12",
            "activity_preferences": "",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]
    day_id = create.get_json()["days"][0]["id"]
    # Add two activities
    a1 = auth_client.post(
        f"/api/trips/{code}/activities",
        json={"day_id": day_id, "title": "First"},
        content_type="application/json",
    ).get_json()["activity"]
    a2 = auth_client.post(
        f"/api/trips/{code}/activities",
        json={"day_id": day_id, "title": "Second"},
        content_type="application/json",
    ).get_json()["activity"]
    # Reorder: put Second before First
    r = auth_client.patch(
        f"/api/trips/{code}/activities/reorder",
        json={"day_id": day_id, "activity_ids": [a2["id"], a1["id"]]},
        content_type="application/json",
    )
    assert r.status_code == 200
    trip = auth_client.get(f"/api/trips/{code}").get_json()
    acts = [x for x in trip["activities"] if x["day_id"] == day_id]
    assert len(acts) == 2
    assert acts[0]["title"] == "Second"
    assert acts[1]["title"] == "First"


def test_delete_flight(auth_client):
    """Add flight, then remove it."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "LA",
            "per_person_budget": 400,
            "num_people": 1,
            "start_date": "2025-07-01",
            "end_date": "2025-07-05",
            "activity_preferences": "",
            "name": "LA",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]
    add = auth_client.post(
        f"/api/trips/{code}/flights",
        json={
            "origin": "NYC",
            "destination": "LA",
            "departure_date": "2025-07-01",
            "return_date": "2025-07-05",
            "cost_estimate": 350,
        },
        content_type="application/json",
    )
    flight_id = add.get_json()["flight"]["id"]

    r = auth_client.delete(f"/api/trips/{code}/flights/{flight_id}")
    assert r.status_code == 200

    trip = auth_client.get(f"/api/trips/{code}").get_json()
    assert len(trip["flights"]) == 0


def test_ai_suggestions_returns_empty_without_key(auth_client):
    """AI suggestions returns empty lists when no API key (mock)."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]

    r = auth_client.get(f"/api/trips/{code}/suggestions")
    assert r.status_code == 200
    data = r.get_json()
    assert data["flights"] == []
    assert data["hotels"] == []


def test_vote_suggestion(auth_client, app):
    """Vote endpoint: user can vote once; duplicate vote returns same count."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]

    with app.app_context():
        from persistence.sqlite.suggestion_repository import create_many
        from persistence.sqlite.trip_repository import SqliteTripRepository

        trip = SqliteTripRepository().get_by_invite_code(code)
        assert trip is not None
        models = create_many(
            trip.id,
            "flight",
            [{"origin": "JFK", "destination": "MIA", "cost_estimate": "250", "description": "Test"}],
        )
        suggestion_id = models[0].id

    r = auth_client.post(f"/api/trips/{code}/suggestions/{suggestion_id}/vote")
    assert r.status_code == 200
    data = r.get_json()
    assert data["vote_count"] == 1
    assert data["has_voted"] is True

    r2 = auth_client.post(f"/api/trips/{code}/suggestions/{suggestion_id}/vote")
    assert r2.status_code == 200
    assert r2.get_json()["vote_count"] == 1  # Same user cannot vote again


def test_budget_summary_in_api(auth_client):
    """Trip API includes budget_summary with spent vs total. Hotel cost is per night."""
    create = auth_client.post(
        "/api/trips",
        json={
            "origin": "NYC",
            "destination": "Miami",
            "per_person_budget": 500,
            "num_people": 2,
            "start_date": "2025-06-10",
            "end_date": "2025-06-14",
            "activity_preferences": "beach",
            "name": "Miami",
        },
        content_type="application/json",
    )
    code = create.get_json()["invite_code"]
    day_id = create.get_json()["days"][0]["id"]

    # Add flight ($400/person x 2 people = $800) + hotel ($200/night x 4 nights = $800) + activity ($50)
    auth_client.post(
        f"/api/trips/{code}/flights",
        json={
            "origin": "NYC",
            "destination": "MIA",
            "departure_date": "2025-06-10",
            "return_date": "2025-06-14",
            "cost_estimate": 400,
        },
        content_type="application/json",
    )
    auth_client.post(
        f"/api/trips/{code}/hotels",
        json={
            "name": "Beach Hotel",
            "check_in_date": "2025-06-10",
            "check_out_date": "2025-06-14",
            "cost_estimate": 200,  # per night; 4 nights = 800
        },
        content_type="application/json",
    )
    auth_client.post(
        f"/api/trips/{code}/activities",
        json={"day_id": day_id, "title": "Kayaking", "cost_estimate": 50},
        content_type="application/json",
    )

    r = auth_client.get(f"/api/trips/{code}")
    assert r.status_code == 200
    data = r.get_json()
    assert "budget_summary" in data
    b = data["budget_summary"]
    assert b["total_budget"] == "1000.00"  # 500 * 2
    assert b["spent"] == "1650.00"  # (400*2) + (200*4) + 50 = 800 + 800 + 50
    assert b["flights_total"] == "800.00"  # 400/person * 2 people
    assert b["hotels_total"] == "800.00"  # 200/night * 4 nights
    assert b["activities_total"] == "50.00"
    assert b["over_budget"] is True
