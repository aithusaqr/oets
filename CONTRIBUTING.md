# Contributing to OETS

OETS is an open standard for execution telemetry. Contributions are welcome — schema feedback, bug reports, test additions, and reference implementations.

## Filing an issue

1. Check existing issues first: https://github.com/aithusaqr/oets/issues
2. Title format: `[Severity] short description` (e.g. `[High] FillEvent.price units undocumented`).
3. Body: state the severity, what's wrong, and what you propose. The v0.1 review tickets (#5–#21) are a good template.

## Proposing a code change

We use a fork → epic-branch → PR → QA-cycle workflow:

### 1. Fork and branch

```bash
gh repo fork aithusaqr/oets --clone
cd oets
git checkout -b <type>/<NN>-short-description epic/code-review-v0.1
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
make generate_python_protos
```

**Do NOT use bare `protoc` on a recent system.** It produces gencode 7.x incompatible with the pinned protobuf 5.x runtime. The Makefile uses `python -m grpc_tools.protoc` (bundled protoc 29.x → gencode 5.x). If you regenerate manually, use `python -m grpc_tools.protoc` not `protoc`.

### 4. Open a PR

Target the epic branch on the fork (or current development branch upstream, when one exists):

```bash
gh pr create --base epic/code-review-v0.1 --title "<type>(<scope>): subject (#NN)"
```

### 5. QA cycle

The reviewer runs three audit iterations on the PR:

1. Iteration 1: audit categories — scope (only changed files relate to the ticket), proto syntax & buf lint, enum hygiene (0-value sentinel, no gaps), field numbering (no collisions with reserved, no renames without `reserved` for old name), schema duplication (no envelope-bearing message duplicates source/timestamps), type consistency, generated code in sync.
2. Iteration 2 & 3: re-audit; if anything drifts, fix and recommit.

The PR ships when three back-to-back iterations are clean (`0/0/0`).

Results are posted as a single `## QA Cycle — N1/N2/N3` comment on the PR.

## Wire-breaking change policy

- v0.1 explicitly accepts wire-breaking changes to fix design errors. `buf breaking` runs in CI with `continue-on-error: true`.
- v0.2+ will tighten this. Breaking changes will require an explicit `[Breaking]` tag in the PR title and a CHANGELOG entry.
- Never reuse a removed field number without declaring `reserved <number>;` and `reserved "name";` first.

## Code style

- Follow buf STANDARD lint where reasonable. Current excepts are documented in `buf.yaml` with the tracking issue for each.
- Enum zero values: prefer `UNKNOWN_<NAME> = 0` or `<NAME>_UNSPECIFIED = 0` (project currently uses the UNKNOWN form; Phase 2 / zachisit/oets#40 will unify on UNSPECIFIED).
- Field names: `lower_snake_case`. Enum value names: `UPPER_SNAKE_CASE`.
- Comments at the top of each `.proto` file explaining scaling conventions (see existing files).

## What "ready to merge" looks like

- Full pytest suite green locally
- CI green (or, when CI is unavailable, local-suite confirmation noted in the QA cycle comment)
- Scope guard: only files in `git diff <merge-base> HEAD --stat` relate to the ticket
- A single consolidated `## QA Cycle — N1/N2/N3` comment on the PR

## See Also

- [README.md](README.md) — project mission and Getting Started
- [CHANGELOG.md](CHANGELOG.md) — version history
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — envelope vs snapshot/delta design
- [docs/SCALING.md](docs/SCALING.md) — int64 monetary scaling
- [LICENSE](LICENSE) — Apache 2.0
