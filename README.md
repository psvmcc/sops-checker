# sops-checker

`sops-checker` inspects the `creation_rules` in `.sops.yaml` and verifies that each matching file already looks SOPS-encrypted. It can optionally encrypt files in place via `sops --encrypt --in-place`. You can grab the latest release from [PyPI](https://pypi.org/project/sops-checker/).

> Built collaboratively with OpenAI Codex to streamline packaging and release prep.

SOPS itself is maintained by the [getsops community](https://github.com/getsops/sops) and contributors—huge thanks to them for the encryption tooling this checker relies on.

## Installation

```bash
pip install sops-checker
```

For development:

```bash
uv pip install -e .
```

### Prerequisites for local workflows

- **sops** – encrypts files when `--fix` is used; install via Homebrew (`brew install sops`) or your package manager.
- **mise** – optional toolchain manager if you rely on the provided `mise.toml` to install Python/uv/just (`mise install`).
- **uv** – fast package manager used in the Just recipes and CI (`brew install uv`).
- **just** – task runner powering the commands in `Justfile` (`brew install just`).
- **gitleaks** – required for `just lint` to run secrets scans (`brew install gitleaks`).

## Usage

```bash
sops-checker [ROOT] [--fix]
```

- `ROOT` defaults to the current directory.
- `--fix` encrypts files that match the rules but are not SOPS-encrypted yet.

```bash
# Dry-run
sops-checker

# Automatically encrypt missing files
sops-checker --fix
```

The command exits non-zero when it finds unencrypted files (unless `--fix` succeeds).

> **Note:** The current implementation inspects files described in `.sops.yaml` creation rules and only understands YAML/plaintext formats. Binary or non-YAML files are treated as unencrypted unless they have the SOPS magic header at the start of the file.
