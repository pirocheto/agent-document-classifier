from typing import TypedDict


class CategoryDescription(TypedDict):
    name: str
    description: str


class Config(TypedDict):
    justification: bool
    confidence: bool
    categories: list[CategoryDescription]


class FileData(TypedDict):
    name: str
    mime_type: str
    bytes: bytes
