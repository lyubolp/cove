"""
Tests for the GET /python_item/{project_id} endpoint (get_all_python_items).

Test database contains:
  Project "Foo" (public)
    - key "python_first", python_value "print('hello')"

  Project "Bar" (private)
    - key "python_third", python_value "print('bar')"

  user_with_access:
    - ProjectUserLink to project "Bar"

  user_with_full_bar_access:
    - ProjectUserLink to project "Bar"

  user_without_access:
    - no links

Access rules:
  | project    | who can access             |
  |------------|----------------------------|
  | public     | everyone (all items shown) |
  | private    | users with project access  |
"""

# ---------------------------------------------------------------------------
# Public project ("Foo") tests
# ---------------------------------------------------------------------------


def test_public_project_anonymous_user_sees_all_items(make_client, seeded_data):
    """Anonymous user on a public project receives all Python items."""
    client = make_client(current_user=None)
    response = client.get(f"/python_item/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "python_first" in keys


def test_public_project_authenticated_user_sees_all_items(make_client, seeded_data):
    """Authenticated user on a public project sees all Python items."""
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/python_item/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "python_first" in keys


def test_public_project_user_without_project_access_sees_all_items(make_client, seeded_data):
    """Authenticated user without project access still sees all items on a public project."""
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/python_item/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "python_first" in keys


# ---------------------------------------------------------------------------
# Private project ("Bar") tests
# ---------------------------------------------------------------------------


def test_private_project_anonymous_user_gets_403(make_client, seeded_data):
    """Anonymous user on a private project is denied access."""
    client = make_client(current_user=None)
    response = client.get(f"/python_item/{seeded_data['bar_id']}")

    assert response.status_code == 403


def test_private_project_user_with_project_access_sees_all_items(make_client, seeded_data):
    """User with project access sees all Python items in a private project."""
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/python_item/{seeded_data['bar_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "python_third" in keys


def test_private_project_user_without_project_access_gets_403(make_client, seeded_data):
    """User without project access is denied access to a private project."""
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/python_item/{seeded_data['bar_id']}")

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_nonexistent_project_returns_404(make_client):
    client = make_client()
    response = client.get("/python_item/does-not-exist")
    assert response.status_code == 404


def test_api_key_auth_for_private_project(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/python_item/{seeded_data['bar_id']}",
        headers={"x-api-key": seeded_data["bar_api_key_raw"]},
    )
    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "python_third" in keys


def test_invalid_api_key_returns_403(make_client, seeded_data):
    client = make_client()
    response = client.get(
        f"/python_item/{seeded_data['bar_id']}",
        headers={"x-api-key": "invalid-key"},
    )
    assert response.status_code == 403
