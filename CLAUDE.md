# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cove is a FastAPI-based REST API for managing collections of configuration items (key-value, JSON, and Python-code items) organized into projects, with per-user access control and JWT/API-key authentication, backed by SQLite via SQLModel.

## Commands

Package manager is `uv`; use `uv run` to execute everything.

```bash
uv run pytest tests/ -v                       # run all tests
uv run pytest tests/test_projects.py -v       # run one test file
uv run pytest tests/test_projects.py::test_name -v  # run a single test

just lint                                     # ruff format, pylint (fail-under 9), mypy, ruff check, complexipy
just test                                     # uv run pytest tests/ -v
just clean                                    # remove caches/coverage artifacts

uv run fastapi dev main.py                    # run the app locally
uv run alembic upgrade head                   # apply DB migrations
uv run alembic revision --autogenerate -m "…" # create a migration after a model change
```

Individual lint tools (from `justfile`), run against `src main.py`:
`uv run pylint src main.py --fail-under 9`, `uv run mypy src main.py --ignore-missing-imports`, `uv run ruff check src main.py`, `uv run complexipy .`.

## Architecture

```
main.py                        # FastAPI app entry point; registers all routers, /health
src/cove/
  dependencies.py              # get_session — yields a SQLModel Session from database.db
  models/
    config_item.py             # ConfigItem (abstract base) → KeyValue, JSONConfig, PythonConfig
    projects.py                # Project, ProjectUserLink
    users.py                   # User, Token, TokenData
    api_keys.py                # APIKey, APIKeyPublic, APIKeyCreated
  routes/
    key_value.py, json_item.py, python_item.py   # CRUD for each config-item type, each mirroring the same route shape
    projects.py                 # project CRUD, /items (aggregate get/clear across all item types), /access (add/remove user)
    users.py                    # register, /token (JWT login)
    api_keys.py                 # create/list/get/rotate/revoke keys scoped to a project
  services/auth/
    oauth2.py                   # JWT logic, password hashing, get_current_user / get_current_user_non_fatal / get_current_user_with_project_access, does_user_have_access_to_project
    api_keys.py                 # API key hashing/verification, does_api_key_grant_access_to_project, api_key_header dependency
alembic/                        # DB migrations (script_location = alembic/, target DB is database.db)
tests/
  conftest.py                   # shared fixtures — see Testing section below
```

All three config-item types (`KeyValue`, `JSONConfig`, `PythonConfig`) inherit `id`/`project_id` from the abstract `ConfigItem` base and follow the same route pattern per type: `GET /{project_id}` (list), `GET /{project_id}/{key}`, `POST /{project_id}/{key}`, `PATCH /{project_id}/{key}`, `DELETE /{project_id}/{key}`. `key_value`'s create route is the outlier, taking `value` as a path segment (`POST /{project_id}/{key}/{value}`) rather than a body/query param.

`KeyValue.value` is always a plain `str`, even for numeric-looking input — do not change this without explicit instruction.

## Access control

Auth is JWT (Bearer token, issued at `POST /users/token`) or an API key via the `x-api-key` header — routes accept either. Visibility rules:

| Project  | Who can access |
|----------|----------------|
| Public   | Everyone, including anonymous |
| Private  | Users with a `ProjectUserLink`, or a valid API key scoped to that project |

Three auth dependencies in `oauth2.py`, used depending on whether the route allows anonymous access:
- `get_current_user` — requires a valid JWT, raises 401 otherwise.
- `get_current_user_non_fatal` — returns `None` for anonymous/invalid tokens, never raises; used on routes that must also serve public data.
- `get_current_user_with_project_access` — requires JWT **and** project membership; raises 401/403. Important: it calls `get_current_user` directly rather than via DI, so overriding `get_current_user` alone in tests does not affect it — it must be overridden separately (see `make_authed_client` in conftest.py).

API keys are one per (user, project) pair, and only grant access to private projects — they cannot create/update/delete projects themselves.

## Testing conventions

- **Never modify `database.db`** — it's the real dev DB. All tests run against isolated in-memory SQLite via `tests/conftest.py`.
- Read-only tests use the session-scoped `seeded_data` / `make_client` (or `make_authed_client`) fixtures — fast, shared across a test run.
- Tests that create/update/delete data use the function-scoped `write_seeded_data` / `make_write_client` / `make_write_authed_client` fixtures instead, for full per-test isolation. Don't use the session-scoped fixtures for mutating tests — they'd leak state into other tests.
- Seed data (`_seed_db` in conftest.py): projects **Foo** (public) and **Bar** (private), each with key-value/JSON/Python items; users `user_with_access`/`user_with_full_bar_access` (access to Bar), `user_with_foo_access` (access to Foo), `user_without_access` (no links); API keys `bar_api_key`/`foo_api_key` scoped accordingly, raw values exposed as `*_raw` in the returned dict.

## Working conventions

- Never implement changes directly without discussion first: present a plan, flag any uncertainty or ambiguity, and wait for explicit approval before touching files.
- Don't create summary or documentation Markdown files unless explicitly asked.
- When making multiple independent file edits, apply them in a single parallel batch — but only after the plan is approved.
