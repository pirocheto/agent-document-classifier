from fastapi import File, UploadFile
from fastapi.exceptions import RequestValidationError


def validate_file(file: UploadFile = File(...)) -> UploadFile:
    """Parse and validate the uploaded file data."""

    if file.filename == "":
        raise RequestValidationError(
            errors=[
                {
                    "loc": ["body", "file"],
                    "msg": "Field required",
                    "type": "value_error.missing",
                }
            ]
        )

    if file.size == 0 or file.content_type is None:
        raise RequestValidationError(
            errors=[
                {
                    "loc": ["body", "file"],
                    "msg": "Invalid file upload.",
                    "type": "value_error.upload_file",
                },
            ]
        )

    return file
