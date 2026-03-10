"""
Main entry point for the Smart Vacation Itinerary Planner.

Run with: python main.py
Then open http://127.0.0.1:5001 in your browser.

Note: Uses port 5001 because macOS AirPlay Receiver often uses port 5000.
"""

from app import app


def main() -> None:
    """Run the Flask web server on port 5001."""
    app.run(debug=True, port=5001)


if __name__ == "__main__":
    main()
