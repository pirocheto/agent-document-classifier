from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import ValidationException

from app.agent.agent import invoke_agent
from app.core.config import get_settings
from app.core.logger import setup_logger
from app.core.middleware import RequestContextMiddleware, RequestLoggingMiddleware
from app.schemas import ClassificationResponseSchema, InvokeInputSchema
from app.utils import get_mimetype

logger = setup_logger()
settings = get_settings()


app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.get("/ping")
def ping() -> dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


ACCEPTED_TYPES = {
    # PDF
    "application/pdf",
    # DOCS
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@app.post("/invocations", response_model=ClassificationResponseSchema)
async def invoke(data: InvokeInputSchema) -> Any:
    """
    Invoke the classification agent.
    """

    mimetype = await get_mimetype(data.file_url)
    if mimetype not in ACCEPTED_TYPES:
        raise ValidationException(
            errors=[
                {
                    "loc": ("body", "file_url"),
                    "msg": f"Unsupported file type: {mimetype}. Supported types are: {', '.join(ACCEPTED_TYPES)}",
                    "type": "value_error.unsupported_file_type",
                }
            ]
        )

    return await invoke_agent(
        file_url=data.file_url,
        categories=[cat.model_dump() for cat in data.categories],
        mimetype=mimetype,
        confidence=data.confidence,
        justification=data.justification,
    )
