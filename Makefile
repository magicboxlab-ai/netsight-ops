# netsight-ops development helpers
# Usage: make <target>

.PHONY: install install-sdk-local test lint clean

# Install netsight-ops in editable mode (pulls netsight-sdk from PyPI/git)
install:
	python -m pip install -e '.[dev]'

# Install with a LOCAL netsight-sdk checkout for cross-repo development.
# Usage: make install-sdk-local SDK=../api-sandbox
SDK ?= ../api-sandbox
install-sdk-local:
	python -m pip install -e '$(SDK)'
	python -m pip install -e '.[dev]'

# Run the test suite
test:
	python -m pytest tests/ -q

# Run linters
lint:
	python -m ruff check netsight_ops/ tests/
	python -m mypy netsight_ops/ --ignore-missing-imports

# Remove build artifacts
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
