"""
Tests for the GET /key_value/{project_id} endpoint (get_all_key_values).

Test database contains:
  Project "Foo" (public)
    - key "first",  value "1", public
    - key "second", value "2", private

  Project "Bar" (private)
    - key "third",  value "3", public
    - key "fourth", value "4", private

  user_with_access:
    - ConfigItemUserLink to item "second" in "Foo"
    - ProjectUserLink to project "Bar"  (no item access to "fourth")

  user_with_full_bar_access:
    - ProjectUserLink to project "Bar"
    - ConfigItemUserLink to item "fourth" in "Bar"

  user_without_access:
    - no links

Access rules:
  | item visibility | public project | private project |
  |-----------------|----------------|-----------------|
  | public          | everyone       | project access  |
  | private         | item access    | item access     |
"""

# ---------------------------------------------------------------------------
# Public project ("Foo") tests
# ---------------------------------------------------------------------------


def test_public_project_anonymous_user_sees_only_public_items(make_client, seeded_data):
    """Anonymous user on a public project receives only public items."""
    client = make_client(current_user=None)
    response = client.get(f"/key_value/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "first" in keys
    assert "second" not in keys


def test_public_project_user_with_item_access_sees_all_items(make_client, seeded_data):
    """Authenticated user with access to the private item sees both items."""
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/key_value/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "first" in keys
    assert "second" in keys


def test_public_project_user_without_item_access_sees_only_public_items(make_client, seeded_data):
    """Authenticated user without item-level access sees only public items."""
    client = make_client(current_user=seeded_data["user_without_access"])
    response = client.get(f"/key_value/{seeded_data['foo_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "first" in keys
    assert "second" not in keys


# ---------------------------------------------------------------------------
# Private project ("Bar") tests
# ---------------------------------------------------------------------------


def test_private_project_anonymous_user_gets_403(make_client, seeded_data):
    """Anonymous user on a private project is denied access."""
    client = make_client(current_user=None)
    response = client.get(f"/key_value/{seeded_data['bar_id']}")

    assert response.status_code == 403


def test_private_project_user_with_only_project_access_sees_public_items_only(make_client, seeded_data):
    """User with project access sees public items but NOT private items (no item-level access)."""
    client = make_client(current_user=seeded_data["user_with_access"])
    response = client.get(f"/key_value/{seeded_data['bar_id']}")

    assert response.status_code == 200
    keys = [item["key"] for item in response.json()]
    assert "third" in keys
    assert "fourth" not in keys


def test_private_project_user_with_project_and_item_access_sees_all_items(make_client, seeded_data):
    """User with project access AND item access sees both public and private items."""
    client = make_client(current_user=seeded_data["user_with_full_bar_access"])
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


def test_nonexistent_project_returns_error(make_client):
    """Requesting a project that does not exist returns an error message."""
    client = make_client(current_user=None)
    response = client.get("/key_value/nonexistent-project-id")

    assert response.status_code == 200
    assert response.json() == {"error": "Project not found"}
