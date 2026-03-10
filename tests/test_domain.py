"""
Unit tests for domain classes: Trip, Day, Activity, Collaborator, Flight.

No mocks or I/O; pure logic and data container behavior.
"""

import unittest
from datetime import date
from decimal import Decimal

from src.domain.trip import Activity, Collaborator, Day, Flight, Hotel, Trip


class TestTrip(unittest.TestCase):
    """Five unit tests for Trip."""

    def _trip(self, **kwargs) -> Trip:
        """Build a Trip with sensible defaults."""
        defaults = {
            "id": 1,
            "name": "Test",
            "origin": "NYC",
            "destination": "MIA",
            "per_person_budget": Decimal("500"),
            "num_people": 2,
            "start_date": date(2025, 6, 10),
            "end_date": date(2025, 6, 10),
            "activity_preferences": "beach",
            "invite_code": "ABC123",
        }
        defaults.update(kwargs)
        return Trip(**defaults)

    def test_total_days_single_day(self) -> None:
        """Same start and end date yields 1 day."""
        trip = self._trip(start_date=date(2025, 6, 10), end_date=date(2025, 6, 10))
        self.assertEqual(trip.total_days(), 1)

    def test_total_days_three_days(self) -> None:
        """Trip spanning 3 calendar days returns 3."""
        trip = self._trip(
            start_date=date(2025, 3, 14),
            end_date=date(2025, 3, 16),
        )
        self.assertEqual(trip.total_days(), 3)

    def test_total_days_one_week(self) -> None:
        """Seven-day trip returns 7."""
        trip = self._trip(
            start_date=date(2025, 3, 15),
            end_date=date(2025, 3, 21),
        )
        self.assertEqual(trip.total_days(), 7)

    def test_trip_attributes_stored(self) -> None:
        """All attributes are stored and readable."""
        trip = self._trip(
            id=42,
            name="My Trip",
            origin="LAX",
            destination="Tokyo",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            invite_code="JPN99",
        )
        self.assertEqual(trip.id, 42)
        self.assertEqual(trip.name, "My Trip")
        self.assertEqual(trip.origin, "LAX")
        self.assertEqual(trip.destination, "Tokyo")
        self.assertEqual(trip.start_date, date(2025, 1, 1))
        self.assertEqual(trip.end_date, date(2025, 1, 5))
        self.assertEqual(trip.invite_code, "JPN99")

    def test_trip_equality_by_value(self) -> None:
        """Two trips with same field values are equal (dataclass __eq__)."""
        a = self._trip(id=1, name="Same", destination="NYC", invite_code="SAME")
        b = self._trip(id=1, name="Same", destination="NYC", invite_code="SAME")
        self.assertEqual(a, b)

    def test_total_budget(self) -> None:
        """Total budget is per_person_budget × num_people."""
        trip = self._trip(per_person_budget=Decimal("300"), num_people=4)
        self.assertEqual(trip.total_budget(), Decimal("1200"))


class TestDay(unittest.TestCase):
    """Five unit tests for Day."""

    def test_day_construction_with_ids(self) -> None:
        """Day stores id, trip_id, date, order."""
        d = Day(id=10, trip_id=1, date=date(2025, 7, 4), order=0)
        self.assertEqual(d.id, 10)
        self.assertEqual(d.trip_id, 1)
        self.assertEqual(d.date, date(2025, 7, 4))
        self.assertEqual(d.order, 0)

    def test_day_id_optional(self) -> None:
        """Day can have id=None before persistence."""
        d = Day(id=None, trip_id=1, date=date(2025, 1, 1), order=2)
        self.assertIsNone(d.id)
        self.assertEqual(d.order, 2)

    def test_day_equality(self) -> None:
        """Two days with same values are equal."""
        a = Day(id=1, trip_id=5, date=date(2025, 6, 1), order=0)
        b = Day(id=1, trip_id=5, date=date(2025, 6, 1), order=0)
        self.assertEqual(a, b)

    def test_day_inequality_different_order(self) -> None:
        """Different order makes days unequal."""
        a = Day(id=1, trip_id=1, date=date(2025, 6, 1), order=0)
        b = Day(id=1, trip_id=1, date=date(2025, 6, 1), order=1)
        self.assertNotEqual(a, b)

    def test_day_date_and_trip_id_independent(self) -> None:
        """date and trip_id can be any valid values."""
        d = Day(id=99, trip_id=100, date=date(2024, 12, 31), order=10)
        self.assertEqual(d.trip_id, 100)
        self.assertEqual(d.date, date(2024, 12, 31))
        self.assertEqual(d.order, 10)


class TestActivity(unittest.TestCase):
    """Five unit tests for Activity."""

    def test_activity_all_fields(self) -> None:
        """Activity stores id, day_id, title, time, cost_estimate, order."""
        a = Activity(
            id=1,
            day_id=5,
            title="Beach",
            time="10:00",
            cost_estimate=Decimal("25.50"),
            order=0,
        )
        self.assertEqual(a.id, 1)
        self.assertEqual(a.day_id, 5)
        self.assertEqual(a.title, "Beach")
        self.assertEqual(a.time, "10:00")
        self.assertEqual(a.cost_estimate, Decimal("25.50"))
        self.assertEqual(a.order, 0)

    def test_activity_optional_time_and_cost(self) -> None:
        """time and cost_estimate can be None."""
        a = Activity(
            id=None,
            day_id=1,
            title="Free walk",
            time=None,
            cost_estimate=None,
            order=2,
        )
        self.assertIsNone(a.time)
        self.assertIsNone(a.cost_estimate)
        self.assertIsNone(a.id)

    def test_activity_equality(self) -> None:
        """Two activities with same values are equal."""
        a = Activity(
            id=1, day_id=1, title="Lunch", time="12:00",
            cost_estimate=Decimal("15"), order=0,
        )
        b = Activity(
            id=1, day_id=1, title="Lunch", time="12:00",
            cost_estimate=Decimal("15"), order=0,
        )
        self.assertEqual(a, b)

    def test_activity_zero_cost(self) -> None:
        """cost_estimate can be zero."""
        a = Activity(
            id=1,
            day_id=1,
            title="Free museum",
            time="09:00",
            cost_estimate=Decimal("0"),
            order=0,
        )
        self.assertEqual(a.cost_estimate, Decimal("0"))

    def test_activity_order_arbitrary(self) -> None:
        """order can be any integer for ordering."""
        a = Activity(
            id=1, day_id=1, title="First", time=None, cost_estimate=None, order=0,
        )
        b = Activity(
            id=2, day_id=1, title="Second", time=None, cost_estimate=None, order=1,
        )
        self.assertLess(a.order, b.order)


class TestCollaborator(unittest.TestCase):
    """Five unit tests for Collaborator."""

    def test_collaborator_attributes(self) -> None:
        """Collaborator stores id, trip_id, name, budget."""
        c = Collaborator(
            id=1,
            trip_id=10,
            name="Alice",
            budget=Decimal("500.00"),
        )
        self.assertEqual(c.id, 1)
        self.assertEqual(c.trip_id, 10)
        self.assertEqual(c.name, "Alice")
        self.assertEqual(c.budget, Decimal("500.00"))

    def test_collaborator_id_optional(self) -> None:
        """id can be None before persistence."""
        c = Collaborator(id=None, trip_id=1, name="Bob", budget=Decimal("0"))
        self.assertIsNone(c.id)
        self.assertEqual(c.name, "Bob")

    def test_collaborator_equality(self) -> None:
        """Two collaborators with same values are equal."""
        a = Collaborator(id=1, trip_id=1, name="Carol", budget=Decimal("100"))
        b = Collaborator(id=1, trip_id=1, name="Carol", budget=Decimal("100"))
        self.assertEqual(a, b)

    def test_collaborator_zero_budget(self) -> None:
        """budget can be zero."""
        c = Collaborator(id=1, trip_id=1, name="Dave", budget=Decimal("0"))
        self.assertEqual(c.budget, Decimal("0"))

    def test_collaborator_different_trips(self) -> None:
        """Same name on different trip_id are different collaborators."""
        a = Collaborator(id=1, trip_id=1, name="Eve", budget=Decimal("50"))
        b = Collaborator(id=2, trip_id=2, name="Eve", budget=Decimal("50"))
        self.assertNotEqual(a, b)
        self.assertEqual(a.name, b.name)


class TestFlight(unittest.TestCase):
    """Five unit tests for Flight."""

    def test_flight_attributes(self) -> None:
        """Flight stores id, trip_id, origin, destination, dates, cost_estimate."""
        f = Flight(
            id=1,
            trip_id=10,
            origin="JFK",
            destination="LAX",
            departure_date=date(2025, 7, 1),
            return_date=date(2025, 7, 15),
            cost_estimate=Decimal("350.00"),
        )
        self.assertEqual(f.id, 1)
        self.assertEqual(f.trip_id, 10)
        self.assertEqual(f.origin, "JFK")
        self.assertEqual(f.destination, "LAX")
        self.assertEqual(f.departure_date, date(2025, 7, 1))
        self.assertEqual(f.return_date, date(2025, 7, 15))
        self.assertEqual(f.cost_estimate, Decimal("350.00"))

    def test_flight_id_optional(self) -> None:
        """id can be None before persistence."""
        f = Flight(
            id=None,
            trip_id=1,
            origin="BOS",
            destination="MIA",
            departure_date=date(2025, 3, 1),
            return_date=date(2025, 3, 8),
            cost_estimate=Decimal("200"),
        )
        self.assertIsNone(f.id)
        self.assertEqual(f.origin, "BOS")

    def test_flight_equality(self) -> None:
        """Two flights with same values are equal."""
        a = Flight(
            id=1,
            trip_id=1,
            origin="ORD",
            destination="DEN",
            departure_date=date(2025, 6, 1),
            return_date=date(2025, 6, 7),
            cost_estimate=Decimal("180"),
        )
        b = Flight(
            id=1,
            trip_id=1,
            origin="ORD",
            destination="DEN",
            departure_date=date(2025, 6, 1),
            return_date=date(2025, 6, 7),
            cost_estimate=Decimal("180"),
        )
        self.assertEqual(a, b)

    def test_flight_zero_cost_estimate(self) -> None:
        """cost_estimate can be zero (e.g. points redemption)."""
        f = Flight(
            id=1,
            trip_id=1,
            origin="SFO",
            destination="HNL",
            departure_date=date(2025, 8, 1),
            return_date=date(2025, 8, 10),
            cost_estimate=Decimal("0"),
        )
        self.assertEqual(f.cost_estimate, Decimal("0"))

    def test_flight_different_trips_unequal(self) -> None:
        """Same route on different trip_id are different flights."""
        a = Flight(
            id=1,
            trip_id=1,
            origin="ATL",
            destination="MCO",
            departure_date=date(2025, 5, 1),
            return_date=date(2025, 5, 5),
            cost_estimate=Decimal("100"),
        )
        b = Flight(
            id=2,
            trip_id=2,
            origin="ATL",
            destination="MCO",
            departure_date=date(2025, 5, 1),
            return_date=date(2025, 5, 5),
            cost_estimate=Decimal("100"),
        )
        self.assertNotEqual(a, b)
        self.assertEqual(a.origin, b.origin)
        self.assertEqual(a.destination, b.destination)

    def test_flight_optional_departure_time_and_link(self) -> None:
        """Flight departure_time and link are optional."""
        f = Flight(
            id=1,
            trip_id=1,
            origin="JFK",
            destination="LAX",
            departure_date=date(2025, 7, 1),
            return_date=date(2025, 7, 15),
            cost_estimate=Decimal("350"),
            departure_time="10:00 AM",
            link="https://google.com/flights",
        )
        self.assertEqual(f.departure_time, "10:00 AM")
        self.assertEqual(f.link, "https://google.com/flights")


class TestHotel(unittest.TestCase):
    """Unit tests for Hotel."""

    def test_hotel_attributes(self) -> None:
        """Hotel stores id, trip_id, name, dates, cost_estimate."""
        h = Hotel(
            id=1,
            trip_id=10,
            name="Beach Resort",
            check_in_date=date(2025, 7, 1),
            check_out_date=date(2025, 7, 5),
            cost_estimate=Decimal("800.00"),
        )
        self.assertEqual(h.id, 1)
        self.assertEqual(h.trip_id, 10)
        self.assertEqual(h.name, "Beach Resort")
        self.assertEqual(h.check_in_date, date(2025, 7, 1))
        self.assertEqual(h.check_out_date, date(2025, 7, 5))
        self.assertEqual(h.cost_estimate, Decimal("800.00"))

    def test_hotel_optional_link(self) -> None:
        """Hotel link defaults to None, can be set."""
        h = Hotel(
            id=1,
            trip_id=1,
            name="Budget Inn",
            check_in_date=date(2025, 1, 1),
            check_out_date=date(2025, 1, 3),
            cost_estimate=Decimal("150"),
            link="https://example.com/hotel",
        )
        self.assertEqual(h.link, "https://example.com/hotel")

    def test_hotel_id_optional(self) -> None:
        """id can be None before persistence."""
        h = Hotel(
            id=None,
            trip_id=1,
            name="New Hotel",
            check_in_date=date(2025, 6, 1),
            check_out_date=date(2025, 6, 7),
            cost_estimate=Decimal("500"),
        )
        self.assertIsNone(h.id)

    def test_hotel_equality(self) -> None:
        """Two hotels with same values are equal."""
        a = Hotel(
            id=1, trip_id=1, name="Same Inn",
            check_in_date=date(2025, 6, 1), check_out_date=date(2025, 6, 5),
            cost_estimate=Decimal("200"),
        )
        b = Hotel(
            id=1, trip_id=1, name="Same Inn",
            check_in_date=date(2025, 6, 1), check_out_date=date(2025, 6, 5),
            cost_estimate=Decimal("200"),
        )
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
