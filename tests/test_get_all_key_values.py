"""
Tests for the GET /key_value/{project_id} endpoint (get_all_key_values).

Test database contains:
  Project "Foo" (public)
    - key "first",  value "1"
    - key "second", value "2"

  Project "Bar" (private)
    - key "third",  value "3"
    - key "fourth", value "4"

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
    """Anonymous user on a public project receives all items."""
    client = make_client(current_user=None)
    response = client.get(f"/key_value/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "first" in keys
    assert "second" in keys


def test_public_project_authenticated_user_sees_all_items(make_client, seeded_data):
    """Authenticated user on a public project sees all items."""
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/key_value/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "first" in keys
    assert "second" in keys


def test_public_project_user_without_project_access_sees_all_items(make_client, seeded_data):
    """Authenticated user without project access still sees all items on a public project."""
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/key_value/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "first" in keys
    assert "second" in keys


# ---------------------------------------------------------------------------
# Private project ("Bar") tests
# ---------------------------------------------------------------------------


def test_private_project_anonymous_user_gets_403(make_client, seeded_data):
    """Anonymous user on a private project is denied access."""
    client = make_client(current_user=None)
    response = client.get(f"/key_value/{seeded_data['bar_id']}")

    assert response.status_code == 403


def test_private_project_user_with_project_access_sees_all_items(make_client, seeded_data):
    """User with project access sees all items in a private project."""
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/key_value/{seeded_data['bar_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "third" in keys
    assert "fourth" in keys


def test_private_project_user_without_project_access_gets_403(make_client, seeded_data):
    """User without project access is denied access to a private project."""
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/key_value/{seeded_data['bar_id']}")

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


# def test_nonexistent_project_returns_error(make_client):
#     """Requesting a project that does not exist returns an error message."""
#     client = make_client(current_user=None)
#     response = client.get("/key_value/nonexistent-project-id")

#     assert response.status_code == 200
#     assert response.json() == {"error": "Project not found"}
