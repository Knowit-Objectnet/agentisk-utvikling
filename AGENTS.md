# AGENTS.md

Guidance for coding agents (Claude Code, opencode, ...) working in this repository.

Spring PetClinic: a Spring Boot 4 / Java 17+ sample app (Spring MVC + Thymeleaf, Spring Data JPA,
H2 by default, optional MySQL/Postgres). Owners have pets, pets have visits, vets have specialties.

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
- Tests are always part of the work. `/speckit-tasks` MUST generate test tasks, even though its
  template calls them optional: the constitution requires a test for every behaviour.
- End every step with one line naming the next step, in the syntax of the harness you are
  running in, plus what to review first. Example: `Next: /speckit-clarify (review spec.md first)`.
- If the user types `next` or asks what to do now, check `specs/` (which of `spec.md`, `plan.md`,
  `tasks.md` exist, which tasks are ticked) to see where they are and answer the same way. Do not
  run the step for them.
- After implement, point them to "Finished early?" in `README.md`.

### Teaching

- **First step of the session:** open with at most 4 lines on what Spec Kit is (below), then do
  the work.
- **After every step:** before the `Next:` line, add a short block headed `What just happened`
  (at most 6 lines): what this step is for, which files it wrote and what each holds, what the
  user should check when reviewing, and one thing to try (an edit or a follow-up question).
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
  Unclear points are marked `[NEEDS CLARIFICATION]`. Review: could a non-developer read it and agree?
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
- **implement** runs the tasks phase by phase and ticks each box in `tasks.md`. Review: stop after
  the P1 phase, run the tests and look at the result before going on.
- **Optional:** `/speckit-checklist` (opencode `/speckit.checklist`, Codex `$speckit-checklist`)
  writes "unit tests for the requirements": questions that check the spec itself is complete.

## Commands

```bash
# Run the app on http://localhost:8080 (H2 in-memory, seeded from db/h2/data.sql)
./mvnw spring-boot:run

# Test suite (~15 s, H2 only; the MySQL/Postgres Testcontainers suites are excluded in pom.xml,
# run them with -Ddocker.tests=true if you have Docker)
./mvnw test

# Single test class
./mvnw -B test -Dtest=VisitControllerTests

# Fix formatting (the build FAILS in the validate phase if code is not formatted)
./mvnw spring-javaformat:apply
```

## Gotchas

- **Formatting is enforced.** `spring-javaformat:validate` runs in the `validate` phase, so an
  unformatted file fails every build, including `test`. Run `./mvnw spring-javaformat:apply`.
  Style: tabs, Spring Java Format conventions.
- **nohttp checkstyle scans every file in the repo** (`**/*`, not only sources). Any `http://`
  URL in any file, including Markdown and spec files, fails the build. Use `https://`.
- **i18n is tested.** `I18nPropertiesSyncTest` fails if an HTML template contains literal text
  instead of `th:text="#{key}"`, or if a key in `messages.properties` is missing from any of the
  translated `messages_*.properties` files. A new UI string means one key in `messages.properties`
  plus the 9 translated files. `messages_en.properties` is intentionally empty (falls back to the
  default) and must stay empty.
- **Three schemas.** Schema and seed data exist for H2, MySQL and Postgres under
  `src/main/resources/db/{h2,mysql,postgres}/`. A column change touches all three `schema.sql`
  files. The H2 and MySQL `data.sql` inserts are positional (no column list), so adding a column
  to `visits`, `pets` etc. breaks startup and every JPA test until those inserts are updated.

## Layout

- `owner/` — `Owner`, `Pet`, `Visit`, `PetType` entities; `OwnerController`, `PetController`,
  `VisitController`; `OwnerRepository` (Spring Data). Visits are reached through the owner
  aggregate (`Owner` → `Pet` → `Visit`); there is no `VisitRepository`.
- `vet/` — `Vet`, `Specialty`, `VetController`, `VetRepository` (cached with Caffeine/JCache).
- `system/` — welcome page, error page, cache and web config.
- `templates/` — Thymeleaf views; `fragments/layout.html` is the page shell.
- Tests mirror the packages under `src/test/java`; controller tests use `@WebMvcTest` with
  mocked repositories, `ClinicServiceTests` uses `@DataJpaTest` against H2.
