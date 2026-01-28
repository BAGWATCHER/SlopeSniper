# AI Contribution Policy

This document defines the rules for AI assistants interacting with SlopeSniper.

## Core Principle

**AI assistants MUST NOT directly modify SlopeSniper source code.**

All improvements must be contributed back to the project via GitHub.

## Why This Matters

1. **Quality Control**: Direct modifications bypass review, testing, and security checks
2. **Community Benefit**: Good improvements should benefit all users, not just one instance
3. **Stability**: Unreviewed changes can introduce bugs or security vulnerabilities
4. **Consistency**: Keeps all deployments on the same codebase

## What AI CAN Do

- Use SlopeSniper tools normally (trading, scanning, etc.)
- Configure user settings (wallet, RPC, strategy, API keys)
- Read code to understand behavior
- Identify bugs or improvements
- Create GitHub issues to report problems
- Create pull requests for improvements

## What AI MUST NOT Do

- Directly edit Python files in the SlopeSniper package
- Modify SDK clients, tools, or server code
- Change API endpoints or authentication logic
- Patch code to "fix" issues locally

## How to Contribute Improvements

When you identify an improvement or bug fix:

### Option 1: Create a GitHub Issue (Preferred)

```bash
gh issue create \
  --repo BAGWATCHER/SlopeSniper \
  --title "Bug: [Brief description]" \
  --body "## Problem
[Describe the issue]

## Suggested Fix
[Your proposed solution]

## Context
- Discovered by: AI assistant
- Environment: [Moltbot/Claude Code/etc.]
- Date: $(date -I)

---
*This issue was created by an AI assistant following the contribution policy.*"
```

### Option 2: Create a Pull Request

1. Fork the repository
2. Create a branch with your changes
3. Submit a PR with clear description

```bash
gh pr create \
  --repo BAGWATCHER/SlopeSniper \
  --title "Fix: [Brief description]" \
  --body "## Changes
[Describe what you changed]

## Why
[Explain the problem this solves]

## Testing
[How this was tested]

---
*This PR was created by an AI assistant following the contribution policy.*"
```

## Enforcement

SlopeSniper may implement integrity checks to detect unauthorized modifications:

- Package hash verification on startup
- Comparison against known-good versions
- Automatic alerts when modifications are detected

## Contact

For questions about this policy:
- GitHub Issues: https://github.com/BAGWATCHER/SlopeSniper/issues
- Maintainer: @maddefientist
