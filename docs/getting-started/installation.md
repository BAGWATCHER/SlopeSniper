# Installation

## Requirements

- Python 3.10 or higher
- A Solana wallet with SOL for transactions

## Install from PyPI

```bash
pip install slopesniper-skill
```

## Install from Source

```bash
git clone https://github.com/slopesniper/slopesniper-skill.git
cd slopesniper-skill
pip install -e .
```

## Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

This includes:
- pytest for testing
- ruff for linting
- mypy for type checking

## Verify Installation

```python
from slopesniper_skill import __version__
print(f"SlopeSniper Skill v{__version__}")
```

## Next Steps

- [Configure your wallet](configuration.md)
- [Try the quick start](quickstart.md)
