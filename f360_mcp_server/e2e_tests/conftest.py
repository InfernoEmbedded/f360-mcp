import sys
import os
import pytest
import httpx
import anyio
import time
import logging
import json

ADDIN_HOST = os.environ.get("F360_ADDIN_HOST")
SKIP_E2E = not ADDIN_HOST

@pytest.fixture(scope="module")
def mcp_server():
    """Starts the MCP server as a subprocess and connects to it."""
    import subprocess
    import time
    import socket
    
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["MCP_TRANSPORT"] = "streamable-http"
    env["MCP_HOST"] = "127.0.0.1"
    env["MCP_PORT"] = "8360"
    env["F360_RECORD_COMMANDS"] = "true"
    
    # Start the server process
    log_file = open("/tmp/mcp_server.out", "w")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "server"],
        env=env,
        stdout=log_file,
        stderr=log_file,
        bufsize=1, # Line buffered
    )
    # We'll attach the log file handle to the process object so we can close it later
    server_proc.log_file = log_file
    
    # Wait for the server to be ready using socket
    base_url = "http://127.0.0.1:8360"
    timeout = 15.0
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(("127.0.0.1", 8360), timeout=1.0):
                break
        except (socket.timeout, ConnectionRefusedError):
            pass
        time.sleep(0.5)
    else:
        server_proc.terminate()
        stdout, stderr = server_proc.communicate()
        raise Exception(f"Server failed to start within {timeout}s.\nSTDOUT: {stdout}\nSTDERR: {stderr}")

    yield base_url

    # Cleanup: kill the server
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_proc.kill()

@pytest.fixture(scope="function")
async def mcp_client(mcp_server):
    """Initializes an MCP session and yields the client and session id."""
    base_url = mcp_server
@pytest.fixture(scope="function")
async def mcp_client(mcp_server):
    """Initializes an MCP session and yields the session metadata."""
    base_url = mcp_server
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        # Initialize MCP session
        init_payload = {
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "e2e-test", "version": "1.0.0"},
            },
            "jsonrpc": "2.0",
            "id": 0,
        }
        resp = await client.post(
            "/mcp", 
            json=init_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
        )
        if resp.status_code != 200:
            raise Exception(f"MCP Handshake failed with status {resp.status_code}: {resp.text}")
            
        session_id = resp.headers.get("mcp-session-id")
        if not session_id:
            raise Exception("MCP Handshake failed: No mcp-session-id in response headers")
        
        # Wait for tools to be discovered
        logger = logging.getLogger("pytest")
        logger.info("Waiting for modeling tools to be discovered...")
        timeout = 60.0 # Increased from 30.0
        start_time = time.time()
        import re
        def parse_mcp(content: bytes) -> dict:
            if not content: return {}
            text = content.decode("utf-8")
            if text.startswith("event:"):
                match = re.search(r"data: (\{.*\})", text)
                if match: return json.loads(match.group(1))
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}

        while time.time() - start_time < timeout:
            list_payload = {
                "method": "tools/list",
                "params": {},
                "jsonrpc": "2.0",
                "id": 1,
            }
            list_resp = await client.post(
                "/mcp", 
                json=list_payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": session_id
                }
            )
            if list_resp.status_code == 200:
                tools_data = parse_mcp(list_resp.content)
                tools = tools_data.get("result", {}).get("tools", [])
                if len(tools) > 5: # We expect ~40+ tools
                    logger.info(f"Discovered {len(tools)} tools. Proceeding.")
                    break
            await anyio.sleep(2.0)
        else:
            raise Exception(f"Tools failed to appear within {timeout}s")

        # We only surrender the session info, not the client itself
        # to avoid event loop issues with shared httpx clients
        yield {"base_url": base_url, "session_id": session_id}
        
        # TEARDOWN: Close active document
        payload = {
            "method": "tools/call",
            "params": {
                "name": "close_document",
                "arguments": {"save": False}
            },
            "jsonrpc": "2.0",
            "id": 999
        }
        await client.post(
            "/mcp", 
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id
            }
        )
