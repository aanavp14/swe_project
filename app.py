"""
Smart Vacation Itinerary Planner — Flask application.

Composition root: wires together the database, repositories, services, and routes.
All dependencies are injected here so services stay testable and decoupled.
"""
import logging
import os

from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (where app.py lives) so it works regardless of cwd
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

logging.basicConfig(level=logging.INFO)

from datetime import datetime as dt
from typing import Optional

from flask import Flask, jsonify, redirect, render_template, url_for
from flask_login import LoginManager, current_user, login_required

from persistence.ai.mock_suggestions import MockAISuggestionsService
from persistence.ai.openai_suggestions import OpenAISuggestionsService
from persistence.invite_code import RandomInviteCodeGenerator
from persistence.sqlite.activity_repository import SqliteActivityRepository
from persistence.sqlite.collaborator_repository import SqliteCollaboratorRepository
from persistence.sqlite.flight_hotel_repository import (
    SqliteFlightRepository,
    SqliteHotelRepository,
)
from persistence.sqlite.models import db
from persistence.sqlite.trip_repository import SqliteDayRepository, SqliteTripRepository
from src.services.add_activity import AddActivityService
from src.services.add_flight import AddFlightService
from src.services.add_hotel import AddHotelService
from src.services.create_trip import CreateTripService
from src.services.get_trip import GetTripService
from src.services.join_trip import JoinTripService
from src.services.leave_trip import LeaveTripService
from src.services.remove_activity import RemoveActivityService
from src.services.reorder_activities import ReorderActivitiesService
from src.services.move_activity import MoveActivityService
from src.services.remove_collaborator import RemoveCollaboratorService
from src.services.remove_trip import RemoveTripService
from src.services.remove_flight import RemoveFlightService
from src.services.remove_hotel import RemoveHotelService
from src.services.update_trip_description import UpdateTripDescriptionService
from persistence.sqlite.models import UserModel
from persistence.sqlite.trip_repository import SqliteTripRepository
from web.routes.auth import bp as auth_bp
from web.routes.trips import create_trips_blueprint
from flask_socketio import SocketIO, emit, join_room, leave_room


socketio = SocketIO(cors_allowed_origins="*")

def _run_migrations(app: Flask) -> None:
    """Apply Alembic migrations for file-based DBs. Use create_all for in-memory (tests)."""
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if ":memory:" in uri:
        db.create_all()
        return
    # Flask-SQLAlchemy resolves relative SQLite paths to instance_path. Match that for Alembic.
    if uri.startswith("sqlite:///") and not uri.startswith("sqlite:////"):
        db_name = uri.replace("sqlite:///", "").split("?")[0]
        if not os.path.isabs(db_name):
            uri = "sqlite:///" + str(Path(app.instance_path) / db_name)
    import subprocess
    env = os.environ.copy()
    env["DATABASE_URI"] = uri
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parent,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic upgrade failed: {result.stderr}")


def create_app() -> Flask:
    """
    Create and configure the Flask app with dependencies injected.

    Order: create app → init DB → create repos → create services → register routes.
    """
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    # SQLite DB lives in instance/ folder (or project root if instance doesn't exist)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URI", "sqlite:///itinerary.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # BASE_URL for generated links (e.g. http://127.0.0.1:5001). If set, invite links use this instead of request host.
    app.config["BASE_URL"] = os.environ.get("BASE_URL", "").rstrip("/") or None
    # Secret key for session cookies (Flask-Login). Use env in production.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    db.init_app(app)
    socketio.init_app(app)
    with app.app_context():
        _run_migrations(app)

    # Repositories handle all DB access (I/O at the edges)
    trip_repo = SqliteTripRepository()
    day_repo = SqliteDayRepository()
    collaborator_repo = SqliteCollaboratorRepository()
    flight_repo = SqliteFlightRepository()
    hotel_repo = SqliteHotelRepository()
    activity_repo = SqliteActivityRepository()
    invite_gen = RandomInviteCodeGenerator()

    # Services contain use-case logic; they depend on abstractions (ports), not DB directly
    create_trip_service = CreateTripService(
        trip_repo=trip_repo,
        day_repo=day_repo,
        invite_code_generator=invite_gen,
    )
    get_trip_service = GetTripService(
        trip_repo=trip_repo,
        day_repo=day_repo,
        collaborator_repo=collaborator_repo,
        flight_repo=flight_repo,
        hotel_repo=hotel_repo,
        activity_repo=activity_repo,
    )
    join_trip_service = JoinTripService(
        trip_repo=trip_repo,
        collaborator_repo=collaborator_repo,
    )
    add_flight_service = AddFlightService(trip_repo=trip_repo, flight_repo=flight_repo)
    add_hotel_service = AddHotelService(trip_repo=trip_repo, hotel_repo=hotel_repo)
    add_activity_service = AddActivityService(
        trip_repo=trip_repo,
        day_repo=day_repo,
        activity_repo=activity_repo,
    )
    remove_collaborator_service = RemoveCollaboratorService(
        trip_repo=trip_repo, collaborator_repo=collaborator_repo
    )
    leave_trip_service = LeaveTripService(
        trip_repo=trip_repo, collaborator_repo=collaborator_repo
    )
    remove_trip_service = RemoveTripService(trip_repo=trip_repo)
    remove_flight_service = RemoveFlightService(trip_repo=trip_repo, flight_repo=flight_repo)
    remove_hotel_service = RemoveHotelService(trip_repo=trip_repo, hotel_repo=hotel_repo)
    remove_activity_service = RemoveActivityService(trip_repo=trip_repo, activity_repo=activity_repo)
    reorder_activities_service = ReorderActivitiesService(
        trip_repo=trip_repo,
        day_repo=day_repo,
        activity_repo=activity_repo,
    )
    move_activity_service = MoveActivityService(
        trip_repo=trip_repo,
        day_repo=day_repo,
        activity_repo=activity_repo,
    )
    update_trip_description_service = UpdateTripDescriptionService(trip_repo=trip_repo)

    # AI suggestions: OpenAI when key set, else mock
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini-search-preview")
    ai_suggestions_service = (
        OpenAISuggestionsService(api_key=api_key, model=model) if api_key else MockAISuggestionsService()
    )

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None
        return UserModel.query.get(uid)

    app.register_blueprint(auth_bp)
    app.register_blueprint(
        create_trips_blueprint(
            create_trip_service,
            get_trip_service,
            join_trip_service,
            collaborator_repo,
            add_flight_service,
            add_hotel_service,
            add_activity_service,
            remove_collaborator_service,
            leave_trip_service,
            remove_trip_service,
            remove_flight_service,
            remove_hotel_service,
            remove_activity_service,
            reorder_activities_service,
            move_activity_service,
            update_trip_description_service,
            ai_suggestions_service=ai_suggestions_service,
        )
    )

    # --- Routes for health check and home page ---
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "RoadMapper API is running"})

    @app.route("/api/ai-status")
    def ai_status():
        """Check if AI is configured. Use a real trip and 'Get AI suggestions' to verify web search."""
        api_key = os.environ.get("OPENAI_API_KEY")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini-search-preview")
        return jsonify({
            "configured": bool(api_key),
            "model": model if api_key else None,
            "message": "AI configured. Create a trip and click 'Get AI suggestions' to test web search."
                if api_key else "Add OPENAI_API_KEY to .env for AI suggestions.",
        }), 200

    @app.route("/api/ai-verify")
    def ai_verify():
        """Make a tiny OpenAI call to verify the key works and show token usage. Check Usage in your OpenAI dashboard after calling this."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "OPENAI_API_KEY not set in .env"}), 400
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say 'ok' in 1 word."}],
                max_tokens=5,
            )
            usage = getattr(r, "usage", None)
            return jsonify({
                "ok": True,
                "key_prefix": api_key[:12] + "..." if len(api_key) > 12 else "(short)",
                "usage": {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                } if usage else None,
                "message": "API works. Check Usage in platform.openai.com (may take a few minutes to appear).",
            }), 200
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/create")
    @login_required
    def create_page():
        return render_template("create-trip.html")

    @app.route("/my-trips")
    @login_required
    def my_trips():
        trip_repo = SqliteTripRepository()
        created = trip_repo.get_by_owner_id(current_user.id)
        joined = trip_repo.get_by_collaborator_user_id(current_user.id)
        return render_template(
            "my-trips.html",
            created_trips=created,
            joined_trips=joined,
        )


    # SocketIO events for Real-Time Chat
    @socketio.on("join_trip")
    def on_join(data):
        if not current_user.is_authenticated:
            return
        invite_code = data.get("invite_code")
        if not invite_code:
            return

        # Verify user is part of trip
        trip_repo = SqliteTripRepository()
        trip = trip_repo.get_by_invite_code(invite_code)
        if not trip:
            return

        is_owner = trip.owner_id == current_user.id
        is_collaborator = any(c.user_id == current_user.id for c in trip.collaborators)

        if not (is_owner or is_collaborator):
            return

        join_room(invite_code)

    @socketio.on("leave_trip")
    def on_leave(data):
        if not current_user.is_authenticated:
            return
        invite_code = data.get("invite_code")
        if not invite_code:
            return
        leave_room(invite_code)

    @socketio.on("send_message")
    def on_send_message(data):
        if not current_user.is_authenticated:
            return

        invite_code = data.get("invite_code")
        message = data.get("message")

        if not invite_code or not message:
            return

        # Verify user is part of trip
        trip_repo = SqliteTripRepository()
        trip = trip_repo.get_by_invite_code(invite_code)
        if not trip:
            return

        is_owner = trip.owner_id == current_user.id
        is_collaborator = any(c.user_id == current_user.id for c in trip.collaborators)

        if not (is_owner or is_collaborator):
            return

        # Use user's real name instead of relying on client data
        user_name = current_user.display_name or current_user.email

        emit("receive_message", {
            "user_name": user_name,
            "message": message,
            "timestamp": dt.utcnow().isoformat()
        }, to=invite_code, room=invite_code)
    return app


app = create_app()


def _format_activity_time(value: Optional[str]) -> str:
    """Format ISO time (e.g. 2026-03-07T23:00:00) as 11:00 PM."""
    if not value or not isinstance(value, str):
        return ""
    s = value.strip()
    if "T" in s:
        try:
            d = dt.fromisoformat(s.replace("Z", "+00:00"))
            return d.strftime("%I:%M %p").lstrip("0")
        except (ValueError, TypeError):
            pass
    return s


app.jinja_env.filters["format_time"] = _format_activity_time

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
