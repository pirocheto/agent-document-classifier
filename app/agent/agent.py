import base64
from typing import Any, Literal, NotRequired, TypedDict

import httpx
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field, create_model

from app.core.config import get_settings
from app.utils import sanitize_name

settings = get_settings()

SYSTEM_PROMPT = """You are a document classification assistant. Your task is to analyze the content of a document and classify it into one of the categories provided by the user.

## Instructions
1. Carefully read the provided document
2. Analyze its content, context, and main characteristics
3. Compare it with the available categories
4. Choose the SINGLE most appropriate category
5. If none of the categories fit well or if the user has not provided any categories, choose "Uncategorized"

## Important Notes
- Don't include any personal data in your response.

Be precise and objective in your classification. If you are unsure, explain your reasoning clearly.

"""  # noqa E501


def get_schema_model(categories: list[dict[str, str]], confidence: bool, justification: bool) -> BaseModel:
    """
    Construct a Pydantic model for the agent response format based on the config.
    """

    categorie_names = tuple(cat["name"] for cat in categories)
    categories_str = "\n".join([f"- {cat['name']}: {cat['description']}" for cat in categories])

    fields: dict[str, Any] = {
        "category": (
            Literal[categorie_names],
            Field(
                ...,
                description=f"The available categories are:\n{categories_str}",
            ),
        )
    }

    if confidence:
        fields["confidence"] = (
            Literal["high", "medium", "low"],
            Field(..., description="Confidence level of the classification."),
        )

    if justification:
        fields["justification"] = (
            str | None,
            Field(None, description="Brief explanation (2-3 sentences) of why this category was chosen."),
        )

    doc = "Classification response schema."
    return create_model("AgentResponse", __doc__=doc, **fields)


def get_messages(file_bytes: bytes, filename: str, mime_type: str):
    """Construct the messages for the agent invocation."""

    b64_file = base64.b64encode(file_bytes).decode()
    safe_name = sanitize_name(filename)
    return [
        {
            "type": "human",
            "content": [
                {
                    "type": "text",
                    "text": "Here is the document to classify.",
                },
                {
                    "type": "file",
                    "base64": b64_file,
                    "mime_type": mime_type,
                    "extras": {"name": safe_name},
                },
            ],
        }
    ]


async def load_file(file_url: str) -> tuple[bytes, str]:
    """Load file bytes from a given file path."""

    async with httpx.AsyncClient() as client:
        response = await client.get(file_url)
        response.raise_for_status()
        file_bytes = response.content

    filename = file_url.split("/")[-1]
    return file_bytes, filename


class StructResponse(TypedDict):
    category: str
    confidence: Literal["high", "medium", "low"]
    justification: NotRequired[str]


async def invoke_agent(
    file_url: str,
    mimetype: str,
    categories: list[dict[str, str]],
    confidence: bool,
    justification: bool,
) -> StructResponse:
    """Invoke the classification agent."""

    model = ChatBedrockConverse(model=settings.bedrock_model_id)
    Schema = get_schema_model(categories, confidence, justification)

    agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        response_format=ToolStrategy(schema=Schema),  # type: ignore
    )

    file_bytes, filename = await load_file(file_url)
    messages = get_messages(file_bytes, filename, mimetype)

    response = agent.invoke({"messages": messages})
    return response["structured_response"]
