"""Integration tests for key-value CRUD endpoints.

Endpoints covered:
  GET    /key_value/{project_id}           (additional cases; core access-rule tests live in
                                            test_get_all_key_values.py)
  GET    /key_value/{project_id}/{key}
  POST   /key_value/{project_id}/{key}/{value}
  PATCH  /key_value/{project_id}/{key}
  DELETE /key_value/{project_id}/{key}

Read tests reuse the session-scoped ``seeded_data`` / ``make_client`` fixtures.
Write tests use the function-scoped ``write_seeded_data`` / ``make_write_client`` fixtures
to guarantee full per-test isolation.
"""

# ---------------------------------------------------------------------------
# GET /key_value/{project_id}  — additional cases
# ---------------------------------------------------------------------------


def test_get_all_key_values_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/key_value/does-not-exist")
    assert response.status_code == 404


def test_get_all_key_values_api_key_auth_for_private_project(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/key_value/{seeded_data['bar_id']}",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "third" in keys
    assert "fourth" in keys


def test_get_all_key_values_invalid_api_key_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/key_value/{seeded_data['bar_id']}",
        headers={"x-api-key": "invalid-key"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /key_value/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_get_key_value_success_public_project(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/key_value/{seeded_data['foo_id']}/first")
    assert response.status_code == 200
    assert response.json() == {"key": "first", "value": "1"}


def test_get_key_value_success_private_project_with_user_auth(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/key_value/{seeded_data['bar_id']}/third")
    assert response.status_code == 200
    assert response.json() == {"key": "third", "value": "3"}


def test_get_key_value_private_project_api_key_auth(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/key_value/{seeded_data['bar_id']}/third",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json() == {"key": "third", "value": "3"}


def test_get_key_value_nonexistent_key_returns_error(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/key_value/{seeded_data['foo_id']}/nonexistent")
    assert response.status_code == 200
    assert "error" in response.json()


def test_get_key_value_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/key_value/does-not-exist/somekey")
    assert response.status_code == 404


def test_get_key_value_private_project_no_auth_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/key_value/{seeded_data['bar_id']}/third")
    assert response.status_code == 403


def test_get_key_value_private_project_without_project_access_returns_403(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/key_value/{seeded_data['bar_id']}/third")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /key_value/{project_id}/{key}/{value}
# ---------------------------------------------------------------------------


def test_create_key_value_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.post(f"/key_value/{write_seeded_data['bar_id']}/newkey/newvalue")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_key_value_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.post(
        f"/key_value/{write_seeded_data['bar_id']}/apikey-created/val",
        headers={"x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_key_value_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.post(f"/key_value/{write_seeded_data['bar_id']}/noauth-key/val")
    assert response.status_code == 403


def test_create_key_value_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.post(f"/key_value/{write_seeded_data['bar_id']}/hacked-key/val")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /key_value/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_update_key_value_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/key_value/{write_seeded_data['bar_id']}/third",
        params={"value": "updated-value"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_key_value_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.patch(
        f"/key_value/{write_seeded_data['bar_id']}/fourth",
        params={"value": "api-updated"},
        headers={"x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_key_value_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.patch(
        f"/key_value/{write_seeded_data['bar_id']}/third",
        params={"value": "hacked"},
    )
    assert response.status_code == 403


def test_update_key_value_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.patch(
        f"/key_value/{write_seeded_data['bar_id']}/third",
        params={"value": "hacked"},
    )
    assert response.status_code == 403


def test_update_nonexistent_key_returns_error(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/key_value/{write_seeded_data['bar_id']}/nonexistent",
        params={"value": "val"},
    )
    assert response.status_code == 200
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# DELETE /key_value/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_delete_key_value_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/key_value/{write_seeded_data['bar_id']}/third")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_delete_key_value_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.delete(
        f"/key_value/{write_seeded_data['bar_id']}/fourth",
        headers={"x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_delete_key_value_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.delete(f"/key_value/{write_seeded_data['bar_id']}/third")
    assert response.status_code == 403


def test_delete_key_value_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.delete(f"/key_value/{write_seeded_data['bar_id']}/third")
    assert response.status_code == 403


def test_delete_nonexistent_key_returns_error(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/key_value/{write_seeded_data['bar_id']}/nonexistent")
    assert response.status_code == 200
    assert "error" in response.json()
