"""Tests for L3: dependency manifest and buf configuration files.

Verifies that buf.yaml, buf.gen.yaml, requirements.txt, and pyproject.toml
contain the expected content so consumers can regenerate the protos reproducibly.
buf itself is NOT invoked — tests are structural only.
"""

import re
import tomllib
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def buf_yaml(repo_root: Path) -> dict:
    """Parsed contents of buf.yaml."""
    path = repo_root / "buf.yaml"
    assert path.is_file(), "buf.yaml does not exist at repo root"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def buf_gen_yaml(repo_root: Path) -> dict:
    """Parsed contents of buf.gen.yaml."""
    path = repo_root / "buf.gen.yaml"
    assert path.is_file(), "buf.gen.yaml does not exist at repo root"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def requirements_txt(repo_root: Path) -> str:
    """Raw text of requirements.txt."""
    path = repo_root / "requirements.txt"
    assert path.is_file(), "requirements.txt does not exist at repo root"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pyproject(repo_root: Path) -> dict:
    """Parsed contents of pyproject.toml."""
    path = repo_root / "pyproject.toml"
    assert path.is_file(), "pyproject.toml does not exist at repo root"
    with path.open("rb") as fh:
        return tomllib.load(fh)


@pytest.fixture(scope="module")
def makefile_text(repo_root: Path) -> str:
    path = repo_root / "Makefile"
    assert path.is_file(), "Makefile does not exist at repo root"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# buf.yaml tests
# ---------------------------------------------------------------------------


def test_buf_yaml_version(buf_yaml: dict):
    """buf.yaml must declare version: v2."""
    assert buf_yaml.get("version") == "v2", (
        f"Expected buf.yaml version 'v2', got {buf_yaml.get('version')!r}"
    )


def test_buf_yaml_has_modules_list(buf_yaml: dict):
    """buf.yaml must have a non-empty 'modules' list."""
    modules = buf_yaml.get("modules")
    assert isinstance(modules, list) and len(modules) > 0, (
        "buf.yaml 'modules' must be a non-empty list"
    )


def test_buf_yaml_module_name(buf_yaml: dict):
    """buf.yaml modules entry must include the expected buf.build name."""
    modules = buf_yaml.get("modules", [])
    names = [m.get("name") for m in modules if isinstance(m, dict)]
    assert "buf.build/aithusaqr/oets" in names, (
        f"Expected module name 'buf.build/aithusaqr/oets' in buf.yaml modules; "
        f"found names: {names!r}"
    )


def test_buf_yaml_lint_uses_standard(buf_yaml: dict):
    """buf.yaml lint.use must contain 'STANDARD'."""
    lint_use = buf_yaml.get("lint", {}).get("use", [])
    assert "STANDARD" in lint_use, (
        f"Expected 'STANDARD' in buf.yaml lint.use; got {lint_use!r}"
    )


def test_buf_yaml_breaking_uses_file(buf_yaml: dict):
    """buf.yaml breaking.use must contain 'FILE'."""
    breaking_use = buf_yaml.get("breaking", {}).get("use", [])
    assert "FILE" in breaking_use, (
        f"Expected 'FILE' in buf.yaml breaking.use; got {breaking_use!r}"
    )


def test_buf_yaml_lint_except_is_list(buf_yaml: dict):
    """buf.yaml lint.except must be a list (may be empty)."""
    lint_except = buf_yaml.get("lint", {}).get("except", [])
    assert isinstance(lint_except, list), (
        f"buf.yaml lint.except must be a list; got {type(lint_except).__name__!r}"
    )


# Closed set of known STANDARD rule names that are valid candidates for
# temporary suppression.  This catches typos that would silently suppress
# nothing (e.g. "ENUM_VALUE_PREFX" would never match anything).
_KNOWN_SUPPRESSIBLE_STANDARD_RULES: frozenset[str] = frozenset(
    {
        "ENUM_ZERO_VALUE_SUFFIX",
        "ENUM_VALUE_PREFIX",
        "PACKAGE_VERSION_SUFFIX",
        "FIELD_LOWER_SNAKE_CASE",
        "MESSAGE_PASCAL_CASE",
        "ENUM_PASCAL_CASE",
        "SERVICE_PASCAL_CASE",
        "RPC_PASCAL_CASE",
        "PACKAGE_LOWER_SNAKE_CASE",
        "IMPORT_NO_WEAK",
        "IMPORT_NO_PUBLIC",
        "ENUM_NO_ALLOW_ALIAS",
        "ONEOF_LOWER_SNAKE_CASE",
        "RPC_REQUEST_STANDARD_NAME",
        "RPC_RESPONSE_STANDARD_NAME",
        "RPC_REQUEST_RESPONSE_UNIQUE",
        "SERVICE_SUFFIX",
        "COMMENT_ENUM",
        "COMMENT_ENUM_VALUE",
        "COMMENT_FIELD",
        "COMMENT_MESSAGE",
        "COMMENT_ONEOF",
        "COMMENT_RPC",
        "COMMENT_SERVICE",
        "PROTOVALIDATE",
        "SYNTAX_SPECIFIED",
        "FIELD_NOT_REQUIRED",
        "PACKAGE_DIRECTORY_MATCH",
        "PACKAGE_SAME_DIRECTORY",
    }
)


def test_buf_yaml_lint_except_rules_are_recognised(buf_yaml: dict):
    """Every rule in lint.except must be a recognised STANDARD rule name.

    This prevents silent no-ops caused by typos (a misspelled rule name would
    suppress nothing while giving false confidence that a violation is covered).
    """
    lint_except = buf_yaml.get("lint", {}).get("except", [])
    if not lint_except:
        pytest.skip("lint.except is empty — nothing to validate")
    unrecognised = [r for r in lint_except if r not in _KNOWN_SUPPRESSIBLE_STANDARD_RULES]
    assert not unrecognised, (
        f"Unrecognised rule(s) in buf.yaml lint.except: {unrecognised!r}. "
        f"Either the rule name is misspelled or it should be added to the "
        f"known-suppressible set in this test."
    )


def test_buf_lint_ignore_includes_settlement_event_stub(buf_yaml: dict):
    """lint.ignore must contain the empty settlement_event.proto stub."""
    lint_ignore = buf_yaml.get("lint", {}).get("ignore", [])
    assert isinstance(lint_ignore, list), (
        f"buf.yaml lint.ignore must be a list; got {type(lint_ignore).__name__!r}"
    )
    assert "common/reconciliation/settlement_event.proto" in lint_ignore, (
        "buf.yaml lint.ignore must include 'common/reconciliation/settlement_event.proto' "
        "(empty stub, tracked in #5) — remove once H1 fills the stub."
    )


def test_buf_lint_ignore_is_valid_paths(buf_yaml: dict, repo_root: Path):
    """Every entry in lint.ignore must resolve to an actual file in the repo.

    Guards against typos that would silently un-ignore the intended path.
    """
    lint_ignore = buf_yaml.get("lint", {}).get("ignore", [])
    if not lint_ignore:
        pytest.skip("lint.ignore is empty or absent — nothing to validate")
    bad = [p for p in lint_ignore if not isinstance(p, str) or not (repo_root / p).is_file()]
    assert not bad, (
        f"lint.ignore entries that are not valid repo-relative file paths: {bad!r}. "
        "Fix the path(s) or remove the stale entry."
    )


# ---------------------------------------------------------------------------
# buf.gen.yaml tests
# ---------------------------------------------------------------------------


def test_buf_gen_yaml_version(buf_gen_yaml: dict):
    """buf.gen.yaml must declare version: v2."""
    assert buf_gen_yaml.get("version") == "v2", (
        f"Expected buf.gen.yaml version 'v2', got {buf_gen_yaml.get('version')!r}"
    )


def test_buf_gen_yaml_has_plugins_list(buf_gen_yaml: dict):
    """buf.gen.yaml must have a non-empty 'plugins' list."""
    plugins = buf_gen_yaml.get("plugins")
    assert isinstance(plugins, list) and len(plugins) > 0, (
        "buf.gen.yaml 'plugins' must be a non-empty list"
    )


def test_buf_gen_yaml_python_plugin_out(buf_gen_yaml: dict):
    """At least one plugin must output to generated/python."""
    plugins = buf_gen_yaml.get("plugins", [])
    out_dirs = [p.get("out") for p in plugins if isinstance(p, dict)]
    assert "generated/python" in out_dirs, (
        f"Expected a plugin with out='generated/python' in buf.gen.yaml; "
        f"found out values: {out_dirs!r}"
    )


# ---------------------------------------------------------------------------
# requirements.txt tests
# ---------------------------------------------------------------------------


def test_requirements_txt_pins_protobuf(requirements_txt: str):
    """requirements.txt must pin protobuf>=5.28,<6."""
    lines = [ln.strip() for ln in requirements_txt.splitlines() if ln.strip() and not ln.startswith("#")]
    protobuf_lines = [ln for ln in lines if ln.startswith("protobuf")]
    assert protobuf_lines, (
        "requirements.txt does not contain a 'protobuf' dependency"
    )
    # Accept either combined or split specifier forms, but must cover >=5.28 and <6.
    spec = protobuf_lines[0]
    assert "5.28" in spec, (
        f"requirements.txt protobuf pin must reference 5.28; got {spec!r}"
    )
    assert "<6" in spec, (
        f"requirements.txt protobuf pin must have upper bound <6; got {spec!r}"
    )


# ---------------------------------------------------------------------------
# pyproject.toml tests
# ---------------------------------------------------------------------------


def test_pyproject_has_project_table(pyproject: dict):
    """pyproject.toml must have a [project] table."""
    assert "project" in pyproject, (
        "pyproject.toml is missing the [project] table"
    )


def test_pyproject_project_name(pyproject: dict):
    """pyproject.toml [project].name must be 'oets'."""
    name = pyproject.get("project", {}).get("name")
    assert name == "oets", (
        f"Expected pyproject.toml project.name='oets', got {name!r}"
    )


def test_pyproject_project_lists_protobuf_dependency(pyproject: dict):
    """pyproject.toml [project].dependencies must include a protobuf entry."""
    deps = pyproject.get("project", {}).get("dependencies", [])
    protobuf_deps = [d for d in deps if d.startswith("protobuf")]
    assert protobuf_deps, (
        f"pyproject.toml project.dependencies does not list 'protobuf'; "
        f"found: {deps!r}"
    )


def test_pyproject_pytest_table_intact(pyproject: dict):
    """pyproject.toml must still have the [tool.pytest.ini_options] table."""
    pytest_cfg = pyproject.get("tool", {}).get("pytest", {}).get("ini_options")
    assert pytest_cfg is not None, (
        "pyproject.toml is missing [tool.pytest.ini_options] — was it accidentally removed?"
    )


# ---------------------------------------------------------------------------
# Makefile buf target tests
# ---------------------------------------------------------------------------


def _collect_phony_targets(makefile_text: str) -> list[str]:
    """Return all targets declared across all .PHONY lines."""
    targets: list[str] = []
    for line in makefile_text.splitlines():
        m = re.match(r"^\.PHONY\s*:\s*(.+)", line)
        if m:
            targets.extend(m.group(1).split())
    return targets


def test_makefile_phony_buf_generate(makefile_text: str):
    """buf_generate must appear in a .PHONY declaration."""
    targets = _collect_phony_targets(makefile_text)
    assert "buf_generate" in targets, (
        f"buf_generate not found in any .PHONY declaration; found: {targets!r}"
    )


def test_makefile_phony_buf_lint(makefile_text: str):
    """buf_lint must appear in a .PHONY declaration."""
    targets = _collect_phony_targets(makefile_text)
    assert "buf_lint" in targets, (
        f"buf_lint not found in any .PHONY declaration; found: {targets!r}"
    )


def test_makefile_phony_buf_breaking(makefile_text: str):
    """buf_breaking must appear in a .PHONY declaration."""
    targets = _collect_phony_targets(makefile_text)
    assert "buf_breaking" in targets, (
        f"buf_breaking not found in any .PHONY declaration; found: {targets!r}"
    )


def test_makefile_buf_generate_recipe(makefile_text: str):
    """buf_generate must be defined as a recipe block."""
    pattern = re.compile(
        r"^buf_generate\s*:.*\n(?:[ \t]+\S.*\n?)+",
        re.MULTILINE,
    )
    assert pattern.search(makefile_text), (
        "buf_generate is declared .PHONY but has no recipe block in Makefile"
    )


def test_makefile_buf_lint_recipe(makefile_text: str):
    """buf_lint must be defined as a recipe block."""
    pattern = re.compile(
        r"^buf_lint\s*:.*\n(?:[ \t]+\S.*\n?)+",
        re.MULTILINE,
    )
    assert pattern.search(makefile_text), (
        "buf_lint is declared .PHONY but has no recipe block in Makefile"
    )


def test_makefile_buf_breaking_recipe(makefile_text: str):
    """buf_breaking must be defined as a recipe block."""
    pattern = re.compile(
        r"^buf_breaking\s*:.*\n(?:[ \t]+\S.*\n?)+",
        re.MULTILINE,
    )
    assert pattern.search(makefile_text), (
        "buf_breaking is declared .PHONY but has no recipe block in Makefile"
    )
