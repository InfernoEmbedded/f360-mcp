#!/usr/bin/env python3
"""
Utility to reload the Fusion 360 MCP Add-in.

Sends a reload_addin command directly to the add-in's TCP socket,
bypassing the MCP server. This is useful when the MCP server itself
needs to be restarted, or when you just want a quick add-in reload
after pushing code changes.

Usage:
    python reload_addin.py [--host HOST] [--port PORT] [--update]

    --host   Add-in host (default: from F360_ADDIN_HOST env, or 127.0.0.1)
    --port   Add-in port (default: from F360_ADDIN_PORT env, or 30011)
    --update Also git pull before reloading (calls update_and_reload_mcp via MCP)
"""

import asyncio
import json
import os
import sys
import argparse
from typing import Any


async def send_tcp_command(host: str, port: int, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send a JSON-RPC command directly to the add-in's TCP socket."""
    request = {
        "method": method,
        "params": params or {},
        "id": 1,
        "jsonrpc": "2.0"
    }
    
    reader, writer = await asyncio.open_connection(host, port)

    payload = json.dumps(request).encode("utf-8") + b"\n"
    writer.write(payload)
    await writer.drain()

    response_bytes = await reader.readline()
    if not response_bytes:
        raise RuntimeError("No response received from add-in")

    response = json.loads(response_bytes.decode("utf-8"))
    
    writer.close()
    await writer.wait_closed()
    
    return response


async def reload_via_tcp(host: str, port: int):
    """Reload the add-in by sending reload_addin directly over TCP."""
    print(f"Connecting to add-in at {host}:{port}...")
    
    # First ping to verify connectivity
    try:
        ping = await send_tcp_command(host, port, "get_version")
        version_result = ping.get("result")
        version = version_result if isinstance(version_result, str) else ping.get("result", {}).get("version", "unknown")
        print(f"Connected! Current add-in version: {version}")
    except Exception as e:
        print(f"Error: Cannot connect to add-in at {host}:{port}: {e}")
        sys.exit(1)
    
    # Send reload command
    print("Sending reload_addin command...")
    try:
        result = await send_tcp_command(host, port, "reload_addin")
        message = result.get("result", {}).get("message", str(result))
        print(f"Result: {message}")
    except Exception as e:
        print(f"Reload command sent (connection may have closed during restart): {e}")
    
    # Wait and verify the add-in comes back
    print("Waiting for add-in to restart...")
    for attempt in range(30):
        await asyncio.sleep(2)
        try:
            ping = await send_tcp_command(host, port, "get_version")
            version_result = ping.get("result")
            new_version = version_result if isinstance(version_result, str) else ping.get("result", {}).get("version", "unknown")
            print(f"Add-in is back! Version: {new_version}")
            return True
        except (ConnectionRefusedError, OSError):
            print(f"  Attempt {attempt + 1}/30 - not ready yet...")
            continue
    
    print("Warning: Add-in did not come back within 60 seconds.")
    return False


async def reload_via_mcp(base_url: str):
    """Reload via the MCP server's update_and_reload_mcp tool."""
    try:
        import httpx
    except ImportError:
        print("Error: httpx is required for MCP-based reload. Install with: pip install httpx")
        sys.exit(1)
    
    async with httpx.AsyncClient(base_url=base_url, timeout=120.0) as client:
        # Initialize MCP session
        init_payload = {
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "reload-utility", "version": "1.0.0"},
            },
            "jsonrpc": "2.0",
            "id": 0,
        }
        resp = await client.post("/mcp", json=init_payload, headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })
        if resp.status_code != 200:
            print(f"Error: MCP handshake failed: {resp.status_code}")
            sys.exit(1)
        
        session_id = resp.headers.get("mcp-session-id")
        
        # Call update_and_reload_mcp
        payload = {
            "method": "tools/call",
            "params": {
                "name": "update_and_reload_mcp",
                "arguments": {"branch": "master"}
            },
            "jsonrpc": "2.0",
            "id": 1,
        }
        print("Calling update_and_reload_mcp via MCP server...")
        resp = await client.post("/mcp", json=payload, headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id,
        })
        print(f"Response: {resp.text[:500]}")


def main():
    parser = argparse.ArgumentParser(description="Reload the Fusion 360 MCP Add-in")
    parser.add_argument("--host", default=os.environ.get("F360_ADDIN_HOST", "127.0.0.1"),
                        help="Add-in host (default: F360_ADDIN_HOST or 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("F360_ADDIN_PORT", "30011")),
                        help="Add-in port (default: F360_ADDIN_PORT or 30011)")
    parser.add_argument("--update", action="store_true",
                        help="Also git pull before reloading (uses MCP server)")
    parser.add_argument("--mcp-url", default="http://127.0.0.1:8360",
                        help="MCP server URL for --update mode")
    
    args = parser.parse_args()
    
    if args.update:
        asyncio.run(reload_via_mcp(args.mcp_url))
    else:
        asyncio.run(reload_via_tcp(args.host, args.port))


if __name__ == "__main__":
    main()
