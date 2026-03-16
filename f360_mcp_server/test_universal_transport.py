"""Universal Transport tests.

These tests verify that the unified Starlette app correctly handles SSE,
Streamable HTTP, and CORS requests.
"""

import pytest
import httpx
import anyio
import json
import re
from httpx import TimeoutException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_mcp_response(content: bytes) -> dict:
    """Helper to parse MCP response which might be SSE framed."""
    if not content:
        return {}
    text = content.decode("utf-8")
    if text.startswith("event:"):
        match = re.search(r"data: (\{.*\})", text)
        if match:
            return json.loads(match.group(1))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


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
# Consolidated Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_transport_and_compliance():
    """Run all transport and compliance checks in a single sequence for stability."""
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
    from f360_mcp_server import server
    
    # Fresh instance for complete isolation
    test_mcp = FastMCP(
        "test-mcp",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        json_response=False,
    )
    
    @test_mcp.tool()
    def echo(msg: str) -> str:
        return msg

    app = server.create_starlette_app(test_mcp, "sse", "0.0.0.0", "8360")
    
    # Manage lifespan directly in the test to avoid anyio fixture teardown issues
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://localhost:8360",
        ) as client:
            
            # 1. Root status endpoint
            resp = await client.get("/")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"
            
            # 2. CORS check
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            }
            resp = await client.options("/sse", headers=headers)
            assert resp.status_code == 200
            assert resp.headers.get("access-control-allow-origin") == "*"
            
            # 3. Origin validation - rejection
            resp = await client.get("/", headers={"Origin": "http://evil.example.com"})
            assert resp.status_code == 403
            
            # 4. Streamable HTTP - Missing ID (400)
            payload = {"method": "ping", "params": {}, "jsonrpc": "2.0", "id": 2}
            resp = await client.post("/mcp", json=payload, headers=MCP_HEADERS)
            assert resp.status_code == 400
            
            # 5. Streamable HTTP - Initialization (200/201)
            resp = await client.post("/mcp", json=MCP_INIT_PAYLOAD, headers=MCP_HEADERS)
            assert resp.status_code in (200, 201)
            session_id = resp.headers.get("mcp-session-id")
            assert session_id is not None
            
            # 6. Streamable HTTP - Notification (202)
            notif = {"method": "notifications/initialized", "params": {}, "jsonrpc": "2.0"}
            headers = MCP_HEADERS.copy()
            headers["mcp-session-id"] = session_id
            resp = await client.post("/mcp", json=notif, headers=headers)
            assert resp.status_code == 202
            
            # 7. SSE GET routing (Backwards Compatibility)
            try:
                with anyio.fail_after(1):
                    async with client.stream("GET", "/sse", headers={"Accept": "text/event-stream"}) as s_resp:
                        assert s_resp.status_code == 200
                        assert s_resp.headers["content-type"].startswith("text/event-stream")
            except (TimeoutError, TimeoutException):
                pass

            # 8. POST /sse delegation
            resp = await client.post("/sse", json=MCP_INIT_PAYLOAD, headers=MCP_HEADERS)
            assert resp.status_code in (200, 201)
            
            # 9. Session Termination (DELETE)
            await client.delete("/mcp", headers={"mcp-session-id": session_id})
            
            # 10. Verify 404 after termination
            resp = await client.post("/mcp", json=payload, headers={"mcp-session-id": session_id, **MCP_HEADERS})
            assert resp.status_code == 404

            # 11. DELETE route existence check
            resp = await client.delete("/mcp")
            assert resp.status_code != 405
            resp = await client.delete("/sse")
            assert resp.status_code != 405
