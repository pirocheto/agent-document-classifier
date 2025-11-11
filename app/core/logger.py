import datetime
import json
import logging
from contextvars import ContextVar
from functools import lru_cache

from opentelemetry.trace import get_current_span
from opentelemetry.trace.span import format_span_id, format_trace_id

from app.core.config import get_settings

settings = get_settings()


context: ContextVar[dict[str, str | None]] = ContextVar("context", default={})  # noqa: B039


class _Logger(logging.Logger):
    """Wrapper around logging.Logger to add extra context support."""

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        record.__dict__["extra"] = extra or {}
        return record


logging.setLoggerClass(_Logger)


def time_to_iso_str(seconds: float) -> str:
    """Get an ISO 8601 string from time in microseconds."""
    ts = datetime.datetime.fromtimestamp(seconds, tz=datetime.UTC)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ctx = context.get()

        span = get_current_span()
        span_ctx = span.get_span_context() if span else None

        log_record = {
            "body": record.getMessage(),
            "severity_number": record.levelno,
            "severity_text": record.levelname,
            "attributes": getattr(record, "extra", {}),
            "timestamp": time_to_iso_str(record.created),
            "trace_id": f"0x{format_trace_id(span_ctx.trace_id)}" if span_ctx else None,
            "span_id": f"0x{format_span_id(span_ctx.span_id)}" if span_ctx else None,
            "request_id": ctx.get("request_id"),
            "user_id": ctx.get("user_id"),
            "resource": {
                "service.name": settings.service_name,
                "service.environment": settings.environment,
            },
        }

        return json.dumps(log_record)


@lru_cache
def setup_logger(name: str = "app") -> logging.Logger:
    """Return a logger configured with OTLP, context filter, and avoid duplicate handlers."""

    logger = logging.getLogger(name)

    formatter = JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(settings.log_level)

    # Allow OpenTelemetry auto-instrumentation to propagate logs
    logger.propagate = True

    return logger
