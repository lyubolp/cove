"""Integration tests for Python code item CRUD endpoints.

Endpoints covered:
  GET    /python_item/{project_id}           (additional cases; core access-rule tests live in
                                              test_get_all_python_items.py)
  GET    /python_item/{project_id}/{key}
  POST   /python_item/{project_id}/{key}     body: {"value": "..."}
  PATCH  /python_item/{project_id}/{key}     body: {"value": "..."}
  DELETE /python_item/{project_id}/{key}

Read tests reuse the session-scoped ``seeded_data`` / ``make_client`` fixtures.
Write tests use the function-scoped ``write_seeded_data`` / ``make_write_client`` fixtures
to guarantee full per-test isolation.
"""

# ---------------------------------------------------------------------------
# GET /python_item/{project_id}  — additional cases
# ---------------------------------------------------------------------------


def test_get_all_python_items_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/python_item/does-not-exist")
    assert response.status_code == 404


def test_get_all_python_items_api_key_auth_for_private_project(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/python_item/{seeded_data['bar_id']}",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "python_third" in keys


def test_get_all_python_items_invalid_api_key_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/python_item/{seeded_data['bar_id']}",
        headers={"x-api-key": "invalid-key"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /python_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_get_python_item_success_public_project(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/python_item/{seeded_data['foo_id']}/python_first")
    assert response.status_code == 200
    assert response.json() == {"key": "python_first", "python_value": "print('hello')"}


def test_get_python_item_success_private_project_with_user_auth(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/python_item/{seeded_data['bar_id']}/python_third")
    assert response.status_code == 200
    assert response.json() == {"key": "python_third", "python_value": "print('bar')"}


def test_get_python_item_private_project_api_key_auth(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/python_item/{seeded_data['bar_id']}/python_third",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json() == {"key": "python_third", "python_value": "print('bar')"}


def test_get_python_item_nonexistent_key_returns_error(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/python_item/{seeded_data['foo_id']}/nonexistent")
    assert response.status_code == 200
    assert "error" in response.json()


def test_get_python_item_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/python_item/does-not-exist/somekey")
    assert response.status_code == 404


def test_get_python_item_private_project_no_auth_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/python_item/{seeded_data['bar_id']}/python_third")
    assert response.status_code == 403


def test_get_python_item_private_project_without_project_access_returns_403(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/python_item/{seeded_data['bar_id']}/python_third")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /python_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_create_python_item_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.post(
        f"/python_item/{write_seeded_data['bar_id']}/new_python_key",
        content="x = 1 + 1",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_python_item_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.post(
        f"/python_item/{write_seeded_data['bar_id']}/apikey_python_key",
        content="import os",
        headers={"Content-Type": "text/plain", "x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_python_item_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.post(
        f"/python_item/{write_seeded_data['bar_id']}/noauth_python_key",
        content="pass",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 403


def test_create_python_item_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.post(
        f"/python_item/{write_seeded_data['bar_id']}/hacked_python_key",
        content="pass",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /python_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_update_python_item_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/python_item/{write_seeded_data['bar_id']}/python_third",
        content="print('updated')",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_python_item_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.patch(
        f"/python_item/{write_seeded_data['bar_id']}/python_third",
        content="print('api-updated')",
        headers={"Content-Type": "text/plain", "x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_python_item_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.patch(
        f"/python_item/{write_seeded_data['bar_id']}/python_third",
        content="hacked()",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 403


def test_update_python_item_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.patch(
        f"/python_item/{write_seeded_data['bar_id']}/python_third",
        content="hacked()",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 403


def test_update_nonexistent_python_key_returns_error(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/python_item/{write_seeded_data['bar_id']}/nonexistent",
        content="pass",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# DELETE /python_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_delete_python_item_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/python_item/{write_seeded_data['bar_id']}/python_third")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_delete_python_item_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.delete(f"/python_item/{write_seeded_data['bar_id']}/python_third")
    assert response.status_code == 403


def test_delete_python_item_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.delete(f"/python_item/{write_seeded_data['bar_id']}/python_third")
    assert response.status_code == 403


def test_delete_nonexistent_python_key_returns_error(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/python_item/{write_seeded_data['bar_id']}/nonexistent")
    assert response.status_code == 200
    assert "error" in response.json()
