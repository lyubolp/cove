"""Integration tests for project management endpoints.

Endpoints covered:
  GET    /project/
  GET    /project/{project_id}
  POST   /project/{name}
  PATCH  /project/{project_id}
  DELETE /project/{project_id}
  POST   /project/{project_id}/access/{user_id}
  DELETE /project/{project_id}/access/{user_id}

Read tests reuse the session-scoped ``seeded_data`` / ``make_client`` fixtures.
Write tests use the function-scoped ``write_seeded_data`` / ``make_write_authed_client``
fixtures to guarantee full per-test isolation.
"""

# ---------------------------------------------------------------------------
# GET /project/
# ---------------------------------------------------------------------------


def test_get_all_projects_anonymous_sees_only_public(make_client, seeded_data):
    client = make_client()
    response = client.get("/project/")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert seeded_data["foo_id"] in ids
    assert seeded_data["bar_id"] not in ids


def test_get_all_projects_user_with_access_sees_private(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get("/project/")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert seeded_data["foo_id"] in ids
    assert seeded_data["bar_id"] in ids


def test_get_all_projects_user_without_access_sees_only_public(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get("/project/")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert seeded_data["foo_id"] in ids
    assert seeded_data["bar_id"] not in ids


def test_get_all_projects_api_key_auth_sees_private(make_client, seeded_data):
    """An API key scoped to Bar grants visibility of Bar in the project list."""
    client = make_client()
    response = client.get("/project/", headers={"x-api-key": seeded_data["bar_api_key_raw"]})
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert seeded_data["bar_id"] in ids


# ---------------------------------------------------------------------------
# GET /project/{project_id}
# ---------------------------------------------------------------------------


def test_get_public_project_anonymous(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/project/{seeded_data['foo_id']}")
    assert response.status_code == 200
    assert response.json()["id"] == seeded_data["foo_id"]


def test_get_private_project_with_user_access(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/project/{seeded_data['bar_id']}")
    assert response.status_code == 200
    assert response.json()["id"] == seeded_data["bar_id"]


def test_get_private_project_without_access_returns_error(make_client, seeded_data):
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/project/{seeded_data['bar_id']}")
    assert response.status_code == 200
    assert "error" in response.json()


def test_get_private_project_anonymous_returns_error(make_client, seeded_data):
    client = make_client()
    response = client.get(f"/project/{seeded_data['bar_id']}")
    assert response.status_code == 200
    assert "error" in response.json()


def test_get_private_project_api_key_auth(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/project/{seeded_data['bar_id']}",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    assert response.json()["id"] == seeded_data["bar_id"]


def test_get_nonexistent_project_returns_error(make_client):
    client = make_client()
    response = client.get("/project/nonexistent-id")
    assert response.status_code == 200
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# POST /project/{name}  — requires get_current_user (mandatory auth)
# ---------------------------------------------------------------------------


def test_create_project_success(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.post("/project/NewProject")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OK"
    assert "project_id" in body


def test_create_project_unauthenticated_returns_401(make_write_client):
    """No auth override for get_current_user — FastAPI returns 401."""
    client = make_write_client()
    response = client.post("/project/NewProject")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /project/{project_id}  — requires project access
# ---------------------------------------------------------------------------


def test_update_project_name(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/project/{write_seeded_data['bar_id']}",
        params={"name": "BarRenamed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_project_visibility(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(
        f"/project/{write_seeded_data['bar_id']}",
        params={"is_public": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_update_project_without_access_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    response = client.patch(
        f"/project/{write_seeded_data['bar_id']}",
        params={"name": "BarHacked"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /project/{project_id}  — requires project access
# ---------------------------------------------------------------------------


def test_delete_project_success(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/project/{write_seeded_data['bar_id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_delete_project_without_access_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    response = client.delete(f"/project/{write_seeded_data['bar_id']}")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /project/{project_id}/access/{user_id}  — requires project access
# ---------------------------------------------------------------------------


def test_add_user_to_project_success(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    new_user_id = write_seeded_data["user_without_access"].id
    response = client.post(f"/project/{write_seeded_data['bar_id']}/access/{new_user_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_add_user_to_project_without_access_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    new_user_id = write_seeded_data["user_with_full_bar_access"].id
    response = client.post(f"/project/{write_seeded_data['bar_id']}/access/{new_user_id}")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /project/{project_id}/access/{user_id}  — requires project access
# ---------------------------------------------------------------------------


def test_remove_user_from_project_success(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    target_user_id = write_seeded_data["user_with_full_bar_access"].id
    response = client.delete(f"/project/{write_seeded_data['bar_id']}/access/{target_user_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_remove_user_from_project_without_access_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    target_user_id = write_seeded_data["user_with_access"].id
    response = client.delete(f"/project/{write_seeded_data['bar_id']}/access/{target_user_id}")
    assert response.status_code == 403


def test_remove_nonexistent_link_returns_error(make_write_authed_client, write_seeded_data):
    """User with access tries to remove a link that does not exist."""
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    target_user_id = write_seeded_data["user_without_access"].id
    response = client.delete(f"/project/{write_seeded_data['bar_id']}/access/{target_user_id}")
    assert response.status_code == 200
    assert "error" in response.json()
