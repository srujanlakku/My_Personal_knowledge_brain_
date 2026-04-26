from pathlib import Path
import shutil

def w(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    size = len(content.encode('utf-8'))
    print(f'OK Written: {path} ({size} bytes)')

# Clean old vectorstore
vs = Path('personal-knowledge-brain/vectorstore')
if vs.exists():
    shutil.rmtree(vs)
    print('OK Old broken vectorstore deleted')
vs.mkdir(exist_ok=True)
(vs / '.gitkeep').touch()

for d in ['src', '.streamlit', 'documents', 'tests', 'logs', 'sessions']:
    Path(f'personal-knowledge-brain/{d}').mkdir(parents=True, exist_ok=True)
print('OK All directories ready')
print()

# config.py
w('personal-knowledge-brain/config.py', '''
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    SUPPORTED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md", ".csv"]
    MAX_RETRIEVAL_DOCS: int = int(os.getenv("MAX_RETRIEVAL_DOCS", "5"))
    SEARCH_TYPE: str = os.getenv("SEARCH_TYPE", "similarity")
    VECTOR_STORE_PATH: str = "./vectorstore"
    DOCUMENTS_PATH: str = "./documents"
    LOGS_PATH: str = "./logs"
    SESSIONS_PATH: str = "./sessions"

    @classmethod
    def update_api_key(cls, api_key: str):
        env_path = Path(".env")
        try:
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                lines = content.split("\\n")
                updated = []
                found = False
                for line in lines:
                    if line.startswith("GOOGLE_API_KEY="):
                        updated.append(f"GOOGLE_API_KEY={api_key}")
                        found = True
                    else:
                        updated.append(line)
                if not found:
                    updated.append(f"GOOGLE_API_KEY={api_key}")
                env_path.write_text("\\n".join(updated), encoding="utf-8")
        except Exception:
            pass
        os.environ["GOOGLE_API_KEY"] = api_key
        cls.GOOGLE_API_KEY = api_key
''')

print()
print("=" * 60)
print("✅ ALL FILES FIXED SUCCESSFULLY!")
print("=" * 60)
print()
print("Next step:")
print("  1. Make sure your API key is valid in .env")
print("  2. Run: pip install --upgrade langchain-google-genai google-genai")
print("  3. Run: streamlit run personal-knowledge-brain/app.py")