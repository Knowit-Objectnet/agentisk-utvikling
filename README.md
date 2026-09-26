# I Hate Money · Spec Kit

## The app

I Hate Money is a small Flask website for shared budgets: flatmates, a trip, a club. A project
has members, members add the bills they paid and say who they were for, and the app works out who
owes whom. Every page is a Flask view plus a Jinja template, data lives in SQLite through
SQLAlchemy, and the mobile app talks to the same data through a REST API.

```mermaid
flowchart LR
    B[Browser] --> W["web.py views<br/>+ WTForms"]
    M[Mobile app] --> A["api/<br/>(REST)"]
    W --> T[Jinja pages]
    W --> D[models.py]
    A --> D
    D --> DB[(SQLite)]
    D -. every change .-> H[History log]
    subgraph Data
        P[Project] -->|has| Pe[Member] -->|pays| Bi[Bill]
        Bi -->|split between| Pe
    end
    DB --- Data
```

## The problem

Rent, internet, a streaming subscription: a shared household pays the same bills every month, and
today someone has to type each one in again. Members want recurring bills: set one up once, and
every occurrence turns up on its date with the right people and amount, never twice. The app is
a single web process with no background jobs, so part of the work is deciding when and how those
bills get created.

It touches most of the app: data model and migrations, the bill form, a new page, the change
history, the API the mobile app uses. It's big on purpose.

## Getting started

Needs [uv](https://docs.astral.sh/uv/) and bash (WSL or Git Bash on Windows). uv installs Python
3.11+ for you. No database server, no Docker.

```bash
uv run --extra dev pytest -q               # the test suite
uv run flask --app workshop run --debug    # look around at http://localhost:5000/demo, then Ctrl+C
git checkout -b my-recurring-bills
```

Open your harness in this folder (`claude`, `opencode` or `codex`) and type:

```text
/speckit-specify Add recurring bills. When adding a bill, a member can make it repeat every week, month or year from the bill's date, optionally until an end date. Every occurrence that has come due is added as a normal bill with the same payer, people, amount and currency, even if nobody opened the project for months. A monthly bill on the 31st falls on the last day of shorter months. An occurrence is never added twice, not even when two members open the project at the same moment, and one that was deleted by hand never comes back. A new page lists the project's recurring bills with their next date. From there a member can edit one (future occurrences only), pause, resume or stop it, and skip the next occurrence. Bills added this way link back to their recurring bill, changes to recurring bills show in the project history, and the API lets the mobile app manage them. Existing bills, exports and the API must keep working.
```

In opencode start with `/speckit.specify`, in Codex with `$speckit-specify`.

Read what the agent writes before you move on. After each step it tells you the next command.
Lost? Type `next`. Want to know why? Type `explain`. You won't finish the whole feature, and that's
fine: the point is to see what each step does. The agent explains each step as you go.

## Steps

| # | Step | What happens | Claude Code | opencode | Codex |
|---|---|---|---|---|---|
| 1 | specify | Agent writes `specs/<feature>/spec.md`: what and why, no code. It may ask up to 3 big questions first. | `/speckit-specify` | `/speckit.specify` | `$speckit-specify` |
| 2 | clarify | Agent asks you up to 5 questions and writes the answers into the spec. | `/speckit-clarify` | `/speckit.clarify` | `$speckit-clarify` |
| 3 | plan | Agent writes `plan.md`: how, which files, checked against the constitution. | `/speckit-plan` | `/speckit.plan` | `$speckit-plan` |
| 4 | tasks | Agent breaks the plan into `tasks.md`, grouped by user story. | `/speckit-tasks` | `/speckit.tasks` | `$speckit-tasks` |
| 5 | analyze | Agent checks spec, plan and tasks against each other. Changes nothing; ask it to fix what it finds. | `/speckit-analyze` | `/speckit.analyze` | `$speckit-analyze` |
| 6 | implement | Agent builds one user story at a time: migration, code, tests. Run it again for the next story. | `/speckit-implement` | `/speckit.implement` | `$speckit-implement` |

## Finished early?

Run the steps again for one of these:

- Split a bill by exact amounts or percentages, with cents that always add up to the total
- Close a period: settle up, archive its bills and start fresh (there is a half-built `Archive` model)
- Spending categories, each with a monthly budget and a warning when it's exceeded
- A weekly email to each member saying what they owe and to whom
