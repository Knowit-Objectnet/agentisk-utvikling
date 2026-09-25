# Workshop: spec-driven development on Spring PetClinic

Spring PetClinic is the canonical Spring Boot sample app: owners, pets, visits and vets. It is small,
but it has real build rules (formatting, i18n, three databases). Your job: add a feature through a
spec-driven development (SDD) harness and meet the Definition of Done.

## 1. Setup (do this before the session)

```bash
# Tools
# Java 17+ (21 recommended), for example: sdk install java 21-tem
curl -LsSf https://astral.sh/uv/install.sh | sh            # uv, needed to install Spec Kit
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.0.11
npm install -g @fission-ai/openspec@1.13.2                  # needs Node 20+

# Repo
git clone <your fork url> spring-petclinic && cd spring-petclinic

# Warm the Maven cache and check the build (about 1 min; no Docker needed)
./mvnw -B test -Dtest='!*Postgres*,!*MySql*' -Dsurefire.failIfNoSpecifiedTests=false

# Run the app on http://localhost:8080
./mvnw spring-boot:run
```

## 2. Pick your track

| Branch | Harness | Flow |
|---|---|---|
| `speckit` | GitHub Spec Kit 1.0.11 | `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement` |
| `openspec` | OpenSpec 1.13.2 | `/opsx:explore` (optional) → `/opsx:propose` → `/opsx:apply` → `/opsx:archive` |
| `baseline` | none | control group: same task, plain prompting |

```bash
git checkout speckit        # or: git checkout openspec
git checkout -b my-cancel-visit
```

Both harness branches ship a constitution (`.specify/memory/constitution.md` or
`openspec/constitution.md`), and `AGENTS.md` lists the build gotchas. Read both before you start.

## 3. Main task (~90 min): cancel an upcoming visit

Paste this as your feature request:

> Receptionists need to cancel an upcoming visit when an owner calls. On the owner details page each
> visit should show whether it's scheduled or cancelled, upcoming visits get a Cancel action, and
> cancelled visits stay visible in history, marked as cancelled. Visits in the past can't be
> cancelled.

Your harness will ask questions, or should: is today "upcoming"? Is a reason required? Can a
cancellation be undone? Decide, and make sure the answers land in the spec.

Tip: every seeded visit is from 2008–2013, so nothing is cancellable out of the box. To try the
feature by hand, book a future visit first, then cancel it:

```bash
curl -s -c jar -b jar -o /dev/null -w '%{http_code}\n' -X POST \
  -d "date=$(date -v+3d +%F 2>/dev/null || date -d '+3 days' +%F)&description=checkup" \
  http://localhost:8080/owners/6/pets/7/visits/new           # expect 302
curl -s -c jar -b jar http://localhost:8080/owners/6 | grep -i -A2 checkup
```

Don't use `curl -L -X POST`: it re-POSTs to the redirect target and you get a confusing 405.

### Definition of Done

1. A visit has a persisted status (or equivalent). The column is in all three
   `db/{h2,mysql,postgres}/schema.sql` files, and existing seed visits still load as scheduled.
2. The owner details page shows each visit's status. Upcoming scheduled visits have a Cancel control
   that submits a **POST**, not a GET link. Cancelled visits stay listed and are marked cancelled.
3. The server enforces the rules. Cancelling a past visit, an already-cancelled visit, or a visit
   whose owner, pet or visit id doesn't match is rejected, not just hidden in the UI.
4. Every new UI string is a message key in `messages.properties` and the 9 translated files
   (`messages_en.properties` stays empty). `I18nPropertiesSyncTest` passes.
5. `@WebMvcTest` tests cover the happy path and each rejection. A persistence test covers the status.
6. The fast suite is green and `./mvnw -B validate` passes (formatting + nohttp).
7. Demo: in the running app, book a future visit, cancel it, and show that it is marked cancelled.
8. Harness artifacts are complete:
   - Spec Kit: spec, plan and tasks with every task checked.
   - OpenSpec: `openspec validate --strict` passes, and the change is archived into `openspec/specs/`.

## 4. Stretch tasks

**Tier 2: a second change on top of your spec (30–60 min)**

- **Reschedule a visit.** Edit the date of an upcoming scheduled visit, under the same rules: past
  or cancelled visits can't be changed. This modifies requirements your first spec already
  describes. Watch how your harness handles that.
- **Upcoming-visits page.** A clinic-wide list of scheduled visits in the next 7 days, paginated
  like the owners list. Constitution Principle II says "no `VisitRepository` without justification".
  Make the design decision explicitly in your plan or design.

**Tier 3: bigger features (a half day or more)**

- **Vets on visits.** Assign a vet when booking. Show the vet on the owner page and each vet's
  upcoming visits on the vets page. Reject double-booking a vet on the same day. This crosses the
  aggregate boundary, and the vet list is cached.
- **Schema migrations with Flyway.** Replace `schema.sql` / `data.sql` with versioned migrations for
  H2, MySQL and Postgres, and prove an existing database volume gets upgraded. This adds a
  dependency, so you must amend the constitution first. That is the exercise.
- **Owner self-service JSON API.** The constitution says "no REST API unless a feature genuinely
  needs it". Write the spec that argues it does (for example a mobile app for owners), amend the
  constitution, then build `GET/POST /api/owners/{id}/visits` with tests.
