"""Shared infrastructure for Fusion 360 E2E tests."""

import os
import json
import base64
import hashlib
import re
import difflib
from pathlib import Path
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

    def _normalize_step_content(self, content: bytes) -> bytes:
        """Strips non-deterministic metadata from STEP files for stable hashing."""
        try:
            text = content.decode("utf-8", errors="ignore")
            # 1. Normalize FILE_NAME section
            text = re.sub(
                r"FILE_NAME\s*\([^;]*\);",
                "FILE_NAME('normalized.step', '2026-03-18T00:00:00Z', (''), (''), 'normalized', 'normalized', '');",
                text,
                flags=re.DOTALL
            )
            # 2. Normalize PRODUCT and PRODUCT_DEFINITION IDs (which often contain timestamps)
            # Example: #95=PRODUCT_DEFINITION('2026-03-18-22-44-39-641','(Unsaved)',#96,#94);
            text = re.sub(
                r"(PRODUCT(?:_DEFINITION)?\s*\(')[^']*(')",
                r"\1normalized-id\2",
                text
            )
            return text.encode("utf-8")
        except Exception as e:
            print(f"Warning: STEP normalization failed: {e}")
            return content

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
        """Exports the current model, compares it to a reference, and saves command history."""
        # 1. Fetch command history from server
        import httpx
        from tests.test_utils import compare_command_logs
        reference_dir = Path(__file__).with_name("references")
        reference_step_path = reference_dir / f"e2e_{test_name}.step"
        update_references = os.environ.get("UPDATE_REFERENCES", "false").lower() == "true"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                history_resp = await client.get(f"{self.base_url}/history")
                if history_resp.status_code == 200:
                    history = history_resp.json().get("command_history", [])
                    # The test name prefix is 'e2e_' to avoid clashing with unit test references
                    compare_command_logs(f"e2e_{test_name}", history, "e2e_tests/references")
        except Exception as e:
            print(f"Warning: Failed to fetch and verify command history: {e}")

        # 2. Export STEP - path must be valid on the Fusion 360 host (always Windows)
        # We use %TEMP% expanded path. Fusion 360 runs on Windows regardless of
        # where the test runner is.
        temp_path = f"C:/Users/Public/Documents/e2e_{test_name}.step"
            
        result = await self.call_tool("export_model", {
            "file_path": temp_path,
            "file_type": "step",
            "send_to_mcp": True
        })
        
        content_b64 = result.get("file_content_base64")
        if not content_b64:
            raise Exception("No file content received from export_model")
            
            
        content_bytes = base64.b64decode(content_b64)
        normalized_content = self._normalize_step_content(content_bytes)
        current_hash = hashlib.sha256(normalized_content).hexdigest()

        if update_references:
            reference_dir.mkdir(parents=True, exist_ok=True)
            reference_step_path.write_bytes(normalized_content)
            print(f"[STABILITY] Updated STEP reference for {test_name} at {reference_step_path}")
        elif reference_step_path.exists():
            reference_bytes = reference_step_path.read_bytes()
            # Reference file is already normalized on save
            reference_step_hash = hashlib.sha256(reference_bytes).hexdigest()
            if current_hash != reference_step_hash:
                # Generate diff for easier analysis
                ref_text = reference_bytes.decode("utf-8", errors="ignore")
                curr_text = normalized_content.decode("utf-8", errors="ignore")
                diff = difflib.unified_diff(
                    ref_text.splitlines(),
                    curr_text.splitlines(),
                    fromfile="reference",
                    tofile="current",
                    lineterm=""
                )
                print(f"\n[STABILITY] STEP mismatch for {test_name}:")
                for line in list(diff)[:50]: # Show first 50 lines of diff
                    print(line)
                
                raise AssertionError(
                    f"STEP stability check failed for {test_name}: "
                    f"expected {reference_step_hash}, got {current_hash}. "
                    f"If this change is intentional, run with UPDATE_REFERENCES=true "
                    f"to update {reference_step_path.name}."
                )
        elif reference_hash:
            if current_hash != reference_hash:
                raise AssertionError(
                    f"STEP stability check failed for {test_name}: "
                    f"expected {reference_hash}, got {current_hash}."
                )
        else:
            raise FileNotFoundError(
                f"Reference STEP file not found for {test_name} at {reference_step_path}. "
                "Run tests with UPDATE_REFERENCES=true to generate it."
            )

        print(f"Test {test_name} STEP Hash: {current_hash}")
        
        return current_hash
