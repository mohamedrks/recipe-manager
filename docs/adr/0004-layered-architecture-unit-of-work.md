# ADR-0004: Layered architecture with per-request unit-of-work session

## Status
Implemented

## Context
Multi-step writes (e.g., creating a recipe + upserting ingredients + linking associations) need to commit or roll back atomically, and business logic needs to stay independent of HTTP and SQL concerns for testability.

## Decision
Three layers: API router (HTTP concerns only) → Service (business rules, ownership checks) → Repository (SQL). One `AsyncSession` is created per request via a FastAPI dependency (`get_db`), which commits on success and rolls back on any unhandled exception. Services never call `session.commit()` directly — only the dependency does.

## Consequences
- Services can be unit-tested with a mocked repository, with no real database needed.
- A bug in any layer that raises an exception automatically rolls back the whole request's writes — no partial recipe/ingredient state can be persisted.
- Concurrent ingredient creation race ("two requests create 'potatoes' simultaneously") is resolved with `INSERT ... ON CONFLICT (name) DO NOTHING` rather than application-level locking.
