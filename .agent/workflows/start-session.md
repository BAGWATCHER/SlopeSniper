---
description: Load project context at the start of every session on SlopeSniper
---

# SlopeSniper Session Start

Follow these steps at the beginning of every session:

## 1. Read Project Context
// turbo
```bash
cat /Users/adamn/SlopeSniper/CONTEXT.md
```

## 2. Check Current Version
// turbo
```bash
/Users/adamn/.local/bin/slopesniper version
```

## 3. Check Git Status
// turbo
```bash
cd /Users/adamn/SlopeSniper && git status
```

## 4. Check for Remote Updates
```bash
cd /Users/adamn/SlopeSniper && git fetch origin && git log --oneline origin/main...HEAD
```
If updates exist, ask user before pulling.

---

> [!CAUTION]
> **DO NOT PUSH TO GITHUB** - This is a professional public repo. We only pull.

**After completing these steps, you have full context on:**
- Project architecture and structure
- SDK clients and tools
- Development workflow and versioning
- Current version and git state
