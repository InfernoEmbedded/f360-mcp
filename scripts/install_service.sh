#!/bin/bash

# Configuration
SERVICE_NAME="fusion360-mcp"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/fusion360-mcp.service.template"
WORKING_DIR="$(cd "${SCRIPT_DIR}/../f360_mcp_server" && pwd)"
VENV_PYTHON="${WORKING_DIR}/venv/bin/python"

# Default values
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (use sudo)"
  exit 1
fi

# Get current non-root user
REAL_USER=${SUDO_USER:-$(whoami)}
REAL_GROUP=$(id -gn "$REAL_USER")

echo "----------------------------------------------------"
echo "Fusion 360 MCP Systemd Service Installer"
echo "Installing for User: $REAL_USER"
echo "Working Directory:   $WORKING_DIR"
echo "----------------------------------------------------"

# Prompt for settings (optional in non-interactive if needed)
if [ -z "$NON_INTERACTIVE" ]; then
    read -p "Enter MCP Host [$DEFAULT_HOST]: " MCP_HOST
    MCP_HOST=${MCP_HOST:-$DEFAULT_HOST}

    read -p "Enter MCP Port [$DEFAULT_PORT]: " MCP_PORT
    MCP_PORT=${MCP_PORT:-$DEFAULT_PORT}
else
    MCP_HOST=${MCP_HOST:-$DEFAULT_HOST}
    MCP_PORT=${MCP_PORT:-$DEFAULT_PORT}
fi

# Fusion 360 Add-in defaults
F360_ADDIN_HOST="127.0.0.1"
F360_ADDIN_PORT="30011"

# Create service file from template
sed -e "s|{{USER}}|$REAL_USER|g" \
    -e "s|{{GROUP}}|$REAL_GROUP|g" \
    -e "s|{{WORKING_DIR}}|$WORKING_DIR|g" \
    -e "s|{{VENV_PYTHON}}|$VENV_PYTHON|g" \
    -e "s|{{MCP_HOST}}|$MCP_HOST|g" \
    -e "s|{{MCP_PORT}}|$MCP_PORT|g" \
    -e "s|{{F360_ADDIN_HOST}}|$F360_ADDIN_HOST|g" \
    -e "s|{{F360_ADDIN_PORT}}|$F360_ADDIN_PORT|g" \
    "$TEMPLATE_FILE" > "$SERVICE_FILE"

echo "Service file created at $SERVICE_FILE"

# Reload and start
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "----------------------------------------------------"
echo "Service $SERVICE_NAME installed and started!"
echo "Check status: systemctl status $SERVICE_NAME"
echo "----------------------------------------------------"
