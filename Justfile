[private]
default:
    @just --list

lint:
    just --fmt --check --unstable
    uv lock --check
    uv run yamllint --format colored -s .
    uv run ruff check .
    uv run gitleaks git -v --no-banner

mise:
    mise trust .
    mise install
    uv sync --locked --extra dev

test:
    uv run pytest -v

build:
    rm -rf dist/
    uv build --no-sources

publish: lint test build
    UV_PUBLISH_TOKEN="$(op read --account my.1password.com 'op://Private/PyPI/token')" uv publish
