"""Database engine and session dependency for the Cove application."""

import os

from sqlmodel import Session, create_engine

engine = create_engine(f"sqlite:///{os.environ.get('COVE_DB_PATH', 'database.db')}")


def get_session():
    """Yield a SQLModel session, closing it automatically when the request is done."""
    with Session(engine) as session:
        yield session
