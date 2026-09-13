"""
Database connection setup.

Creates the SQLAlchemy engine + session that every part of the backend
(API routes, services) will import to talk to the database.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/hr_advisor.db")

# check_same_thread=False is required for SQLite when used with FastAPI,
# since FastAPI can handle a request in a different thread than it was created in.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

if DATABASE_URL.startswith("sqlite"):
    # SQLite ignores foreign key constraints (and ON DELETE CASCADE) unless
    # this pragma is turned on for every connection. Without it, the
    # cascade="all, delete-orphan" / ondelete="CASCADE" settings in
    # database/models.py would silently do nothing.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
