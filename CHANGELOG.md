# Changelog

All notable changes to OETS protos are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and OETS adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The current version is communicated by `OetsEventEnvelope.oets_version` (see `validation/oets_version.py`). Wire-incompatible changes warrant a MAJOR bump; new optional fields warrant MINOR; editorial / non-breaking warrant PATCH.

## [Unreleased]

### Added
- Apache 2.0 `LICENSE`
- `CONTRIBUTING.md` describing the fork → PR workflow
- `CHANGELOG.md` (this file)
- `docs/SCALING.md` documenting the int64 monetary-field scaling convention
- `docs/ARCHITECTURE.md` documenting the envelope-bearing vs snapshot/delta message-type split
- `validation/oets_version.py` — SemVer 2.0.0 validator for `OetsEventEnvelope.oets_version`
- GitHub Actions workflow (`.github/workflows/ci.yml`) with Python 3.11 / 3.12 / 3.13 matrix, `buf lint`, `buf breaking`, and `pytest`
- `buf.yaml`, `buf.gen.yaml` for buf-based generation and lint
- `pyproject.toml` `[project]` table with `requires-python = ">=3.11"`
- `requirements.txt`, `requirements-test.txt` pinning the runtime + dev dependencies
- Pytest infrastructure (`tests/conftest.py`, hygiene/structure/CI test files)

### Fixed
- `.gitignore` now excludes `build/`, `*.egg-info/`, `dist/` so editable installs don't pollute the worktree
- Makefile: added `.PHONY` declarations, removed dead `PYTHONPATH=` inline from the `generate_python_protos` recipe

[Unreleased]: https://github.com/aithusaqr/oets/compare/main...HEAD
