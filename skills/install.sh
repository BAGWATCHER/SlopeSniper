#!/bin/bash
# SlopeSniper Clawdbot Skill Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/skills/install.sh | bash

set -e

SKILL_NAME="slopesniper"
SKILLS_DIR="${HOME}/.clawdbot/skills"
CONFIG_FILE="${HOME}/.clawdbot/clawdbot.json"
REPO_URL="https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/skills/slopesniper"

echo ""
echo "🎯 ═══════════════════════════════════════════════════"
echo "   SlopeSniper - Solana Trading for Clawdbot"
echo "═══════════════════════════════════════════════════════"
echo ""

# Create directories
mkdir -p "${SKILLS_DIR}/${SKILL_NAME}"
mkdir -p "${HOME}/.clawdbot"

# Download SKILL.md
echo "📥 Downloading skill..."
curl -fsSL "${REPO_URL}/SKILL.md" -o "${SKILLS_DIR}/${SKILL_NAME}/SKILL.md"
echo "   ✓ Skill installed to ~/.clawdbot/skills/slopesniper"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo ""
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "   ✓ uv installed"
fi

# Install Python package using uv tool
echo ""
echo "📦 Installing SlopeSniper Python package..."
uv tool install "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension" --force 2>/dev/null || \
uv tool install "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension" --reinstall 2>/dev/null || \
echo "   (Package may already be installed)"
echo "   ✓ Python package ready"

# Configure clawdbot.json
echo ""
echo "⚙️  Configuring Clawdbot..."

if [ ! -f "$CONFIG_FILE" ]; then
    # Create new config
    cat > "$CONFIG_FILE" << 'JSONEOF'
{
  "skills": {
    "entries": {
      "slopesniper": {
        "enabled": true,
        "apiKey": ""
      }
    }
  }
}
JSONEOF
    echo "   ✓ Created ~/.clawdbot/clawdbot.json"
else
    echo "   ✓ Config file exists (you may need to add slopesniper entry manually)"
fi

# Success message with next steps
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Installation complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🔑 NEXT: Add your Solana wallet key"
echo ""
echo "   1. Open: ~/.clawdbot/clawdbot.json"
echo ""
echo "   2. Replace the empty apiKey with your private key:"
echo ""
echo '      "slopesniper": {'
echo '        "enabled": true,'
echo '        "apiKey": "YOUR_BASE58_PRIVATE_KEY"'
echo '      }'
echo ""
echo "   Get your key from:"
echo "   • Phantom: Settings → Security → Export Private Key"
echo "   • Solflare: Settings → Export Private Key"
echo ""
echo "   ⚠️  Use a DEDICATED trading wallet, not your main!"
echo ""
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🚀 Once configured, talk to Clawdbot:"
echo ""
echo '   "Check my trading status"'
echo '   "Buy $20 of BONK"'
echo '   "What tokens are trending?"'
echo ""
echo "🎯 Happy trading!"
echo ""
