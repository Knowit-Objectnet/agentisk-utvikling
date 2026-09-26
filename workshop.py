"""Run I Hate Money locally for the workshop.

    uv run flask --app workshop run --debug

The database is a SQLite file next to this script (workshop.db), not /tmp, and
cookies work over plain HTTP so you can log in on http://localhost:5000.
Migrations run on startup. Delete workshop.db to start again from empty.
"""

from pathlib import Path

from ihatemoney.babel_utils import compile_catalogs
from ihatemoney.run import create_app

HERE = Path(__file__).resolve().parent


class WorkshopSettings:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(HERE / 'workshop.db').as_posix()}"
    SECRET_KEY = "workshop-only-not-a-secret"
    SESSION_COOKIE_SECURE = False
    ACTIVATE_DEMO_PROJECT = True
    # Flask-Mail sends nothing while TESTING is on (invites, password reminders).
    TESTING = True


compile_catalogs()
app = create_app(WorkshopSettings)
