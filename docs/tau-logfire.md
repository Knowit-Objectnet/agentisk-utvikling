# Observe Tau in Logfire

The devenv-installed `tau` includes an opt-in Logfire extension. It traces the
agent's own loop; Tau does not use Pydantic AI, so `instrument_pydantic_ai()` is
not involved. No upstream Tau source changes or provider monkey-patches are used.

## Enable

Reload your devenv/direnv environment after changing `devenv.nix`. This
demonstration branch enables both tracing and content capture in devenv by
default. The extension itself is opt-in outside this environment.

Since Tau is already instrumented, connect this directory to the existing
project without launching another coding agent:

```bash
devenv shell
logfire-cli --region eu --org psoland auth
logfire-cli --region eu --org psoland init use --name starter-project --permission send
tau
```

The devenv provides `logfire-cli` through a pinned `uvx` wrapper. The first run
downloads the CLI (requiring network access); later runs reuse uv's tool cache.
No global installation is needed.

Complete the browser login when prompted. `init use` creates a send-only write
token and saves it locally; skip it if this directory already has valid
credentials for that project. No token export or tracing flags are needed in
this branch's devenv.

Alternatively, you can run the full guided setup wizard:

```bash
logfire-cli --region=eu --org 'psoland' wizard --project 'starter-project' --task 'instrumentation'
```

The wizard guides a coding agent through setup; it is not required to install
this extension again. Its local SDK write credential in
`.logfire/logfire_credentials.json` is supported automatically when you run Tau
from that project directory. The `.logfire/` directory is gitignored. Use
`LOGFIRE_CREDENTIALS_DIR` if the credential directory is elsewhere; do not commit
it or use symlinked credential paths.

Alternatively, supply your project's **write token** through your existing secret
manager or environment. An exported token takes precedence over local wizard
credentials. Then run:

```bash
export LOGFIRE_TOKEN="<your project write token>" # omit when using wizard credentials
export TAU_LOGFIRE_ENABLED=1
export TAU_LOGFIRE_CAPTURE_CONTENT=1
tau
```

Do not commit the token or put it in `devenv.nix`. Do not reuse a production
project unless its access and retention rules are appropriate for source code.

In Logfire's Live view, filter by service `tau`. Expand a `Tau agent run`, its
turns, `chat <model>` spans, and `execute_tool <name>` spans. Model spans use
GenAI message attributes for Logfire's LLM panel and token badges.

**The content flag is necessary to see the system prompt, conversation, and tool
arguments/results.** This branch sets it in devenv; without it, only metadata
is exported. Disable tracing without changing your environment setup:

```bash
TAU_LOGFIRE_ENABLED=0 tau
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `TAU_LOGFIRE_ENABLED` | off | Enable tracing (`1`, `true`, `yes`, or `on`, case-insensitive) |
| `LOGFIRE_TOKEN` | unset | Project write token; takes precedence over local wizard credentials |
| `LOGFIRE_CREDENTIALS_DIR` | `.logfire` in Tau's working directory | SDK credential directory when no token is exported |
| `TAU_LOGFIRE_CAPTURE_CONTENT` | off | Opt into prompts, responses, exposed thinking, and tool payloads |
| `TAU_LOGFIRE_MAX_CONTENT_CHARS` | `16000` | Text/structure budget per content attribute (maximum `100000`) |
| `TAU_LOGFIRE_MAX_MESSAGES` | `100` | Most recent conversation messages captured per model request (maximum `1000`) |

The defaults above are the extension defaults. This demonstration branch sets
`TAU_LOGFIRE_ENABLED=1` and `TAU_LOGFIRE_CAPTURE_CONTENT=1` in `devenv.nix`.

The Python SDK automatically selects the EU or US endpoint from your write
token; `--region=eu` on the wizard chooses where to authenticate and select the
project. You do not need to set `LOGFIRE_BASE_URL` for an ordinary EU project.
Logfire's normal environment settings, such as `LOGFIRE_ENVIRONMENT` and
`LOGFIRE_SEND_TO_LOGFIRE`, remain available. `LOGFIRE_BASE_URL` can override the
endpoint for special deployments; avoid an override that conflicts with your
project's region.
Console logging and metric export are disabled to avoid interfering with Tau's
TUI, print output, and RPC protocol. When using an exported token, local Logfire
state is kept below `TAU_HOME`; when using wizard credentials, the SDK uses their
directory. Missing credentials disable tracing with a warning, never an
interactive login or automatic project creation inside Tau.

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
