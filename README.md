# Agentic workshop

Add a feature to an existing codebase using a spec-driven harness.

## Start

```bash
git clone git@github.com:joexbayer/agentic-workshop.git
cd agentic-workshop
git checkout petclinic/openspec     # pick a branch below
```

Then follow `README.md` on that branch.

## Branches

| | Spec Kit | OpenSpec |
|---|---|---|
| fakeredis (Python) | `fakeredis/speckit` | `fakeredis/openspec` |
| Spring PetClinic (Java) | `petclinic/speckit` | `petclinic/openspec` |

## Needs

- An agent: Claude Code, opencode or Codex
- fakeredis: uv, Docker
- PetClinic: Java 17+
- Spec Kit: bash (WSL/Git Bash on Windows)
- OpenSpec: Node 20+ and `npm i -g @fission-ai/openspec@1.13.2`
