# Contributing

Thanks for your interest in contributing to SlopeSniper Skill!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/slopesniper/slopesniper-skill.git
cd slopesniper-skill
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=slopesniper_skill --cov-report=html
```

## Linting

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

## Type Checking

```bash
mypy src/
```

## Building Docs

```bash
pip install -e ".[docs]"
mkdocs serve
```

Visit http://localhost:8000 to preview.

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests and linting
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Code Style

- Use type hints for all function parameters and return values
- Follow [PEP 8](https://pep8.org/) style guidelines
- Write docstrings for public functions
- Keep functions focused and small
- Add tests for new functionality

## Commit Messages

Use clear, descriptive commit messages:

- `feat: Add new token search functionality`
- `fix: Handle expired intent gracefully`
- `docs: Update installation guide`
- `test: Add policy gate tests`
- `refactor: Simplify quote flow`

## Reporting Issues

When reporting issues, please include:

1. Python version
2. Package version
3. Steps to reproduce
4. Expected vs actual behavior
5. Any error messages

## Security Issues

For security vulnerabilities, please email security@slopesniper.io instead of opening a public issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
