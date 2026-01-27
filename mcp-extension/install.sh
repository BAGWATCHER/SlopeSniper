#!/bin/bash
#
# SlopeSniper Installer for Claude Desktop
# Run: curl -fsSL https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/mcp-extension/install.sh | bash
#

set -e

echo "🚀 Installing SlopeSniper for Claude Desktop..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for required tools
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv (Python package manager)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Set install directory
INSTALL_DIR="$HOME/.slopesniper"
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo "📁 Installing to: $INSTALL_DIR"

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main 2>/dev/null || true
else
    echo "📦 Downloading SlopeSniper..."
    git clone https://github.com/maddefientist/SlopeSniper.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR/mcp-extension"

# Install dependencies
echo "📚 Installing dependencies..."
uv sync --quiet

# Update Claude Desktop config
echo "⚙️  Configuring Claude Desktop..."

# Create config directory if needed
mkdir -p "$(dirname "$CONFIG_FILE")"

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    # Backup existing config
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"

    # Check if slopesniper already configured
    if grep -q "slopesniper" "$CONFIG_FILE"; then
        echo -e "${GREEN}✓ SlopeSniper already in config${NC}"
    else
        # Add slopesniper to existing config using Python
        python3 << EOF
import json
import os

config_path = os.path.expanduser("$CONFIG_FILE")
with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['slopesniper'] = {
    "command": "uv",
    "args": ["run", "--directory", "$INSTALL_DIR/mcp-extension", "python", "-m", "slopesniper_mcp.server"]
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("Added slopesniper to config")
EOF
    fi
else
    # Create new config
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "slopesniper": {
      "command": "uv",
      "args": ["run", "--directory", "$INSTALL_DIR/mcp-extension", "python", "-m", "slopesniper_mcp.server"]
    }
  }
}
EOF
fi

echo ""
echo -e "${GREEN}✅ SlopeSniper installed successfully!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Restart Claude Desktop (Cmd+Q, then reopen)"
echo ""
echo "2. Configure your wallet:"
echo "   • Open Claude Desktop → Settings → Developer"
echo "   • Find 'slopesniper' in MCP Servers"
echo "   • Add environment variable:"
echo "     SOLANA_PRIVATE_KEY = <your_private_key>"
echo ""
echo "3. Start trading! Say:"
echo '   "Check my trading status"'
echo '   "Buy $20 of BONK"'
echo '   "What tokens are trending?"'
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}⚠️  SECURITY TIP: Use a dedicated trading wallet!${NC}"
echo "   Only fund it with amounts you're willing to risk."
echo ""
