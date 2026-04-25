
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "Personal Knowledge Brain")
    APP_VERSION: str = os.getenv("APP_VERSION", "3.0.0")
    DEBUG_MODE: bool = (
        os.getenv("DEBUG_MODE", "False").lower() == "true"
    )
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_OUTPUT_TOKENS: int = int(
        os.getenv("MAX_OUTPUT_TOKENS", "2048")
    )
    # text-embedding-004 is correct for google-genai 1.73.1
    EMBEDDING_MODEL: str = "text-embedding-004"
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_FILE_SIZE_MB: int = int(
        os.getenv("MAX_FILE_SIZE_MB", "50")
    )
    SUPPORTED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".txt", ".md", ".csv"
    ]
    MAX_RETRIEVAL_DOCS: int = int(
        os.getenv("MAX_RETRIEVAL_DOCS", "5")
    )
    SEARCH_TYPE: str = os.getenv("SEARCH_TYPE", "similarity")
    VECTOR_STORE_PATH: str = os.getenv(
        "VECTOR_STORE_PATH", "./vectorstore"
    )
    DOCUMENTS_PATH: str = os.getenv(
        "DOCUMENTS_PATH", "./documents"
    )
    LOGS_PATH: str = os.getenv("LOGS_PATH", "./logs")
    SESSIONS_PATH: str = os.getenv(
        "SESSIONS_PATH", "./sessions"
    )
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./sessions/knowledge_brain.db"
    )
    MAX_CHAT_HISTORY: int = int(
        os.getenv("MAX_CHAT_HISTORY", "20")
    )
    ENABLE_STREAMING: bool = (
        os.getenv("ENABLE_STREAMING", "True").lower() == "true"
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

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
            errors.append("GOOGLE_API_KEY missing!")
        elif cls.GOOGLE_API_KEY == "your_google_api_key_here":
            errors.append("Replace placeholder API key!")
        elif not cls.GOOGLE_API_KEY.startswith("AIza"):
            errors.append("API key format wrong!")
        cls.create_directories()
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "api_key_set": (
                bool(cls.GOOGLE_API_KEY)
                and cls.GOOGLE_API_KEY != "your_google_api_key_here"
                and cls.GOOGLE_API_KEY.startswith("AIza")
            ),
        }

    @classmethod
    def update_api_key(cls, api_key: str):
        env_path = Path(".env")
        try:
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                lines = content.split("\n")
                updated, found = [], False
                for line in lines:
                    if line.startswith("GOOGLE_API_KEY="):
                        updated.append(
                            f"GOOGLE_API_KEY={api_key}"
                        )
                        found = True
                    else:
                        updated.append(line)
                if not found:
                    updated.append(f"GOOGLE_API_KEY={api_key}")
                env_path.write_text(
                    "\n".join(updated), encoding="utf-8"
                )
        except Exception as e:
            print(f"Warning: {e}")
        os.environ["GOOGLE_API_KEY"] = api_key
        cls.GOOGLE_API_KEY = api_key


config = Config()
config.create_directories()
