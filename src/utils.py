
import os
import re
import uuid
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# MUST BE FIRST
load_dotenv(override=True)


def validate_api_key(api_key: str) -> dict:
    """
    Validates Google API key using gemini-embedding-001.
    This is the ONLY stable embedding model as of April 2025.
    DO NOT use text-embedding-004 — it returns 404.
    DO NOT use models/embedding-001 — it is deprecated.
    """
    if not api_key:
        return {"valid": False, "message": "No API key provided."}

    api_key = api_key.strip()

    if not api_key.startswith("AIza"):
        return {
            "valid": False,
            "message": "❌ Key must start with AIza. Check your key.",
        }
    if len(api_key) < 35:
        return {
            "valid": False,
            "message": "❌ Key too short. Copy the complete key.",
        }

    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        emb = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",  # ONLY correct model
            google_api_key=api_key,        # ALWAYS pass explicitly
        )
        r = emb.embed_query("API key validation test")
        if r and len(r) > 0:
            return {
                "valid": True,
                "message": (
                    f"✅ API key valid! "
                    f"Model: gemini-embedding-001 | "
                    f"Dims: {len(r)}"
                ),
            }
        return {
            "valid": False,
            "message": "❌ Empty response from embedding model.",
        }
    except Exception as e:
        err = str(e)
        if "404" in err or "not found" in err.lower():
            return {
                "valid": False,
                "message": (
                    "❌ 404 Error: Wrong model name in code. "
                    "Run fix_model.py to correct it."
                ),
            }
        if "API Key not found" in err or "INVALID_ARGUMENT" in err:
            return {
                "valid": False,
                "message": (
                    "❌ Key rejected by Google. "
                    "Get a new key at: "
                    "https://aistudio.google.com/app/apikey"
                ),
            }
        if "quota" in err.lower() or "429" in err:
            return {
                "valid": False,
                "message": "❌ Rate limit exceeded. Wait 1 min and retry.",
            }
        return {"valid": False, "message": f"❌ Error: {err[:200]}"}


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
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r" {4,}", "   ", text)
    return text.strip()


def is_supported_file(filename: str) -> bool:
    from config import Config
    return Path(filename).suffix.lower() in Config.SUPPORTED_EXTENSIONS


def create_session_id() -> str:
    return str(uuid.uuid4())


def chunk_list(lst: list, size: int) -> List[list]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]
