# ADR-0002: Use PostgreSQL over SQLite/MongoDB

## Status
Implemented

## Context
Recipes have a relational shape (`users → recipes → recipe_ingredients → ingredients`) and the spec requires combinable filters: vegetarian flag, servings, ingredient include/exclude, and free-text search over instructions.

## Decision
Use PostgreSQL 16 as the system of record.

- SQLite: fine for fast unit tests, but weak concurrent-write handling and no first-class full-text search — not viable as the integration/production datastore.
- MongoDB: workable for nested ingredient lists, but weaker relational integrity for the owner→recipes relationship, and the team would need aggregation-pipeline patterns for combined filters instead of plain SQL.
- PostgreSQL: native `tsvector`/GIN indexing covers instruction text search, `EXISTS`/`NOT EXISTS` subqueries handle ingredient include/exclude efficiently, and SQLAlchemy/Alembic support is mature.

## Consequences
- A `GIN(to_tsvector('english', instructions))` index (migration `0e80b1b4dd26`) keeps `instructions_contains` filtering off a full table scan as data grows.
