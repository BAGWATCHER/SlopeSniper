#!/bin/bash
# SlopeSniper Clawdbot Skill Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/skills/install.sh | bash

set -e

SKILL_NAME="slopesniper"
SKILLS_DIR="${HOME}/.clawdbot/skills"
REPO_URL="https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/skills/slopesniper"

echo "🎯 Installing SlopeSniper skill for Clawdbot..."

# Create skills directory if needed
mkdir -p "${SKILLS_DIR}/${SKILL_NAME}"

# Download SKILL.md
echo "📥 Downloading skill definition..."
curl -fsSL "${REPO_URL}/SKILL.md" -o "${SKILLS_DIR}/${SKILL_NAME}/SKILL.md"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "⚠️  'uv' not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python package
echo "📦 Installing SlopeSniper package..."
uv pip install --system "slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension" 2>/dev/null || \
uv pip install "slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension"

echo ""
echo "✅ SlopeSniper installed!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Add your wallet key to ~/.clawdbot/clawdbot.json:"
echo ""
echo '   {
     "skills": {
       "entries": {
         "slopesniper": {
           "apiKey": "YOUR_SOLANA_PRIVATE_KEY"
         }
       }
     }
   }'
echo ""
echo "2. Restart Clawdbot gateway"
echo ""
echo "3. Say 'check my status' to verify setup"
echo ""
echo "🎯 Happy trading!"
