# taskflow — synthetic benchmark fixture

A small, self-contained, deliberately-imperfect Python project used as a
**controlled test environment**. It is not a real product — it exists so
that coding tasks can be posed against a known, reproducible codebase
with known-correct outcomes.

## What's in here

- `src/taskflow/` — a multi-module task-manager CLI (models, dates,
  storage backends, core operations, reporting, plugins, CLI). Coherent
  and runnable, with a few **intentionally seeded bugs** that span more
  than one module.
- `tests/` — a pytest suite. Most tests pass; a handful **fail by
  design**, encoding the seeded bugs and a couple of unimplemented
  features. The failing tests are the acceptance criteria: a task is
  "done" when its target test goes green.
- `issues/`, `pull_requests/`, `docs/CHANGELOG.md` — mock project
  artifacts (bug reports, draft PRs, a changelog) that give the tasks
  realistic context.

## Using it

```bash
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest -q      # see which tests pass / fail by design
```

The seeded bugs (e.g. a cross-module leap-year/recurrence crash, a
non-atomic store write) and the failing-by-design tests define the
mechanical tasks. Point whatever you're evaluating at this fixture and
score it by whether the target tests pass.

That's all this repo is — a fixture.
