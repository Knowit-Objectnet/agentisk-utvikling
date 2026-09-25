# Spring PetClinic · Spec Kit

## 1. Setup

- An agent: Claude Code, opencode or Codex
- Java 17+
- bash (WSL/Git Bash on Windows)

```bash
./mvnw -B test -Dtest='!*Postgres*,!*MySql*' -Dsurefire.failIfNoSpecifiedTests=false
./mvnw spring-boot:run      # http://localhost:8080
git checkout -b my-cancel-visit
```

## 2. Steps

Read `.specify/memory/constitution.md` first. Review each step's output before the next.

| Step | Claude Code | opencode | Codex |
|---|---|---|---|
| specify | `/speckit-specify` | `/speckit.specify` | `$speckit-specify` |
| clarify | `/speckit-clarify` | `/speckit.clarify` | `$speckit-clarify` |
| plan | `/speckit-plan` | `/speckit.plan` | `$speckit-plan` |
| tasks | `/speckit-tasks` | `/speckit.tasks` | `$speckit-tasks` |
| analyze | `/speckit-analyze` | `/speckit.analyze` | `$speckit-analyze` |
| implement | `/speckit-implement` | `/speckit.implement` | `$speckit-implement` |

## 3. Task

> Receptionists need to cancel an upcoming visit when an owner calls. On the owner details page each
> visit should show whether it's scheduled or cancelled, upcoming visits get a Cancel action, and
> cancelled visits stay visible in history, marked as cancelled. Visits in the past can't be cancelled.

All seed visits are in the past. Book a future one first:

```bash
curl -s -c jar -b jar -o /dev/null -w '%{http_code}\n' -X POST \
  -d "date=$(date -v+3d +%F 2>/dev/null || date -d '+3 days' +%F)&description=checkup" \
  http://localhost:8080/owners/6/pets/7/visits/new
```

## 4. Done when

- [ ] Visit status persisted; column in all 3 `db/*/schema.sql`; seed visits load as scheduled
- [ ] Owner page shows status; Cancel is a **POST** form, only on upcoming scheduled visits; cancelled visits stay listed
- [ ] Server rejects: past visit, already cancelled, mismatched owner/pet/visit ids
- [ ] New strings in `messages.properties` + the 9 translated files (`messages_en` stays empty)
- [ ] `@WebMvcTest` for happy path + each rejection; persistence test for status
- [ ] Fast suite green and `./mvnw -B validate` passes
- [ ] Works in the running app

## 5. Hints

<details><summary>Blank visit saved / validation fails on save</summary>

`VisitController` has a class-wide `@ModelAttribute` that runs before every handler. Put the cancel endpoint elsewhere.

</details>

<details><summary>App won't start after adding a column</summary>

`db/h2/data.sql` and `db/mysql/data.sql` insert visits positionally. Add the value.

</details>

<details><summary>Null id in persistence test</summary>

`OwnerRepository.save()` merges. Flush, clear, reload the owner, then assert.

</details>

<details><summary>MockMvc `xpath()` throws</summary>

HTML5 isn't XML. Use `content().string(containsString(...))`.

</details>

<details><summary>Build fails before tests run</summary>

`./mvnw spring-javaformat:apply`. No `http://` URLs anywhere (localhost is fine).

</details>

<details><summary>`I18nPropertiesSyncTest` fails</summary>

Literal text in a template, or a missing key. `messages_en.properties` has no trailing newline.

</details>

<details><summary>405 when testing with curl</summary>

Don't use `curl -L -X POST`.

</details>

## 6. Next

- Reschedule an upcoming visit (same rules)
- Upcoming-visits page: next 7 days, all owners, paginated

## 7. Advanced

- Vets on visits: assign a vet, show schedules, reject double-booking
- Spring Security: receptionist and vet roles (amend the constitution first)
- Flyway migrations for H2, MySQL and Postgres (amend the constitution first)
- Owner JSON API for visits (amend the constitution first)
