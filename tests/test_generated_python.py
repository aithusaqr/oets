"""Sanity checks that every committed _pb2.py file imports without error."""

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest


def _collect_pb2_modules(repo_root: Path) -> list[tuple[str, Path]]:
    """Return (dotted_module_name, file_path) pairs for all *_pb2.py under generated/python."""
    generated_root = repo_root / "generated" / "python"
    result = []
    for pb2_file in sorted(generated_root.rglob("*_pb2.py")):
        # Build a dotted module name relative to generated_root, e.g. common.account_pb2
        rel = pb2_file.relative_to(generated_root)
        module_name = ".".join(rel.with_suffix("").parts)
        result.append((module_name, pb2_file))
    return result


_REPO_ROOT = Path(__file__).parent.parent
_PB2_MODULES = _collect_pb2_modules(_REPO_ROOT)


@pytest.mark.parametrize(
    "module_name,pb2_file",
    _PB2_MODULES,
    ids=[mod for mod, _ in _PB2_MODULES],
)
def test_pb2_module_imports_cleanly(module_name: str, pb2_file: Path):
    """Each _pb2.py committed under generated/python/ must be importable without ImportError."""
    # generated/python is already on sys.path via conftest autouse fixture,
    # but guard in case this test is run in isolation.
    generated = str(_REPO_ROOT / "generated" / "python")
    if generated not in sys.path:
        sys.path.insert(0, generated)

    try:
        # Use importlib to avoid polluting the permanent module cache on failure;
        # if already imported from a previous parametrised call, just verify it's there.
        if module_name in sys.modules:
            mod = sys.modules[module_name]
        else:
            mod = importlib.import_module(module_name)
    except ImportError as exc:
        pytest.fail(
            f"ImportError loading {module_name} ({pb2_file.relative_to(_REPO_ROOT)}): {exc}\n"
            "This indicates the committed _pb2.py is broken or its protobuf runtime dep is missing."
        )

    # Verify the module object is real and has a DESCRIPTOR attribute (standard for pb2 files).
    assert hasattr(mod, "DESCRIPTOR"), (
        f"{module_name} imported but has no DESCRIPTOR attribute — "
        "may not be a valid compiled protobuf module"
    )
