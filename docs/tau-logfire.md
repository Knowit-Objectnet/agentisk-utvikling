# Observe Tau in Logfire

The devenv-installed `tau` includes an opt-in Logfire extension. It traces the
agent's own loop; Tau does not use Pydantic AI, so `instrument_pydantic_ai()` is
not involved. No upstream Tau source changes or provider monkey-patches are used.

## Enable

Reload your devenv/direnv environment after changing `devenv.nix`. Create a
Logfire project and supply its **write token** through your existing secret
manager or environment, then run:

```bash
export LOGFIRE_TOKEN="<your project write token>"
export TAU_LOGFIRE_ENABLED=1
export TAU_LOGFIRE_CAPTURE_CONTENT=1
tau
```

Do not commit the token or put it in `devenv.nix`. Do not reuse a production
project unless its access and retention rules are appropriate for source code.

In Logfire's Live view, filter by service `tau`. Expand a `Tau agent run`, its
turns, `chat <model>` spans, and `execute_tool <name>` spans. Model spans use
GenAI message attributes for Logfire's LLM panel and token badges.

Tracing is disabled by default. **The content flag is necessary to see the
system prompt, conversation, and tool arguments/results.** Without it, only
metadata is exported. Disable tracing without changing your environment setup:

```bash
TAU_LOGFIRE_ENABLED=0 tau
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `TAU_LOGFIRE_ENABLED` | off | Enable tracing (`1`, `true`, `yes`, or `on`, case-insensitive) |
| `LOGFIRE_TOKEN` | unset | Logfire project write token; missing token disables tracing with a warning |
| `TAU_LOGFIRE_CAPTURE_CONTENT` | off | Opt into prompts, responses, exposed thinking, and tool payloads |
| `TAU_LOGFIRE_MAX_CONTENT_CHARS` | `16000` | Text/structure budget per content attribute (maximum `100000`) |
| `TAU_LOGFIRE_MAX_MESSAGES` | `100` | Most recent conversation messages captured per model request (maximum `1000`) |

Logfire's normal environment settings, such as `LOGFIRE_ENVIRONMENT` and
`LOGFIRE_BASE_URL` (if your project is in another region), remain available.
Console logging and metric export are disabled to avoid interfering with Tau's
TUI, print output, and RPC protocol. Local Logfire state is kept below the
existing `TAU_HOME`, not in the user-wide profile.

The launcher supplies a packaged extension using `--extension`; user-supplied
extensions and CLI arguments still work. Tau intentionally loads explicit
extensions even with `--no-extensions`. Use `TAU_LOGFIRE_ENABLED=0` to disable
this one. Management commands such as `tau sessions`, `tau providers`, and
`tau --version` retain their normal behaviour.

## Captured data

- One trace per user-triggered agent run, including observable overflow retries,
  correlated by `tau.session.id`.
- Turn/model spans, system instructions, conversation messages, final assembled
  responses, tool-call IDs, and provider-exposed thinking text.
- Tool name, requested arguments, returned content/details, duration, and errors.
- Available token/cache/reasoning usage, response ID/model, and Tau response timing.
- Observable compaction and automatic retry spans.

Tokens are recorded only on model spans to avoid double-counting. Cached input
is included in the input-token total and also reported separately. Tau defaults
missing usage/cost to zero, so the extension omits zero values rather than
claiming unknown usage is free. Positive Tau-reported cost is recorded;
Logfire may otherwise estimate cost for supported models. Such estimates are
not necessarily your actual bill, particularly with subscription authentication.

### Privacy and limits

Content capture sends source code and command output to Logfire. Treat the
project as sensitive. Logfire's default scrubbing stays enabled, but **Logfire
exempts GenAI message fields from its normal scrubber**. The extension therefore
adds best-effort redaction for common secret assignments, structured credential
keys, authorization values, common API-token formats, and PEM private keys.
This cannot detect every secret. Leave content capture off for sensitive work.

Images retain only their MIME type; base64 image data and opaque signatures are
omitted. Large content is truncated with `[truncated]` and
`tau.content.truncated=true`; older omitted messages are counted separately.
Budgets bound text and structure, not the exact byte size of JSON after escaping.
Already truncated Tau tool output cannot be recovered by this integration.

## Known boundaries

- Model inputs are Tau's active conversation transcript, labelled
  `tau.context.source=agent_transcript_not_wire_payload`. Provider-specific
  history repair, payload conversion, and tool definitions are not captured as
  exact outgoing HTTP payloads.
- Model spans begin at turn boundaries. Use `tau.response.duration_ms` and
  `tau.response.time_to_first_output_ms` for Tau's measured response timing;
  span duration may also include session naming and other turn preparation.
- Internal HTTP retry attempts, separate session-name/compaction model requests,
  streaming deltas, and model reasoning not exposed by the provider are not
  recorded as individual model spans.
- Export is asynchronous and best-effort. Unavailable Logfire must not prevent
  agent execution. Normal process exit requests a two-second flush, although
  SDK retries/shutdown may take longer. Abrupt termination can lose buffered data.

## Test

```bash
devenv shell test-tau-logfire
```

This builds the actual packaged runtime and runs offline tests with an in-memory
Logfire exporter, including Tau's real agent loop, extension loading/reload, CLI
management commands, redaction, cancellation, errors, and missing credentials.
It does not need a Logfire token or a model API key and sends no telemetry.

For a live smoke test, enable both flags and ask Tau to read a harmless fixture
file and explain it. Verify the prompt, model messages, read-tool arguments and
result, parent/child spans, and token badge in your dedicated Logfire project.
