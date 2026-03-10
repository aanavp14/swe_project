# RoadMapper

RoadMapper is a collaborative trip planner that helps groups organize flights, hotels, and daily activities in one place. Create a trip, share an invite link, and everyone can add their budget, save AI-suggested options, and build the itinerary together.  

## Features

- **Create trips** — Log in to create trips; enter origin, destination, dates, per-person budget, and activity preferences
- **User accounts** — Sign up and log in; your trips are linked to your account
- **Invite collaborators** — Share a link; friends add their name and budget (no account needed)
- **Flights & hotels** — Add manually or get AI suggestions with real search links (Google Flights, Kayak, Booking.com)
- **Daily itinerary** — Day-by-day activities with times and costs; drag-and-drop to reorder or move between days; AI can suggest activities by query
- **Budget tracker** — See total spent (flights + hotels + activities) vs budget; over-budget warnings
- **Printable itinerary** — Generate a PDF-ready summary with flights, hotels, activities, and traveler info

## Tech Stack

- **Backend:** Flask, Pydantic (request validation)
- **Database:** SQLite (Flask-SQLAlchemy)
- **AI:** OpenAI with web search (optional; app works without it)
- **Frontend:** HTML, Tailwind CSS, vanilla JavaScript

## Setup

1. **Clone and install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables** (optional)

   Create a `.env` file in the project root:

   | Variable | Description |
   |----------|-------------|
   | `OPENAI_API_KEY` | OpenAI API key for AI suggestions (flights, hotels, activities). Omit to run without AI. |
   | `DATABASE_URI` | SQLite URI (default: `sqlite:///itinerary.db`) |
   | `BASE_URL` | Base URL for invite links (e.g. `http://localhost:5001`). If unset, links use the request host. |
   | `SECRET_KEY` | Secret key for session cookies (required for login). Omit to use a default dev key; set a strong value in production. |

3. **Run migrations** (for file-based DB; tests use in-memory and skip this)
   ```bash
   alembic upgrade head
   ```
   Or start the app—it runs migrations automatically.

4. **Run the app**
   ```bash
   python main.py
   ```
   Open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser.

## Project Structure

```
├── alembic.ini         # Alembic config
├── app.py              # Composition root: wires DB, repos, services, routes
├── main.py             # Entry point (runs on port 5001)
├── migrations/         # Alembic schema migrations
├── src/
│   ├── domain/         # Trip, Day, Activity, Collaborator, Flight, Hotel
│   ├── ports/          # Repository and AI interfaces
│   └── services/       # Use cases (create trip, add flight, join, etc.)
├── persistence/
│   ├── sqlite/         # DB models and repository implementations
│   └── ai/             # OpenAI and mock suggestion implementations
├── web/routes/         # Flask routes (thin HTTP layer)
├── templates/          # Jinja HTML templates
└── static/             # CSS, JS
```

## Testing

```bash
pytest tests/ -v
```

- **Unit tests** (`test_domain.py`): Domain entities (Trip, Day, Activity, Collaborator, Flight, Hotel).
- **Integration tests** (`test_services.py`): Use cases with real SQLite repositories.
- **API tests** (`test_api.py`): HTTP endpoints via Flask test client (create trip, join, add/remove flights/hotels/activities, budget summary).

## License

MIT
