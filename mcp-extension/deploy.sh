#!/bin/bash
# Deploy SlopeSniper API to webvm
#
# Prerequisites:
#   - SSH access to webvm (192.168.1.220)
#   - Docker and docker-compose installed on webvm
#   - SOLANA_PRIVATE_KEY set on target

set -e

REMOTE_HOST="${REMOTE_HOST:-192.168.1.220}"
REMOTE_USER="${REMOTE_USER:-admin}"
REMOTE_DIR="/opt/slopesniper"

echo "Deploying SlopeSniper API to $REMOTE_HOST..."

# Create remote directory and sync files
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"

# Sync mcp-extension directory (contains Dockerfile, docker-compose, and src)
rsync -avz --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.venv' \
    --exclude 'uv.lock' \
    "$(dirname "$0")/" \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

echo "Files synced. Building and starting container..."

# Build and start on remote
ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose up -d --build"

echo ""
echo "Deployment complete!"
echo ""
echo "API running at: http://$REMOTE_HOST:8420"
echo ""
echo "Next steps:"
echo "  1. Set up Cloudflare Tunnel to expose port 8420"
echo "  2. Point tunnel to: slopesniper.maddefientist.com"
echo "  3. Test: curl https://slopesniper.maddefientist.com/config/jup"
echo ""
