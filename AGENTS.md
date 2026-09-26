# AGENTS.md

Guidance for coding agents (Claude Code, opencode, ...) working in this repository.

Spring PetClinic: a Spring Boot 4 / Java 17+ sample app (Spring MVC + Thymeleaf, Spring Data JPA,
H2 by default, optional MySQL/Postgres). Owners have pets, pets have visits, vets have specialties.

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
- Before archive, `openspec validate <change> --strict` must pass.
- The `openspec` CLI prints its own `Next: openspec ...` hints. Those are for you; the user only
  ever gets the slash command.
- End every step with one line naming the next step, in the syntax of the harness you are
  running in, plus what to review first. Example: `Next: /opsx:apply (review tasks.md first)`.
- If the user types `next` or asks what to do now, check `openspec/changes/` to see where they
  are and answer the same way. Do not run the step for them.
- After archive, point them to "Finished early?" in `README.md`.

### Teaching

- **First step of the session:** open with at most 4 lines on what OpenSpec is (below), then do
  the work.
- **After every step:** before the `Next:` line, add a short block headed `What just happened`
  (at most 6 lines): what this step is for, which files it wrote and what each holds, what the
  user should check when reviewing, and one thing to try (a CLI command or an edit).
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
- **Optional:** `/opsx:explore` (opencode `/opsx-explore`, Codex `$openspec-explore`) is a thinking partner before
  proposing. Nothing gets written.

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
