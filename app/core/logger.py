import datetime
import json
import logging
import traceback
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

        ctx = context.get()
        span = get_current_span()
        span_ctx = span.get_span_context() if span else None

        data = {
            "trace_id": f"{format_trace_id(span_ctx.trace_id)}" if span_ctx else None,
            "span_id": f"{format_span_id(span_ctx.span_id)}" if span_ctx else None,
            "request_id": ctx.get("request_id"),
            "user_id": ctx.get("user_id"),
        }
        record.__dict__.update(data)
        return record


logging.setLoggerClass(_Logger)


def time_to_iso_str(seconds: float) -> str:
    """Get an ISO 8601 string from time in microseconds."""
    ts = datetime.datetime.fromtimestamp(seconds, tz=datetime.UTC)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class JSONFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style="%", validate=True, *, defaults=None):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
        empty_record = logging.LogRecord(
            name="",
            level=logging.NOTSET,
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None,
        )
        self.default_attributes = set(empty_record.__dict__.keys())

    def format(self, record: logging.LogRecord) -> str:
        attributes = {k: v for k, v in record.__dict__.items() if k not in self.default_attributes}

        log_record = {
            "body": record.getMessage(),
            "timestamp": time_to_iso_str(record.created),
            "severity_number": record.levelno,
            "severity_text": record.levelname,
            "attributes": attributes,
            "trace_id": getattr(record, "trace_id", None),
            "span_id": getattr(record, "span_id", None),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "resource": {
                "service.name": settings.service_name,
                "service.environment": settings.environment,
            },
        }

        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_record.update(
                {
                    "exception.type": exc_type.__name__,  # type: ignore[union-attr]
                    "exception.message": str(exc_value),
                    "exception.stacktrace": "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                }
            )

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

    logger.propagate = False
    return logger
