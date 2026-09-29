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

## Petters verktøy

Dette er verktøy jeg bruker eller utforsker ved siden av workshopen, **ikke krav** for å følge
oppgavene over. Flere av oppsettene finnes i mitt offentlige
[dotfiles-repo](https://github.com/psoland/os-config).

### Arbeidsmiljø og parallelle oppgaver

- [devenv](https://devenv.sh/) definerer reproduserbare utviklingsmiljøer med Nix. Jeg bruker
  `devenv.nix` og `devenv shell` for prosjektavhengigheter; dotfiles har egne maler som kan
  opprettes med for eksempel `init-devenv-py` eller `init-devenv-ts`.
- [Git worktrees](https://git-scm.com/docs/git-worktree) lar meg sjekke ut flere grener fra samme
  repo samtidig, slik at oppgaver og agentøkter ikke tråkker på hverandres filer. Zsh-funksjonen
  [`wt`](https://github.com/psoland/os-config/blob/main/modules/home/programs/zsh_wt.sh) gir
  `wt clone <url>` (bare repo i `.bare`), `wt add <gren> [base]`, `wt ls` og `wt rm <sti>`.
  `wt rmo <sti>` sletter **også grenen på origin**; den bruker jeg bare når det er tilsiktet.
- [tmux](https://github.com/tmux/tmux/wiki) holder terminaløkter, vinduer og paneler i gang når
  jeg kobler fra, blant annet over SSH. I dotfiles er prefikset `Ctrl+s`; `t` kobler til eller
  starter en økt, og `td c` setter opp Neovim ved siden av OpenCode.
- [`ts`](https://github.com/psoland/os-config/blob/main/profiles/home/ts.sh) er mitt eget oppsett
  for en *navngitt* tmux-utviklingsøkt: `ts <øktnavn> [sti]` starter vinduer for Neovim, Hunk og
  terminal, med OpenCode i sidepanelene.
- [Tailscale](https://tailscale.com/) kobler maskinene mine sammen i et privat nett, slik at jeg
  kan bruke SSH og interne tjenester på tvers av enheter. Dotfiles har også Tailscale Serve-ruter
  på utvalgte maskiner og `drop <fil> <enhet>` for å sende filer med Taildrop.
- [Varlock](https://varlock.dev/) deklarerer og validerer miljøvariabler i `.env.schema`, og kan
  hente hemmeligheter uten å legge verdiene i repoet. Jeg bruker det blant annet med Bitwarden for
  å gi OpenCode tilgang til Knowit AI Gateway via `voc2`-oppstarten i dotfiles.

### Agenter og ferdigheter

- [OpenCode](https://opencode.ai/v2/docs/) er hovedagenten min for å utforske, endre og teste kode
  fra terminalen. Jeg starter den med `opencode` (eller `oc`), og har egne agenter, kommandoer og
  integrasjoner konfigurert i [dotfiles-repoet](https://github.com/psoland/os-config/tree/main/config/opencode).
- [Pi](https://pi.dev/) er en minimal, utvidbar kodeagent jeg kan starte med `pi` når jeg vil ha
  en enklere agentøkt. `td p` åpner Pi ved siden av Neovim i tmux; felles agentinstruksjoner og
  promptmaler kommer fra dotfiles.
- [Codex Remote](https://learn.chatgpt.com/docs/remote) lar meg starte, følge opp, godkjenne og
  gjennomgå Codex-oppgaver fra mobilen mens de kjøres på en tilkoblet Mac eller Windows-PC. Det
  er et alternativ når jeg vil styre en lokal kodeøkt uten å sitte ved maskinen, forutsatt at
  funksjonen er tilgjengelig for kontoen min.
- [skills.sh](https://skills.sh/) er en katalog og CLI for gjenbrukbare agentferdigheter. Jeg
  bruker slike *skills* til å gi agenter oppgavespesifikke instrukser i stedet for å putte alt i
  én stor prompt; dotfiles deler egne skills mellom flere agenter.
- [grill-me](https://www.aihero.dev/skills-grill-me) er en skill for å la agenten stille
  avklarende spørsmål i runder før en uklar idé blir til en plan eller spesifikasjon. Den kan
  startes med `/grill-me` i en agent der den er installert; den skriver ikke prosjektfiler.
- **Knowit Brand** er min egen
  [`knowit-brand`-skill](https://github.com/psoland/os-config/tree/main/config/agents/skills/knowit-brand).
  Jeg ber agenten bruke den når jeg lager Knowit-materiell, slik at farger, typografi, logo og
  layout følger «Nordic Skies»-profilen.

### Review, visualisering og dokumenter

- [Hunk](https://www.hunk.dev/) er en terminalbasert diff- og reviewvisning der både jeg og
  agenten kan kommentere endringer. Jeg bruker `hd` for arbeidskopien, `hdm` mot `main`, `hds`
  for staged endringer og `hda <fil>` når jeg vil kommentere også uendrede linjer i en hel fil.
- **Dokumentkommentarer** er min
  [hjemmelagde Neovim-plugin](https://github.com/psoland/os-config/tree/main/config/nvim/local/document-comments.nvim)
  for kommentarer forankret i Markdown.
  Jeg markerer tekst og trykker `<leader>aa`, eksporterer åpne kommentarer med `<leader>ax`, lar
  agenten behandle dem med `/comments` og går selv gjennom/avklarer resultatet. Kommentarene
  lagres per prosjekt i `.document-comments/`.
- [Sideshow](https://sideshow.sh/) gir agenter en visuell tavle for mockups, diagrammer, diff-er
  og annet innhold som jeg kan se og kommentere underveis. MCP-tilkoblingen finnes i OpenCode-
  oppsettet mitt, men er for øyeblikket deaktivert.
- [Executor](https://executor.sh/) samler API-er og MCP-integrasjoner bak ett endepunkt med
  tilgangskontroll. Jeg har det aktivert som MCP i OpenCode, slik at agenten kan finne og bruke
  tilkoblede verktøy uten at hvert enkelt må konfigureres i agenten.
- [Typst](https://typst.app/) er et system for å sette opp og generere dokumenter, særlig PDF.
  I `proposals`-repoet skriver jeg tilbud i Markdown og bruker Pandoc med
  `templates/knowit.typst` og `--pdf-engine typst` til å lage PDF-er i Knowit-profil. I det
  repoet gir `devenv shell` meg Pandoc og Typst.

### Webgrensesnitt og nettleser

- [shadcn/ui](https://ui.shadcn.com/) gir tilgjengelige, tilpassbare komponenter som legges i
  appens egen kildekode. Jeg bruker det som utgangspunkt for React-grensesnitt; en shadcn-MCP er
  konfigurert i OpenCode, men er deaktivert som standard.
- [agent-browser](https://github.com/vercel-labs/agent-browser) er en CLI for nettleserautomatisering
  laget for agenter. Ved webarbeid kan agenten åpne en side, hente et tilgjengelighets-snapshot,
  klikke på elementer og ta skjermbilder for å kontrollere resultatet.

## Lisenser

Hver gren inneholder applikasjonens egen lisens og en `THIRD-PARTY-NOTICES.md`.
Spring PetClinic er lisensiert under Apache-2.0, I Hate Money har en lisens i
BSD-stil, og Spec Kit og OpenSpec er MIT-lisensiert. Denne øvelsen er ikke
tilknyttet eller godkjent av noen av disse prosjektene.
