# Agentic workshop

Try a spec-driven workflow (Spec Kit or OpenSpec) inside your coding agent, on a big feature in a
real codebase. You won't finish the feature. The point is to see what each step does, and the
agent explains each step as you go.

## Start

```bash
git clone git@github.com:Knowit-Objectnet/agentisk-utvikling.git
cd agentisk-utvikling
git checkout petclinic/openspec     # pick a branch below
```

Then follow `README.md` on that branch.

## Branches

| | Spec Kit | OpenSpec | The feature |
|---|---|---|---|
| Spring PetClinic (Java) | `petclinic/speckit` | `petclinic/openspec` | Vet appointments with schedules |
| I Hate Money (Python, Flask) | `ihatemoney/speckit` | `ihatemoney/openspec` | Recurring bills |

## Needs

- An agent: Claude Code, opencode or Codex
- PetClinic: Java 17+
- I Hate Money: [uv](https://docs.astral.sh/uv/)
- Spec Kit: bash (WSL or Git Bash on Windows)
- OpenSpec: Node 20+ and `npm i -g @fission-ai/openspec@1.13.2`

No Docker and no database server. Tests run locally in seconds.

## Tau observability

The devenv-installed Tau agent supports opt-in Logfire tracing, including system
prompts, model messages, and tool calls. See [setup and privacy controls](docs/tau-logfire.md).

## Licences

Each branch carries its app's own licence and a `THIRD-PARTY-NOTICES.md`. Spring PetClinic is
Apache-2.0, I Hate Money uses a BSD-style licence, and Spec Kit and OpenSpec are MIT. This workshop
is not affiliated with or endorsed by any of these projects.
