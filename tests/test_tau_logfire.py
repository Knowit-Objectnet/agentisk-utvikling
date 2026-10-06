"""Offline contract tests against Tau 0.4.6 and Logfire's actual span processor."""

import asyncio
import json
import os
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import logfire
import logfire._internal.config as logfire_config
import pytest
import tau_logfire
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode
from tau_agent.events import (
    AgentEndEvent,
    AgentStartEvent,
    MessageEndEvent,
    MessageStartEvent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    TurnEndEvent,
    TurnStartEvent,
)
from tau_agent.harness import AgentHarness, AgentHarnessConfig
from tau_agent.messages import (
    AssistantMessage,
    ImageContent,
    TextContent,
    ThinkingContent,
    ToolCall,
    ToolResultMessage,
    Usage,
    UsageCost,
    UserMessage,
)
from tau_agent.provider_events import AssistantDoneEvent, AssistantStartEvent
from tau_agent.tools import AgentTool, AgentToolResult
from tau_coding.extensions import ExtensionRuntime
from tau_coding.paths import TauPaths
from tau_coding.resources import TauResourcePaths
from tau_logfire import CaptureOptions, ContentEncoder, TauObserver


@pytest.fixture
def exporter(tmp_path):
    exporter = InMemorySpanExporter()
    logfire.configure(
        send_to_logfire=False,
        console=False,
        metrics=False,
        inspect_arguments=False,
        scrubbing=logfire.ScrubbingOptions(),
        data_dir=tmp_path,
        additional_span_processors=[SimpleSpanProcessor(exporter)],
    )
    return exporter


@pytest.fixture
def context():
    return SimpleNamespace(
        session_id="test-session",
        model="test-model",
        provider_name="openai",
        system_prompt="You are a coding agent.",
        transcript=(UserMessage(content="Read hello.py"),),
    )


def observer(content=True, **kwargs):
    return TauObserver(trace.get_tracer("tau-logfire", "1"), CaptureOptions(content=content, **kwargs))


def event(kind, **kwargs):
    return SimpleNamespace(type=kind, **kwargs)


def start(obs, ctx):
    obs.handle(AgentStartEvent(), ctx)
    obs.handle(TurnStartEvent(), ctx)
    obs.handle(MessageStartEvent(message=AssistantMessage(model=ctx.model)), ctx)


def finish(obs, ctx, message=None):
    message = message or AssistantMessage(model=ctx.model, content="Done")
    obs.handle(MessageEndEvent(message=message), ctx)
    obs.handle(TurnEndEvent(message=message), ctx)
    obs.handle(AgentEndEvent(), ctx)
    obs.handle(event("agent_settled"), ctx)


def spans(exporter):
    return {span.name: span for span in exporter.get_finished_spans()}


def test_hierarchy_messages_usage_and_no_current_context(exporter, context):
    obs = observer()
    start(obs, context)
    obs.handle(MessageEndEvent(message=AssistantMessage(
        model=context.model,
        content=[ToolCall(id="call-1", name="read", arguments={"path": "hello.py"})],
        stop_reason="toolUse",
        usage=Usage(input=10, output=5, cache_read=3, cost=UsageCost(total=0.001)),
    )), context)
    obs.handle(ToolExecutionStartEvent(tool_call_id="call-1", tool_name="read", args={"path": "hello.py"}), context)
    obs.handle(ToolExecutionEndEvent(tool_call_id="call-1", tool_name="read", result=AgentToolResult(content="print('hello')"), is_error=False), context)
    obs.handle(event("turn_end"), context)
    obs.handle(event("agent_settled"), context)
    captured = spans(exporter)
    run = captured["Tau agent run"]
    turn = captured["Tau turn 1"]
    model = captured["chat test-model"]
    tool = captured["execute_tool read"]
    assert turn.parent.span_id == run.context.span_id
    assert model.parent.span_id == tool.parent.span_id == turn.context.span_id
    assert model.kind == SpanKind.CLIENT
    assert {s.context.trace_id for s in captured.values()} == {run.context.trace_id}
    assert not trace.get_current_span().get_span_context().is_valid
    assert json.loads(model.attributes["gen_ai.system_instructions"])[0]["content"] == context.system_prompt
    assert json.loads(model.attributes["gen_ai.input.messages"])[0]["parts"][0]["content"] == "Read hello.py"
    assert json.loads(model.attributes["gen_ai.output.messages"])[0]["parts"][0]["arguments"] == {"path": "hello.py"}
    assert model.attributes["gen_ai.usage.input_tokens"] == 13
    assert model.attributes["operation.cost"] == 0.001
    assert "gen_ai.usage.input_tokens" not in run.attributes
    assert json.loads(tool.attributes["gen_ai.tool.call.arguments"]) == {"path": "hello.py"}
    assert "print('hello')" in tool.attributes["gen_ai.tool.call.result"]


def test_metadata_only_never_reads_content(exporter, context):
    class MetadataContext:
        session_id = context.session_id
        model = context.model
        provider_name = context.provider_name

        @property
        def system_prompt(self):
            raise AssertionError("metadata mode read prompt")

        @property
        def transcript(self):
            raise AssertionError("metadata mode read history")

    obs = observer(content=False)
    ctx = MetadataContext()
    start(obs, ctx)
    finish(obs, ctx, AssistantMessage(model=ctx.model, content="private", error_message="private"))
    serialized = str([dict(s.attributes) for s in exporter.get_finished_spans()])
    assert "private" not in serialized
    assert "gen_ai.input.messages'" not in serialized
    assert not obs.warned


def test_content_redaction_and_structured_args(exporter, context):
    context.system_prompt = "password=very-secret-password"
    obs = observer()
    start(obs, context)
    obs.handle(ToolExecutionStartEvent(tool_call_id="s", tool_name="bash", args={"api_key": "never-export-this"}), context)
    obs.handle(ToolExecutionEndEvent(tool_call_id="s", tool_name="bash", result=AgentToolResult(content="ok"), is_error=False), context)
    finish(obs, context)
    serialized = str([dict(s.attributes) for s in exporter.get_finished_spans()])
    assert "never-export-this" not in serialized
    assert "very-secret-password" not in serialized


@pytest.mark.parametrize("secret", [
    'api_key="this-is-a-private-key"',
    "ACCESS_TOKEN='this-is-a-private-key'",
    "Authorization: Bearer this-is-a-private-key",
    "Authorization: Basic this-is-a-private-key",
    "Bearer this-is-a-private-key",
    "sk-proj-thisisaprivatetoken0000000000",
    "-----BEGIN RSA PRIVATE KEY-----\nthis-is-a-private-key\n-----END RSA PRIVATE KEY-----",
])
def test_common_secret_text_patterns_are_redacted(secret):
    result = ContentEncoder(1000).text(secret)
    assert "this-is-a-private-key" not in result
    assert "thisisaprivatetoken" not in result
    assert "[redacted" in result


def test_ordinary_json_data_is_preserved_but_images_and_signatures_are_omitted():
    result = ContentEncoder(1000).value({
        "data": {"message": "tool output"},
        "content": [{"type": "image", "mimeType": "image/png", "data": "BASE64_IMAGE"}],
        "textSignature": "PRIVATE_SIGNATURE",
    })
    assert result["data"]["message"] == "tool output"
    assert "BASE64_IMAGE" not in str(result)
    assert "PRIVATE_SIGNATURE" not in str(result)


def test_camel_case_credential_keys_are_redacted():
    result = ContentEncoder(1000).value({"apiKey": "secret-one", "credentials": "secret-two"})
    assert result == {"apiKey": "[redacted]", "credentials": "[redacted]"}


def test_thinking_images_and_tool_results(exporter, context):
    context.transcript = (
        UserMessage(content=[ImageContent(data="SECRET_BASE64_IMAGE", mime_type="image/png")]),
        ToolResultMessage(tool_call_id="x", tool_name="read", content="source code"),
    )
    obs = observer()
    start(obs, context)
    finish(obs, context, AssistantMessage(model=context.model, content=[
        ThinkingContent(thinking="visible thinking", thinking_signature="PRIVATE_SIGNATURE"),
        ThinkingContent(thinking="hidden thinking", redacted=True),
        TextContent(text="Done"),
    ]))
    attrs = spans(exporter)["chat test-model"].attributes
    serialized = str(dict(attrs))
    assert "SECRET_BASE64_IMAGE" not in serialized
    assert "PRIVATE_SIGNATURE" not in serialized
    assert "hidden thinking" not in serialized
    assert "visible thinking" in serialized
    inputs = json.loads(attrs["gen_ai.input.messages"])
    assert inputs[1]["role"] == "tool"
    assert inputs[1]["parts"][0]["type"] == "tool_call_response"
    assert "result" in inputs[1]["parts"][0]


def test_limits_keep_json_valid_and_mark_truncation(exporter, context):
    context.system_prompt = "x" * 1000
    context.transcript = tuple(UserMessage(content="y" * 1000) for _ in range(10))
    obs = observer(max_chars=40, max_messages=2)
    start(obs, context)
    finish(obs, context)
    attrs = spans(exporter)["chat test-model"].attributes
    assert attrs["tau.content.truncated"]
    assert attrs["tau.content.omitted_messages"] == 8
    assert len(json.loads(attrs["gen_ai.input.messages"])) == 2
    assert "[truncated]" in attrs["gen_ai.system_instructions"]


def test_deep_and_wide_tool_data_is_bounded():
    encoder = ContentEncoder(40)
    result = encoder.value({str(n): [""] * 1000 for n in range(1000)})
    assert encoder.truncated
    assert len(json.dumps(result)) < 1000


@pytest.mark.parametrize("block", [TextContent(text=""), ImageContent(data="", mime_type="image/png")])
def test_empty_and_image_message_blocks_are_bounded(block):
    encoder = ContentEncoder(40)
    result = encoder.message(UserMessage(content=[block] * 1000))
    assert encoder.truncated
    assert len(result["parts"]) <= 40
    assert len(json.dumps(result)) < 3000


@pytest.mark.parametrize("reason", ["error", "aborted"])
def test_model_errors_and_cancellation(exporter, context, reason):
    obs = observer()
    start(obs, context)
    finish(obs, context, AssistantMessage(model=context.model, stop_reason=reason, error_message="Request failed"))
    captured = spans(exporter)
    assert captured["chat test-model"].status.status_code == StatusCode.ERROR
    assert captured["Tau agent run"].status.status_code == StatusCode.ERROR


def test_settled_cleans_interrupted_tools(exporter, context):
    obs = observer()
    start(obs, context)
    obs.handle(ToolExecutionStartEvent(tool_call_id="x", tool_name="bash", args={}), context)
    obs.handle(event("agent_settled"), context)
    assert not obs.tools and obs.run is obs.turn is obs.model is None
    assert all(s.status.status_code == StatusCode.ERROR for s in exporter.get_finished_spans())


def test_inputs_survive_failure_before_first_model_chunk(exporter, context):
    obs = observer()
    obs.handle(AgentStartEvent(), context)
    obs.handle(TurnStartEvent(), context)
    obs.handle(event("agent_settled"), context)
    model = spans(exporter)["chat test-model"]
    assert model.status.status_code == StatusCode.ERROR
    assert "Read hello.py" in model.attributes["gen_ai.input.messages"]


def test_tool_error_is_not_a_model_error(exporter, context):
    obs = observer()
    start(obs, context)
    obs.handle(ToolExecutionStartEvent(tool_call_id="x", tool_name="bash", args={}), context)
    obs.handle(ToolExecutionEndEvent(tool_call_id="x", tool_name="bash", result=AgentToolResult(content="Failed"), is_error=True), context)
    finish(obs, context)
    assert spans(exporter)["execute_tool bash"].status.status_code == StatusCode.ERROR
    assert spans(exporter)["chat test-model"].status.status_code != StatusCode.ERROR


def test_retry_compaction_and_resume(exporter, context):
    obs = observer()
    start(obs, context)
    obs.handle(MessageEndEvent(message=AssistantMessage(model=context.model, stop_reason="error")), context)
    obs.handle(AgentEndEvent(), context)
    obs.handle(event("compaction_start"), context)
    obs.handle(event("compaction_end", aborted=False), context)
    obs.handle(event("auto_retry_start"), context)
    start(obs, context)
    obs.handle(event("auto_retry_end", success=True), context)
    finish(obs, context)
    assert len([s for s in exporter.get_finished_spans() if s.name == "Tau agent run"]) == 1
    assert len({s.context.trace_id for s in exporter.get_finished_spans()}) == 1
    # A resumed/new prompt gets a separate trace with the same session id.
    start(obs, context)
    finish(obs, context)
    assert len({s.context.trace_id for s in exporter.get_finished_spans()}) == 2


def test_reload_shutdown_closes_only_previous_generation(exporter, context):
    old, new = observer(), observer()
    start(old, context)
    old.shutdown(event("session_shutdown", reason="reload"), context)
    start(new, context)
    finish(new, context)
    runs = [s for s in exporter.get_finished_spans() if s.name == "Tau agent run"]
    assert len(runs) == 2
    assert old.run is None
    assert runs[0].status.status_code == StatusCode.ERROR
    assert runs[1].status.status_code != StatusCode.ERROR


def test_missing_usage_and_cost_are_not_reported_as_zero(exporter, context):
    obs = observer()
    start(obs, context)
    finish(obs, context)
    attrs = spans(exporter)["chat test-model"].attributes
    assert not any(key.startswith("gen_ai.usage.") for key in attrs)
    assert "operation.cost" not in attrs


def test_telemetry_failure_does_not_escape_and_warns_once(context, capsys):
    tracer = Mock()
    tracer.start_span.side_effect = RuntimeError("credentials should not be printed")
    obs = TauObserver(tracer, CaptureOptions())
    obs.handle(AgentStartEvent(), context)
    obs.handle(AgentStartEvent(), context)
    stderr = capsys.readouterr().err
    assert stderr.count("Tau will continue") == 1
    assert "credentials" not in stderr


def test_disabled_and_missing_credentials_never_configure(monkeypatch, tmp_path):
    api = Mock()
    api.context.cwd = tmp_path
    api.context.paths.home = tmp_path / "tau-home"
    configure = Mock()
    monkeypatch.setattr(logfire, "configure", configure)
    monkeypatch.delenv("TAU_LOGFIRE_ENABLED", raising=False)
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    monkeypatch.delenv("LOGFIRE_CREDENTIALS_DIR", raising=False)
    tau_logfire.setup(api)
    api.on.assert_not_called()
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    tau_logfire.setup(api)
    configure.assert_not_called()
    api.context.ui.notify.assert_called_once()


def test_setup_configures_once_across_reload_and_retains_scrubbing(monkeypatch, tmp_path):
    api = Mock()
    api.context.paths.home = tmp_path
    configure = Mock()
    monkeypatch.setattr(logfire, "configure", configure)
    monkeypatch.setattr(tau_logfire, "_configured", False)
    monkeypatch.setattr(tau_logfire.atexit, "register", Mock())
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.setenv("LOGFIRE_TOKEN", "not-a-real-token")
    tau_logfire.setup(api)
    tau_logfire.setup(api)
    configure.assert_called_once()
    assert configure.call_args.kwargs["console"] is False
    assert configure.call_args.kwargs["token"] == "not-a-real-token"
    assert configure.call_args.kwargs["data_dir"] == tmp_path / "logfire"
    assert isinstance(configure.call_args.kwargs["scrubbing"], logfire.ScrubbingOptions)
    assert api.on.call_count == 4  # two subscriptions per generation


@pytest.mark.parametrize("custom_directory", [False, True])
def test_setup_uses_wizard_credentials_without_exported_token(monkeypatch, tmp_path, custom_directory):
    api = Mock()
    api.context.cwd = tmp_path
    api.context.paths.home = tmp_path / "tau-home"
    credentials_dir = tmp_path / ("custom-logfire" if custom_directory else ".logfire")
    credentials_dir.mkdir()
    (credentials_dir / "logfire_credentials.json").write_text("{}")
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    monkeypatch.delenv("LOGFIRE_SEND_TO_LOGFIRE", raising=False)
    if custom_directory:
        monkeypatch.setenv("LOGFIRE_CREDENTIALS_DIR", str(credentials_dir))
    else:
        monkeypatch.delenv("LOGFIRE_CREDENTIALS_DIR", raising=False)
    monkeypatch.setattr(tau_logfire, "_configured", False)
    monkeypatch.setattr(tau_logfire.atexit, "register", Mock())
    configure = Mock()
    monkeypatch.setattr(logfire, "configure", configure)
    tau_logfire.setup(api)
    assert configure.call_args.kwargs["token"] is None
    assert configure.call_args.kwargs["data_dir"] == credentials_dir
    assert configure.call_args.kwargs["send_to_logfire"] == "if-token-present"
    assert api.on.call_count == 2
    api.context.ui.notify.assert_not_called()


@pytest.mark.parametrize("symlink_directory", [False, True])
def test_setup_rejects_symlinked_wizard_credentials(monkeypatch, tmp_path, symlink_directory):
    api = Mock()
    api.context.cwd = tmp_path
    api.context.paths.home = tmp_path / "tau-home"
    target = tmp_path / "actual-credentials"
    target.mkdir()
    (target / "logfire_credentials.json").write_text("{}")
    credentials_dir = tmp_path / ".logfire"
    if symlink_directory:
        credentials_dir.symlink_to(target, target_is_directory=True)
    else:
        credentials_dir.mkdir()
        (credentials_dir / "logfire_credentials.json").symlink_to(target / "logfire_credentials.json")
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    monkeypatch.delenv("LOGFIRE_CREDENTIALS_DIR", raising=False)
    configure = Mock()
    monkeypatch.setattr(logfire, "configure", configure)
    tau_logfire.setup(api)
    configure.assert_not_called()
    api.on.assert_not_called()
    assert "symlinks" in api.context.ui.notify.call_args.args[0]


def test_explicit_export_setting_is_left_to_sdk(monkeypatch, tmp_path):
    api = Mock()
    api.context.paths.home = tmp_path
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.setenv("LOGFIRE_TOKEN", "not-a-real-token")
    monkeypatch.setenv("LOGFIRE_SEND_TO_LOGFIRE", "false")
    monkeypatch.setattr(tau_logfire, "_configured", False)
    monkeypatch.setattr(tau_logfire.atexit, "register", Mock())
    configure = Mock()
    monkeypatch.setattr(logfire, "configure", configure)
    tau_logfire.setup(api)
    assert configure.call_args.kwargs["send_to_logfire"] is None


def test_real_sdk_loads_wizard_credentials_and_exports_to_eu_offline(monkeypatch, tmp_path, context):
    api = Mock()
    api.context.cwd = tmp_path
    api.context.paths.home = tmp_path / "tau-home"
    credentials_dir = tmp_path / ".logfire"
    credentials_dir.mkdir()
    (credentials_dir / "logfire_credentials.json").write_text(json.dumps({
        "token": "not-a-real-token",
        "project_name": "test-project",
        "project_url": "https://logfire-eu.pydantic.dev/test-org/test-project",
        "logfire_api_url": "https://logfire-eu.pydantic.dev",
    }))
    exporter = InMemorySpanExporter()
    create_exporter = Mock(return_value=exporter)
    # Replace only the network boundaries; retain real SDK credential loading,
    # region selection, span processing, and batched export.
    monkeypatch.setattr(logfire_config, "BodySizeCheckingOTLPSpanExporter", create_exporter)
    monkeypatch.setattr(logfire_config.LogfireConfig, "_initialize_credentials_from_token", Mock(return_value=None))
    monkeypatch.setattr(tau_logfire, "_configured", False)
    monkeypatch.setattr(tau_logfire.atexit, "register", Mock())
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    for name in ("LOGFIRE_TOKEN", "LOGFIRE_CREDENTIALS_DIR", "LOGFIRE_SEND_TO_LOGFIRE", "LOGFIRE_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    try:
        tau_logfire.setup(api)
        api.context.ui.notify.assert_not_called()
        assert create_exporter.call_args.kwargs["endpoint"] == "https://logfire-eu.pydantic.dev/v1/traces"
        assert create_exporter.call_args.kwargs["headers"]["Authorization"] == "not-a-real-token"
        obs = api.on.call_args_list[0].args[1].__self__
        start(obs, context)
        finish(obs, context)
        assert logfire.force_flush(timeout_millis=2000)
        assert "chat test-model" in spans(exporter)
    finally:
        logfire.configure(send_to_logfire=False, console=False, metrics=False, data_dir=tmp_path)


def test_invalid_config_is_nonfatal(monkeypatch):
    api = Mock()
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.setenv("LOGFIRE_TOKEN", "not-a-real-token")
    monkeypatch.setenv("TAU_LOGFIRE_MAX_MESSAGES", "not-an-integer")
    tau_logfire.setup(api)
    api.on.assert_not_called()
    api.context.ui.notify.assert_called_once()


def test_sdk_configuration_failure_is_nonfatal(monkeypatch, tmp_path):
    api = Mock()
    api.context.paths.home = tmp_path
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.setenv("LOGFIRE_TOKEN", "not-a-real-token")
    monkeypatch.setattr(tau_logfire, "_configured", False)
    monkeypatch.setattr(logfire, "configure", Mock(side_effect=RuntimeError("offline")))
    tau_logfire.setup(api)
    api.on.assert_not_called()
    api.context.ui.notify.assert_called_once()
    assert not tau_logfire._configured


def test_flush_failure_is_nonfatal(monkeypatch):
    monkeypatch.setattr(logfire, "force_flush", Mock(side_effect=RuntimeError("offline")))
    tau_logfire.flush()
    logfire.force_flush.assert_called_once_with(timeout_millis=2000)


def test_real_tau_loop_multiple_turns_and_current_context(exporter):
    """A real Tau loop verifies event order and prompt/tool-history visibility."""
    seen = []

    class Provider:
        async def stream_response(self, **kwargs):
            seen.append(kwargs["messages"])
            message = AssistantMessage(model="test-model", content=(
                [ToolCall(id="call-1", name="read", arguments={"path": "hello.py"})]
                if len(seen) == 1 else [TextContent(text="Done")]
            ), stop_reason="toolUse" if len(seen) == 1 else "stop")
            yield AssistantStartEvent(partial=AssistantMessage(model="test-model"))
            yield AssistantDoneEvent(message=message, reason=message.stop_reason)

    async def execute(*args):
        return AgentToolResult(content="print('hello')")

    tool = AgentTool(name="read", label="Read", description="Read a file", parameters={"type": "object"}, execute_fn=execute)
    harness = AgentHarness(AgentHarnessConfig(provider=Provider(), model="test-model", system="Coding agent", tools=[tool]))
    obs = observer()

    async def on_event(evt):
        ctx = SimpleNamespace(session_id="loop-test", model="test-model", provider_name="openai", system_prompt=harness.config.system, transcript=harness.messages)
        obs.handle(evt, ctx)
        assert not trace.get_current_span().get_span_context().is_valid

    harness.subscribe(on_event)

    async def run():
        async for _ in harness.prompt("Read hello.py"):
            pass
        obs.handle(event("agent_settled"), None)

    asyncio.run(run())
    models = [s for s in exporter.get_finished_spans() if s.name == "chat test-model"]
    assert len(models) == 2
    assert len(seen) == 2
    first_input = json.loads(models[0].attributes["gen_ai.input.messages"])
    second_input = json.loads(models[1].attributes["gen_ai.input.messages"])
    assert first_input[0]["parts"][0]["content"] == "Read hello.py"
    assert second_input[-1]["role"] == "tool"
    assert len([s for s in exporter.get_finished_spans() if s.name == "Tau agent run"]) == 1
    assert not obs.warned


def test_real_extension_loading_and_reload(context, monkeypatch, tmp_path):
    exporter = InMemorySpanExporter()
    original_configure = logfire.configure

    def configure_offline(**kwargs):
        kwargs["send_to_logfire"] = False
        return original_configure(
            additional_span_processors=[SimpleSpanProcessor(exporter)],
            **kwargs,
        )

    configure = Mock(side_effect=configure_offline)
    monkeypatch.setattr(logfire, "configure", configure)
    monkeypatch.setattr(tau_logfire.atexit, "register", Mock())
    entry = tmp_path / "extension.py"
    entry.write_text("from tau_logfire import setup\n")
    paths = TauPaths(home=tmp_path)
    runtime = ExtensionRuntime(paths=paths, built_in_extensions=())
    resources = TauResourcePaths(root=tmp_path, paths=paths, agents_root=None)
    monkeypatch.setenv("TAU_LOGFIRE_ENABLED", "1")
    monkeypatch.setenv("TAU_LOGFIRE_CAPTURE_CONTENT", "1")
    monkeypatch.setenv("LOGFIRE_TOKEN", "not-a-real-token")
    monkeypatch.setattr(tau_logfire, "_configured", False)
    context.messages = context.transcript

    async def run():
        for reason in ("reload", "quit"):
            runtime.load(resources, extra_paths=(entry,), include_resource_dirs=False)
            runtime.bind(context)
            await runtime.emit_session_start("startup")
            await runtime.emit_event(AgentStartEvent())
            await runtime.emit_event(TurnStartEvent())
            await runtime.emit_event(MessageStartEvent(message=AssistantMessage(model=context.model)))
            await runtime.emit_event(MessageEndEvent(message=AssistantMessage(model=context.model, content="Done")))
            await runtime.emit_event(event("agent_settled"))
            await runtime.emit_session_shutdown(reason)
            runtime.reset_for_reload()
        await runtime.aclose()

    asyncio.run(run())
    runs = [s for s in exporter.get_finished_spans() if s.name == "Tau agent run"]
    assert len(runs) == 2
    assert len([s for s in exporter.get_finished_spans() if s.name == "chat test-model"]) == 2
    assert all(s.resource.attributes["service.name"] == "tau" for s in exporter.get_finished_spans())
    configure.assert_called_once()


def test_exporter_failure_does_not_interrupt_agent(context, tmp_path):
    class UnavailableExporter(SpanExporter):
        def export(self, spans):
            raise RuntimeError("Logfire unavailable")

    exporter = InMemorySpanExporter()
    logfire.configure(
        send_to_logfire=False,
        console=False,
        metrics=False,
        data_dir=tmp_path,
        additional_span_processors=[
            SimpleSpanProcessor(UnavailableExporter()),
            SimpleSpanProcessor(exporter),
        ],
    )
    obs = observer()
    start(obs, context)
    finish(obs, context)
    assert len(exporter.get_finished_spans()) == 3
    assert not obs.disabled


@pytest.mark.parametrize("args", [["--version"], ["--help"], ["sessions"], ["providers"]])
@pytest.mark.parametrize("enabled_flag", ["0", "1"])
def test_packaged_cli_preserves_management_commands(args, enabled_flag, tmp_path):
    cli = os.environ.get("TAU_LOGFIRE_CLI")
    if cli is None:
        pytest.skip("CLI packaging tests run through devenv's test-tau-logfire script")
    result = subprocess.run(
        [cli, *args],
        env={**os.environ, "TAU_HOME": str(tmp_path), "TAU_LOGFIRE_ENABLED": enabled_flag, "LOGFIRE_TOKEN": ""},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "[tau-logfire]" not in result.stdout
