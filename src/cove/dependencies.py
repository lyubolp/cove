"""Database engine and session dependency for the Cove application."""

from sqlmodel import Session, create_engine

engine = create_engine("sqlite:///database.db")


def get_session():
    """Yield a SQLModel session, closing it automatically when the request is done."""
    with Session(engine) as session:
        yield session
