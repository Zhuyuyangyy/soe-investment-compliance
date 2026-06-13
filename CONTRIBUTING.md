# Contributing to SOE Investment Compliance

Thank you for your interest in contributing to the SOE Investment Compliance system.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. Run tests to verify setup:
   ```bash
   pytest tests/ -v
   ```

## Code Standards

- **Python**: Follow PEP 8 style guide
- **Linting**: Use `ruff check` before committing
- **Formatting**: Use `ruff format` for consistent formatting
- **Type Hints**: Add type hints to all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions

## Testing

- Write tests for all new features
- Maintain 80%+ test coverage
- Run the full test suite before submitting PR:
  ```bash
  pytest tests/ -v --cov=backend --cov-report=term-missing
  ```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Add/update tests as needed
4. Ensure all tests pass
5. Update documentation if applicable
6. Submit a pull request with a clear description

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Include relevant logs and error messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
