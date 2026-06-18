# ADR-0005: Ship single-instance Docker deployment; defer multi-replica topology

## Status
Deferred — documented but not implemented in this delivery

## Context
The original architecture plan (`docs/architecture.md` §13–14) called for nginx load-balancing across two API replicas, plus Prometheus + Grafana for visualizing per-instance metrics, as a way to demonstrate the stateless design (no in-process session/rate-limit state) under real multi-instance conditions.

## Decision
Ship a working single-instance `docker compose up --build` (Dockerfile, `migrate` one-shot service, `api` service) and defer the nginx/2-replica/Grafana topology.

## Consequences
- The stateless-design claim (Redis-backed rate limiting and JWT blacklist, no in-process state) is implemented but not visually proven under load-balanced conditions — there's no running demo showing two replicas behaving consistently.
- Prometheus metrics (`/health/metrics`) and structured logs work today and are scrape-ready; only the Prometheus/Grafana containers and nginx upstream config from the plan are missing, not the instrumentation itself.
- Revisiting this only requires adding the nginx/Prometheus/Grafana services and config files already specified in `docs/architecture.md` — no application code changes are needed.
