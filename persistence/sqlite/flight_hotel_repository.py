"""
SQLite implementation of FlightRepository and HotelRepository.

Converts between domain Flight/Hotel and SQLAlchemy models.
"""

from decimal import Decimal

from src.domain.trip import Flight, Hotel

from persistence.sqlite.models import FlightModel, HotelModel, db


class SqliteFlightRepository:
    """FlightRepository implementation using SQLite."""

    def create(self, flight: Flight) -> Flight:
        """Save flight to DB and return it with id set."""
        model = FlightModel(
            trip_id=flight.trip_id,
            origin=flight.origin,
            destination=flight.destination,
            departure_date=flight.departure_date,
            return_date=flight.return_date,
            cost_estimate=flight.cost_estimate,
            departure_time=flight.departure_time or None,
            link=flight.link or None,
        )
        db.session.add(model)
        db.session.commit()
        return Flight(
            id=model.id,
            trip_id=model.trip_id,
            origin=model.origin,
            destination=model.destination,
            departure_date=model.departure_date,
            return_date=model.return_date,
            cost_estimate=Decimal(str(model.cost_estimate)),
            departure_time=model.departure_time,
            link=getattr(model, "link", None),
        )

    def get_by_trip_id(self, trip_id: int) -> list[Flight]:
        """Load all flights for a trip."""
        models = FlightModel.query.filter_by(trip_id=trip_id).all()
        return [
            Flight(
                id=m.id,
                trip_id=m.trip_id,
                origin=m.origin,
                destination=m.destination,
                departure_date=m.departure_date,
                return_date=m.return_date,
                cost_estimate=Decimal(str(m.cost_estimate)),
                departure_time=getattr(m, "departure_time", None),
                link=getattr(m, "link", None),
            )
            for m in models
        ]

    def delete_by_id(self, flight_id: int) -> bool:
        """Delete one flight by id."""
        model = FlightModel.query.get(flight_id)
        if model is None:
            return False
        db.session.delete(model)
        db.session.commit()
        return True


class SqliteHotelRepository:
    """HotelRepository implementation using SQLite."""

    def create(self, hotel: Hotel) -> Hotel:
        """Save hotel to DB and return it with id set."""
        model = HotelModel(
            trip_id=hotel.trip_id,
            name=hotel.name,
            check_in_date=hotel.check_in_date,
            check_out_date=hotel.check_out_date,
            cost_estimate=hotel.cost_estimate,
            link=hotel.link or None,
        )
        db.session.add(model)
        db.session.commit()
        return Hotel(
            id=model.id,
            trip_id=model.trip_id,
            name=model.name,
            check_in_date=model.check_in_date,
            check_out_date=model.check_out_date,
            cost_estimate=Decimal(str(model.cost_estimate)),
            link=getattr(model, "link", None),
        )

    def get_by_trip_id(self, trip_id: int) -> list[Hotel]:
        """Load all hotels for a trip."""
        models = HotelModel.query.filter_by(trip_id=trip_id).all()
        return [
            Hotel(
                id=m.id,
                trip_id=m.trip_id,
                name=m.name,
                check_in_date=m.check_in_date,
                check_out_date=m.check_out_date,
                cost_estimate=Decimal(str(m.cost_estimate)),
                link=getattr(m, "link", None),
            )
            for m in models
        ]

    def delete_by_id(self, hotel_id: int) -> bool:
        """Delete one hotel by id."""
        model = HotelModel.query.get(hotel_id)
        if model is None:
            return False
        db.session.delete(model)
        db.session.commit()
        return True
