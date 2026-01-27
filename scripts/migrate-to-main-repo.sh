#!/bin/bash
#
# SlopeSniper Migration Script: Fork → Main Repository
#
# This script updates all references from the fork (BAGWATCHER/SlopeSniper)
# to the main repository (BAGWATCHER/SlopeSniper) before creating a PR.
#
# Usage:
#   ./scripts/migrate-to-main-repo.sh [--dry-run]
#
# Options:
#   --dry-run    Show what would be changed without making changes
#

set -e

# Configuration
FROM_REPO="BAGWATCHER/SlopeSniper"
TO_REPO="BAGWATCHER/SlopeSniper"
FROM_USER="maddefientist"
TO_USER="BAGWATCHER"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}=== DRY RUN MODE ===${NC}"
    echo ""
fi

echo -e "${BLUE}SlopeSniper Migration Script${NC}"
echo "================================"
echo ""
echo "From: $FROM_REPO"
echo "To:   $TO_REPO"
echo ""

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo -e "${YELLOW}Scanning for references to $FROM_REPO...${NC}"
echo ""

# Count occurrences
echo "Files containing '$FROM_REPO':"
echo ""

TOTAL_COUNT=0
for file in $(find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.json" -o -name "*.toml" -o -name "*.yml" -o -name "*.yaml" \) 2>/dev/null | grep -v '.git/' | grep -v 'node_modules/' | grep -v '__pycache__/'); do
    if [ -f "$file" ]; then
        count=$(grep -c "$FROM_REPO" "$file" 2>/dev/null || true)
        if [ -n "$count" ] && [ "$count" -gt 0 ] 2>/dev/null; then
            echo "  $file: $count occurrence(s)"
            TOTAL_COUNT=$((TOTAL_COUNT + count))
        fi
    fi
done

echo ""
echo -e "Total: ${YELLOW}$TOTAL_COUNT${NC} occurrences in repository"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Dry run complete. No changes made.${NC}"
    echo ""
    echo "To apply changes, run without --dry-run:"
    echo "  ./scripts/migrate-to-main-repo.sh"
    exit 0
fi

# Confirm before proceeding
echo -e "${RED}This will modify files in place.${NC}"
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${YELLOW}Applying changes...${NC}"
echo ""

# Apply replacements
CHANGED_FILES=0

for file in $(find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.json" -o -name "*.toml" -o -name "*.yml" -o -name "*.yaml" \) 2>/dev/null | grep -v '.git/' | grep -v 'node_modules/' | grep -v '__pycache__/'); do
    if [ -f "$file" ] && grep -q "$FROM_REPO" "$file" 2>/dev/null; then
        echo "  Updating: $file"

        # Replace full repo path
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|$FROM_REPO|$TO_REPO|g" "$file"
        else
            sed -i "s|$FROM_REPO|$TO_REPO|g" "$file"
        fi

        CHANGED_FILES=$((CHANGED_FILES + 1))
    fi
done

echo ""
echo -e "${GREEN}Migration complete!${NC}"
echo ""
echo "Changed files: $CHANGED_FILES"
echo ""
echo -e "${YELLOW}=== MANUAL STEPS REQUIRED ===${NC}"
echo ""
echo "1. GitHub Token for Issue System (config/callback.json):"
echo "   - Generate a new GitHub Personal Access Token for $TO_REPO"
echo "   - Token needs: repo scope (for creating issues)"
echo "   - Encode using the XOR scheme in integrity.py"
echo "   - Update 'gh' field in config/callback.json"
echo ""
echo "2. Verify Jupiter API Key (config/jup.json):"
echo "   - The bundled Jupiter key can remain the same"
echo "   - Or generate a new key at: https://www.helius.dev"
echo ""
echo "3. Recalculate Integrity Hashes (config/integrity.json):"
echo "   - Run: python3 -c 'from slopesniper_skill.integrity import calculate_hashes; print(calculate_hashes())'"
echo "   - Update integrity.json with new hashes"
echo ""
echo "4. GitHub Actions/Secrets:"
echo "   - If using GitHub Actions, set up repository secrets"
echo "   - JUPITER_API_KEY (optional)"
echo "   - Any deployment secrets needed"
echo ""
echo -e "${BLUE}=== AUTOMATED STEPS ===${NC}"
echo ""
echo "  1. Review changes: git diff"
echo "  2. Test the installation scripts work"
echo "  3. Commit: git add -A && git commit -m 'chore: migrate URLs to main repo'"
echo "  4. Create PR to $TO_REPO"
echo ""
