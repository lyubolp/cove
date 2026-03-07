from typing import Annotated

import pytest
from fastapi import Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from cove.dependencies import get_session

# Import all models so SQLModel.metadata is fully populated before create_all
from cove.models.api_keys import APIKey
from cove.models.config_item import KeyValue
from cove.models.projects import Project, ProjectUserLink
from cove.models.users import User
from cove.services.auth.api_keys import get_api_key_hash
from cove.services.auth.oauth2 import (
    does_user_have_access_to_project,
    get_current_user,
    get_current_user_non_fatal,
    get_current_user_with_project_access,
)
from main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


def _seed_db(session):
    """Seed projects, items, users, links and API keys into *session*.

    Returns a dict with all IDs and objects needed by tests.
    Works with any session (session-scoped or function-scoped).
    """
    # Projects
    foo = Project(name="Foo", is_public=True)
    bar = Project(name="Bar", is_public=False)
    session.add(foo)
    session.add(bar)
    session.flush()

    # Items
    first = KeyValue(project_id=foo.id, key="first", value="1")
    second = KeyValue(project_id=foo.id, key="second", value="2")
    third = KeyValue(project_id=bar.id, key="third", value="3")
    fourth = KeyValue(project_id=bar.id, key="fourth", value="4")
    session.add_all([first, second, third, fourth])
    session.flush()

    # Users
    user_with_access = User(username="user_with_access", password_hash="not_a_real_hash")
    user_without_access = User(username="user_without_access", password_hash="not_a_real_hash")
    user_with_full_bar_access = User(username="user_with_full_bar_access", password_hash="not_a_real_hash")
    user_with_foo_access = User(username="user_with_foo_access", password_hash="not_a_real_hash")
    session.add_all(
        [
            user_with_access,
            user_without_access,
            user_with_full_bar_access,
            user_with_foo_access,
        ]
    )
    session.flush()

    # Access links
    session.add(ProjectUserLink(project_id=bar.id, user_id=user_with_access.id))
    session.add(ProjectUserLink(project_id=bar.id, user_id=user_with_full_bar_access.id))
    session.add(ProjectUserLink(project_id=foo.id, user_id=user_with_foo_access.id))

    # API key for user_with_access scoped to Bar
    bar_api_key_raw = "test-bar-api-key-raw-value"
    bar_api_key = APIKey(
        user_id=user_with_access.id,
        key=get_api_key_hash(bar_api_key_raw),
        access_for_project_id=bar.id,
    )
    session.add(bar_api_key)

    # API key for user_with_foo_access scoped to Foo
    foo_api_key_raw = "test-foo-api-key-raw-value"
    foo_api_key = APIKey(
        user_id=user_with_foo_access.id,
        key=get_api_key_hash(foo_api_key_raw),
        access_for_project_id=foo.id,
    )
    session.add(foo_api_key)

    session.commit()

    return {
        "foo_id": foo.id,
        "bar_id": bar.id,
        "user_with_access": user_with_access,
        "user_without_access": user_without_access,
        "user_with_full_bar_access": user_with_full_bar_access,
        "user_with_foo_access": user_with_foo_access,
        "bar_api_key_id": bar_api_key.id,
        "bar_api_key_raw": bar_api_key_raw,
        "foo_api_key_id": foo_api_key.id,
        "foo_api_key_raw": foo_api_key_raw,
    }


@pytest.fixture(scope="session")
def seeded_data(test_engine):
    with Session(test_engine, expire_on_commit=False) as session:
        data = _seed_db(session)
    # Objects are detached after session closes; column attributes remain accessible
    return data


@pytest.fixture
def make_client(test_engine):
    """
    Factory fixture that returns a TestClient configured with:
    - get_session overridden to use the in-memory test database
    - get_current_user_non_fatal overridden to return the provided user (or None)

    Usage:
        client = make_client(current_user=some_user)
        client = make_client()  # anonymous
    """

    def _make(current_user=None):
        def override_get_session():
            with Session(test_engine) as session:
                yield session

        def override_get_current_user():
            return current_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_current_user_non_fatal] = override_get_current_user

        return TestClient(app)

    yield _make

    app.dependency_overrides.clear()


@pytest.fixture
def make_authed_client(test_engine):
    """
    Factory fixture for endpoints that use ``get_current_user`` (mandatory auth).
    Overrides ``get_current_user``, ``get_current_user_non_fatal``, and
    ``get_current_user_with_project_access`` so that no real JWT is required.

    Usage:
        client = make_authed_client(current_user=some_user)
    """

    def _make(current_user):
        def override_get_session():
            with Session(test_engine) as session:
                yield session

        def override_get_current_user():
            return current_user

        async def override_get_current_user_with_project_access(
            project_id: str,
            session: Annotated[Session, Depends(get_session)],
        ):
            if current_user is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            has_access = await does_user_have_access_to_project(session, current_user, project_id)
            if not has_access:
                raise HTTPException(status_code=403, detail="User does not have access to this project")
            return current_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_user_non_fatal] = override_get_current_user
        app.dependency_overrides[get_current_user_with_project_access] = override_get_current_user_with_project_access

        return TestClient(app)

    yield _make

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Write-test fixtures — function-scoped, fully isolated DB per test
# ---------------------------------------------------------------------------


@pytest.fixture
def write_engine():
    """A fresh in-memory SQLite engine seeded anew for every test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture
def write_seeded_data(write_engine):
    """Fresh seed data backed by the per-test write_engine."""
    with Session(write_engine, expire_on_commit=False) as session:
        data = _seed_db(session)
    return data


@pytest.fixture
def make_write_client(write_engine):
    """Like ``make_client`` but uses the function-scoped ``write_engine``."""

    def _make(current_user=None):
        def override_get_session():
            with Session(write_engine) as session:
                yield session

        def override_get_current_user():
            return current_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_current_user_non_fatal] = override_get_current_user

        return TestClient(app)

    yield _make

    app.dependency_overrides.clear()


@pytest.fixture
def make_write_authed_client(write_engine):
    """Like ``make_authed_client`` but uses the function-scoped ``write_engine``."""

    def _make(current_user):
        def override_get_session():
            with Session(write_engine) as session:
                yield session

        def override_get_current_user():
            return current_user

        async def override_get_current_user_with_project_access(
            project_id: str,
            session: Annotated[Session, Depends(get_session)],
        ):
            if current_user is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            has_access = await does_user_have_access_to_project(session, current_user, project_id)
            if not has_access:
                raise HTTPException(status_code=403, detail="User does not have access to this project")
            return current_user

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_user_non_fatal] = override_get_current_user
        app.dependency_overrides[get_current_user_with_project_access] = override_get_current_user_with_project_access

        return TestClient(app)

    yield _make

    app.dependency_overrides.clear()
