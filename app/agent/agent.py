import base64
from typing import Any, Literal, NotRequired, TypedDict

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.messages import FileContentBlock, HumanMessage, TextContentBlock
from langchain_aws import ChatBedrockConverse
from pydantic import Field, create_model

from app.agent.types import Config, FileData
from app.agent.utils import sanitize_name
from app.core.config import get_settings

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


class StructResponse(TypedDict):
    category: str
    confidence: Literal["high", "medium", "low"]
    justification: NotRequired[str]


def get_schema_model(config: Config):
    """
    Construct a Pydantic model for the agent response format based on the config.
    """

    category_names = [cat["name"] for cat in config["categories"]]
    categories_str = "\n".join([f"- {cat['name']}: {cat['description']}" for cat in config["categories"]])

    fields: dict[str, Any] = {
        "category": (
            Literal[tuple(category_names)],
            Field(
                ...,
                description=f"The available categories are:\n{categories_str}",
            ),
        )
    }

    if config.get("confidence"):
        fields["confidence"] = (
            Literal["high", "medium", "low"],
            Field(..., description="Confidence level of the classification."),
        )

    if config.get("justification"):
        fields["justification"] = (
            str | None,
            Field(None, description="Brief explanation (2-3 sentences) of why this category was chosen."),
        )

    doc = "Classification response schema."
    Model = create_model("AgentResponse", __doc__=doc, **fields)
    return Model


def get_messages(file: FileData, config: Config) -> list[HumanMessage]:
    """Construct the messages for the agent invocation."""

    b64_file = base64.b64encode(file["bytes"]).decode()
    safe_name = sanitize_name(file["name"])

    messages = [
        HumanMessage(
            content_blocks=[
                TextContentBlock(
                    type="text",
                    text="Here is the document to classify.",
                ),
                FileContentBlock(
                    type="file",
                    base64=b64_file,
                    mime_type=file["mime_type"],
                    extras={"name": safe_name},
                ),
            ]
        )
    ]
    return messages


model = ChatBedrockConverse(model=settings.bedrock_model_id)


def init_agent(config: Config):
    """Initialize the classification agent."""

    AgentResponseSchema = get_schema_model(config)
    response_format = ToolStrategy(schema=AgentResponseSchema)

    agent = create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        response_format=response_format,
    )
    return agent


def invoke_agent(file_data: FileData, config: Config) -> StructResponse:
    """Invoke the classification agent."""

    agent = init_agent(config)
    messages = get_messages(file_data, config)

    response = agent.invoke({"messages": messages})
    return response["structured_response"]
