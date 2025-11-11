from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, Form, UploadFile

from app.agent.agent import invoke_agent
from app.agent.types import Config, FileData
from app.core.config import get_settings
from app.core.deps import validate_file
from app.core.logger import setup_logger
from app.core.middleware import RequestContextMiddleware, RequestLoggingMiddleware
from app.schemas import ClassificationResponseSchema, ConfigRequestSchema

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


@app.post("/invocations", response_model=ClassificationResponseSchema)
def invoke(
    file: Annotated[UploadFile, Depends(validate_file)],
    config: Annotated[ConfigRequestSchema, Form()],
) -> Any:
    """
    Invoke the classification agent.
    """

    validated_file = validate_file(file)

    file_data: FileData = {
        "name": cast(str, validated_file.filename),
        "mime_type": cast(str, validated_file.content_type),
        "bytes": validated_file.file.read(),
    }

    invoke_config: Config = {
        "confidence": config.confidence,
        "justification": config.justification,
        "categories": [{"name": cat.name, "description": cat.description} for cat in config.categories],
    }

    found_category = invoke_agent(file_data=file_data, config=invoke_config)
    return found_category
