#!/bin/bash
# SlopeSniper Moltbot Skill Installer/Updater
# Usage: curl -fsSL https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/skills/install.sh | bash

set -e

SKILL_NAME="slopesniper"
REPO_URL="https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/skills/slopesniper"
PACKAGE_URL="slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension"

# Detect Moltbot/Clawdbot skills directory (supports both for backward compatibility)
detect_skills_dir() {
    # Check common locations - moltbot first, then clawdbot fallback
    local possible_dirs=(
        "$(npm root -g 2>/dev/null)/moltbot/skills"
        "$(dirname $(which moltbot 2>/dev/null) 2>/dev/null)/../lib/node_modules/moltbot/skills"
        "${HOME}/.moltbot/skills"
        "/usr/local/lib/node_modules/moltbot/skills"
        "/usr/lib/node_modules/moltbot/skills"
        "$(npm root -g 2>/dev/null)/clawdbot/skills"
        "$(dirname $(which clawdbot 2>/dev/null) 2>/dev/null)/../lib/node_modules/clawdbot/skills"
        "${HOME}/.clawdbot/skills"
        "/usr/local/lib/node_modules/clawdbot/skills"
        "/usr/lib/node_modules/clawdbot/skills"
    )

    for dir in "${possible_dirs[@]}"; do
        if [ -d "$dir" ] 2>/dev/null; then
            echo "$dir"
            return 0
        fi
    done

    # Fallback to ~/.moltbot/skills (new default)
    echo "${HOME}/.moltbot/skills"
}

SKILLS_DIR=$(detect_skills_dir)

# Detect if this is an update or fresh install
IS_UPDATE=false
if command -v slopesniper &> /dev/null; then
    IS_UPDATE=true
fi

echo ""
echo "==============================================================="
if [ "$IS_UPDATE" = true ]; then
    echo "   SlopeSniper - Updating..."
else
    echo "   SlopeSniper - Solana Trading for Moltbot"
fi
echo "==============================================================="
echo ""
echo "Skills directory: ${SKILLS_DIR}"
echo ""

# Create directories
mkdir -p "${SKILLS_DIR}/${SKILL_NAME}"

# Download SKILL.md (always update to get latest docs)
echo "Downloading skill definition..."
curl -fsSL "${REPO_URL}/SKILL.md" -o "${SKILLS_DIR}/${SKILL_NAME}/SKILL.md"
echo "   Done: ${SKILLS_DIR}/${SKILL_NAME}/SKILL.md"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "   Done: uv installed"
fi

# Install/Update Python package
echo ""
if [ "$IS_UPDATE" = true ]; then
    echo "Updating SlopeSniper..."
else
    echo "Installing SlopeSniper..."
fi

# Try uv tool install with --force (works for both install and update)
if uv tool install "${PACKAGE_URL}" --force 2>/dev/null; then
    echo "   Done: slopesniper CLI ready"
else
    # Fallback: try with --reinstall flag
    if uv tool install "${PACKAGE_URL}" --reinstall 2>/dev/null; then
        echo "   Done: slopesniper CLI ready"
    else
        echo "   Warning: uv tool install had issues, trying pip..."
        uv pip install --force-reinstall "${PACKAGE_URL}" 2>/dev/null || \
            pip install --force-reinstall "${PACKAGE_URL}" 2>/dev/null || \
            echo "   Error: Installation failed. Try manually with uv or pip."
    fi
fi

# Success message
echo ""
echo "==============================================================="
if [ "$IS_UPDATE" = true ]; then
    echo "   Update complete!"
    echo "==============================================================="
    echo ""
    echo "Check your version:"
    echo ""
    echo "   slopesniper version"
else
    echo "   Installation complete!"
    echo "==============================================================="
    echo ""
    echo "NEXT STEP: Run this command to set up your wallet:"
    echo ""
    echo "   slopesniper setup"
    echo ""
    echo "This will:"
    echo "   1. Guide you through wallet creation (interactive)"
    echo "   2. Display your private key (SAVE IT SECURELY!)"
    echo "   3. Confirm you've backed up your key"
    echo "   4. Show your wallet address to fund"
    echo ""
    echo "Then send SOL to your wallet and start trading!"
fi
echo ""
echo "To update in the future, run:"
echo ""
echo "   slopesniper update"
echo ""
echo "==============================================================="
echo ""
