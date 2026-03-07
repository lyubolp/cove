# Cove — Copilot Instructions

## Project Overview

Cove is a FastAPI-based REST API for managing collections of configuration items (key-value pairs) organized into projects. It supports per-user access control at the project level, backed by a SQLite database via SQLModel.

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
    config_item.py             # KeyValue
    projects.py                # Project, ProjectUserLink
    users.py                   # User, Token, TokenData
    api_keys.py                # APIKey, APIKeyPublic, APIKeyCreated
  routes/
    key_value.py               # CRUD routes for key-value items
    projects.py                # Project management routes
    users.py                   # Auth / user management routes
    api_keys.py                # API key management routes
  services/
    auth/
      oauth2.py                # JWT logic, password hashing, get_current_user*, does_user_have_access_to_project
      api_keys.py              # API key hashing and verification helpers
alembic/                       # DB migrations
tests/
  conftest.py                  # Shared pytest fixtures (test engine, seed data, client factories)
  test_get_all_key_values.py   # Access-rule tests for GET /key_value/{project_id}
  test_key_value.py            # Full CRUD tests for key-value endpoints
  test_projects.py             # Full CRUD tests for project endpoints
  test_api_keys.py             # Full CRUD tests for API key endpoints
  test_users.py                # User creation, login, and health tests
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

### `ProjectUserLink`
Links a `User` to a `Project` (project-level access).

### `User`
| Field | Type |
|---|---|
| `id` | `str` (UUID) |
| `username` | `str` |
| `password_hash` | `str` |

## Access Control Rules

Access rules for `GET /key_value/{project_id}`:

| Project | Who can access |
|---|---|
| Public | Everyone (including anonymous) — all items returned |
| Private | Users with project access — all items returned |

Access is granted via:
- **Project access:** a `ProjectUserLink` row for `(project_id, user_id)`

## Authentication

- Routes use `get_current_user` (requires valid JWT, raises 401 if missing/invalid), `get_current_user_non_fatal` (returns `None` for anonymous requests, never raises), or `get_current_user_with_project_access` (mandatory auth + project membership check, raises 401/403).
- Tokens are issued at `POST /users/token`.
- API keys are passed via the `x-api-key` request header and are accepted by key-value and project routes as an alternative to JWT.

## Testing Conventions

- **Never modify `database.db`** — all tests use an isolated in-memory SQLite database.
- Test DB fixtures live in `tests/conftest.py`.
- Run tests via the VS Code Test Explorer (configured in `.vscode/settings.json`).
  - Alternatively from the terminal: `uv run pytest tests/ -v`

### Fixture overview

| Fixture | Scope | Purpose |
|---|---|---|
| `test_engine` | session | Single shared in-memory engine for the whole test run |
| `seeded_data` | session | Seed data dict backed by `test_engine` |
| `make_client` | function | `TestClient` factory — overrides `get_session` + `get_current_user_non_fatal`; accepts `current_user=None` for anonymous |
| `make_authed_client` | function | Like `make_client` but also overrides `get_current_user` and `get_current_user_with_project_access`; for mandatory-auth endpoints |
| `write_engine` | function | Fresh in-memory engine seeded per test — used by write tests |
| `write_seeded_data` | function | Seed data dict backed by `write_engine` |
| `make_write_client` | function | Like `make_client` but uses `write_engine` |
| `make_write_authed_client` | function | Like `make_authed_client` but uses `write_engine` |

**Rule:** read-only tests use the session-scoped `seeded_data` / `make_client` fixtures. Tests that create, update, or delete data use the function-scoped `write_seeded_data` / `make_write_client` / `make_write_authed_client` fixtures to guarantee full per-test isolation.

**`get_current_user_with_project_access` note:** this dependency calls `get_current_user` directly (not via DI), so overriding `get_current_user` alone is insufficient. `make_authed_client` and `make_write_authed_client` override it explicitly, re-implementing the project-access check against the injected session.

### Test seed data (`conftest.py` — `_seed_db`)

| Entity | Details |
|---|---|
| Project **Foo** | `is_public=True` |
| Project **Bar** | `is_public=False` |
| Item `"first"` | Foo, `value="1"` |
| Item `"second"` | Foo, `value="2"` |
| Item `"third"` | Bar, `value="3"` |
| Item `"fourth"` | Bar, `value="4"` |
| `user_with_access` | Project access to Bar; owns `bar_api_key` |
| `user_with_full_bar_access` | Project access to Bar |
| `user_without_access` | No access links |
| `user_with_foo_access` | Project access to Foo; owns `foo_api_key` |
| `bar_api_key` | Hashed API key scoped to Bar; raw value exposed as `bar_api_key_raw` |
| `foo_api_key` | Hashed API key scoped to Foo; raw value exposed as `foo_api_key_raw` |

The seed dict also exposes `bar_api_key_id` and `foo_api_key_id` for ownership tests.

## Constraints & Hard Rules

- **Never modify `database.db`** under any circumstances.
- `KeyValue.value` is always a `str` — do not change the model to support other types without explicit instruction.
- Do not create summary or documentation Markdown files unless explicitly asked.
- **Never implement changes directly.** Always present a plan first, discuss any uncertainties or ambiguities, and wait for explicit user approval before touching any file.
- If anything about a request is unclear, ask before planning. If anything about the plan itself is uncertain, flag it before proceeding.
- When making multiple independent file edits, always apply them in a single parallel batch — but only after the user has approved the plan.
