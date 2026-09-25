# CLAUDE.md

Guidance for coding agents working in this repository.

Spring PetClinic: a Spring Boot 4 / Java 17+ sample app (Spring MVC + Thymeleaf, Spring Data JPA,
H2 by default, optional MySQL/Postgres). Owners have pets, pets have visits, vets have specialties.

## Commands

```bash
# Run the app on http://localhost:8080 (H2 in-memory, seeded from db/h2/data.sql)
./mvnw spring-boot:run

# Fast test run: skips the MySQL/Postgres Testcontainers suites (no Docker needed)
./mvnw -B test -Dtest='!*Postgres*,!*MySql*' -Dsurefire.failIfNoSpecifiedTests=false

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
  `messages_*.properties` files. A new UI string means one key in all 11 files.
- **Three schemas.** Schema and seed data exist for H2, MySQL and Postgres under
  `src/main/resources/db/{h2,mysql,postgres}/`. A column change touches all three `schema.sql`
  files (and `data.sql` if seed rows need the column).

## Layout

- `owner/` — `Owner`, `Pet`, `Visit`, `PetType` entities; `OwnerController`, `PetController`,
  `VisitController`; `OwnerRepository` (Spring Data). Visits are reached through the owner
  aggregate (`Owner` → `Pet` → `Visit`); there is no `VisitRepository`.
- `vet/` — `Vet`, `Specialty`, `VetController`, `VetRepository` (cached with Caffeine/JCache).
- `system/` — welcome page, error page, cache and web config.
- `templates/` — Thymeleaf views; `fragments/layout.html` is the page shell.
- Tests mirror the packages under `src/test/java`; controller tests use `@WebMvcTest` with
  mocked repositories, `ClinicServiceTests` uses `@DataJpaTest` against H2.
