import asyncio
import json
import socket
import sys
import uuid
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Configuration
ADDIN_HOST = '127.0.0.1'
ADDIN_PORT = 30011

mcp = FastMCP("fusion360-mcp")

async def send_to_addin(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to send JSON-RPC to the Fusion 360 Add-In."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())
    }
    
    # We use a blocking socket here but wrap it in an asyncio executor
    # or just use asyncio sockets. For simplicity, we'll try standard sockets
    # since these are fast local calls.
    
    def sync_request():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0) # 5 second timeout
            s.connect((ADDIN_HOST, ADDIN_PORT))
            s.sendall(json.dumps(request).encode('utf-8') + b'\n')
            
            # Read response
            buffer = ""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                if '\n' in buffer:
                    break
            
            return buffer.strip()

    try:
        response_data = await asyncio.to_thread(sync_request)
        response = json.loads(response_data)
        
        if "error" in response:
            raise Exception(f"Fusion 360 Error: {response['error']}")
            
        return response.get("result", {})
    except ConnectionRefusedError:
        raise Exception(f"Could not connect to Fusion 360 Add-In at {ADDIN_HOST}:{ADDIN_PORT}. Is it running?")
    except json.JSONDecodeError:
        raise Exception("Invalid response from Fusion 360 Add-In.")

@mcp.tool()
async def create_sketch(plane_name: str = "XY") -> Dict[str, Any]:
    """
    Creates a new empty sketch in the active Fusion 360 design.
    Plane name can be "XY", "XZ", or "YZ".
    Returns the newly created sketch name.
    """
    return await send_to_addin('create_sketch', {"plane_name": plane_name})

@mcp.tool()
async def add_circle(sketch_name: str, x: float, y: float, radius: float) -> Dict[str, Any]:
    """
    Adds a circle to an existing sketch in Fusion 360.
    Dimensions are in centimeters (cm).
    """
    return await send_to_addin('add_circle', {
        "sketch_name": sketch_name,
        "x": x,
        "y": y,
        "radius": radius
    })

@mcp.tool()
async def add_line(sketch_name: str, x1: float, y1: float, x2: float, y2: float) -> Dict[str, Any]:
    """
    Adds a line to an existing sketch in Fusion 360.
    Dimensions are in centimeters (cm).
    """
    return await send_to_addin('add_line', {
        "sketch_name": sketch_name,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2
    })

if __name__ == "__main__":
    # Start as a standard io server for Claude Desktop / general MCP clients
    mcp.run(transport='stdio')
