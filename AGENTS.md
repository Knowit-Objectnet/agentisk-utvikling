# AGENTS.md

Guidance for coding agents (Claude Code, opencode, Codex, ...) working in this repository.

This is a workshop. The user builds a small website from an empty folder: type a start and a
destination, get bus trips from Entur's open APIs, draw the chosen trip on a map. The task is in
`README.md`.

## Working with the user

- The user picks the language, framework and tools. If they haven't, ask before you scaffold.
- No backend, database or login unless they ask for one: the APIs can be called from the browser.
- Build in slices (search, then results, then map). Get each one working end to end, tell the
  user how to run it, then stop so they can try it.
- Once the stack is chosen, add a `## Commands` section here (run, test, lint).

## Entur API

- Every request sends `ET-Client-Name: <company>-<application>` (e.g. `knowit-workshop-ola`). No
  API key.
- Docs: fetch `https://developer.entur.no/llms.txt`; any docs page is Markdown with `.md` added.
- Geocoder: `GET https://api.entur.io/geocoder/v3/autocomplete?q=...`. Use v3 only: v1/v2 are
  deprecated and their parameters and response shape differ. Coordinates are `[lon, lat]`.
- Journey Planner: `POST https://api.entur.io/journey-planner/v3/graphql`, query `trip`. Don't
  guess field names: check the schema (introspection or
  `https://api.entur.io/graphql-explorer/journey-planner-v3`) and try the query with a real
  request first.
- If `modes.transportModes` is set, also set `accessMode: foot` and `egressMode: foot`, or trips
  from coordinates come back empty with no error.
- Leg geometry is `pointsOnLink.points`: Google encoded polyline, precision 5.
- The app must show "Data made available by Entur", plus the map tiles' attribution.
