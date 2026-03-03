# config-service
A service for accessing configuration items

The application should provide CRUD actions on configuration items.

Configuration items can be key:value pairs, whole JSON files, Python files and other.

We can have production and development configurations.

Projects are either public (no API key needed) or private (login or API key needed).

Some items in public projects can also be private.

## Config item CRUD

- Create
- Toogle access (public/private)
- Change value
- Delete item
- Get an item by key

## Project CRUD

- Create
- Edit name
- Toogle access
- Delete project
- Get all items in project

## Auth

- Account creation
- Account login
- Limit access based on access rules
- Add people to project and items
- API keys registration

## Production/development configurations

## JSON files

## Python files


## Access rules

Visibility of:

|             | Public project | Private project |
|-------------|----------------|-----------------|
| Public item | Everyone       | Project access  |
| Private item| Item access    | Item access     |
