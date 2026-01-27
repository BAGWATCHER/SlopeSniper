# SlopeSniper Production Launch Checklist

## Pre-Launch Verification

### Code Quality
- [x] All code merged to main branch
- [x] URLs updated to production repo (BAGWATCHER/SlopeSniper)
- [x] Install scripts tested
- [ ] Run full test suite
- [ ] Verify no hardcoded test keys

### Security Review
- [x] Private keys never logged or exposed
- [x] Two-step swap confirmation for large trades
- [x] Rugcheck integration for scam protection
- [x] Policy gates enforced
- [ ] Review for any security vulnerabilities

### Documentation
- [x] README updated with all install methods
- [x] SKILL.md follows Clawdbot spec
- [x] COWORK.md for Cowork users
- [x] GETTING_STARTED.md for Claude Desktop

---

## ClawdHub Publication

### 1. Login to ClawdHub
```bash
clawdhub login
```

### 2. Publish the Skill
```bash
cd /Users/admin/hoss/SlopeSniper
clawdhub publish ./skills/slopesniper \
  --slug slopesniper \
  --name "SlopeSniper" \
  --version 1.0.0 \
  --changelog "Initial release: Trade Solana tokens via natural language" \
  --tags latest,solana,trading,defi
```

### 3. Verify Publication
```bash
clawdhub info slopesniper
```

---

## Installation URLs (Production)

### Clawdbot (after ClawdHub publish)
```bash
clawdhub install slopesniper
```

### Direct Install (curl)
```bash
curl -fsSL https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/skills/install.sh | bash
```

### Manual Install
```bash
git clone https://github.com/BAGWATCHER/SlopeSniper.git
cp -r SlopeSniper/skills/slopesniper ~/.clawdbot/skills/
```

---

## Post-Launch

### Monitoring
- [ ] Monitor GitHub issues for bug reports
- [ ] Check ClawdHub download stats
- [ ] Gather user feedback

### Future Updates
```bash
# Bump version and republish
clawdhub sync --all --bump patch --changelog "Bug fixes"
```

---

## Quick Test Commands

```bash
# Test the skill locally
cd /Users/admin/hoss/SlopeSniper/mcp-extension
uv run python -c "
from slopesniper_skill import get_status
import asyncio
print(asyncio.run(get_status()))
"

# Test the API server
uv run uvicorn slopesniper_api.server:app --port 8420 &
curl http://localhost:8420/status
```

---

## Contact

- GitHub: https://github.com/BAGWATCHER/SlopeSniper
- Issues: https://github.com/BAGWATCHER/SlopeSniper/issues
