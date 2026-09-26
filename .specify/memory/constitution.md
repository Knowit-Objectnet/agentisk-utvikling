<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Bump rationale: Initial ratification for the agentic-workshop fork of spring-petclinic.
Added sections: Core Principles I–V, Code Quality Standards, Development Workflow, Governance.
Deferred TODOs: none.
-->

# Spring PetClinic Constitution

## Core Principles

### I. Sample-App Simplicity (NON-NEGOTIABLE)

PetClinic exists to show idiomatic Spring Boot. Every change MUST be the simplest thing a Spring
developer would recognise.

- Use the existing stack only: Spring MVC + Thymeleaf, Spring Data JPA, Bean Validation, H2 by
  default. New runtime dependencies require an amendment to this constitution.
- Follow the existing package-by-feature layout (`owner/`, `vet/`, `system/`). A new package
  requires a new domain concept, not organisational preference.
- No service layer, DTO mapping layer, or REST API unless a feature genuinely needs it; controllers
  talk to Spring Data repositories directly, as the existing code does.

Rationale: readers copy this code. Clever architecture teaches the wrong lesson.

### II. Aggregate Boundaries

`Owner` is the aggregate root for `Pet` and `Visit`. Changes to pets and visits MUST go through the
owner (`OwnerRepository`), as `PetController` and `VisitController` already do.

- Do not add a `VisitRepository` or `PetRepository` to bypass the aggregate unless a spec states
  why the aggregate cannot serve the use case.
- Domain rules (e.g. "a visit in the past cannot be changed") live on the entity or in a
  validator, not only in a template.

### III. Test Every Behaviour

Every user-visible behaviour MUST be pinned by a test.

- Controller behaviour: `@WebMvcTest` tests in the matching `*ControllerTests` class, with mocked
  repositories, asserting status, view name, model attributes and validation errors.
- Persistence behaviour: `@DataJpaTest` in `ClinicServiceTests` against H2.
- A bug fix MUST start with a failing test that reproduces it.
- The fast suite (`./mvnw test`)
  MUST pass before a change is considered done.

### IV. Every Database, Every Language

PetClinic ships three databases and eleven languages; a feature is not done until all of them work.

- Schema changes MUST be applied to all three `src/main/resources/db/{h2,mysql,postgres}/schema.sql`
  files, and to the matching `data.sql` when seed rows need the new column.
- Every user-visible string MUST be a message key rendered with `th:text="#{key}"`, and every new
  key MUST exist in `messages.properties` and the 9 translated `messages_*.properties` files
  (`I18nPropertiesSyncTest` enforces this). `messages_en.properties` is intentionally empty and
  MUST stay empty. English text in non-English files is acceptable; missing keys are not.

### V. Accessible, Consistent UI

New screens and controls MUST reuse the existing Bootstrap layout and fragments
(`fragments/layout.html`, `inputField.html`, `selectField.html`).

- State-changing actions MUST use `POST` (a form with a button), never a `GET` link.
- Every page MUST remain usable without JavaScript.

## Code Quality Standards

- Code MUST be formatted with Spring Java Format (`./mvnw spring-javaformat:apply`); the build
  fails in the `validate` phase otherwise.
- No `http://` URLs anywhere in the repository, including docs and specs: the nohttp checkstyle
  rule scans every file.
- Keep the Apache 2.0 licence header on every new Java file, copied from an existing file.

## Development Workflow

- One feature per branch; commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`,
  `test:`, `chore:`).
- A change is done when: the fast suite is green, `./mvnw -B validate` passes, the feature works in
  the running app (`./mvnw spring-boot:run`), and the spec's acceptance scenarios are each covered
  by a test.

## Governance

This constitution supersedes conflicting habits and prior precedent in this fork.

- **Amendments**: proposed as a change to this file with a rationale and a version bump.
- **Versioning**: MAJOR for removing or redefining a principle, MINOR for adding one or materially
  expanding guidance, PATCH for wording.
- **Compliance**: every plan MUST include a constitution check against Principles I–V; a violation
  MUST be justified in the plan's Complexity Tracking table or removed.
- **Runtime guidance**: `AGENTS.md` holds operational detail (commands, gotchas, layout) and MUST
  NOT contradict this file.

**Version**: 1.0.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-09-25
