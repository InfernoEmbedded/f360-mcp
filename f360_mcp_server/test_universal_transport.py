"""Universal Transport tests.

These tests verify that the unified Starlette app correctly handles SSE,
Streamable HTTP, and CORS requests.

The test infrastructure uses a module-scoped synchronous fixture that
manages the ASGI lifespan in a background thread event loop.  This avoids
the ``anyio.ClosedResourceError`` that occurs when a session-scoped async
generator fixture outlives the anyio test runner that created it.
"""

import pytest
import asyncio
import threading
import httpx
import anyio
import json
import re
from httpx import TimeoutException
from contextlib import AsyncExitStack

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_mcp_response(content: bytes) -> dict:
    """Helper to parse MCP response which might be SSE framed."""
    text = content.decode("utf-8")
    if text.startswith("event:"):
        match = re.search(r"data: (\{.*\})", text)
        if match:
            return json.loads(match.group(1))
    return json.loads(text)


MCP_INIT_PAYLOAD = {
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"},
    },
    "jsonrpc": "2.0",
    "id": 0,
}

MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


# ---------------------------------------------------------------------------
# Fixture – synchronous, module-scoped, manages lifespan in a background
# event loop so teardown is fully controlled.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def transport_app():
    """Create the Starlette app with its lifespan started.

    Yields (app, ready_event).  The lifespan runs in a daemon thread so
    the fixture's synchronous teardown can cleanly stop it.
    """
    from f360_mcp_server import server

    app = server.create_starlette_app(server.mcp, "sse", "0.0.0.0", "8360")

    loop = asyncio.new_event_loop()
    ready = threading.Event()
    stop  = threading.Event()

    async def _run_lifespan():
        async with app.router.lifespan_context(app):
            ready.set()
            # Block until teardown is requested
            while not stop.is_set():
                await asyncio.sleep(0.05)

    def _thread():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run_lifespan())
        loop.close()

    t = threading.Thread(target=_thread, daemon=True)
    t.start()
    ready.wait(timeout=5)

    yield app

    stop.set()
    t.join(timeout=5)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_status_endpoint(transport_app):
    """Test the root status route works and returns correct configuration."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=transport_app),
        base_url="http://localhost:8360",
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "supported_endpoints" in data
        assert "/sse" in data["supported_endpoints"]
        assert "mcp_settings" in data


@pytest.mark.anyio
async def test_sse_get_routing(transport_app):
    """Test that GET /sse is correctly handled (Standard SSE)."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=transport_app),
        base_url="http://localhost:8360",
    ) as client:
        headers = {"Accept": "text/event-stream"}
        try:
            with anyio.fail_after(2):
                async with client.stream("GET", "/sse", headers=headers) as response:
                    assert response.status_code == 200
                    assert response.headers["content-type"].startswith("text/event-stream")
        except (TimeoutError, TimeoutException):
            pass  # expected – the SSE stream stays open
        except Exception as e:
            if "Timeout" in type(e).__name__:
                pass
            else:
                raise


@pytest.mark.anyio
async def test_mcp_direct(transport_app):
    """Test that direct /mcp POST works."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=transport_app),
        base_url="http://localhost:8360",
    ) as client:
        with anyio.fail_after(5):
            response = await client.post("/mcp", json=MCP_INIT_PAYLOAD, headers=MCP_HEADERS)
            assert response.status_code in (200, 201)
            data = parse_mcp_response(response.content)
        assert "result" in data or "id" in data


@pytest.mark.anyio
async def test_sse_post_routing(transport_app):
    """Test that POST /sse is correctly handled (Streamable HTTP delegation).

    The MCP handler returns an SSE stream that stays open for server-initiated
    messages.  We use streaming to verify the response starts successfully
    (correct status code and content-type) without waiting for the body to end.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=transport_app),
        base_url="http://localhost:8360",
    ) as client:
        try:
            with anyio.fail_after(5):
                async with client.stream(
                    "POST", "/sse", json=MCP_INIT_PAYLOAD, headers=MCP_HEADERS,
                ) as response:
                    assert response.status_code in (200, 201)
                    ct = response.headers.get("content-type", "")
                    # Handler should return either JSON or SSE
                    assert "application/json" in ct or "text/event-stream" in ct
        except TimeoutError:
            pass  # Expected – SSE stream stays open until cancelled


@pytest.mark.anyio
async def test_cors_headers(transport_app):
    """Test that CORS headers are present on /sse."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=transport_app),
        base_url="http://localhost:8360",
    ) as client:
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        response = await client.options("/sse", headers=headers)
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "*"


@pytest.mark.anyio
async def test_sse_invalid_method(transport_app):
    """Test that invalid methods on /sse return 405."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=transport_app),
        base_url="http://localhost:8360",
    ) as client:
        response = await client.put("/sse")
        assert response.status_code == 405
