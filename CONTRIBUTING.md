# Contributing to SlopeSniper Skill

Thanks for your interest in contributing! See our [full contributing guide](https://slopesniper.github.io/slopesniper-skill/contributing/) for details.

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

## Code Style

- Type hints required
- PEP 8 style
- Docstrings for public functions

## Security Issues

Email security@slopesniper.io for vulnerabilities.
