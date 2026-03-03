# Cove — Copilot Instructions

## Project Overview

Cove is a FastAPI-based REST API for managing collections of configuration items (key-value pairs) organized into projects. It supports per-user access control at both the project and item level, backed by a SQLite database via SQLModel.

## Tech Stack

- **Language:** Python 3.12+
- **Package manager:** `uv` (use `uv run` to execute scripts and tests)
- **Web framework:** FastAPI
- **ORM / DB layer:** SQLModel + SQLAlchemy, SQLite
- **Auth:** JWT (`pyjwt`), password hashing via `pwdlib[argon2]`
- **Testing:** `pytest`, FastAPI `TestClient` (sync), in-memory SQLite for test isolation
- **Virtual environment:** `.venv/` managed by `uv`

## Project Structure

```
main.py                        # FastAPI app entry point
src/cove/
  dependencies.py              # get_session — yields a SQLModel Session from database.db
  models/
    config_item.py             # KeyValue, ConfigItemUserLink
    projects.py                # Project, ProjectUserLink
    users.py                   # User, APIKey, Token, TokenData
  routes/
    key_value.py               # CRUD routes for key-value items
    projects.py                # Project management routes
    users.py                   # Auth / user management routes
  services/
    auth.py                    # JWT logic, password hashing, access-check helpers
alembic/                       # DB migrations
tests/
  conftest.py                  # Shared pytest fixtures (test engine, seed data, client factory)
  test_access_rules.py
  test_get_all_key_values.py
```

## Data Models

### `Project`
| Field | Type | Notes |
|---|---|---|
| `id` | `str` (UUID) | PK |
| `name` | `str` | |
| `is_public` | `bool` | |

### `KeyValue`
| Field | Type | Notes |
|---|---|---|
| `id` | `str` (UUID) | PK, inherited from `ConfigItem` |
| `project_id` | `str` | FK → `project.id` |
| `key` | `str` | |
| `value` | `str` | Always a string, even for numeric-looking values |
| `is_public` | `bool` | |

### `ConfigItemUserLink`
Links a `User` to a specific `KeyValue` item (item-level access).

### `ProjectUserLink`
Links a `User` to a `Project` (project-level access).

### `User`
| Field | Type |
|---|---|
| `id` | `str` (UUID) |
| `username` | `str` |
| `password_hash` | `str` |

## Access Control Rules

These are the **intended** access rules for `GET /key_value/{project_id}`:

| | Public project | Private project |
|---|---|---|
| **Public item** | Everyone (including anonymous) | Users with project access |
| **Private item** | Users with item access | Users with item access |

Access is granted via:
- **Project access:** a `ProjectUserLink` row for `(project_id, user_id)`
- **Item access:** a `ConfigItemUserLink` row for `(config_item_id, user_id)`

> Note: the current implementation may not fully reflect these rules yet — tests are being used to drive the implementation toward them.

## Authentication

- Routes use `get_current_user` (requires valid JWT, raises 401 if missing/invalid) or `get_current_user_non_fatal` (returns `None` for anonymous requests, never raises).
- Tokens are issued at `POST /users/token`.

## Testing Conventions

- **Never modify `database.db`** — all tests use an isolated in-memory SQLite database.
- Test DB fixtures live in `tests/conftest.py` and are session-scoped for performance.
- The `make_client` fixture is a factory that accepts a `current_user` and returns a `TestClient` with `get_session` and `get_current_user_non_fatal` overridden.
- Run tests with: `uv run pytest tests/ -v`

### Test seed data (`conftest.py`)

| Entity | Details |
|---|---|
| Project **Foo** | `is_public=True` |
| Project **Bar** | `is_public=False` |
| Item `"first"` | Foo, `value="1"`, `is_public=True` |
| Item `"second"` | Foo, `value="2"`, `is_public=False` |
| Item `"third"` | Bar, `value="3"`, `is_public=True` |
| Item `"fourth"` | Bar, `value="4"`, `is_public=False` |
| `user_with_access` | Item access to `"second"` + project access to Bar (no item access to `"fourth"`) |
| `user_with_full_bar_access` | Project access to Bar + item access to `"fourth"` |
| `user_without_access` | No access links |

## Constraints & Hard Rules

- **Never modify `database.db`** under any circumstances.
- `KeyValue.value` is always a `str` — do not change the model to support other types without explicit instruction.
- Do not create summary or documentation Markdown files unless explicitly asked.
- **Never implement changes directly.** Always present a plan first, discuss any uncertainties or ambiguities, and wait for explicit user approval before touching any file.
- If anything about a request is unclear, ask before planning. If anything about the plan itself is uncertain, flag it before proceeding.
- When making multiple independent file edits, always apply them in a single parallel batch — but only after the user has approved the plan.
