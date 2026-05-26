# Contributing to OETS

OETS is an open standard for execution telemetry. Contributions are welcome — schema feedback, bug reports, test additions, and reference implementations.

## Filing an issue

1. Check existing issues first: https://github.com/aithusaqr/oets/issues
2. Title format: `[Severity] short description` (e.g. `[High] FillEvent.price units undocumented`).
3. Body: state the severity, what's wrong, and what you propose.

## Proposing a code change

### 1. Fork and branch

```bash
gh repo fork aithusaqr/oets --clone
cd oets
git checkout -b <type>/<NN>-short-description main
```

Branch types: `fix/`, `feat/`, `chore/`, `docs/`, `test/`, `refactor/`.

### 2. Implement with tests

Every change needs real pytest coverage. Test bar:
- Meaningful assertions with informative failure messages — no `assert True` or `assert isinstance(x, expected_type)` slop.
- For schema changes, include a wire-level roundtrip test (construct, serialize, deserialize, assert equality).
- For doc-only changes, include structural assertions about the docs (e.g. "this section exists").

Run the full suite before opening a PR:

```bash
pip install -r requirements.txt -r requirements-test.txt
pytest tests/
```

### 3. Regenerate Python bindings if you touched a `.proto`

```bash
source .venv/bin/activate   # or your venv's activation command
make generate_python_protos
```

**Important:** the runtime `protobuf` version pinned in `requirements.txt` must be compatible with the gencode in the committed `_pb2.py` files. The protobuf Python runtime rejects `runtime.minor < gencode.minor`, so regenerating against a much newer `protoc` than the runtime pin will silently break consumers.

### 4. Open a PR

```bash
gh pr create --base main --title "<type>(<scope>): subject (#NN)"
```

## Wire-breaking change policy

- `buf breaking` runs in CI with `continue-on-error: true` for v0.1 so design errors can still be fixed. v0.2+ will tighten this.
- Breaking changes require an entry in `CHANGELOG.md` under the appropriate section (wire-breaking vs source-breaking).
- Never reuse a removed field number without declaring `reserved <number>;` and `reserved "name";` first.

## Code style

- Follow buf STANDARD lint where reasonable. Current excepts are documented in `buf.yaml` with the rationale for each.
- Field names: `lower_snake_case`. Enum value names: `UPPER_SNAKE_CASE`.
- Enum zero values: every enum should declare a zero-value sentinel (either `UNKNOWN_<NAME> = 0` or `<NAME>_UNSPECIFIED = 0`).

## What "ready to merge" looks like

- Full pytest suite green locally
- CI green
- Scope guard: only files in `git diff main...HEAD --stat` relate to the ticket

## See Also

- [README.md](README.md) — project mission and Getting Started
- [CHANGELOG.md](CHANGELOG.md) — version history
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — message-type design principles
- [docs/SCALING.md](docs/SCALING.md) — int64 monetary scaling convention
- [LICENSE](LICENSE) — Apache 2.0
