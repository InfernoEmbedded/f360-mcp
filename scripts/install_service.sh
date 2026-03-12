#!/bin/bash

# Configuration
SERVICE_NAME="fusion360-mcp"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/fusion360-mcp.service.template"
WORKING_DIR="$(cd "${SCRIPT_DIR}/../f360_mcp_server" && pwd)"
VENV_PYTHON="${WORKING_DIR}/venv/bin/python"

# Default values
DEFAULT_MCP_HOST="0.0.0.0"
DEFAULT_MCP_PORT="8000"
DEFAULT_F360_HOST="127.0.0.1"
DEFAULT_F360_PORT="30011"

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

# Ensure venv exists
if [ ! -d "$WORKING_DIR/venv" ]; then
    echo "Virtual environment not found. Creating it..."
    if ! runuser -u "$REAL_USER" -- python3 -m venv "$WORKING_DIR/venv"; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
    echo "Installing dependencies..."
    if ! runuser -u "$REAL_USER" -- "$VENV_PYTHON" -m pip install --upgrade pip; then
        echo "Error: Failed to upgrade pip."
        exit 1
    fi
    if ! runuser -u "$REAL_USER" -- "$VENV_PYTHON" -m pip install -r "$WORKING_DIR/requirements.txt"; then
        echo "Error: Failed to install dependencies."
        exit 1
    fi
    echo "Virtual environment setup complete."
else
    echo "Existing virtual environment found."
fi

# Prompt for settings
if [ -z "$NON_INTERACTIVE" ]; then
    read -p "Enter MCP HTTP Host [$DEFAULT_MCP_HOST]: " MCP_HOST
    MCP_HOST=${MCP_HOST:-$DEFAULT_MCP_HOST}

    read -p "Enter MCP HTTP Port [$DEFAULT_MCP_PORT]: " MCP_PORT
    MCP_PORT=${MCP_PORT:-$DEFAULT_MCP_PORT}

    read -p "Enter Fusion 360 Add-in Host [$DEFAULT_F360_HOST]: " F360_HOST
    F360_HOST=${F360_HOST:-$DEFAULT_F360_HOST}

    read -p "Enter Fusion 360 Add-in Port [$DEFAULT_F360_PORT]: " F360_PORT
    F360_PORT=${F360_PORT:-$DEFAULT_F360_PORT}
else
    MCP_HOST=${MCP_HOST:-$DEFAULT_MCP_HOST}
    MCP_PORT=${MCP_PORT:-$DEFAULT_MCP_PORT}
    F360_HOST=${F360_HOST:-$DEFAULT_F360_HOST}
    F360_PORT=${F360_PORT:-$DEFAULT_F360_PORT}
fi

# Create environment file
ENV_FILE="/etc/default/fusion360-mcp"
echo "Creating environment file at $ENV_FILE..."
cat <<EOF > "$ENV_FILE"
# Fusion 360 MCP Server Configuration
MCP_TRANSPORT=sse
MCP_HOST=$MCP_HOST
MCP_PORT=$MCP_PORT
F360_ADDIN_HOST=$F360_HOST
F360_ADDIN_PORT=$F360_PORT
EOF

chmod 644 "$ENV_FILE"

# Create service file from template
echo "Creating service file at $SERVICE_FILE..."
sed -e "s|{{USER}}|$REAL_USER|g" \
    -e "s|{{GROUP}}|$REAL_GROUP|g" \
    -e "s|{{WORKING_DIR}}|$WORKING_DIR|g" \
    -e "s|{{VENV_PYTHON}}|$VENV_PYTHON|g" \
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
