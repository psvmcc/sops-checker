# Repository Guidelines

## Project Structure & Module Organization
- `src/sops_checker/`: production code. `cli.py` holds the CLI logic, `__init__.py` exposes `__version__`, and `__main__.py` enables `python -m sops_checker`.
- `sops-checker.py`: convenience entry point that injects `src/` into `PYTHONPATH` for ad-hoc runs.
- `tests/`: unit (`test_cli.py`), integration (`test_integration.py`), and shared fixtures under `tests/fixtures/repo/`.
- Root files of note: `pyproject.toml` (packaging/config), `Justfile` (dev shortcuts), `.github/workflows/` (CI/release), `LICENSE`, and `README.md`.

## Build, Test, and Development Commands
- `uv sync` – create or refresh the managed virtualenv (installs base + extras declared in `pyproject.toml`). Use `UV_CACHE_DIR=.uv-cache uv sync` if cache permissions are limited.
- `just lint` – runs `ruff check .` through uv.
- `just test` – executes `uv run pytest` across all suites.
- `just publish` – `uv publish` to PyPI (make sure `PYPI_API_TOKEN` is configured).
- `gitleaks` is expected to be available on PATH for the lint recipe; install via Homebrew or binaries from upstream.
- `uv run sops-checker --help` – run the CLI without installing globally.
- All files (Python modules, shell snippets, `Justfile`, etc.) must use 4 spaces per indent level—never tabs.

## Coding Style & Naming Conventions
- Python 3.8+ codebase; follow PEP 8 with Ruff enforcing formatting/linting. Run `ruff check` before submitting.
- Use type hints and descriptive names (`looks_sops_encrypted`, `iter_rule_matches`).
- Stick to snake_case for functions/modules, SCREAMING_SNAKE_CASE for constants (e.g., `GREEN`, `RESET`).

## Testing Guidelines
- Pytest is the testing framework; files live under `tests/` and should be named `test_*.py`. Use fixtures (`fixture_repo`) for shared setups.
- Ensure new features include both unit coverage in `test_cli.py` and high-level coverage in `test_integration.py`.
- Run `just test` (or `uv run pytest`) locally; CI will run Ruff, Yamllint, and Pytest on every push/PR.

## Commit & Pull Request Guidelines
- No commit history exists yet; adopt short, imperative subjects (e.g., `Add integration fixtures`, `Fix Ruff warnings`) and detail motivation/body when necessary.
- PRs should describe the change, list testing commands/results, and link issues when applicable. For user-visible CLI changes, include sample output or screenshots/log excerpts.

## Security & Configuration Tips
- Keep `.sops.yaml` accurate: tests rely on `tests/fixtures/repo` matching real-world rules.
- When testing `--fix`, ensure `sops` is on `PATH` or mimic it via the integration helper script pattern (`tests/test_integration.py`’s fake binary).
