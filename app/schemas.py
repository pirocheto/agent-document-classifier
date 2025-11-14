from typing import Literal

from pydantic import BaseModel, Field


class CategoryDescriptionSchema(BaseModel):
    """Description of a category for document classification."""

    name: str = Field(
        ...,
        description="The name of the category.",
    )
    description: str = Field(
        ...,
        description="A brief description of the category.",
    )


class InvokeInputSchema(BaseModel):
    """Request schema for invoking the classification agent."""

    file_url: str = Field(
        ...,
        description="URL of the document to classify.",
    )

    categories: list[CategoryDescriptionSchema] = Field(
        min_length=2,
        max_length=10,
        description="List of categories with their descriptions for document classification. "
        "true will slow down processing time",
        examples=[
            [
                {"name": "Finance", "description": "Documents related to financial matters."},
                {"name": "Legal", "description": "Documents related to legal matters."},
                {"name": "HR", "description": "Documents related to human resources."},
            ],
        ],
    )

    confidence: bool = Field(
        default=False,
        description="Whether to include a confidence level for the classification.",
    )

    justification: bool = Field(
        default=False,
        description="Whether to include a justification for the chosen category.",
    )


class ClassificationResponseSchema(BaseModel):
    """Document classification Response."""

    category: str = Field(
        ...,
        description="The chosen category for the document classification.",
    )
    confidence: Literal["high", "medium", "low"] | None = Field(
        None,
        description="Confidence level of the classification.",
    )
    justification: str | None = Field(
        None,
        description="Brief explanation (2-3 sentences) of why this category was chosen.",
    )
