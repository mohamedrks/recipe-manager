# ADR-0003: JWT access + refresh tokens with Redis-backed revocation

## Status
Implemented

## Context
Each user owns a private recipe collection, so the API needs stateless authentication that scales across multiple instances without a shared in-process session store — and refresh tokens need to be revocable on logout.

## Decision
Issue short-lived JWT access tokens (15 min) and longer-lived refresh tokens (7 days). On logout or refresh, the previous refresh token's hash is written to Redis with a TTL matching its remaining lifetime; `AuthService.refresh`/`get_current_user` check that blacklist before honoring a token.

## Consequences
- Revocation requires Redis to be reachable; if Redis is down, `refresh`/`logout` fail (the unhandled Redis exception surfaces as a 500) — plain access-token requests are unaffected since those aren't blacklist-checked.
- Storing a SHA-256 hash (`token_hash`) rather than the raw token in Redis avoids holding live, replayable bearer tokens in a second datastore.
