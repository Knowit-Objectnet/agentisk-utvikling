# Agentisk utvikling

Dette repoet inneholder øvingsprosjekter til
[kurset i agentisk utvikling](https://academy.knowit.no/kurs/agentisk-utvikling).
Se [forberedelsesguiden](FORBEREDELSER.md) for hva du kan gjøre før kurset:
ta med eget prosjekt eller en idé, og installer gjerne en kodeagent på forhånd.
Vi anbefaler [OpenCode](https://opencode.ai/v2/docs/), men du kan bruke den
agenten du ønsker.

## Øvingsprosjekter

Har du ikke et eget prosjekt, kan du bruke et av eksemplene under. Grenene
inneholder en egen øvelse i spesifikasjonsdrevet utvikling med Spec Kit eller
OpenSpec: Prøv en større funksjon i en eksisterende kodebase, og la agenten
forklare hva hvert steg gjør. Du trenger ikke bli ferdig med funksjonen.

### Kom i gang

```bash
git clone https://github.com/Knowit-Objectnet/agentisk-utvikling.git
cd agentisk-utvikling
git checkout petclinic/openspec     # velg en gren fra tabellen under
```

Følg deretter `README.md` på grenen du valgte.

### Grener

| Prosjekt | Spec Kit | OpenSpec | Oppgave |
|---|---|---|---|
| Spring PetClinic (Java) | `petclinic/speckit` | `petclinic/openspec` | Veterinæravtaler med timeplaner |
| I Hate Money (Python, Flask) | `ihatemoney/speckit` | `ihatemoney/openspec` | Gjentakende regninger |

### Forutsetninger for disse øvelsene

- En kodeagent, for eksempel [OpenCode](https://opencode.ai/v2/docs/), Claude Code eller Codex
- PetClinic: Java 17+
- I Hate Money: [uv](https://docs.astral.sh/uv/)
- Spec Kit: bash (WSL eller Git Bash på Windows)
- OpenSpec: Node 20+ og `npm i -g @fission-ai/openspec@1.13.2`

Du trenger verken Docker eller en databaseserver. Testene kjører lokalt på få sekunder.

## Mer om verktøy

Se [Petters verktøy](PETTERS-VERKTOY.md) for et utvalg verktøy jeg bruker eller
utforsker ved siden av kurset. De er ikke krav for å delta.

## Lisenser

Hver gren inneholder applikasjonens egen lisens og en `THIRD-PARTY-NOTICES.md`.
Spring PetClinic er lisensiert under Apache-2.0, I Hate Money har en lisens i
BSD-stil, og Spec Kit og OpenSpec er MIT-lisensiert. Denne øvelsen er ikke
tilknyttet eller godkjent av noen av disse prosjektene.
