"""Opt-in Logfire extension for Tau 0.4.6 (no provider monkey-patching)."""

from __future__ import annotations

import atexit
import json
import os
import re
import sys
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any
from weakref import WeakSet

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer
from tau_agent.messages import AssistantMessage
from tau_coding.extensions import ExtensionAPI

_configured = False
_observers: WeakSet[TauObserver] = WeakSet()
_TRUE = {"1", "true", "yes", "on"}
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:[\w-]*(?:password|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|credential)[\w-]*|token)\b"
    r"[\"']?\s*[:=]\s*)(?:\"[^\"\n]*\"|'[^'\n]*'|[^\s,;\}\]]+)"
)
_AUTH_TOKEN = re.compile(r"(?i)\b(?:Bearer|Basic)\s+[a-z0-9._~+/=-]{8,}")
_API_TOKEN = re.compile(
    r"\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,})\b"
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL
)
_JSON_ATTRIBUTES = {
    "gen_ai.system_instructions": {"type": "array"},
    "gen_ai.input.messages": {"type": "array"},
    "gen_ai.output.messages": {"type": "array"},
    "gen_ai.tool.call.arguments": {"type": "object"},
    "gen_ai.tool.call.result": {},
}


def enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUE


@dataclass(frozen=True)
class CaptureOptions:
    content: bool = False
    max_chars: int = 16_000
    max_messages: int = 100

    @classmethod
    def from_environment(cls) -> CaptureOptions:
        def limit(name: str, default: int, maximum: int) -> int:
            return min(maximum, max(1, int(os.environ.get(name, str(default)))))

        return cls(
            content=enabled(os.environ.get("TAU_LOGFIRE_CAPTURE_CONTENT")),
            max_chars=limit("TAU_LOGFIRE_MAX_CONTENT_CHARS", 16_000, 100_000),
            max_messages=limit("TAU_LOGFIRE_MAX_MESSAGES", 100, 1_000),
        )


class ContentEncoder:
    """Bound each JSON attribute without exporting binary data or signatures."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.remaining = limit
        self.truncated = False

    def text(self, value: str) -> str:
        # Logfire intentionally does not scrub GenAI message fields.
        # This is best effort, not a guarantee that arbitrary source code is safe.
        value = _PRIVATE_KEY.sub("[redacted private key]", value)
        value = _AUTH_TOKEN.sub("[redacted authorization]", value)
        value = _SECRET_ASSIGNMENT.sub(r"\1[redacted]", value)
        value = _API_TOKEN.sub("[redacted API token]", value)
        size = min(len(value), self.remaining)
        self.remaining -= size
        if size < len(value):
            self.truncated = True
            return value[:size] + " [truncated]"
        return value

    def value(self, value: Any, depth: int = 0) -> Any:
        if depth > 12 or self.remaining <= 0:
            self.truncated = True
            return "[truncated]"
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if self.remaining <= 0:
                    self.truncated = True
                    break
                name = self.text(str(key))
                self.remaining -= 1
                # Secrets in structured payloads are removed before SDK scrubbing.
                normalized = str(key).lower().replace("-", "_")
                compact = normalized.replace("_", "")
                if any(
                    word in compact
                    for word in (
                        "password",
                        "secret",
                        "token",
                        "apikey",
                        "authorization",
                        "credential",
                    )
                ):
                    result[name] = "[redacted]"
                elif (
                    normalized == "data" and value.get("type") == "image"
                ) or normalized.replace("_", "") in {
                    "imagedata",
                    "textsignature",
                    "thinkingsignature",
                    "thoughtsignature",
                }:
                    result[name] = "[omitted]"
                else:
                    result[name] = self.value(item, depth + 1)
            return result
        if isinstance(value, (list, tuple)):
            result = []
            for item in value:
                if self.remaining <= 0:
                    self.truncated = True
                    break
                self.remaining -= 1
                result.append(self.value(item, depth + 1))
            return result
        self.remaining -= 1
        return (
            value
            if value is None or isinstance(value, (int, float, bool))
            else self.text(str(value))
        )

    def message(self, message: Any) -> dict[str, Any]:
        role = getattr(message, "role", "user")
        content = getattr(message, "content", "")
        parts = []
        if isinstance(content, str):
            parts.append({"type": "text", "content": self.text(content)})
        else:
            for block in content:
                if self.remaining <= 0:
                    self.truncated = True
                    break
                kind = getattr(block, "type", "")
                if kind == "text":
                    parts.append({"type": "text", "content": self.text(block.text)})
                elif kind == "thinking":
                    parts.append(
                        {
                            "type": "thinking",
                            "content": "[redacted]"
                            if block.redacted
                            else self.text(block.thinking),
                        }
                    )
                elif kind == "toolCall":
                    parts.append(
                        {
                            "type": "tool_call",
                            "id": block.id,
                            "name": block.name,
                            "arguments": self.value(block.arguments),
                        }
                    )
                elif kind == "image":
                    parts.append({"type": "blob", "mime_type": block.mime_type})
        if role == "toolResult":
            parts = [
                {
                    "type": "tool_call_response",
                    "id": message.tool_call_id,
                    "name": message.tool_name,
                    "result": parts,
                }
            ]
            role = "tool"
        elif role == "bashExecution":
            role = "user"
            parts = [
                {
                    "type": "text",
                    "content": self.text(f"$ {message.command}\n{message.output}"),
                }
            ]
        elif role == "custom":
            role = "user"
        result = {"role": role, "parts": parts}
        if isinstance(message, AssistantMessage):
            result["finish_reason"] = message.stop_reason
        return result


class TauObserver:
    """Keep spans independent of the task-local current OpenTelemetry context."""

    def __init__(self, tracer: Tracer, options: CaptureOptions) -> None:
        self.tracer = tracer
        self.options = options
        self.run: Span | None = None
        self.turn: Span | None = None
        self.model: Span | None = None
        self.tools: dict[str, Span] = {}
        self.operations: dict[str, Span] = {}
        self.turn_index = 0
        self.warned = False
        self.disabled = False

    def start(
        self,
        name: str,
        parent: Span | None,
        attributes: dict[str, Any] | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ) -> Span:
        # Never keep attach/detach tokens across event callbacks, reloads or tasks.
        context = (
            trace.set_span_in_context(parent, Context())
            if parent is not None
            else Context()
        )
        return self.tracer.start_span(
            name,
            context=context,
            kind=kind,
            attributes={
                "logfire.msg": name,
                "logfire.span_type": "span",
                "logfire.json_schema": json.dumps(
                    {"type": "object", "properties": _JSON_ATTRIBUTES}
                ),
                **(attributes or {}),
            },
        )

    def capture(
        self, span: Span, key: str, build: Callable[[ContentEncoder], Any]
    ) -> None:
        if not self.options.content:
            return
        encoder = ContentEncoder(self.options.max_chars)
        value = build(encoder)
        span.set_attribute(key, json.dumps(value, ensure_ascii=False))
        if encoder.truncated:
            span.set_attribute("tau.content.truncated", True)

    def inputs(self, span: Span, context: Any) -> None:
        if not self.options.content:
            return  # Do not even read prompt/history in metadata-only mode.
        self.capture(
            span,
            "gen_ai.system_instructions",
            lambda e: [{"type": "text", "content": e.text(context.system_prompt)}],
        )
        messages = context.transcript
        if len(messages) > self.options.max_messages:
            span.set_attribute("tau.content.truncated", True)
            span.set_attribute(
                "tau.content.omitted_messages",
                len(messages) - self.options.max_messages,
            )
        self.capture(
            span,
            "gen_ai.input.messages",
            lambda e: [e.message(m) for m in messages[-self.options.max_messages :]],
        )
        span.set_attribute("tau.context.source", "agent_transcript_not_wire_payload")

    def error(self, span: Span | None, code: str, detail: str | None = None) -> None:
        if span is None:
            return
        span.set_status(Status(StatusCode.ERROR))
        span.set_attribute("error.type", code)
        span.set_attribute("logfire.level_num", 17)
        if detail and self.options.content:
            span.set_attribute(
                "tau.error.message", ContentEncoder(self.options.max_chars).text(detail)
            )

    def response(self, message: AssistantMessage) -> None:
        if self.model is None:
            return
        span = self.model
        span.set_attribute(
            "gen_ai.response.model", message.response_model or message.model
        )
        if message.provider != "unknown":
            span.set_attribute("tau.response.provider", message.provider)
            span.set_attribute(
                "gen_ai.system",
                "openai" if message.provider == "openai-codex" else message.provider,
            )
        span.set_attribute("gen_ai.response.finish_reasons", [message.stop_reason])
        if message.response_id:
            span.set_attribute("gen_ai.response.id", message.response_id)
        usage = message.usage
        # Tau input excludes cached tokens; GenAI input_tokens includes them.
        input_tokens = usage.input + usage.cache_read + usage.cache_write
        if input_tokens:
            span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        # Tau defaults missing usage/cost to zero; do not claim unknown usage is free.
        for field, key in {
            "output": "gen_ai.usage.output_tokens",
            "cache_read": "gen_ai.usage.cache_read.input_tokens",
            "cache_write": "gen_ai.usage.cache_creation.input_tokens",
            "reasoning": "gen_ai.usage.reasoning.output_tokens",
        }.items():
            value = getattr(usage, field, None)
            if value:
                span.set_attribute(key, value)
        if usage.cost.total > 0:
            span.set_attribute("operation.cost", usage.cost.total)
        if message.timing:
            span.set_attribute(
                "tau.response.duration_ms", message.timing.total_duration_ms
            )
            if message.timing.time_to_first_output_ms is not None:
                span.set_attribute(
                    "tau.response.time_to_first_output_ms",
                    message.timing.time_to_first_output_ms,
                )
        self.capture(span, "gen_ai.output.messages", lambda e: [e.message(message)])
        if message.stop_reason in {"error", "aborted"}:
            self.error(span, message.stop_reason, message.error_message)
            self.error(self.run, message.stop_reason)
        span.end()
        self.model = None

    def close_turn(self, interrupted: bool = False) -> None:
        for span in [self.model, *self.tools.values(), self.turn]:
            if span is not None:
                if interrupted:
                    self.error(span, "interrupted")
                span.end()
        self.model = self.turn = None
        self.tools.clear()

    def close(self, interrupted: bool = False) -> None:
        remaining = [
            self.model,
            *self.tools.values(),
            self.turn,
            *self.operations.values(),
            self.run,
        ]
        self.run = self.turn = self.model = None
        self.tools.clear()
        self.operations.clear()
        for span in remaining:
            if span is not None:
                with suppress(Exception):
                    if interrupted:
                        self.error(span, "interrupted")
                    span.end()

    def handle(self, event: Any, context: Any) -> None:
        """Fail closed on instrumentation errors, without touching Tau's agent state."""
        if self.disabled:
            return
        try:
            self.dispatch(event, context)
        except Exception:  # noqa: BLE001 - telemetry must not break the agent
            self.disabled = True
            self.close(interrupted=True)
            if not self.warned:
                print(
                    "[tau-logfire] Could not record telemetry; Tau will continue.",
                    file=sys.stderr,
                )
                self.warned = True

    def dispatch(self, event: Any, context: Any) -> None:
        kind = event.type
        if kind == "agent_start":
            # Overflow retry starts another core run before agent_settled.
            if self.run is None:
                self.run = self.start(
                    "Tau agent run",
                    None,
                    {
                        "tau.session.id": context.session_id or "unindexed",
                        "gen_ai.conversation.id": context.session_id or "unindexed",
                        "gen_ai.operation.name": "invoke_agent",
                        "gen_ai.agent.name": "tau",
                        "gen_ai.request.model": context.model,
                        "gen_ai.system": context.provider_name,
                        "tau.provider.name": context.provider_name,
                        "tau.capture_content": self.options.content,
                    },
                )
            self.turn_index = 0
        elif kind == "turn_start":
            self.close_turn(interrupted=True)
            self.turn_index = getattr(event, "turn_index", self.turn_index)
            self.turn = self.start(
                f"Tau turn {self.turn_index + 1}",
                self.run,
                {"tau.turn.index": self.turn_index},
            )
            self.model = self.start(
                f"chat {context.model}",
                self.turn,
                {
                    "gen_ai.operation.name": "chat",
                    "gen_ai.system": context.provider_name,
                    "gen_ai.request.model": context.model,
                    "tau.timing.source": "turn_boundary",
                },
                kind=SpanKind.CLIENT,
            )
            # Preserve inputs even if the provider fails before its first event.
            # message_start refreshes this after any queued steering is applied.
            self.inputs(self.model, context)
        elif kind == "message_start" and isinstance(event.message, AssistantMessage):
            if self.model is not None:
                # Steering and the current prompt have entered history by this point.
                self.inputs(self.model, context)
        elif kind == "message_end" and isinstance(event.message, AssistantMessage):
            self.response(event.message)
        elif kind == "tool_execution_start":
            previous = self.tools.pop(event.tool_call_id, None)
            if previous is not None:
                self.error(previous, "interrupted")
                previous.end()
            span = self.start(
                f"execute_tool {event.tool_name}",
                self.turn or self.run,
                {
                    "gen_ai.operation.name": "execute_tool",
                    "gen_ai.tool.name": event.tool_name,
                    "gen_ai.tool.call.id": event.tool_call_id,
                },
            )
            self.tools[event.tool_call_id] = span
            self.capture(
                span, "gen_ai.tool.call.arguments", lambda e: e.value(event.args)
            )
        elif kind == "tool_execution_end":
            span = self.tools.get(event.tool_call_id)
            if span is not None:
                self.capture(
                    span,
                    "gen_ai.tool.call.result",
                    lambda e: e.value(event.result.model_dump(mode="json")),
                )
                span.set_attribute("tau.tool.is_error", event.is_error)
                if event.is_error:
                    self.error(span, "tool_error")
                span.end()
                self.tools.pop(event.tool_call_id, None)
        elif kind == "turn_end":
            self.close_turn(interrupted=self.model is not None or bool(self.tools))
            self.turn_index += 1
        elif kind == "agent_end":
            self.close_turn(interrupted=self.model is not None or bool(self.tools))
        elif kind in {"compaction_start", "auto_retry_start"}:
            name = kind.removesuffix("_start")
            previous = self.operations.pop(name, None)
            if previous is not None:
                self.error(previous, "interrupted")
                previous.end()
            self.operations[name] = self.start(f"Tau {name}", self.run)
            self.operation_metadata(self.operations[name], event)
        elif kind in {"compaction_end", "auto_retry_end"}:
            span = self.operations.pop(kind.removesuffix("_end"), None)
            if span is not None:
                self.operation_metadata(span, event)
                if getattr(event, "aborted", False) or not getattr(
                    event, "success", True
                ):
                    self.error(span, "operation_failed")
                span.end()
        elif kind == "agent_settled":
            self.close(
                interrupted=self.model is not None
                or bool(self.tools)
                or bool(self.operations)
            )

    def operation_metadata(self, span: Span, event: Any) -> None:
        for field in (
            "reason",
            "attempt",
            "max_attempts",
            "delay_ms",
            "success",
            "aborted",
            "will_retry",
        ):
            value = getattr(event, field, None)
            if isinstance(value, (str, int, bool)):
                span.set_attribute(f"tau.{field}", value)

    def shutdown(self, event: Any, context: Any) -> None:
        self.close(interrupted=True)


def flush() -> None:
    """Request a short best-effort exit flush (never per token/tool call)."""
    for observer in list(_observers):
        try:
            observer.close(interrupted=True)
        except Exception:  # noqa: BLE001, S110 - process-exit cleanup
            pass
    try:
        import logfire

        logfire.force_flush(timeout_millis=2_000)
    except Exception:  # noqa: BLE001, S110 - process-exit cleanup
        pass


def setup(tau: ExtensionAPI) -> None:
    global _configured
    if not enabled(os.environ.get("TAU_LOGFIRE_ENABLED")):
        return
    if not os.environ.get("LOGFIRE_TOKEN", "").strip():
        tau.context.ui.notify(
            "Logfire disabled: LOGFIRE_TOKEN is not set.", level="warning"
        )
        return
    try:
        options = CaptureOptions.from_environment()
        if not _configured:
            import logfire

            logfire.configure(
                token=os.environ["LOGFIRE_TOKEN"],
                service_name="tau",
                service_version="0.4.6",
                console=False,
                metrics=False,
                inspect_arguments=False,
                add_baggage_to_attributes=False,
                scrubbing=logfire.ScrubbingOptions(),
                data_dir=tau.context.paths.home / "logfire",
            )
            _configured = True
            atexit.register(flush)
        observer = TauObserver(trace.get_tracer("tau-logfire", "1"), options)
        _observers.add(observer)
        tau.on("agent_event", observer.handle)
        tau.on("session_shutdown", observer.shutdown)
    except Exception:  # noqa: BLE001 - configuration must not break the agent
        tau.context.ui.notify(
            "Logfire disabled: telemetry configuration failed.", level="warning"
        )
