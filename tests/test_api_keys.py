"""Integration tests for API key management endpoints.

Endpoints covered:
  POST   /api_keys/{project_id}   — create (requires auth + project access)
  GET    /api_keys/               — list   (requires auth)
  GET    /api_keys/{key_id}       — get    (requires auth, owner-only)
  PATCH  /api_keys/{key_id}       — rotate (requires auth, owner-only)
  DELETE /api_keys/{key_id}       — revoke (requires auth, owner-only)

Read tests (list / get) reuse the session-scoped ``seeded_data`` / ``make_authed_client``
fixtures.  Write tests (create / rotate / delete) use the function-scoped
``write_seeded_data`` / ``make_write_authed_client`` fixtures.

TODO: verify the intended behaviour of rotate_api_key — the current implementation stores
an unhashed UUID as the key value instead of hashing a freshly generated raw key, and then
returns the DB model directly.  This means the rotated key cannot be used for authentication.
"""

# ---------------------------------------------------------------------------
# POST /api_keys/{project_id}
# ---------------------------------------------------------------------------


def test_create_api_key_success(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.post(f"/api_keys/{write_seeded_data['bar_id']}")
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["access_for_project_id"] == write_seeded_data["bar_id"]
    assert "key" in body


def test_create_api_key_no_project_access_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    response = client.post(f"/api_keys/{write_seeded_data['bar_id']}")
    assert response.status_code == 403


def test_create_api_key_unauthenticated_returns_401(make_write_client, write_seeded_data):
    """No get_current_user override — FastAPI's OAuth2 scheme returns 401."""
    client = make_write_client()
    response = client.post(f"/api_keys/{write_seeded_data['bar_id']}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api_keys/
# ---------------------------------------------------------------------------


def test_list_api_keys_returns_own_keys(make_authed_client, seeded_data):
    client = make_authed_client(current_user=seeded_data["user_with_access"])
    response = client.get("/api_keys/")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(k["id"] == seeded_data["bar_api_key_id"] for k in body)


def test_list_api_keys_does_not_expose_key_value(make_authed_client, seeded_data):
    """Raw key must never appear in list responses."""
    client = make_authed_client(current_user=seeded_data["user_with_access"])
    response = client.get("/api_keys/")
    assert response.status_code == 200
    for key_obj in response.json():
        assert "key" not in key_obj


def test_list_api_keys_returns_empty_for_user_with_no_keys(make_authed_client, seeded_data):
    client = make_authed_client(current_user=seeded_data["user_without_access"])
    response = client.get("/api_keys/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_api_keys_unauthenticated_returns_401(make_client):
    client = make_client()
    response = client.get("/api_keys/")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api_keys/{key_id}
# ---------------------------------------------------------------------------


def test_get_api_key_success(make_authed_client, seeded_data):
    client = make_authed_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/api_keys/{seeded_data['bar_api_key_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == seeded_data["bar_api_key_id"]
    assert "key" not in body


def test_get_api_key_not_owned_returns_403(make_authed_client, seeded_data):
    """A user cannot retrieve another user's API key."""
    client = make_authed_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/api_keys/{seeded_data['bar_api_key_id']}")
    assert response.status_code == 403


def test_get_api_key_nonexistent_returns_404(make_authed_client, seeded_data):
    client = make_authed_client(current_user=seeded_data["user_with_access"])
    response = client.get("/api_keys/nonexistent-id")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api_keys/{key_id}  (rotate)
# ---------------------------------------------------------------------------


def test_rotate_api_key_success(make_write_authed_client, write_seeded_data):
    # TODO: verify the intended behaviour of rotate_api_key — see module docstring.
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch(f"/api_keys/{write_seeded_data['bar_api_key_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == write_seeded_data["bar_api_key_id"]
    assert "key" in body


def test_rotate_api_key_not_owned_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    response = client.patch(f"/api_keys/{write_seeded_data['bar_api_key_id']}")
    assert response.status_code == 403


def test_rotate_api_key_nonexistent_returns_404(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.patch("/api_keys/nonexistent-id")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api_keys/{key_id}
# ---------------------------------------------------------------------------


def test_delete_api_key_success(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete(f"/api_keys/{write_seeded_data['bar_api_key_id']}")
    assert response.status_code == 204


def test_delete_api_key_not_owned_returns_403(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_without_access"])
    response = client.delete(f"/api_keys/{write_seeded_data['bar_api_key_id']}")
    assert response.status_code == 403


def test_delete_api_key_nonexistent_returns_404(make_write_authed_client, write_seeded_data):
    client = make_write_authed_client(current_user=write_seeded_data["user_with_access"])
    response = client.delete("/api_keys/nonexistent-id")
    assert response.status_code == 404
