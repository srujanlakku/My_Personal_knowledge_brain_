
import os
import re
import uuid
from pathlib import Path
from typing import List
from loguru import logger


def setup_logging(log_path: str = "./logs") -> None:
    Path(log_path).mkdir(parents=True, exist_ok=True)
    logger.add(
        f"{log_path}/app.log",
        rotation="10 MB",
        level="INFO",
        encoding="utf-8",
    )


def validate_api_key(api_key: str) -> dict:
    if not api_key:
        return {"valid": False, "message": "No API key provided"}
    if api_key == "your_google_api_key_here":
        return {"valid": False, "message": "Still placeholder key!"}
    if not api_key.startswith("AIza"):
        return {
            "valid": False,
            "message": "Key must start with AIza",
        }
    if len(api_key) < 35:
        return {
            "valid": False,
            "message": "Key too short. Copy the full key.",
        }
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        result = client.models.embed_content(
            model="text-embedding-004",
            contents="validation test",
        )
        dims = len(result.embeddings[0].values)
        return {
            "valid": True,
            "message": f"API key valid! Embedding dims: {dims}",
        }
    except Exception as e:
        err = str(e)
        if "API Key not found" in err or "INVALID_ARGUMENT" in err:
            return {
                "valid": False,
                "message": (
                    "Key rejected by Google. "
                    "Create new: https://aistudio.google.com/app/apikey"
                ),
            }
        if "quota" in err.lower():
            return {
                "valid": False,
                "message": "Quota exceeded. Wait and retry.",
            }
        return {"valid": False, "message": err[:200]}


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    return f"{size_bytes / 1024 ** 3:.1f} GB"


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text
    )
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r" {4,}", "   ", text)
    return text.strip()


def is_supported_file(filename: str) -> bool:
    from config import Config
    return (
        Path(filename).suffix.lower() in Config.SUPPORTED_EXTENSIONS
    )


def create_session_id() -> str:
    return str(uuid.uuid4())


def chunk_list(lst: list, size: int) -> List[list]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]
