import mimetypes
import re
import unicodedata

import httpx

ACCEPTED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


async def get_mimetype(url: str) -> str | None:
    """Get the MIME type of a file from its URL."""

    async with httpx.AsyncClient() as client:
        # Perform a HEAD request to avoid downloading the entire file
        response = await client.head(url, follow_redirects=True)
        if response.status_code != 200:
            return None

        # Check MIME type from headers
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type is not None:
            return content_type

        # Fallback: infer MIME type from file extension
        ext = url.split("?")[0].split(".")[-1].lower()
        return mimetypes.types_map.get(f".{ext}")


def sanitize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ASCII", "ignore").decode("ASCII")

    name = name.lower().replace(" ", "_")
    name = re.sub(r"[^a-z0-9_-]", "_", name)
    return name
