"""
Database configuration module.
This file establishes the connection with the SQLite database
and defines the session management for data access.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./uber_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """ Generator function to create a new database session. Used as a dependency in API routes. """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
