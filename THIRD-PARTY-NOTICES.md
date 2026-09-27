# Third-party notices

This workshop branch is built from the open-source projects below. It is not affiliated with or
endorsed by any of them.

## Spring PetClinic

- Source: <https://github.com/spring-projects/spring-petclinic>, commit `818c4136`.
- Licence: Apache License 2.0. The full text is in `LICENSE.txt`, and the copyright headers in the
  source files are unchanged.
- Changed for this workshop:
  - `README.md` is replaced by the workshop guide. The original is `UPSTREAM-README.md`, unchanged.
  - `pom.xml`: the MySQL and Postgres test suites, which need Docker, are skipped by default;
    `./mvnw test -Ddocker.tests=true` runs them again.
  - Added: `AGENTS.md`, `CLAUDE.md`, `THIRD-PARTY-NOTICES.md` and the spec tool files below.

## Spec Kit

- Source: <https://github.com/github/spec-kit>, specify-cli 1.0.11.
- Files from it: `.specify/`, `.claude/skills/speckit-*`, `.agents/skills/speckit-*` and
  `.opencode/commands/speckit.*`.
- Changed for this workshop: `.specify/memory/constitution.md` is written for this project, and
  the tasks skill (all three copies) and `.specify/templates/tasks-template.md` say tests are
  required instead of optional.
- Licence: MIT.

```text
MIT License

Copyright GitHub, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
