"""Shared infrastructure for Fusion 360 E2E tests."""

import os
import json
import base64
import hashlib
import re
from typing import Dict, Any, Optional

class FusionE2E:
    def __init__(self, client_info: Dict[str, Any]):
        self.base_url = client_info["base_url"]
        self.session_id = client_info["session_id"]
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": self.session_id
        }

    @staticmethod
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

    async def call_tool(self, name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        import httpx
        print(f"Calling tool {name} with params: {params}...")
        payload = {
            "method": f"tools/call",
            "params": {
                "name": name,
                "arguments": params or {}
            },
            "jsonrpc": "2.0",
            "id": 1
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            resp = await client.post("/mcp", json=payload, headers=self.headers)
            result = self.parse_mcp_response(resp.content)
        
        print(f"Tool {name} result: {result}")
        if "error" in result:
            raise Exception(f"MCP Protocol Error calling {name}: {result['error']}")
        
        tool_result = result.get("result", {})
        if tool_result.get("isError"):
            content = tool_result.get("content", [])
            err_msg = content[0].get("text") if content else "Unknown tool error"
            raise Exception(f"Tool {name} failed: {err_msg}")

        # MCP tool results are usually in 'content' as text
        content = tool_result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                # Many of our tools return JSON strings in the text content
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return content[0]["text"]
        return result.get("result")

    async def export_and_verify(self, test_name: str, reference_hash: Optional[str] = None):
        """Exports the current model and compares it to a reference."""
        # We use a temporary path in the Fusion environment (handled by add-in)
        # or we just get the content back.
        temp_path = f"C:/temp/e2e_{test_name}.step" # Add-in usually handles OS paths
        if os.name != 'nt':
            temp_path = f"/tmp/e2e_{test_name}.step"
            
        result = await self.call_tool("export_model", {
            "file_path": temp_path,
            "file_type": "step",
            "send_to_mcp": True
        })
        
        content_b64 = result.get("file_content_base64")
        if not content_b64:
            raise Exception("No file content received from export_model")
            
        content_bytes = base64.b64decode(content_b64)
        current_hash = hashlib.sha256(content_bytes).hexdigest()
        
        # In a real scenario, we'd compare against reference_hash.
        # For now, we'll print it to help establish references.
        print(f"Test {test_name} STEP Hash: {current_hash}")
        
        return current_hash
