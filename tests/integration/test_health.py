from httpx import AsyncClient


async def test_liveness(client: AsyncClient) -> None:
    r = await client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_readiness(client: AsyncClient) -> None:
    r = await client.get("/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_metrics_endpoint(client: AsyncClient) -> None:
    r = await client.get("/health/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
    assert "http_request_duration_seconds" in r.text
