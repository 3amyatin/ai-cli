# ai-cli task runner

# list available recipes
default:
    @just --list

# run the CLI with arguments
run *ARGS:
    uv run ai {{ARGS}}

# install as uv tool (editable)
install:
    uv tool install -e .

# update dependencies
update:
    uv lock --upgrade
    uv sync

# sync venv with lockfile
sync:
    uv sync

# run tests
test *ARGS:
    uv run pytest {{ARGS}}

# lint
lint:
    uv run ruff check ai_cli/ tests/

# format code
fmt:
    uv run ruff format ai_cli/ tests/

# lint + format
check: lint fmt

# fix lint issues automatically
fix:
    uv run ruff check --fix ai_cli/ tests/
