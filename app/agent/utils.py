import re
import unicodedata


def sanitize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ASCII", "ignore").decode("ASCII")

    name = name.lower().replace(" ", "_")
    name = re.sub(r"[^a-z0-9_-]", "_", name)
    return name
