from pathlib import Path
import shutil

def w(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    size = len(content.encode('utf-8'))
    print(f'Written: {path} ({size} bytes)')

# Clean old broken vectorstore
vs = Path('personal-knowledge-brain/vectorstore')
if vs.exists():
    shutil.rmtree(vs)
    print('Old broken vectorstore deleted')
vs.mkdir(exist_ok=True)
(vs / '.gitkeep').touch()

print('Fixing all files for gemini-embedding-001...')
print()

# ── FILE 1: config.py ─────────────────────────────────────────────
w('personal-knowledge-brain/config.py', '''
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# MUST BE FIRST LINE — before any class or function
load_dotenv(override=True)


class Config:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")

    # ✅ CORRECT stable GA model (April 2025)
    # ❌ text-embedding-004     → DEAD → 404 error
    # ❌ models/embedding-001   → DEAD → 404 error
    EMBEDDING_MODEL: str = "gemini-embedding-001"

    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    SUPPORTED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".txt", ".md", ".csv"
    ]
    MAX_RETRIEVAL_DOCS: int = int(os.getenv("MAX_RETRIEVAL_DOCS", "5"))
    SEARCH_TYPE: str = os.getenv("SEARCH_TYPE", "similarity")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./vectorstore")
    DOCUMENTS_PATH: str = os.getenv("DOCUMENTS_PATH", "./documents")
    LOGS_PATH: str = os.getenv("LOGS_PATH", "./logs")
    SESSIONS_PATH: str = os.getenv("SESSIONS_PATH", "./sessions")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./sessions/knowledge_brain.db"
    )
    MAX_CHAT_HISTORY: int = int(os.getenv("MAX_CHAT_HISTORY", "20"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    APP_NAME: str = os.getenv("APP_NAME", "Personal Knowledge Brain")
    APP_VERSION: str = os.getenv("APP_VERSION", "3.0.0")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"

    @classmethod
    def create_directories(cls):
        for d in [
            cls.VECTOR_STORE_PATH,
            cls.DOCUMENTS_PATH,
            cls.LOGS_PATH,
            cls.SESSIONS_PATH,
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> dict:
        errors = []
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is missing!")
        elif not cls.GOOGLE_API_KEY.startswith("AIza"):
            errors.append("GOOGLE_API_KEY format is invalid!")
        cls.create_directories()
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "api_key_set": (
                bool(cls.GOOGLE_API_KEY)
                and cls.GOOGLE_API_KEY.startswith("AIza")
            ),
        }

    @classmethod
    def update_api_key(cls, api_key: str):
        env_path = Path(".env")
        try:
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                lines = content.split("\\n")
                updated, found = [], False
                for line in lines:
                    if line.startswith("GOOGLE_API_KEY="):
                        updated.append(f"GOOGLE_API_KEY={api_key}")
                        found = True
                    else:
                        updated.append(line)
                if not found:
                    updated.append(f"GOOGLE_API_KEY={api_key}")
                env_path.write_text(
                    "\\n".join(updated), encoding="utf-8"
                )
        except Exception as e:
            print(f"Warning updating .env: {e}")
        os.environ["GOOGLE_API_KEY"] = api_key
        cls.GOOGLE_API_KEY = api_key


config = Config()
config.create_directories()
''')

# ── FILE 2: src/utils.py ──────────────────────────────────────────
w('personal-knowledge-brain/src/utils.py', '''
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
    text = text.replace("\\x00", "")
    text = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text)
    text = re.sub(r"\\n{4,}", "\\n\\n\\n", text)
    text = re.sub(r" {4,}", "   ", text)
    return text.strip()


def is_supported_file(filename: str) -> bool:
    from config import Config
    return Path(filename).suffix.lower() in Config.SUPPORTED_EXTENSIONS


def create_session_id() -> str:
    return str(uuid.uuid4())


def chunk_list(lst: list, size: int) -> List[list]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]
''')

print()
print("=" * 60)
print("ALL FILES FIXED WITH CORRECT EMBEDDING MODEL!")
print("=" * 60)
print()
print("✅ config.py            → EMBEDDING_MODEL = gemini-embedding-001")
print("✅ src/utils.py         → validate_api_key uses gemini-embedding-001")
print()
print("Next step: Run verification test")