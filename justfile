packages := "grader,desktop"
project_content := "src main.py"

init:
    python3 -m venv .venv
    venv
    pip install -r requirements.txt

# Linting
lint:
    uv run ruff format
    uv run pylint {{project_content}} --fail-under 9
    uv run mypy {{project_content}} --ignore-missing-imports
    uv run ruff check {{project_content}}
    uv run complexipy .

# Tests
test: unit_tests functional_tests

unit_tests:
    uv run -m unittest discover -s tests/unit -p "test_*.py" -v

functional_tests:
    uv run -m unittest discover -s tests/functional -p "test_*.py"

coverage:
    uv run coverage run --source={{packages}} -m unittest discover -s tests/unit -p "test_*.py"
    uv run coverage lcov -o lcov.info
    uv run coverage report -m --fail-under 85 --sort=cover

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


build_diagrams:
    java -jar ~/plantuml-1.2025.4.jar ./docs/diagrams/*.puml -o out

build_docker:
    uv sync
    uv lock
    docker build -f Dockerfile -t pygrader:latest .
