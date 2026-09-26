# Spring PetClinic · Spec Kit

## The app

PetClinic is a small website for a vet clinic, built with Spring Boot. Staff look up owners, add
their pets, and record visits. Every page is a Spring controller plus a Thymeleaf template. Data
lives in an in-memory H2 database: an owner has pets, a pet has visits, and the clinic has vets.

```mermaid
flowchart LR
    B[Browser] --> C["Controllers<br/>(Owner, Pet, Visit, Vet)"]
    C --> T[Thymeleaf pages]
    C --> R[Repositories]
    R --> DB[(H2 in-memory)]
    subgraph Data
        O[Owner] -->|has| P[Pet] -->|has| V[Visit]
        Vet
    end
    DB --- Data
```

## The problem

A visit today is only a date and a note, and vets aren't involved at all. The clinic wants real
appointments: a visit is booked with a specific vet at a specific time, only when the clinic is
open, and a vet can never be in two places at once. Receptionists want to see who is booked when.

## Getting started

Needs Java 17+, bash (WSL or Git Bash on Windows). No database server, no Docker.

```bash
./mvnw test                  # ~15 s, no Docker needed
./mvnw spring-boot:run       # look around at http://localhost:8080, then Ctrl+C
git checkout -b my-appointments
```

Open your harness in this folder (`claude`, `opencode` or `codex`) and type:

```text
/speckit-specify Turn visits into appointments. A visit is booked with a specific vet at a start time, lasts 30 minutes, and must fall inside clinic opening hours (Monday to Friday, 08:00 to 16:00). A vet can't be double-booked and appointments can't be in the past. The booking form only offers the chosen vet's free times, the owner page shows each visit's vet and time, and each vet gets a page with their appointments for a day. Existing visits must keep working.
```

In opencode start with `/speckit.specify`, in Codex with `$speckit-specify`.

Read what the agent writes before you move on. After each step it tells you the next command.
Lost? Type `next`. You don't have to finish: the point is to see what each step does.

## Steps

| # | Step | What happens | Claude Code | opencode | Codex |
|---|---|---|---|---|---|
| 1 | specify | Agent writes `specs/<feature>/spec.md`: what and why, no code. | `/speckit-specify` | `/speckit.specify` | `$speckit-specify` |
| 2 | clarify | Agent asks you up to 5 questions and writes the answers into the spec. | `/speckit-clarify` | `/speckit.clarify` | `$speckit-clarify` |
| 3 | plan | Agent writes `plan.md`: how, which files, checked against the constitution. | `/speckit-plan` | `/speckit.plan` | `$speckit-plan` |
| 4 | tasks | Agent breaks the plan into `tasks.md`, grouped by user story. | `/speckit-tasks` | `/speckit.tasks` | `$speckit-tasks` |
| 5 | analyze | Agent checks spec, plan and tasks against each other. Changes nothing; ask it to fix what it finds. | `/speckit-analyze` | `/speckit.analyze` | `$speckit-analyze` |
| 6 | implement | Agent works through the tasks: code, tests, translations. | `/speckit-implement` | `/speckit.implement` | `$speckit-implement` |

## Finished early?

Run the steps again for one of these:

- Cancel and reschedule appointments (past ones stay locked)
- Merge duplicate owners without losing a pet or a visit
- Invoices: price per visit type, multi-pet discount, VAT, rounding per locale
- Vaccination tracker: due and overdue vaccines per pet, with a clinic-wide overdue list
