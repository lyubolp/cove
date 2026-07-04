# packages := "grader,desktop"
project_content := "src main.py"

init:
    python3 -m venv .venv
    venv
    pip install -r requirements.txt

# Linting
lint:
    uv run ruff check {{project_content}} --fix
    uv run ruff format {{project_content}}
    uv run mypy {{project_content}} --ignore-missing-imports
    uv run complexipy .

# Tests
test:
    uv run pytest tests/ -v

coverage:
    uv run pytest tests/ --cov={{project_content}} --cov-report=term-missing --cov-report=lcov:lcov.info --cov-fail-under=85

# docs:
#     uv run sphinx-apidoc -o docs/source grader
#     uv run sphinx-build -b html docs/source docs/build

# Cleaning
clean:
    rm -rf .coverage
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -f lcov.info
    rm -rf __pycache__
    rm -rf .complexipy_cache
