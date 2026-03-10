"""
Service integration tests.

Tests use cases with real SQLite repositories (in-memory). No HTTP layer.
"""

import pytest
from datetime import date
from decimal import Decimal

from persistence.sqlite.activity_repository import SqliteActivityRepository
from persistence.sqlite.collaborator_repository import SqliteCollaboratorRepository
from persistence.sqlite.flight_hotel_repository import SqliteFlightRepository, SqliteHotelRepository
from persistence.sqlite.models import db
from persistence.sqlite.trip_repository import SqliteDayRepository, SqliteTripRepository
from src.domain.trip import Activity, Collaborator, Day, Flight, Hotel, Trip
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

from tests.conftest import FakeInviteCodeGenerator


@pytest.fixture
def repos(app):
    """Create repositories with app context and fresh DB."""
    with app.app_context():
        db.create_all()
        trip_repo = SqliteTripRepository()
        day_repo = SqliteDayRepository()
        collaborator_repo = SqliteCollaboratorRepository()
        flight_repo = SqliteFlightRepository()
        hotel_repo = SqliteHotelRepository()
        activity_repo = SqliteActivityRepository()
        yield {
            "trip": trip_repo,
            "day": day_repo,
            "collaborator": collaborator_repo,
            "flight": flight_repo,
            "hotel": hotel_repo,
            "activity": activity_repo,
        }
        db.session.remove()
        db.drop_all()


@pytest.fixture
def create_trip_svc(repos):
    """CreateTripService with fake invite generator."""
    return CreateTripService(
        trip_repo=repos["trip"],
        day_repo=repos["day"],
        invite_code_generator=FakeInviteCodeGenerator("ABC123"),
    )


@pytest.fixture
def get_trip_svc(repos):
    """GetTripService."""
    return GetTripService(
        trip_repo=repos["trip"],
        day_repo=repos["day"],
        collaborator_repo=repos["collaborator"],
        flight_repo=repos["flight"],
        hotel_repo=repos["hotel"],
        activity_repo=repos["activity"],
    )


def test_create_trip_service(create_trip_svc, get_trip_svc):
    """CreateTripService creates trip and days."""
    result = create_trip_svc.execute(
        origin="NYC",
        destination="Miami",
        per_person_budget=Decimal("500"),
        num_people=2,
        start_date=date(2025, 6, 10),
        end_date=date(2025, 6, 14),
        activity_preferences="beach",
        name="Beach Trip",
    )
    assert result.trip.id is not None
    assert result.trip.invite_code == "ABC123"
    assert result.trip.origin == "NYC"
    assert len(result.days) == 5

    loaded = get_trip_svc.execute("ABC123")
    assert loaded is not None
    assert loaded.trip.name == "Beach Trip"
    assert len(loaded.days) == 5


def test_create_trip_invalid_dates(create_trip_svc):
    """CreateTripService raises ValueError for end_date < start_date."""
    with pytest.raises(ValueError, match="end_date"):
        create_trip_svc.execute(
            origin="NYC",
            destination="Miami",
            per_person_budget=Decimal("500"),
            num_people=2,
            start_date=date(2025, 6, 14),
            end_date=date(2025, 6, 10),
            activity_preferences="",
            name="Bad",
        )


def test_join_trip_service(create_trip_svc, get_trip_svc, repos):
    """JoinTripService adds collaborator."""
    create_trip_svc.execute(
        origin="NYC",
        destination="Boston",
        per_person_budget=Decimal("200"),
        num_people=1,
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 3),
        activity_preferences="",
        name="Boston",
    )
    join_svc = JoinTripService(
        trip_repo=repos["trip"],
        collaborator_repo=repos["collaborator"],
    )
    result = join_svc.execute(
        invite_code="ABC123",
        name="Alice",
        budget=Decimal("250"),
    )
    assert result.collaborator.id is not None
    assert result.collaborator.name == "Alice"

    loaded = get_trip_svc.execute("ABC123")
    assert len(loaded.collaborators) == 1
    assert loaded.collaborators[0].name == "Alice"


def test_join_trip_not_found(repos):
    """JoinTripService raises ValueError for unknown invite code."""
    join_svc = JoinTripService(
        trip_repo=repos["trip"],
        collaborator_repo=repos["collaborator"],
    )
    with pytest.raises(ValueError, match="Trip not found"):
        join_svc.execute(
            invite_code="NOSUCH",
            name="Bob",
            budget=Decimal("100"),
        )


def test_add_flight_service(create_trip_svc, get_trip_svc, repos):
    """AddFlightService adds flight to trip."""
    create_trip_svc.execute(
        origin="JFK",
        destination="LHR",
        per_person_budget=Decimal("1000"),
        num_people=1,
        start_date=date(2025, 9, 1),
        end_date=date(2025, 9, 10),
        activity_preferences="",
        name="London",
    )
    add_flight = AddFlightService(
        trip_repo=repos["trip"],
        flight_repo=repos["flight"],
    )
    result = add_flight.execute(
        invite_code="ABC123",
        origin="JFK",
        destination="LHR",
        departure_date=date(2025, 9, 1),
        return_date=date(2025, 9, 10),
        cost_estimate=Decimal("650"),
    )
    assert result.flight.id is not None
    assert result.flight.cost_estimate == Decimal("650")

    loaded = get_trip_svc.execute("ABC123")
    assert len(loaded.flights) == 1
    assert loaded.flights[0].origin == "JFK"


def test_add_hotel_service(create_trip_svc, get_trip_svc, repos):
    """AddHotelService adds hotel to trip."""
    create_trip_svc.execute(
        origin="NYC",
        destination="Miami",
        per_person_budget=Decimal("800"),
        num_people=2,
        start_date=date(2025, 6, 10),
        end_date=date(2025, 6, 14),
        activity_preferences="",
        name="Miami",
    )
    add_hotel = AddHotelService(
        trip_repo=repos["trip"],
        hotel_repo=repos["hotel"],
    )
    result = add_hotel.execute(
        invite_code="ABC123",
        name="Beach Resort",
        check_in_date=date(2025, 6, 10),
        check_out_date=date(2025, 6, 14),
        cost_estimate=Decimal("1200"),
    )
    assert result.hotel.id is not None
    assert result.hotel.name == "Beach Resort"

    loaded = get_trip_svc.execute("ABC123")
    assert len(loaded.hotels) == 1


def test_add_activity_service(create_trip_svc, get_trip_svc, repos):
    """AddActivityService adds activity to day."""
    result = create_trip_svc.execute(
        origin="NYC",
        destination="Miami",
        per_person_budget=Decimal("500"),
        num_people=1,
        start_date=date(2025, 6, 10),
        end_date=date(2025, 6, 12),
        activity_preferences="",
        name="Miami",
    )
    day_id = result.days[0].id

    add_activity = AddActivityService(
        trip_repo=repos["trip"],
        day_repo=repos["day"],
        activity_repo=repos["activity"],
    )
    add_result = add_activity.execute(
        invite_code="ABC123",
        day_id=day_id,
        title="Beach volleyball",
        time="14:00",
        cost_estimate=Decimal("0"),
    )
    assert add_result is not None
    assert add_result.activity.title == "Beach volleyball"

    loaded = get_trip_svc.execute("ABC123")
    assert len(loaded.activities) == 1
    assert loaded.activities[0].title == "Beach volleyball"


def test_remove_flight_service(create_trip_svc, get_trip_svc, repos):
    """RemoveFlightService removes flight."""
    create_trip_svc.execute(
        origin="NYC",
        destination="LA",
        per_person_budget=Decimal("400"),
        num_people=1,
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 5),
        activity_preferences="",
        name="LA",
    )
    add_flight = AddFlightService(
        trip_repo=repos["trip"],
        flight_repo=repos["flight"],
    )
    add_flight.execute(
        invite_code="ABC123",
        origin="NYC",
        destination="LA",
        departure_date=date(2025, 7, 1),
        return_date=date(2025, 7, 5),
        cost_estimate=Decimal("350"),
    )

    remove_flight = RemoveFlightService(
        trip_repo=repos["trip"],
        flight_repo=repos["flight"],
    )
    loaded_before = get_trip_svc.execute("ABC123")
    flight_id = loaded_before.flights[0].id

    remove_flight.execute(invite_code="ABC123", flight_id=flight_id)

    loaded_after = get_trip_svc.execute("ABC123")
    assert len(loaded_after.flights) == 0
