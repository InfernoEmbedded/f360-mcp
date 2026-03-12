# Fusion 360 MCP Wrapper

An Model Context Protocol (MCP) server that provides a bridge between AI agents (like Claude Desktop) and Autodesk Fusion 360. It allows agents to perform complex CAD operations, modify designs, and query model state directly through the Fusion 360 API.

## Architecture

The project consists of two main components:

1.  **Fusion 360 Add-In (`f360_mcp_addin`)**: A Python Add-In that runs inside Fusion 360. It acts as a TCP server (default port 30011), listening for JSON-RPC commands and executing them via the native Fusion 360 API (`adsk`).
2.  **MCP Server (`f360_mcp_server`)**: A standalone Python application that implements the Model Context Protocol. It acts as a bridge, receiving MCP tool calls from an AI client and forwarding them to the Fusion 360 Add-In over a socket connection.

## Features

-   **Sketches**: Create sketches, lines, circles, rectangles, and apply constraints/dimensions.
-   **Solid Modeling**: Extrude, Revolve, Sweep, Loft, Fillet, Chamfer, Shell, and more.
-   **Management**: List, rename, and delete bodies, features, components, and construction geometry.
-   **Materials & Appearances**: Query available materials/appearances and apply them to bodies.
-   **Integration**: Export models (STEP/STL/F3D), execute custom internal scripts, and monitor design health (errors/warnings).

## Prerequisites

-   Autodesk Fusion 360
-   Python 3.12 or higher (for the MCP server)

## Installation

### 1. Install the Fusion 360 Add-In

1.  Open Fusion 360.
2.  Go to the **Utilities** tab and click on **Add-Ins** > **Scripts and Add-Ins**.
3.  Select the **Add-Ins** tab.
4.  Click the **+** (plus) icon to add a new add-in.
5.  Navigate to the `f360_mcp_addin` directory in this project and select it.
6.  Select **f360_mcp_addin** in the list and click **Run**.
    -   *Note: Check "Run on Startup" if you want it to always be available.*

### 2. Set up the MCP Server

1.  Navigate to the `f360_mcp_server` directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Configuration

The MCP server can be configured via environment variables:
-   `F360_ADDIN_HOST`: The IP address where Fusion 360 is running (default: `127.0.0.1`).
-   `F360_ADDIN_PORT`: The port the Add-In is listening on (default: `30011`).

### Running with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "/path/to/your/python",
      "args": [
        "/path/to/f360-mcp/f360_mcp_server/server.py",
        "--transport", "stdio"
      ],
      "env": {
        "F360_ADDIN_HOST": "127.0.0.1",
        "F360_ADDIN_PORT": "30011"
      }
    }
  }
}
```

### Running with Open WebUI (Native HTTP/SSE)

The server supports native SSE (Server-Sent Events) for direct integration with web interfaces like Open WebUI.

1.  Start the MCP server in SSE mode:
    ```bash
    # Ensure virtualenv is active
    python server.py --transport sse --host 0.0.0.0 --port 8000
    ```
2.  In Open WebUI, go to **Settings** > **External Tools**.
3.  Click **+** to add a new server.
4.  Set the **Type** to `MCP (Streamable HTTP)`.
5.  Set the **Server URL** to `http://your-ip:8000/sse`.
6.  Click **Save**.

### Running as a Systemd Service (Linux)

For persistent access, you can install the MCP server as a background service:

1.  **Run the install script**:
    ```bash
    sudo ./scripts/install_service.sh
    ```
2.  **Follow the prompts** to set the host (e.g., `0.0.0.0`) and port (e.g., `8000`).
3.  **Manage the service**:
    ```bash
    # Check status
    sudo systemctl status fusion360-mcp
    
    # Restart
    sudo systemctl restart fusion360-mcp
    ```

### Command Line Arguments

The `server.py` supports several configurations:
-   `--transport`: `stdio` (default) or `sse`.
-   `--host`: Host for SSE server (default: `127.0.0.1`).
-   `--port`: Port for SSE server (default: `8000`).

Environment variables can also be used: `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`.


## Development and Testing

The project includes a comprehensive suite of unit tests using a threaded mock server.

To run the tests:
1.  Navigate to the `f360_mcp_server` directory.
2.  Ensure your virtual environment is active.
3.  Run pytest:
    ```bash
    export PYTHONPATH=$PYTHONPATH:.  # Add current dir to path
    pytest -v
    ```

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See [LICENCE.txt](LICENCE.txt) for details.
