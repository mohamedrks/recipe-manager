# ADR-0001: Use FastAPI over Flask/Django

## Status
Implemented

## Context
The API needs async I/O for DB-bound request handling, automatic OpenAPI documentation, and strong request/response validation, while staying lean enough not to add ceremony beyond what a CRUD + filtering API needs.

## Decision
Use FastAPI + Uvicorn, with SQLAlchemy 2.0 async and Pydantic v2.

- Flask + Flask-RESTX: async is bolted on, OpenAPI/validation wiring is manual.
- Django REST Framework: batteries-included but heavyweight for this scope; ORM is sync-first, working against the async requirement.
- FastAPI: native async, automatic Swagger/ReDoc generation from Pydantic schemas, and a dependency-injection system that maps directly onto a layered router → service → repository design.

## Consequences
- Smaller plugin ecosystem than Django for things this project doesn't need (admin panel, batteries-included auth).
