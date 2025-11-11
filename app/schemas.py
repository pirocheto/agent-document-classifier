import json
from typing import Literal

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, model_validator


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


class ConfigRequestSchema(BaseModel):
    """Configuration for document classification."""

    confidence: bool = Field(
        default=False,
        description="Whether to include a confidence level for the classification.",
    )

    justification: bool = Field(
        default=False,
        description="Whether to include a justification for the chosen category.",
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

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            try:
                return cls(**json.loads(value))
            except json.JSONDecodeError as e:
                raise RequestValidationError(
                    errors=[
                        {
                            "loc": ["body", "config"],
                            "msg": "Invalid JSON format.",
                            "type": "value_error.jsondecode",
                            "input": value,
                        }
                    ]
                ) from e
        return value

    @model_validator(mode="after")
    def validate_unique_categories(self):
        """Ensure that category names are unique."""

        duplicate_names = set()
        seen_names = set()
        for category in self.categories:
            if category.name in seen_names:
                duplicate_names.add(category.name)
            else:
                seen_names.add(category.name)
        if duplicate_names:
            raise RequestValidationError(
                errors=[
                    {
                        "loc": ["body", "config", "categories"],
                        "msg": f"Duplicate category names found: {', '.join(duplicate_names)}",
                        "type": "value_error.duplicate_categories",
                        "input": self.categories,
                    }
                ]
            )
        return self


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
