# AGENTS.md

Guidance for coding agents (Claude Code, opencode, Codex, ...) working in this repository.

I Hate Money: a Flask 3 / Python 3.11+ web app for shared budgets. A project has members (with a
weight), members pay bills, each bill is split between the members it was for, and the app works
out who owes whom. Server-rendered Jinja + WTForms, SQLAlchemy 2 with Alembic migrations, SQLite by
default, a REST API used by the mobile app, and a change history built on SQLAlchemy-Continuum.

## Workshop flow (OpenSpec)

This branch is a workshop. The user is here to **learn OpenSpec by using it** on one large
feature. They may not finish, and that is fine. Your job is to run each step well AND teach the
tool while you do it.

| # | Step | Claude Code | opencode | Codex |
|---|---|---|---|---|
| 1 | propose | `/opsx:propose` | `/opsx-propose` | `$openspec-propose` |
| 2 | apply | `/opsx:apply` | `/opsx-apply` | `$openspec-apply-change` |
| 3 | archive | `/opsx:archive` | `/opsx-archive` | `$openspec-archive-change` |

### Running the steps

- Do only the step the user ran, then stop so they can review it.
- **propose: one slice per change.** If the request needs more than about 10 requirements, propose
  only the first useful vertical slice as this change and list the rest in `proposal.md` under
  "Follow-up changes". The user runs the whole flow again for each follow-up.
- **apply: one task group per run.** Finish and test one group, tick its boxes, then stop and
  report how many tasks are left. The user runs apply again for the next group.
- **archive only a finished change.** Archive merges the delta into `openspec/specs/`, which means
  "this is how the system behaves now". If tasks are still open, say so plainly, recommend NOT
  archiving (leave the change active and come back to it), and never pick "sync" for them.
- Before archive, `openspec validate <change> --strict` must pass.
- The `openspec` CLI prints its own `Next: openspec ...` hints. Those are for you; the user only
  ever gets the slash command.
- End every step with one line naming the next step, in the syntax of the harness you are
  running in, plus what to review first. Example: `Next: /opsx:apply (review tasks.md first)`.
  After a partial apply, name both options: `Next: /opsx:apply (group 2) or /opsx:archive once all
  tasks are done`.
- If the user types `next` or asks what to do now, check `openspec/changes/` to see where they
  are and answer the same way. Do not run the step for them.
- After archive, point them to the first "Follow-up change" in `proposal.md`, or to "Finished
  early?" in `README.md` if there is none.

### Teaching

- **First step of the session:** open with at most 4 lines on what OpenSpec is (below) and on
  how the session works (you stop after each step; their job is to read and edit what you wrote),
  then do the work.
- **After every step:** before the `Next:` line, add a short block headed `What just happened`
  (at most 7 lines): what this step is for, which files it wrote and what each holds, the most
  interesting thing the step found (a constitution conflict, a missing feature, an edge case),
  what the user should check, and one thing to try. After propose, the thing to try is an edit:
  name one decision in their artifacts they could flip.
- **`explain`:** if the user types `explain` (or asks why/how), explain the current step in more
  depth using their own artifacts as the examples. Quote a requirement, a scenario, a task.
- **Changes of mind:** if the user wants something different, show the OpenSpec way: edit the
  artifact (proposal, spec delta, design or tasks) first, then the code. The spec leads.
- Keep it short and concrete. Never lecture before doing the work.

What to teach:

- **The idea.** OpenSpec keeps two things apart. `openspec/specs/` is the truth about how the
  system behaves today. `openspec/changes/<name>/` is one proposed change, reviewed before any code
  is written. Archiving a change merges it into the specs, so the specs grow with the code.
  `openspec/config.yaml` feeds project context and rules into every step; `openspec/constitution.md`
  holds the rules nobody may break.
- **propose** writes four artifacts: `proposal.md` (why, what changes, non-goals),
  `specs/<capability>/spec.md` (a *delta*: ADDED / MODIFIED / REMOVED requirements, each with
  WHEN/THEN scenarios), `design.md` (decisions and the alternatives rejected) and `tasks.md`
  (checkbox list). Review: is every requirement testable, are non-goals honest, is the design
  choice the one you would make? Try: `openspec show <change>`, `openspec validate <change> --strict`,
  `openspec status --change <change>`.
- **apply** works `tasks.md` top to bottom and ticks each box. Scenarios become tests. If the code
  needs to differ from the spec, update the spec delta first. Review: pick one scenario and find
  its test. Try: keep `tasks.md` open and watch the boxes tick.
- **archive** validates, merges the delta into `openspec/specs/<capability>/spec.md` and moves the
  change to `openspec/changes/archive/`. Review: read the merged spec; this is what the next
  change builds on. Try: `openspec list --specs`, `openspec view`.
- **Optional:** `/opsx:explore` (Codex: `$openspec-explore`) is a thinking partner before
  proposing. Nothing gets written.

## Commands

```bash
# Run the app on http://localhost:5000 (SQLite file workshop.db; migrations run on startup).
# Try /demo for a ready-made project.
uv run flask --app workshop run --debug

# Test suite: about 10 s, in-memory SQLite, exchange rates mocked. Expect "146 passed, 5 skipped":
# the skips are upstream's ("Currency conversion is broken").
uv run --extra dev pytest -q

# One file, one test
uv run --extra dev pytest -q ihatemoney/tests/budget_test.py
uv run --extra dev pytest -q ihatemoney/tests/budget_test.py -k test_manage_bills

# Lint (CI runs `ruff check` only; pytest runs neither). Existing code is not ruff-format clean,
# so format only the files you created.
uv run --extra dev ruff check .
uv run --extra dev ruff format path/to/new_file.py

# New Alembic migration after changing models.py (autogenerated, review it)
uv run flask --app workshop db migrate -d ihatemoney/migrations -m "add bill series"

# Check migrations: applies them to workshop.db, then lists what the models have that the
# database lacks. It exits (unlike `flask run`), so use it after every model change. It always
# reports the 5 known upstream differences (see Gotchas) and exits 1; anything else is yours.
uv run flask --app workshop db check -d ihatemoney/migrations
```

## Gotchas

- **Every schema change needs an Alembic migration** in `ihatemoney/migrations/versions/`. The app
  never calls `create_all()`: `create_app()` runs `upgrade()` on startup, in the running app and in
  every test. The test fixture then calls `db.create_all()`, which creates missing tables but never
  adds columns. So:
  - a new column without a migration fails the tests (`no such column`);
  - a new table without a migration passes every test and breaks the running app
    (`no such table`). Run `db check` (see Commands) after every model change.
- **Upstream models and migrations already differ in 5 places**, so `db check` never passes and
  every autogenerated migration contains them: `bill_version.bill_type` (TEXT vs Enum),
  `billowers.bill_id` and `billowers.person_id` (NOT NULL), `project.logging_preference` (VARCHAR
  vs Enum) and `project_version.password` (length 128 vs 256). Delete those operations from your
  migration and keep only your own.
- **Read every autogenerated migration.** `db migrate` first upgrades `workshop.db` to the latest
  revision, then diffs it against the models. It misses data migrations, and on SQLite changing
  or dropping a column, or adding a foreign key, needs `op.batch_alter_table`. On `bill`, `person`
  and `billowers` a batch must keep `table_kwargs={"sqlite_autoincrement": True}` (see
  `cb038f79982e_sqlite_autoincrement.py`).
- **SQLite here does not enforce foreign keys** (no `PRAGMA foreign_keys`); PostgreSQL and MariaDB
  in CI do. Give every new foreign key a delete path in code (project deletion, member removal).
- **Versioned models.** `Project`, `Person` and `Bill` have `__versioned__ = {}`, so
  SQLAlchemy-Continuum keeps a `<table>_version` table for each. A new versioned model needs its
  `_version` table in the migration too (see `2dcb0c0048dc_autologger.py`), and a new column on
  one of them needs the same column on its `_version` table (see `7a9b38559992`). The history
  page only knows these three types: `history.py` builds its queries per type and
  `templates/history.html` renders them.
- **Translations.** Wrap every user-facing string in `_()` (Python, from `flask_babel`) or
  `{{ _("...") }}` (templates). Do not edit `messages.pot` or the `.po` files: translators work on
  Weblate and extraction is a release step. Untranslated strings fall back to English.
- **The API is a public contract.** The mobile app uses `/api/projects/...` (see `docs/api.md`).
  Existing fields and endpoints must keep their shape; add, don't change. `BillForm` serves both
  the web pages and the API's POST/PUT, so a new form field must be optional, and `api_test.py`
  compares whole JSON objects, so a new field in a response means updating those expected dicts.
- **Money is a float** (`Bill.amount`, `converted_amount`) and bills store both the original
  currency and the amount converted to the project currency. Don't change that as a side effect.
- **"Today" is `datetime.now()`** in forms and models, and there is no time-freezing library.
  Tests that depend on the date must control it (for example with pytest's `monkeypatch`).
- **Tests are classes.** Subclass `IhatemoneyTestCase` (`tests/common/ihatemoney_testcase.py`); it
  provides `self.client`, `self.app`, `post_project()`, `login()` and a mocked currency converter
  (USD 1, EUR 0.8, CAD 1.2, PLN 4). CSRF is off in tests.

## Layout

- `ihatemoney/models.py`: `Project` → `Person` (members) → `Bill` (payer, owers, amount, date,
  currency). Balances and settlements are computed in `Project`, not stored.
- `ihatemoney/web.py`: every page (one Flask blueprint, `main`). Project pages live under
  `/<project_id>/`, and `g.project` is the logged-in project.
- `ihatemoney/forms.py`: WTForms forms; `BillForm.export()` builds a new `Bill`, `save()` updates
  one. The API reuses these forms.
- `ihatemoney/api/`: Flask-RESTful handlers in `common.py`, routes in `v1/resources.py`.
- `ihatemoney/history.py` + `templates/history.html`: the change log, read from Continuum's
  version tables.
- `ihatemoney/templates/`: Jinja; `layout.html` is the shell, `forms.html` holds form macros,
  `list_bills.html` is the main project page.
- `ihatemoney/migrations/versions/`: Alembic revisions, applied on every startup.
- `ihatemoney/tests/`: `budget_test.py` (web flows), `api_test.py`, `history_test.py`,
  `import_test.py`, `main_test.py` (config, mail, admin).
