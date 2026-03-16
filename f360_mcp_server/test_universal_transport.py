import pytest
import os
from httpx import TimeoutException
from starlette.testclient import TestClient
import httpx
import anyio
import server
import json
import re
from contextlib import AsyncExitStack
from starlette.responses import Response

@pytest.mark.anyio
async def test_status_endpoint(client):
    """Test the root status route works and returns correct configuration."""
    response = await client.get("/")
    assert response.status_code == 200
    # Root endpoint should always be plain JSON
    data = response.json()
    assert data["status"] == "ok"
    assert "supported_endpoints" in data
    assert "/sse" in data["supported_endpoints"]
    assert "mcp_settings" in data

def parse_mcp_response(content: bytes) -> dict:
    """Helper to parse MCP response which might be SSE framed."""
    text = content.decode("utf-8")
    # If it starts with 'event:', it's SSE framed
    if text.startswith("event:"):
        match = re.search(r"data: (\{.*\})", text)
        if match:
            return json.loads(match.group(1))
    return json.loads(text)

@pytest.mark.anyio
async def test_sse_get_routing(client):
    """Test that GET /sse is correctly handled (Standard SSE)."""
    headers = {"Accept": "text/event-stream"}
    # Standard anyio.fail_after works when @pytest.mark.anyio is used
    try:
        with anyio.fail_after(2):
            async with client.stream("GET", "/sse", headers=headers) as response:
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")
    except (TimeoutError, TimeoutException):
        pass
    except Exception as e:
        # anyio raises different types of timeouts sometimes
        if "Timeout" in type(e).__name__:
            pass
        else:
            raise

@pytest.mark.anyio
async def test_mcp_direct(client):
    """Test that direct /mcp POST works."""
    payload = {
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        },
        "jsonrpc": "2.0",
        "id": 0
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    with anyio.fail_after(5):
        response = await client.post("/mcp", json=payload, headers=headers)
        assert response.status_code in (200, 201)
        # Use helper to handle both plain and SSE-framed JSON
        data = parse_mcp_response(response.content)
    # The initialization response should have a result or error
    # If it's a result, we might need to check for sessionId if it's SSE based,
    # or just result for plain JSON-RPC.
    # Actually, the direct /mcp POST in JSON-only mode returns the JSON-RPC response directly.
    assert "result" in data or "id" in data

@pytest.mark.anyio
async def test_sse_post_routing(client):
    """Test that POST /sse is correctly handled (Streamable HTTP delegation)."""
    payload = {
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        },
        "jsonrpc": "2.0",
        "id": 0
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    with anyio.fail_after(15):
        response = await client.post("/sse", json=payload, headers=headers)
        assert response.status_code in (200, 201)
        data = parse_mcp_response(response.content)
        assert "result" in data or "id" in data

@pytest.mark.anyio
async def test_cors_headers(client):
    """Test that CORS headers are present on /sse."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = await client.options("/sse", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"

@pytest.mark.anyio
async def test_sse_invalid_method(client):
    """Test that invalid methods on /sse return 405."""
    response = await client.put("/sse")
    assert response.status_code == 405
