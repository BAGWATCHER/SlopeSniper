#!/bin/bash
# SlopeSniper Clawdbot Skill Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/skills/install.sh | bash

set -e

SKILL_NAME="slopesniper"
SKILLS_DIR="${HOME}/.clawdbot/skills"
REPO_URL="https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/skills/slopesniper"

echo ""
echo "==============================================================="
echo "   SlopeSniper - Solana Trading for Clawdbot"
echo "==============================================================="
echo ""

# Create directories
mkdir -p "${SKILLS_DIR}/${SKILL_NAME}"

# Download SKILL.md
echo "Downloading skill..."
curl -fsSL "${REPO_URL}/SKILL.md" -o "${SKILLS_DIR}/${SKILL_NAME}/SKILL.md"
echo "   Done: ~/.clawdbot/skills/slopesniper"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "   Done: uv installed"
fi

# Install Python package using uv tool
echo ""
echo "Installing SlopeSniper..."
uv tool install "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension" --force 2>/dev/null || \
uv tool install "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension" --reinstall 2>/dev/null || \
echo "   (Package may already be installed)"
echo "   Done: slopesniper CLI ready"

# Success message
echo ""
echo "==============================================================="
echo "   Installation complete!"
echo "==============================================================="
echo ""
echo "NEXT STEP: Run this command to set up your wallet:"
echo ""
echo "   slopesniper status"
echo ""
echo "This will:"
echo "   1. Auto-generate a new trading wallet"
echo "   2. Display your private key (SAVE IT!)"
echo "   3. Show your wallet address to fund"
echo ""
echo "Then send SOL to your wallet and start trading!"
echo ""
echo "==============================================================="
echo ""
