import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from cove.dependencies import get_session

# Import all models so SQLModel.metadata is fully populated before create_all
from cove.models.api_keys import APIKey
from cove.models.config_item import KeyValue
from cove.models.projects import Project, ProjectUserLink
from cove.models.users import User
from cove.services.auth.oauth2 import get_current_user_non_fatal
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


@pytest.fixture(scope="session")
def seeded_data(test_engine):
    with Session(test_engine, expire_on_commit=False) as session:
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
        session.add_all([user_with_access, user_without_access, user_with_full_bar_access])
        session.flush()

        # user_with_access: project access to Bar
        project_link = ProjectUserLink(project_id=bar.id, user_id=user_with_access.id)
        session.add_all([project_link])

        # user_with_full_bar_access: project access to Bar
        full_project_link = ProjectUserLink(project_id=bar.id, user_id=user_with_full_bar_access.id)
        session.add_all([full_project_link])

        session.commit()

    # Objects are detached after session closes; column attributes remain accessible
    return {
        "foo_id": foo.id,
        "bar_id": bar.id,
        "user_with_access": user_with_access,
        "user_without_access": user_without_access,
        "user_with_full_bar_access": user_with_full_bar_access,
    }


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
