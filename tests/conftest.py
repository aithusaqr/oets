"""Project-level pytest fixtures for the OETS proto repo."""

from pathlib import Path
import sys
import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def proto_files(repo_root: Path) -> list[Path]:
    """All .proto files found under common/."""
    return sorted(repo_root.joinpath("common").rglob("*.proto"))


@pytest.fixture(scope="session")
def proto_text(repo_root: Path):
    """Callable fixture: read a .proto file as text given its Path."""

    def _read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    return _read


@pytest.fixture(scope="session", autouse=True)
def _add_generated_python_to_syspath(repo_root: Path):
    """Ensure generated/python is on sys.path so _pb2 modules are importable."""
    generated = str(repo_root / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)
