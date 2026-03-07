# Cove
A service for managing configuration items (key-value pairs) organised into projects. Projects have per-user access control and support both JWT and API-key authentication.

## Config item CRUD

- Get all items in a project
- Get a single item by key
- Create an item (key + string value)
- Update an item's value or visibility
- Delete an item

## Project CRUD

- List all accessible projects
- Get a project by ID
- Create a project
- Update a project's name or visibility (public / private)
- Delete a project
- Add a user to a project
- Remove a user from a project

## Auth

- Account creation
- Account login — issues a JWT token
- Limit access based on project visibility and project membership
- API key management: create, list, retrieve, rotate, and revoke keys scoped to a project

## Production/development configurations

> **Planned — not yet implemented.**

## JSON files

> **Planned — not yet implemented.**

## Python files

> **Planned — not yet implemented.**

## Access rules

Authentication can be provided as a JWT (Bearer token) or an API key via the `x-api-key` request header.

|          | Public project         | Private project                                |
|----------|------------------------|------------------------------------------------|
| Any item | Everyone (incl. anon.) | Users with project access, or a valid API key  |

> Per-item access control is planned but not yet implemented.
