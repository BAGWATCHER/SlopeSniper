# Contributing to SlopeSniper Skill

Thanks for your interest in contributing! See our [full contributing guide](https://slopesniper.github.io/slopesniper-skill/contributing/) for details.

## Version Control

We follow semantic versioning with issue-based patch increments:

**Format:** `0.MINOR.PATCH` (beta) → `MAJOR.MINOR.PATCH` (stable)

**Issue-based versioning:**
- Each GitHub issue addressed increments the patch version
- Example: Issues addressed at version `0.3.0` become `0.3.01`, `0.3.02`, etc.
- Multiple issues in one PR still get individual patch bumps

**Workflow:**
1. Fork to your account (e.g., `maddefientist/SlopeSniper`)
2. Create/use `bagwatcher-release` branch for staging changes
3. Address issue → bump version to `0.X.0Y` where Y is the issue sequence
4. Open PR back to `bagwatcher/slopesniper` main branch
5. Version file: `mcp-extension/src/slopesniper_skill/__init__.py`

**Version bump locations:**
- Primary: `mcp-extension/src/slopesniper_skill/__init__.py` (`__version__`)
- Keep other version strings in sync when doing major releases

## Quick Start

```bash
# Clone and setup
git clone https://github.com/slopesniper/slopesniper-skill.git
cd slopesniper-skill
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Make changes with tests
4. Run `pytest` and `ruff check`
5. Open a PR
6. **Pre-merge testing** (see below)

## Pre-Merge Testing (REQUIRED)

**Before merging any PR, test the dev branch as an actual install:**

```bash
# Install from dev branch (catches dependency/import issues)
uv tool install --force "git+https://github.com/maddefientist/SlopeSniper.git@bagwatcher-release#subdirectory=mcp-extension"

# Verify CLI works
slopesniper version
slopesniper status
```

> **Why this matters:** v0.3.2 shipped with a breaking import (`websockets` module missing at runtime). Local `pytest` passed because it uses the dev venv with all deps installed, but the global install failed because the new dependency wasn't being pulled. Always test the real install path before merging.

## Code Style

- Type hints required
- PEP 8 style
- Docstrings for public functions

## Security Issues

Email security@slopesniper.io for vulnerabilities.
