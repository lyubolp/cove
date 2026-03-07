"""Integration tests for user management and auth endpoints.

Endpoints covered:
  POST /users/        — create user
  POST /users/token   — login / obtain JWT
  GET  /health        — liveness check

All tests use the function-scoped ``make_write_client`` / ``write_engine`` fixtures so
that user-creation and login operations are fully isolated and use real password hashing
without touching the shared session-scoped database.
"""

# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


def test_health_returns_200(make_write_client):
    client = make_write_client()
    response = client.get("/health")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /users/
# ---------------------------------------------------------------------------


def test_create_user_success(make_write_client):
    client = make_write_client()
    response = client.post("/users/", params={"username": "newuser", "password": "secret"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "newuser"
    assert "id" in body
    # Password hash must never be a plain-text match of the supplied password
    assert body["password_hash"] != "secret"


def test_create_user_duplicate_username_returns_400(make_write_client):
    client = make_write_client()
    client.post("/users/", params={"username": "dupuser", "password": "secret"})
    response = client.post("/users/", params={"username": "dupuser", "password": "other"})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /users/token
# ---------------------------------------------------------------------------


def test_login_success_returns_token(make_write_client):
    client = make_write_client()
    client.post("/users/", params={"username": "tokenuser", "password": "pass123"})

    response = client.post("/users/token", data={"username": "tokenuser", "password": "pass123"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(make_write_client):
    client = make_write_client()
    client.post("/users/", params={"username": "logintest", "password": "correct"})

    response = client.post("/users/token", data={"username": "logintest", "password": "wrong"})

    assert response.status_code == 401


def test_login_unknown_user_returns_401(make_write_client):
    client = make_write_client()
    response = client.post("/users/token", data={"username": "ghost", "password": "any"})
    assert response.status_code == 401
