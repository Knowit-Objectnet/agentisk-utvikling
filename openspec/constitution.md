# I Hate Money Constitution

## Core Principles

### I. Simplicity First (NON-NEGOTIABLE)

The maintainers put simplicity and stability above new features (see `UPSTREAM-README.md`).
Every change MUST be the simplest thing that works for a small, self-hosted app.

- Use the existing stack only: the runtime dependencies in `pyproject.toml` (Flask, Jinja,
  WTForms, SQLAlchemy + Alembic, SQLAlchemy-Continuum, Flask-Babel, Flask-RESTful,
  python-dateutil, ...). A new runtime dependency requires an amendment to this constitution.
- The app is one WSGI process that an admin can run anywhere. No background workers, task queues,
  schedulers or cron jobs: work happens inside a request or a `flask` CLI command.
- Every page MUST work without JavaScript. Keep the little JavaScript there is optional.
- No accounts for people: a project is shared through its id, password or invitation link.

Rationale: self-hosters run this on small servers with no extra services, and a few volunteers
maintain it.

### II. Every Schema Change Is Migrated

- Every change to a model's columns or tables MUST come with an Alembic revision in
  `ihatemoney/migrations/versions/` that upgrades and downgrades.
- Migrations MUST run on SQLite, PostgreSQL and MariaDB (CI tests all three). On SQLite,
  changing or dropping a column or adding a foreign key needs `op.batch_alter_table`.
- A migration MUST leave no drift: `flask --app workshop db check -d ihatemoney/migrations`
  passes after it.
- Existing projects MUST keep working after the upgrade: when new columns need values for old
  rows, the migration fills them.

### III. Test Every Behaviour

Every user-visible behaviour MUST be pinned by a test.

- Web flows in `budget_test.py`, API behaviour in `api_test.py`, history entries in
  `history_test.py`, import and export in `import_test.py`, all subclassing `IhatemoneyTestCase`.
- Tests never touch the network and never sleep. Behaviour that depends on today's date MUST read
  it through one function that tests can replace (for example with `monkeypatch`).
- A bug fix MUST start with a failing test that reproduces it.
- The full suite (`uv run --extra dev pytest`) MUST pass before a change is considered done.

### IV. Public Contracts Stay Stable

The mobile app and other clients depend on the API; people depend on their exports.

- Existing API endpoints and fields MUST keep their shape. New endpoints and new optional fields
  are fine, and MUST be documented in `docs/api.md`.
- Exports (JSON, CSV) MUST stay importable: a new field is optional on import, and a file
  exported before the change still imports.

### V. Money Changes Are Accountable and Translatable

- Anything that changes who owes what (bills, members, weights) MUST show up in the project
  history when the project has history enabled, and MUST respect the project's logging preference.
  Never record IP addresses.
- Every user-visible string MUST be wrapped in `_()` or `{{ _("...") }}`. Do not edit
  `messages.pot` or `.po` files; translations come from Weblate.

## Code Quality Standards

- `uv run --extra dev ruff check .` MUST pass (CI runs it; migrations are excluded). New files
  MUST be `ruff format` clean. Existing files are not, so match their style and never reformat
  code a change does not touch.
- Follow the existing structure: views in `web.py`, forms in `forms.py`, models in `models.py`,
  API handlers in `api/common.py`. A new module requires a new domain concept, not preference.
- State-changing actions MUST use `POST` with the CSRF-protected forms, never a `GET` link.

## Development Workflow

- One feature per branch; commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`,
  `test:`, `chore:`).
- A change is done when: the full suite is green, `ruff check` is clean, `db check` passes on a
  database created before the change, the feature works in the browser
  (`uv run flask --app workshop run`), and each of the spec's acceptance scenarios is covered by a
  test.

## Governance

This constitution supersedes conflicting habits and prior precedent in this fork.

- **Amendments**: proposed as a change to this file with a rationale and a version bump.
- **Versioning**: MAJOR for removing or redefining a principle, MINOR for adding one or materially
  expanding guidance, PATCH for wording.
- **Compliance**: every change's `design.md` MUST end with a "Constitution check" table, one row
  per Principle I–V; a violation MUST be justified in that table or removed.
- **Runtime guidance**: `AGENTS.md` holds operational detail (commands, gotchas, layout) and MUST
  NOT contradict this file.

**Version**: 1.0.0 | **Ratified**: 2026-09-26 | **Last Amended**: 2026-09-26
