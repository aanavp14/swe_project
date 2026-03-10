"""Use-case services. Depend on ports (repositories)."""

from src.services.add_flight import AddFlightResult, AddFlightService
from src.services.add_hotel import AddHotelResult, AddHotelService
from src.services.create_trip import CreateTripResult, CreateTripService
from src.services.get_trip import GetTripService
from src.services.join_trip import JoinTripResult, JoinTripService
from src.services.remove_activity import RemoveActivityResult, RemoveActivityService
from src.services.remove_collaborator import RemoveCollaboratorResult, RemoveCollaboratorService
from src.services.remove_flight import RemoveFlightResult, RemoveFlightService
from src.services.remove_hotel import RemoveHotelResult, RemoveHotelService

__all__ = [
    "AddFlightResult",
    "AddFlightService",
    "AddHotelResult",
    "AddHotelService",
    "CreateTripResult",
    "CreateTripService",
    "GetTripService",
    "JoinTripResult",
    "JoinTripService",
    "RemoveActivityResult",
    "RemoveActivityService",
    "RemoveCollaboratorResult",
    "RemoveCollaboratorService",
    "RemoveFlightResult",
    "RemoveFlightService",
    "RemoveHotelResult",
    "RemoveHotelService",
]
