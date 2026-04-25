
import os
from pathlib import Path

# Always write files with UTF-8 encoding
def write_file(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

# ── Create all directories ──────────────────────────────
dirs = [
    ".streamlit", "documents", "vectorstore",
    "src", "tests", "logs", "sessions", "assets"
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)
    Path(d + "/.gitkeep").touch()
print("✅ All directories created!")

# ── FILE 1: .env ────────────────────────────────────────
write_file(".env", """GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-1.5-flash
TEMPERATURE=0.3
MAX_OUTPUT_TOKENS=2048
EMBEDDING_MODEL=models/embedding-001
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50
SUPPORTED_EXTENSIONS=.pdf,.docx,.txt,.md,.csv
MAX_RETRIEVAL_DOCS=5
SIMILARITY_THRESHOLD=0.3
SEARCH_TYPE=similarity
VECTOR_STORE_PATH=./vectorstore
DOCUMENTS_PATH=./documents
LOGS_PATH=./logs
SESSIONS_PATH=./sessions
DATABASE_URL=sqlite:///./sessions/knowledge_brain.db
APP_NAME=Personal Knowledge Brain
APP_VERSION=2.0.0
DEBUG_MODE=False
LOG_LEVEL=INFO
MAX_CHAT_HISTORY=20
ENABLE_STREAMING=True
""")

# ── FILE 2: .env.example ────────────────────────────────
write_file(".env.example", """# Copy this to .env and fill values
# Get FREE Google API key: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-1.5-flash
TEMPERATURE=0.3
MAX_OUTPUT_TOKENS=2048
EMBEDDING_MODEL=models/embedding-001
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50
SUPPORTED_EXTENSIONS=.pdf,.docx,.txt,.md,.csv
MAX_RETRIEVAL_DOCS=5
SIMILARITY_THRESHOLD=0.3
SEARCH_TYPE=similarity
VECTOR_STORE_PATH=./vectorstore
DOCUMENTS_PATH=./documents
LOGS_PATH=./logs
SESSIONS_PATH=./sessions
DATABASE_URL=sqlite:///./sessions/knowledge_brain.db
APP_NAME=Personal Knowledge Brain
APP_VERSION=2.0.0
DEBUG_MODE=False
LOG_LEVEL=INFO
MAX_CHAT_HISTORY=20
ENABLE_STREAMING=True
""")

# ── FILE 3: .gitignore ───────────────────────────────────
write_file(".gitignore", """.env
venv/
__pycache__/
*.pyc
*.pyo
vectorstore/
*.db
*.sqlite
logs/
.DS_Store
.pytest_cache/
dist/
build/
*.egg-info/
.streamlit/secrets.toml
""")

# ── FILE 4: .streamlit/config.toml ──────────────────────
write_file(".streamlit/config.toml", """[theme]
primaryColor = "#6C63FF"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1E1E2E"
textColor = "#FAFAFA"
font = "sans serif"

[server]
maxUploadSize = 50
enableCORS = false
enableXsrfProtection = true
headless = true

[browser]
gatherUsageStats = false
""")

# ── FILE 5: config.py ────────────────────────────────────
write_file("config.py", '''"""
config.py - Central configuration for Personal Knowledge Brain
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    APP_NAME: str = os.getenv("APP_NAME", "Personal Knowledge Brain")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

    # CRITICAL: This is the ONLY working embedding model
    # DO NOT change to text-embedding-004 or any other model
    EMBEDDING_MODEL: str = "models/embedding-001"

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    SUPPORTED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".txt", ".md", ".csv"
    ]

    MAX_RETRIEVAL_DOCS: int = int(os.getenv("MAX_RETRIEVAL_DOCS", "5"))
    SIMILARITY_THRESHOLD: float = float(
        os.getenv("SIMILARITY_THRESHOLD", "0.3")
    )
    SEARCH_TYPE: str = os.getenv("SEARCH_TYPE", "similarity")

    VECTOR_STORE_PATH: str = os.getenv(
        "VECTOR_STORE_PATH", "./vectorstore"
    )
    DOCUMENTS_PATH: str = os.getenv("DOCUMENTS_PATH", "./documents")
    LOGS_PATH: str = os.getenv("LOGS_PATH", "./logs")
    SESSIONS_PATH: str = os.getenv("SESSIONS_PATH", "./sessions")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./sessions/knowledge_brain.db"
    )

    MAX_CHAT_HISTORY: int = int(os.getenv("MAX_CHAT_HISTORY", "20"))
    ENABLE_STREAMING: bool = (
        os.getenv("ENABLE_STREAMING", "True").lower() == "true"
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def create_directories(cls):
        for d in [
            cls.VECTOR_STORE_PATH, cls.DOCUMENTS_PATH,
            cls.LOGS_PATH, cls.SESSIONS_PATH
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> dict:
        errors = []
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY missing!")
        elif cls.GOOGLE_API_KEY == "your_google_api_key_here":
            errors.append("Replace placeholder API key!")
        cls.create_directories()
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "api_key_set": bool(cls.GOOGLE_API_KEY) and
                           cls.GOOGLE_API_KEY != "your_google_api_key_here"
        }

    @classmethod
    def update_api_key(cls, api_key: str):
        env_path = Path(".env")
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
        os.environ["GOOGLE_API_KEY"] = api_key
        cls.GOOGLE_API_KEY = api_key


config = Config()
config.create_directories()
''')

# ── FILE 6: src/__init__.py ──────────────────────────────
write_file("src/__init__.py", '''"""
Personal Knowledge Brain - Source Package
"""
''')

# ── FILE 7: src/utils.py ─────────────────────────────────
write_file("src/utils.py", '''"""
utils.py - Utility functions for Personal Knowledge Brain
"""
import os
import re
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from loguru import logger


def setup_logging(log_path: str = "./logs") -> None:
    """Configure loguru logging."""
    Path(log_path).mkdir(parents=True, exist_ok=True)
    logger.add(
        f"{log_path}/app.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


def validate_api_key(api_key: str) -> dict:
    """Test Google API key with a real embedding call."""
    if not api_key or api_key == "your_google_api_key_here":
        return {"valid": False, "message": "API key not provided"}
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        emb = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key,
        )
        result = emb.embed_query("test")
        if result and len(result) > 0:
            return {"valid": True, "message": "API key is valid!"}
        return {"valid": False, "message": "Empty embedding result"}
    except Exception as e:
        return {"valid": False, "message": str(e)[:200]}


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    return f"{size_bytes / 1024 ** 3:.1f} GB"


def sanitize_text(text: str) -> str:
    """Clean text for safe embedding."""
    if not text:
        return ""
    text = text.replace("\\x00", "")
    text = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text)
    text = re.sub(r"\\n{4,}", "\\n\\n\\n", text)
    text = re.sub(r" {4,}", "   ", text)
    return text.strip()


def is_supported_file(filename: str) -> bool:
    """Check if file extension is supported."""
    from config import Config
    ext = Path(filename).suffix.lower()
    return ext in Config.SUPPORTED_EXTENSIONS


def validate_url(url: str) -> dict:
    """Validate and test URL accessibility."""
    try:
        import validators
        import requests
        if not validators.url(url):
            return {"valid": False, "message": "Invalid URL format"}
        response = requests.head(url, timeout=10)
        return {
            "valid": True,
            "message": f"URL accessible (status: {response.status_code})"
        }
    except Exception as e:
        return {"valid": False, "message": str(e)[:100]}


def get_file_extension(filename: str) -> str:
    """Return lowercase file extension."""
    return Path(filename).suffix.lower()


def calculate_confidence(score: float) -> dict:
    """Convert similarity score to confidence level."""
    pct = round(score * 100, 1)
    if score >= 0.8:
        return {"level": "High", "color": "green", "pct": pct}
    elif score >= 0.5:
        return {"level": "Medium", "color": "orange", "pct": pct}
    return {"level": "Low", "color": "red", "pct": pct}


def create_session_id() -> str:
    """Generate unique session ID."""
    return str(uuid.uuid4())


def chunk_list(lst: list, size: int) -> List[list]:
    """Split list into batches."""
    return [lst[i:i+size] for i in range(0, len(lst), size)]
''')

# ── FILE 8: src/document_processor.py ───────────────────
write_file("src/document_processor.py", '''"""
document_processor.py - Load and chunk all document types
"""
import os
import re
from pathlib import Path
from typing import List
import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config
from src.utils import sanitize_text


class DocumentProcessor:
    """Handles loading and chunking of all document types."""

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\\n\\n", "\\n", ". ", " ", ""],
        )

    def load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF with PyMuPDF, fallback to PyPDF2."""
        docs = []
        try:
            import fitz
            doc = fitz.open(file_path)
            for i in range(len(doc)):
                text = doc[i].get_text()
                if text.strip():
                    docs.append(Document(
                        page_content=sanitize_text(text),
                        metadata={
                            "source": file_path,
                            "filename": Path(file_path).name,
                            "page": i + 1,
                            "total_pages": len(doc),
                            "file_type": "pdf",
                        }
                    ))
            doc.close()
        except Exception:
            try:
                import PyPDF2
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        if text.strip():
                            docs.append(Document(
                                page_content=sanitize_text(text),
                                metadata={
                                    "source": file_path,
                                    "filename": Path(file_path).name,
                                    "page": i + 1,
                                    "total_pages": len(reader.pages),
                                    "file_type": "pdf",
                                }
                            ))
            except Exception as e:
                logger.error(f"PDF load failed {file_path}: {e}")
        return docs

    def load_docx(self, file_path: str) -> List[Document]:
        """Load DOCX file."""
        try:
            import docx2txt
            text = docx2txt.process(file_path)
            if text.strip():
                return [Document(
                    page_content=sanitize_text(text),
                    metadata={
                        "source": file_path,
                        "filename": Path(file_path).name,
                        "file_type": "docx",
                    }
                )]
        except Exception as e:
            logger.error(f"DOCX load failed {file_path}: {e}")
        return []

    def load_txt(self, file_path: str) -> List[Document]:
        """Load TXT with encoding detection."""
        for enc in ["utf-8", "latin-1", "ascii", "cp1252"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    text = f.read()
                return [Document(
                    page_content=sanitize_text(text),
                    metadata={
                        "source": file_path,
                        "filename": Path(file_path).name,
                        "file_type": "txt",
                        "encoding": enc,
                    }
                )]
            except Exception:
                continue
        logger.error(f"TXT load failed: {file_path}")
        return []

    def load_markdown(self, file_path: str) -> List[Document]:
        """Load Markdown file."""
        return self.load_txt(file_path)

    def load_csv(self, file_path: str) -> List[Document]:
        """Load CSV using pandas."""
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            docs = []
            for i, row in df.iterrows():
                text = " | ".join(
                    [f"{col}: {val}" for col, val in row.items()
                     if pd.notna(val)]
                )
                docs.append(Document(
                    page_content=sanitize_text(text),
                    metadata={
                        "source": file_path,
                        "filename": Path(file_path).name,
                        "file_type": "csv",
                        "row": i + 1,
                    }
                ))
            return docs
        except Exception as e:
            logger.error(f"CSV load failed {file_path}: {e}")
            return []

    def load_url(self, url: str) -> List[Document]:
        """Scrape URL content."""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            for tag in soup(["script","style","nav","footer"]):
                tag.decompose()
            text = soup.get_text(separator="\\n", strip=True)
            text = re.sub(r"\\n{3,}", "\\n\\n", text)
            return [Document(
                page_content=sanitize_text(text),
                metadata={
                    "source": url,
                    "filename": url,
                    "file_type": "url",
                }
            )]
        except Exception as e:
            logger.error(f"URL load failed {url}: {e}")
            return []

    def load_uploaded_file(self, uploaded_file) -> List[Document]:
        """Handle Streamlit uploaded file."""
        try:
            save_path = Path(Config.DOCUMENTS_PATH) / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return self._load_by_extension(str(save_path))
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return []

    def chunk_documents(
        self, documents: List[Document]
    ) -> List[Document]:
        """Split documents into chunks."""
        if not documents:
            return []
        chunks = self.splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
        return chunks

    def _load_by_extension(self, file_path: str) -> List[Document]:
        """Route to correct loader by extension."""
        ext = Path(file_path).suffix.lower()
        loaders = {
            ".pdf": self.load_pdf,
            ".docx": self.load_docx,
            ".doc": self.load_docx,
            ".txt": self.load_txt,
            ".md": self.load_markdown,
            ".csv": self.load_csv,
        }
        loader = loaders.get(ext)
        if loader:
            return loader(file_path)
        logger.warning(f"Unsupported: {ext}")
        return []
''')

# ── FILE 9: src/embeddings_manager.py ───────────────────
write_file("src/embeddings_manager.py", '''"""
embeddings_manager.py - ChromaDB vector store management
FIXED: Uses models/embedding-001 (only working model for v1beta)
"""
import os
from pathlib import Path
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
import chromadb
from config import Config


class EmbeddingsManager:
    """
    Manages document embeddings and ChromaDB vector storage.

    CRITICAL NOTE:
    The ONLY working embedding model for Google API v1beta is:
    models/embedding-001
    
    DO NOT use:
    - models/text-embedding-004 (causes 404 error)
    - text-embedding-004 (causes 404 error)
    - gemini-embedding-001 (only works with newer SDK)
    """

    COLLECTION_NAME = "knowledge_brain"

    def __init__(self):
        """Initialize embeddings and ChromaDB."""
        self._embeddings = None
        self._vectorstore = None
        self._client = None
        self._initialize()

    def _initialize(self) -> None:
        """Set up embeddings model and ChromaDB client."""
        try:
            api_key = Config.GOOGLE_API_KEY
            if not api_key or api_key == "your_google_api_key_here":
                logger.warning("No API key set yet")
                return

            # FIXED: Use models/embedding-001
            # This is the only model supported by embedContent
            # on API version v1beta with langchain-google-genai 2.x
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key,
                task_type="retrieval_document",
            )

            # Test embedding works
            test = self._embeddings.embed_query("test")
            if not test:
                raise ValueError("Embedding test returned empty!")
            logger.info("Embedding model loaded successfully!")

            # Initialize ChromaDB with PersistentClient
            Path(Config.VECTOR_STORE_PATH).mkdir(
                parents=True, exist_ok=True
            )
            self._client = chromadb.PersistentClient(
                path=Config.VECTOR_STORE_PATH
            )

            # Load existing vectorstore if available
            if self.vectorstore_exists():
                self._vectorstore = Chroma(
                    client=self._client,
                    collection_name=self.COLLECTION_NAME,
                    embedding_function=self._embeddings,
                )
                logger.info("Loaded existing vectorstore!")
            else:
                logger.info("No vectorstore yet - ready for documents")

        except Exception as e:
            logger.error(f"EmbeddingsManager init failed: {e}")
            raise

    def reinitialize(self, api_key: str) -> None:
        """Reinitialize with new API key."""
        Config.GOOGLE_API_KEY = api_key
        self._embeddings = None
        self._vectorstore = None
        self._client = None
        self._initialize()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    def create_vectorstore(
        self, documents: List[Document]
    ) -> Optional[Chroma]:
        """Create vectorstore from document chunks."""
        if not documents:
            raise ValueError("No documents to embed!")

        logger.info(f"Embedding {len(documents)} chunks...")

        # Clear existing collection
        try:
            self._client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass

        # Process in batches of 50 for reliability
        batch_size = 50
        batches = [
            documents[i:i+batch_size]
            for i in range(0, len(documents), batch_size)
        ]

        self._vectorstore = Chroma.from_documents(
            documents=batches[0],
            embedding=self._embeddings,
            client=self._client,
            collection_name=self.COLLECTION_NAME,
        )

        for i, batch in enumerate(batches[1:], 1):
            self._vectorstore.add_documents(batch)
            logger.info(f"Batch {i+1}/{len(batches)} embedded!")

        count = self._vectorstore._collection.count()
        logger.info(f"Vectorstore created: {count} chunks!")
        return self._vectorstore

    def add_documents(self, documents: List[Document]) -> int:
        """Add documents to existing vectorstore."""
        if not documents:
            return 0
        if self._vectorstore is None:
            self.create_vectorstore(documents)
            return len(documents)
        try:
            self._vectorstore.add_documents(documents)
            return len(documents)
        except Exception as e:
            logger.error(f"Add documents failed: {e}")
            return 0

    def get_retriever(self, k: int = None):
        """Return configured retriever."""
        if self._vectorstore is None:
            return None
        k = k or Config.MAX_RETRIEVAL_DOCS
        return self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    def get_vectorstore_stats(self) -> dict:
        """Return vectorstore statistics."""
        empty = {
            "total_chunks": 0, "total_documents": 0,
            "storage_size": "0 KB", "indexed_files": []
        }
        if self._vectorstore is None:
            return empty
        try:
            col = self._vectorstore._collection
            total_chunks = col.count()
            results = col.get(include=["metadatas"])
            sources = list(set(
                m.get("filename", m.get("source", "Unknown"))
                for m in results["metadatas"] if m
            ))
            return {
                "total_chunks": total_chunks,
                "total_documents": len(sources),
                "storage_size": self._get_storage_size(),
                "indexed_files": sources,
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return empty

    def vectorstore_exists(self) -> bool:
        """Check if vectorstore has documents."""
        try:
            cols = self._client.list_collections()
            names = [c.name for c in cols]
            if self.COLLECTION_NAME in names:
                col = self._client.get_collection(self.COLLECTION_NAME)
                return col.count() > 0
            return False
        except Exception:
            return False

    def delete_all(self) -> bool:
        """Delete entire vectorstore."""
        try:
            self._client.delete_collection(self.COLLECTION_NAME)
            self._vectorstore = None
            logger.info("Vectorstore cleared!")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def is_ready(self) -> bool:
        """Check if embeddings manager is ready."""
        return self._embeddings is not None

    def _get_storage_size(self) -> str:
        """Get human readable vectorstore size."""
        path = Path(Config.VECTOR_STORE_PATH)
        if not path.exists():
            return "0 KB"
        size = sum(
            f.stat().st_size
            for f in path.rglob("*") if f.is_file()
        )
        if size < 1024:
            return f"{size} B"
        elif size < 1024**2:
            return f"{size/1024:.1f} KB"
        return f"{size/1024**2:.1f} MB"
''')

# ── FILE 10: src/memory_manager.py ──────────────────────
write_file("src/memory_manager.py", '''"""
memory_manager.py - Chat history and session management
"""
import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from loguru import logger

from langchain.memory import ConversationBufferWindowMemory
from config import Config


class MemoryManager:
    """Manages chat history with LangChain + SQLite."""

    def __init__(self):
        self._memory = ConversationBufferWindowMemory(
            k=Config.MAX_CHAT_HISTORY,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )
        self._db_path = (
            Path(Config.SESSIONS_PATH) / "chat_history.db"
        )
        self._messages = []
        self._last_user_msg = ""
        self._init_db()

    def _init_db(self) -> None:
        """Create SQLite tables."""
        Path(Config.SESSIONS_PATH).mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                sources TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_message(
        self,
        role: str,
        content: str,
        sources: List[dict] = None
    ) -> None:
        """Add message to memory."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = {
            "role": role,
            "content": content,
            "sources": sources or [],
            "timestamp": timestamp,
        }
        self._messages.append(message)
        if role == "user":
            self._last_user_msg = content
        elif role == "assistant" and self._last_user_msg:
            try:
                self._memory.save_context(
                    {"input": self._last_user_msg},
                    {"answer": content}
                )
            except Exception as e:
                logger.error(f"Memory save error: {e}")

    def get_langchain_memory(self):
        """Return LangChain memory object."""
        return self._memory

    def get_chat_history(self) -> list:
        """Return chat history for chain."""
        return self._memory.chat_memory.messages

    def get_display_messages(self) -> List[dict]:
        """Return messages for UI display."""
        return self._messages

    def clear_memory(self) -> None:
        """Clear all chat history."""
        self._memory.clear()
        self._messages = []
        self._last_user_msg = ""

    def get_message_count(self) -> int:
        """Return message count."""
        return len(self._messages)

    def save_session(self, name: str) -> str:
        """Save session to SQLite."""
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT INTO sessions VALUES (?,?,?)",
            (session_id, name, now)
        )
        for msg in self._messages:
            conn.execute(
                "INSERT INTO messages "
                "(session_id, role, content, sources, timestamp)"
                " VALUES (?,?,?,?,?)",
                (
                    session_id, msg["role"], msg["content"],
                    json.dumps(msg.get("sources", [])),
                    msg.get("timestamp", now),
                )
            )
        conn.commit()
        conn.close()
        return session_id

    def get_all_sessions(self) -> List[dict]:
        """Return all saved sessions."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.execute(
                "SELECT id, name, created_at FROM sessions "
                "ORDER BY created_at DESC"
            )
            sessions = [
                {"id": r[0], "name": r[1], "created": r[2]}
                for r in cursor.fetchall()
            ]
            conn.close()
            return sessions
        except Exception:
            return []
''')

# ── FILE 11: src/rag_chain.py ────────────────────────────
write_file("src/rag_chain.py", '''"""
rag_chain.py - Core RAG pipeline
"""
import os
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from config import Config


class RAGChain:
    """Core RAG pipeline: LLM + Retriever + Memory."""

    def __init__(self, embeddings_manager, memory_manager):
        self.embeddings_manager = embeddings_manager
        self.memory_manager = memory_manager
        self._llm = None
        self._chain = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize LLM."""
        try:
            if not Config.GOOGLE_API_KEY or \\
               Config.GOOGLE_API_KEY == "your_google_api_key_here":
                logger.warning("No API key for RAG chain")
                return
            self._llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                google_api_key=Config.GOOGLE_API_KEY,
                temperature=Config.TEMPERATURE,
                max_output_tokens=Config.MAX_OUTPUT_TOKENS,
                convert_system_message_to_human=True,
            )
            retriever = self.embeddings_manager.get_retriever()
            if retriever:
                self._chain = self._build_chain(retriever)
                logger.info("RAG chain initialized!")
        except Exception as e:
            logger.error(f"RAG chain init failed: {e}")

    def _build_chain(
        self, retriever
    ) -> ConversationalRetrievalChain:
        """Build conversational retrieval chain."""
        prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template="""You are a personal knowledge assistant.

RULES:
1. Answer ONLY using the context below
2. Always cite: [Document Name, Page X]
3. If not found, say: "I couldn't find this in your knowledge base."
4. Use bullet points for clarity
5. Be thorough but concise

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer:"""
        )
        return ConversationalRetrievalChain.from_llm(
            llm=self._llm,
            retriever=retriever,
            memory=self.memory_manager.get_langchain_memory(),
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt},
            verbose=False,
        )

    def rebuild_chain(self) -> None:
        """Rebuild chain after new documents added."""
        try:
            retriever = self.embeddings_manager.get_retriever()
            if retriever and self._llm:
                self._chain = self._build_chain(retriever)
                logger.info("Chain rebuilt!")
        except Exception as e:
            logger.error(f"Rebuild failed: {e}")

    def reinitialize(self) -> None:
        """Reinitialize after API key update."""
        self._llm = None
        self._chain = None
        self._initialize()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10)
    )
    def get_response(self, question: str) -> dict:
        """Get RAG response for question."""
        validation = self._validate_question(question)
        if not validation["valid"]:
            return {
                "answer": validation["message"],
                "sources": [], "error": True
            }
        if self._chain is None:
            return {
                "answer": (
                    "Please upload documents first, "
                    "then I can answer questions!"
                ),
                "sources": [], "error": True
            }
        try:
            result = self._chain({
                "question": question,
                "chat_history": (
                    self.memory_manager.get_chat_history()
                ),
            })
            answer = result.get("answer", "No answer generated")
            source_docs = result.get("source_documents", [])
            sources = self._format_sources(source_docs)
            return {"answer": answer, "sources": sources, "error": False}
        except Exception as e:
            logger.error(f"Response error: {e}")
            return {
                "answer": f"Error: {str(e)[:200]}",
                "sources": [], "error": True
            }

    def _format_sources(
        self, source_docs: List[Document]
    ) -> List[dict]:
        """Format source documents."""
        seen = set()
        sources = []
        for doc in source_docs:
            meta = doc.metadata
            filename = meta.get(
                "filename", meta.get("source", "Unknown")
            )
            page = meta.get("page", "N/A")
            key = f"{filename}_{page}"
            if key not in seen:
                seen.add(key)
                sources.append({
                    "filename": filename,
                    "page": page,
                    "preview": doc.page_content[:200] + "...",
                    "file_type": meta.get("file_type", "doc"),
                })
        return sources

    def _validate_question(self, question: str) -> dict:
        """Validate question input."""
        if not question or not question.strip():
            return {"valid": False, "message": "Please enter a question"}
        if len(question) > 1000:
            return {
                "valid": False,
                "message": "Question too long (max 1000 chars)"
            }
        return {"valid": True, "message": "OK"}
''')

# ── FILE 12: app.py ──────────────────────────────────────
write_file("app.py", '''"""
app.py - Personal Knowledge Brain - Main Streamlit Application
"""
import os
import sys
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# Page config MUST be first Streamlit call
st.set_page_config(
    page_title="Personal Knowledge Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Safe imports with error handling
try:
    from config import Config
    from src.utils import validate_api_key, format_file_size
    from src.document_processor import DocumentProcessor
    from src.embeddings_manager import EmbeddingsManager
    from src.rag_chain import RAGChain
    from src.memory_manager import MemoryManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Run: pip install -r requirements.txt")
    st.stop()

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #6C63FF, #3B82F6);
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 1rem;
    color: white;
}
.chat-user {
    background: linear-gradient(135deg, #6C63FF, #8B5CF6);
    color: white;
    padding: 1rem;
    border-radius: 12px;
    margin: 0.5rem 0;
}
.chat-ai {
    background: #1E1E2E;
    border: 1px solid #6C63FF;
    color: #FAFAFA;
    padding: 1rem;
    border-radius: 12px;
    margin: 0.5rem 0;
}
.source-card {
    background: #262640;
    border-left: 3px solid #6C63FF;
    padding: 0.5rem;
    border-radius: 6px;
    margin: 0.3rem 0;
    font-size: 0.85rem;
}
.status-bar {
    background: #1E1E2E;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    border: 1px solid #333;
    margin-bottom: 1rem;
}
.stButton>button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "messages": [],
        "rag_chain": None,
        "embeddings_manager": None,
        "memory_manager": None,
        "vectorstore_ready": False,
        "api_key_valid": False,
        "processing": False,
        "docs_processed": [],
        "stats": {
            "total_chunks": 0,
            "total_documents": 0,
            "storage_size": "0 KB",
            "indexed_files": [],
        }
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def init_managers():
    """Initialize or reinitialize all AI managers."""
    try:
        if st.session_state.memory_manager is None:
            st.session_state.memory_manager = MemoryManager()
        st.session_state.embeddings_manager = EmbeddingsManager()
        st.session_state.rag_chain = RAGChain(
            st.session_state.embeddings_manager,
            st.session_state.memory_manager,
        )
        # Check if vectorstore already has data
        if st.session_state.embeddings_manager.vectorstore_exists():
            st.session_state.vectorstore_ready = True
            stats = (
                st.session_state.embeddings_manager
                .get_vectorstore_stats()
            )
            st.session_state.stats = stats
        return True
    except Exception as e:
        st.error(f"Initialization error: {e}")
        return False


def render_sidebar():
    """Render complete sidebar."""
    with st.sidebar:
        # Branding
        st.markdown("## Personal Knowledge Brain")
        st.markdown("*Your AI-powered second brain*")
        st.divider()

        # API Key Section
        st.markdown("### API Key")
        current_key = Config.GOOGLE_API_KEY
        display_key = (
            current_key
            if current_key and current_key != "your_google_api_key_here"
            else ""
        )
        api_key = st.text_input(
            "Google API Key",
            value=display_key,
            type="password",
            placeholder="AIza...",
            help="Get free key: https://aistudio.google.com/app/apikey",
            key="api_key_input"
        )

        if st.button("Validate & Save Key", key="validate_key"):
            if api_key:
                with st.spinner("Validating..."):
                    result = validate_api_key(api_key)
                if result["valid"]:
                    Config.update_api_key(api_key)
                    st.session_state.api_key_valid = True
                    init_managers()
                    st.success("API key valid!")
                    st.rerun()
                else:
                    st.error(f"Invalid: {result['message']}")
            else:
                st.warning("Please enter an API key")

        if not st.session_state.api_key_valid:
            st.info(
                "Get FREE key: "
                "[aistudio.google.com](https://aistudio.google.com/app/apikey)"
            )
        else:
            st.success("API Key: Active")

        st.divider()

        # Document Upload
        st.markdown("### Upload Documents")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "txt", "md", "csv"],
            accept_multiple_files=True,
            key="file_uploader",
            help="Supports: PDF, DOCX, TXT, MD, CSV"
        )

        if uploaded_files:
            for f in uploaded_files:
                size = format_file_size(f.size)
                st.caption(f"📄 {f.name} ({size})")

        if uploaded_files and st.button(
            "Process Documents", key="process_btn"
        ):
            if not st.session_state.api_key_valid:
                st.error("Please validate API key first!")
            else:
                process_documents(uploaded_files)

        st.divider()

        # URL Input
        st.markdown("### Add URL")
        url_input = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            key="url_input"
        )
        if st.button("+ Add URL", key="add_url_btn"):
            if url_input and st.session_state.api_key_valid:
                process_url(url_input)
            elif not st.session_state.api_key_valid:
                st.error("Validate API key first!")
            else:
                st.warning("Enter a URL first")

        st.divider()

        # Knowledge Base Stats
        st.markdown("### Knowledge Base")
        stats = st.session_state.stats
        ready = st.session_state.vectorstore_ready
        status = "Ready" if ready else "Empty"
        color = "green" if ready else "gray"
        st.markdown(
            f"<span style='color:{color};font-weight:bold;'>"
            f"{status}</span>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", stats.get("total_documents", 0))
        with col2:
            st.metric("Chunks", stats.get("total_chunks", 0))

        st.caption(f"Storage: {stats.get('storage_size', '0 KB')}")

        if stats.get("indexed_files"):
            with st.expander("Indexed Files"):
                for f in stats["indexed_files"]:
                    st.caption(f"📄 {f}")

        if st.button("Clear Knowledge Base", key="clear_kb"):
            if st.session_state.embeddings_manager:
                st.session_state.embeddings_manager.delete_all()
                st.session_state.vectorstore_ready = False
                st.session_state.stats = {
                    "total_chunks": 0, "total_documents": 0,
                    "storage_size": "0 KB", "indexed_files": []
                }
                st.success("Cleared!")
                st.rerun()

        st.divider()

        # Clear Chat
        if st.button("Clear Chat History", key="clear_chat"):
            if st.session_state.memory_manager:
                st.session_state.memory_manager.clear_memory()
            st.session_state.messages = []
            st.success("Chat cleared!")
            st.rerun()


def process_documents(uploaded_files):
    """Process uploaded documents."""
    progress = st.progress(0)
    status = st.empty()

    try:
        processor = DocumentProcessor()
        all_docs = []

        status.text("Reading files...")
        progress.progress(20)

        for f in uploaded_files:
            docs = processor.load_uploaded_file(f)
            all_docs.extend(docs)

        if not all_docs:
            st.error("No text extracted from files!")
            return

        status.text("Chunking text...")
        progress.progress(50)
        chunks = processor.chunk_documents(all_docs)

        status.text("Creating embeddings...")
        progress.progress(75)
        st.session_state.embeddings_manager.create_vectorstore(chunks)

        status.text("Finalizing...")
        progress.progress(90)

        st.session_state.rag_chain.rebuild_chain()
        st.session_state.vectorstore_ready = True
        stats = (
            st.session_state.embeddings_manager.get_vectorstore_stats()
        )
        st.session_state.stats = stats

        progress.progress(100)
        status.text("Done!")

        st.success(
            f"Processed {len(uploaded_files)} files! "
            f"({len(chunks)} chunks created)"
        )
        st.rerun()

    except Exception as e:
        st.error(f"Processing failed: {e}")
        progress.empty()


def process_url(url: str):
    """Process URL content."""
    try:
        with st.spinner(f"Loading {url}..."):
            processor = DocumentProcessor()
            docs = processor.load_url(url)
            if not docs:
                st.error("Could not load URL content!")
                return
            chunks = processor.chunk_documents(docs)
            st.session_state.embeddings_manager.add_documents(chunks)
            st.session_state.rag_chain.rebuild_chain()
            st.session_state.vectorstore_ready = True
            stats = (
                st.session_state.embeddings_manager
                .get_vectorstore_stats()
            )
            st.session_state.stats = stats
            st.success(f"URL loaded! ({len(chunks)} chunks)")
            st.rerun()
    except Exception as e:
        st.error(f"URL processing failed: {e}")


def render_chat():
    """Render main chat interface."""
    # Header
    st.markdown("""
    <div class='main-header'>
        <h1>Personal Knowledge Brain</h1>
        <p>Chat with your documents using AI-powered RAG</p>
    </div>
    """, unsafe_allow_html=True)

    # Status bar
    stats = st.session_state.stats
    api_ok = "API" if st.session_state.api_key_valid else "No API"
    docs = stats.get("total_documents", 0)
    chunks = stats.get("total_chunks", 0)
    ready = "Ready" if st.session_state.vectorstore_ready else "Not Ready"

    st.markdown(
        f"<div class='status-bar'>"
        f"{api_ok} | "
        f"Documents: {docs} | "
        f"Chunks: {chunks} | "
        f"{ready}"
        f"</div>",
        unsafe_allow_html=True
    )

    # Welcome screen
    if not st.session_state.vectorstore_ready:
        st.markdown("### Get Started")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(
                "**Step 1**\\n\\n"
                "Get free API key at "
                "[aistudio.google.com](https://aistudio.google.com/app/apikey)"
            )
        with col2:
            st.info(
                "**Step 2**\\n\\n"
                "Upload documents in the sidebar\\n\\n"
                "PDF, DOCX, TXT, MD, CSV"
            )
        with col3:
            st.info(
                "**Step 3**\\n\\n"
                "Ask anything about your documents!"
            )
        return

    # Chat messages
    messages = st.session_state.messages
    if not messages:
        st.info(
            "Knowledge base is ready! Ask anything about your documents."
        )

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        timestamp = msg.get("timestamp", "")

        if role == "user":
            st.markdown(
                f"<div class='chat-user'>"
                f"<b>You</b> <small>{timestamp}</small>"
                f"<br>{content}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='chat-ai'>"
                f"<b>AI</b> <small>{timestamp}</small>"
                f"<br>{content}</div>",
                unsafe_allow_html=True
            )
            if sources:
                with st.expander(f"Sources ({len(sources)})"):
                    for src in sources:
                        st.markdown(
                            f"<div class='source-card'>"
                            f"<b>{src.get('filename','Unknown')}</b>"
                            f" | Page: {src.get('page','N/A')}<br>"
                            f"<small>{src.get('preview','')}</small>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

    # Chat input
    if st.session_state.vectorstore_ready:
        question = st.chat_input(
            "Ask anything about your documents...",
            key="chat_input"
        )
        if question:
            handle_question(question)
    else:
        st.chat_input(
            "Upload documents first...",
            disabled=True,
            key="chat_disabled"
        )


def handle_question(question: str):
    """Handle user question and get AI response."""
    # Add user message
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "sources": [],
        "timestamp": timestamp,
    })
    st.session_state.memory_manager.add_message("user", question)

    # Get AI response
    with st.spinner("Searching knowledge base..."):
        try:
            result = st.session_state.rag_chain.get_response(question)
            answer = result.get("answer", "No response generated")
            sources = result.get("sources", [])

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "timestamp": timestamp,
            })
            st.session_state.memory_manager.add_message("assistant", answer, sources)
            st.rerun()
        except Exception as e:
            st.error(f"Error generating response: {e}")


if __name__ == "__main__":
    # Initialize app
    init_session_state()
    if st.session_state.api_key_valid and not st.session_state.embeddings_manager:
        init_managers()
    render_sidebar()
    render_chat()
''')

print("\n✅ ALL FILES CREATED SUCCESSFULLY!")
