"""Integration tests for JSON item CRUD endpoints.

Endpoints covered:
  GET    /json_item/{project_id}           (additional cases; core access-rule tests live in
                                            test_get_all_json_items.py)
  GET    /json_item/{project_id}/{key}
  POST   /json_item/{project_id}/{key}     body: {"value": {...}}
  PATCH  /json_item/{project_id}/{key}     body: {"value": {...}}
  DELETE /json_item/{project_id}/{key}

Read tests reuse the session-scoped ``seeded_data`` / ``make_client`` fixtures.
Write tests use the function-scoped ``write_seeded_data`` / ``make_write_client`` fixtures
to guarantee full per-test isolation.
"""

# ---------------------------------------------------------------------------
# GET /json_item/{project_id}  — additional cases
# ---------------------------------------------------------------------------


def test_get_all_json_items_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/json_item/does-not-exist")
    assert response.status_code == 404


def test_get_all_json_items_api_key_auth_for_private_project(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/json_item/{seeded_data['bar_id']}",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "json_third" in keys


def test_get_all_json_items_invalid_api_key_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/json_item/{seeded_data['bar_id']}",
        headers={"x-api-key": "invalid-key"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /json_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_get_json_item_success_public_project(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/json_item/{seeded_data['foo_id']}/json_first")
    assert response.status_code == 200
    assert response.json() == {"key": "json_first", "json_value": {"count": 1}}


def test_get_json_item_success_private_project_with_user_auth(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/json_item/{seeded_data['bar_id']}/json_third")
    assert response.status_code == 200
    assert response.json() == {"key": "json_third", "json_value": {"count": 3}}


def test_get_json_item_private_project_api_key_auth(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/json_item/{seeded_data['bar_id']}/json_third",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json() == {"key": "json_third", "json_value": {"count": 3}}


def test_get_json_item_nonexistent_key_returns_error(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/json_item/{seeded_data['foo_id']}/nonexistent")
    assert response.status_code == 200
    assert "error" in response.json()


def test_get_json_item_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/json_item/does-not-exist/somekey")
    assert response.status_code == 404


def test_get_json_item_private_project_no_auth_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/json_item/{seeded_data['bar_id']}/json_third")
    assert response.status_code == 403


def test_get_json_item_private_project_without_project_access_returns_403(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/json_item/{seeded_data['bar_id']}/json_third")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /json_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_create_json_item_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.post(
        f"/json_item/{write_seeded_data['bar_id']}/new_json_key",
        json={"value": {"foo": "bar"}},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_json_item_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.post(
        f"/json_item/{write_seeded_data['bar_id']}/apikey_json_key",
        json={"value": {"x": 1}},
        headers={"x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_json_item_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.post(
        f"/json_item/{write_seeded_data['bar_id']}/noauth_json_key",
        json={"value": {}},
    )
    assert response.status_code == 403


def test_create_json_item_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.post(
        f"/json_item/{write_seeded_data['bar_id']}/hacked_json_key",
        json={"value": {}},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /json_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_update_json_item_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/json_item/{write_seeded_data['bar_id']}/json_third",
        json={"value": {"count": 99}},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_json_item_api_key_auth(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.patch(
        f"/json_item/{write_seeded_data['bar_id']}/json_third",
        json={"value": {"count": 42}},
        headers={"x-api-key": write_seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_json_item_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.patch(
        f"/json_item/{write_seeded_data['bar_id']}/json_third",
        json={"value": {"hacked": True}},
    )
    assert response.status_code == 403


def test_update_json_item_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.patch(
        f"/json_item/{write_seeded_data['bar_id']}/json_third",
        json={"value": {"hacked": True}},
    )
    assert response.status_code == 403


def test_update_nonexistent_json_key_returns_error(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/json_item/{write_seeded_data['bar_id']}/nonexistent",
        json={"value": {}},
    )
    assert response.status_code == 200
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# DELETE /json_item/{project_id}/{key}
# ---------------------------------------------------------------------------


def test_delete_json_item_success(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/json_item/{write_seeded_data['bar_id']}/json_third")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_delete_json_item_no_auth_returns_403(make_write_client, write_seeded_data):
    client = make_write_client()
    response = client.delete(f"/json_item/{write_seeded_data['bar_id']}/json_third")
    assert response.status_code == 403


def test_delete_json_item_without_project_access_returns_403(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_without_access"])
    response = client.delete(f"/json_item/{write_seeded_data['bar_id']}/json_third")
    assert response.status_code == 403


def test_delete_nonexistent_json_key_returns_error(make_write_client, write_seeded_data):
    client = make_write_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/json_item/{write_seeded_data['bar_id']}/nonexistent")
    assert response.status_code == 200
    assert "error" in response.json()
