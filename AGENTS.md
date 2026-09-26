# AGENTS.md

Guidance for coding agents (Claude Code, opencode, Codex, ...) working in this repository.

I Hate Money: a Flask 3 / Python 3.11+ web app for shared budgets. A project has members (with a
weight), members pay bills, each bill is split between the members it was for, and the app works
out who owes whom. Server-rendered Jinja + WTForms, SQLAlchemy 2 with Alembic migrations, SQLite by
default, a REST API used by the mobile app, and a change history built on SQLAlchemy-Continuum.

## Workshop flow (Spec Kit)

This branch is a workshop. The user is here to **learn Spec Kit by using it** on one large
feature. They may not finish, and that is fine. Your job is to run each step well AND teach the
tool while you do it.

| # | Step | Claude Code | opencode | Codex |
|---|---|---|---|---|
| 1 | specify | `/speckit-specify` | `/speckit.specify` | `$speckit-specify` |
| 2 | clarify | `/speckit-clarify` | `/speckit.clarify` | `$speckit-clarify` |
| 3 | plan | `/speckit-plan` | `/speckit.plan` | `$speckit-plan` |
| 4 | tasks | `/speckit-tasks` | `/speckit.tasks` | `$speckit-tasks` |
| 5 | analyze | `/speckit-analyze` | `/speckit.analyze` | `$speckit-analyze` |
| 6 | implement | `/speckit-implement` | `/speckit.implement` | `$speckit-implement` |

### Running the steps

- Do only the step the user ran, then stop so they can review it.
- Tests are always part of the work. `/speckit-tasks` MUST generate test tasks: the constitution
  requires a test for every behaviour.
- **implement: one user story per run.** Do the setup and foundational phases plus the next story,
  test it, tick its boxes, then stop and report how many tasks are left. The user runs implement
  again for the next story. This overrides the implement skill's "execute all tasks".
- **analyze:** a deviation already justified in the plan's Complexity Tracking table is at most
  HIGH, not CRITICAL (this overrides the analyze skill). If the user asks you to fix findings,
  list every file you changed, give an old-to-new map if task IDs moved, and suggest re-running
  analyze.
- The `specify` CLI is not installed. The scripts in `.specify/scripts/bash/` cover every step.
- End every step with one line naming the next step, in the syntax of the harness you are
  running in, plus what to review first. Example: `Next: /speckit-clarify (review spec.md first)`.
- If the user types `next` or asks what to do now, check `specs/` (which of `spec.md`, `plan.md`,
  `tasks.md` exist, which tasks are ticked) to see where they are and answer the same way. Do not
  run the step for them.
- After a partial implement, the next step is `implement` again for the next story. Point to
  "Finished early?" in `README.md` only when every box in `tasks.md` is ticked.

### Teaching

- **First step of the session:** open with at most 4 lines on what Spec Kit is (below) and on
  how the session works (you stop after each step; their job is to read and edit what you wrote),
  then do the work.
- **After every step:** before the `Next:` line, add a short block headed `What just happened`
  (at most 7 lines): what this step is for, which files it wrote and what each holds, the most
  interesting thing the step found (a constitution conflict, a gap, an edge case), what the user
  should check, and one thing to try. After specify and plan, the thing to try is an edit: name
  one decision in their artifacts they could flip.
- **`explain`:** if the user types `explain` (or asks why/how), explain the current step in more
  depth using their own artifacts as the examples. Quote a requirement, a plan decision, a task.
- **Changes of mind:** if the user wants something different, show the Spec Kit way: fix the
  earliest artifact that is wrong (spec, then plan, then tasks) and redo the steps after it.
- Keep it short and concrete. Never lecture before doing the work.

What to teach:

- **The idea.** Spec Kit goes from *what* to *how* to *do*, one artifact per step, all in
  `specs/<NNN-feature>/`. `.specify/memory/constitution.md` holds the project's rules, and the plan
  step checks the design against it. Each step reads the previous artifacts, so a mistake fixed
  early is cheap and one fixed late is expensive.
- **specify** writes `spec.md`: user stories with priorities (P1 is the smallest useful slice),
  acceptance scenarios, functional requirements and success criteria, with no technology in it.
  It may ask up to 3 questions about big scope decisions it can't guess; clarify later asks the
  finer questions. Review: could a non-developer read it and agree?
- **clarify** asks up to 5 questions, one at a time, and records each answer in a
  `## Clarifications` section of the spec. Review: did the answers land as requirements? Try:
  answer with your own choice instead of the recommended one.
- **plan** writes `plan.md` (tech context, constitution check, project structure), `research.md`
  (decisions and rejected alternatives), `data-model.md`, `contracts/` and `quickstart.md`.
  Review: the constitution check, and whether you would make the same design choices.
- **tasks** writes `tasks.md`: numbered tasks grouped by user story, `[P]` marks tasks that can run
  in parallel, tests come before the code they cover. Review: can you stop after the P1 phase and
  have something working?
- **analyze** is read-only. It cross-checks spec, plan and tasks for gaps, duplicates and
  constitution conflicts and ranks them. Try: ask the agent to fix the top findings, then re-run it.
- **implement** runs the tasks for one story and ticks each box in `tasks.md` (`[X]`). The ticks are
  how a later run, or a new session, knows where to resume. Review: run the tests and look at the
  result in the app before going on.
- **Optional:** `/speckit-checklist` (opencode `/speckit.checklist`, Codex `$speckit-checklist`)
  writes "unit tests for the requirements": questions that check the spec itself is complete.

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
