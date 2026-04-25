from pathlib import Path

def w(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    size = len(content.encode('utf-8'))
    print(f'Written: {path} ({size} bytes)')

for d in ['.streamlit','documents','vectorstore',
          'src','tests','logs','sessions']:
    Path(d).mkdir(parents=True, exist_ok=True)
print('Directories ready!')
print()

# FILE 1: config.py
w('config.py', '''
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
                lines = content.split("\\n")
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
                    "\\n".join(updated), encoding="utf-8"
                )
        except Exception as e:
            print(f"Warning: {e}")
        os.environ["GOOGLE_API_KEY"] = api_key
        cls.GOOGLE_API_KEY = api_key


config = Config()
config.create_directories()
''')

# FILE 2: src/__init__.py
w('src/__init__.py', '# Personal Knowledge Brain\n')

# FILE 3: src/utils.py
w('src/utils.py', '''
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
    text = text.replace("\\x00", "")
    text = re.sub(
        r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text
    )
    text = re.sub(r"\\n{4,}", "\\n\\n\\n", text)
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
''')

# FILE 4: src/embeddings_manager.py
w('src/embeddings_manager.py', '''
import os
from pathlib import Path
from typing import List, Optional
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import chromadb
from config import Config


class EmbeddingsManager:
    """
    Embeddings manager using text-embedding-004.

    Compatible versions:
    - langchain-google-genai 4.2.2
    - google-genai 1.73.1
    - chromadb 1.5.8
    - langchain-chroma 1.1.0
    - langchain 1.2.15

    google-generativeai must be UNINSTALLED.
    Run: pip uninstall google-generativeai -y
    """

    COLLECTION_NAME = "knowledge_brain"
    EMBEDDING_MODEL = "text-embedding-004"
    BATCH_SIZE = 50

    def __init__(self):
        self._embeddings: Optional[
            GoogleGenerativeAIEmbeddings
        ] = None
        self._vectorstore: Optional[Chroma] = None
        self._client: Optional[chromadb.PersistentClient] = None
        self._ready: bool = False
        self._initialize()

    def _initialize(self) -> None:
        api_key = Config.GOOGLE_API_KEY
        if not api_key or api_key in [
            "", "your_google_api_key_here"
        ]:
            logger.warning("No API key. Waiting for user.")
            return
        if not api_key.startswith("AIza"):
            logger.error("Invalid API key format!")
            return
        try:
            self._setup_embeddings(api_key)
            self._setup_chromadb()
            self._load_existing()
            self._ready = True
            logger.info("EmbeddingsManager ready!")
        except Exception as e:
            self._ready = False
            logger.error(f"Init failed: {e}")
            raise

    def _setup_embeddings(self, api_key: str) -> None:
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=self.EMBEDDING_MODEL,
            google_api_key=api_key,
            task_type="retrieval_document",
        )
        test = self._embeddings.embed_query("init test")
        if not test:
            raise ValueError("Embedding test failed!")
        logger.info(
            f"Embeddings ready! "
            f"Model={self.EMBEDDING_MODEL} Dims={len(test)}"
        )

    def _setup_chromadb(self) -> None:
        Path(Config.VECTOR_STORE_PATH).mkdir(
            parents=True, exist_ok=True
        )
        self._client = chromadb.PersistentClient(
            path=Config.VECTOR_STORE_PATH
        )
        logger.info("ChromaDB ready!")

    def _load_existing(self) -> None:
        if self.vectorstore_exists():
            self._vectorstore = Chroma(
                client=self._client,
                collection_name=self.COLLECTION_NAME,
                embedding_function=self._embeddings,
            )
            count = self._vectorstore._collection.count()
            logger.info(f"Loaded vectorstore: {count} chunks")

    def reinitialize(self, api_key: str) -> None:
        Config.update_api_key(api_key)
        self._embeddings = None
        self._vectorstore = None
        self._client = None
        self._ready = False
        self._initialize()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=30),
    )
    def create_vectorstore(
        self, documents: List[Document]
    ) -> Chroma:
        if not documents:
            raise ValueError("No documents!")
        if not self._embeddings:
            raise RuntimeError("Not initialized!")
        try:
            self._client.delete_collection(
                self.COLLECTION_NAME
            )
        except Exception:
            pass
        batches = chunk_list(documents, self.BATCH_SIZE)
        self._vectorstore = Chroma.from_documents(
            documents=batches[0],
            embedding=self._embeddings,
            client=self._client,
            collection_name=self.COLLECTION_NAME,
        )
        for i, batch in enumerate(batches[1:], 2):
            self._vectorstore.add_documents(batch)
            logger.info(
                f"Batch {i}/{len(batches)} embedded!"
            )
        count = self._vectorstore._collection.count()
        logger.info(f"Vectorstore done: {count} chunks!")
        return self._vectorstore

    def add_documents(
        self, documents: List[Document]
    ) -> int:
        if not documents:
            return 0
        if self._vectorstore is None:
            self.create_vectorstore(documents)
            return len(documents)
        self._vectorstore.add_documents(documents)
        return len(documents)

    def get_retriever(self, k: int = None):
        if self._vectorstore is None:
            return None
        k = k or Config.MAX_RETRIEVAL_DOCS
        return self._vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def get_vectorstore_stats(self) -> dict:
        empty = {
            "total_chunks": 0,
            "total_documents": 0,
            "storage_size": "0 KB",
            "indexed_files": [],
        }
        if self._vectorstore is None:
            return empty
        try:
            col = self._vectorstore._collection
            total = col.count()
            results = col.get(include=["metadatas"])
            sources = list(set(
                m.get(
                    "filename",
                    m.get("source", "Unknown")
                )
                for m in results.get("metadatas", [])
                if m
            ))
            return {
                "total_chunks": total,
                "total_documents": len(sources),
                "storage_size": self._get_size(),
                "indexed_files": sorted(sources),
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return empty

    def vectorstore_exists(self) -> bool:
        if not self._client:
            return False
        try:
            cols = self._client.list_collections()
            names = [c.name for c in cols]
            if self.COLLECTION_NAME in names:
                col = self._client.get_collection(
                    self.COLLECTION_NAME
                )
                return col.count() > 0
            return False
        except Exception:
            return False

    def delete_all(self) -> bool:
        try:
            if self._client:
                self._client.delete_collection(
                    self.COLLECTION_NAME
                )
            self._vectorstore = None
            logger.info("Vectorstore deleted!")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def is_ready(self) -> bool:
        return self._ready and self._embeddings is not None

    def _get_size(self) -> str:
        path = Path(Config.VECTOR_STORE_PATH)
        if not path.exists():
            return "0 KB"
        size = sum(
            f.stat().st_size
            for f in path.rglob("*")
            if f.is_file()
        )
        if size < 1024 ** 2:
            return f"{size/1024:.1f} KB"
        return f"{size/1024**2:.1f} MB"


def chunk_list(lst: list, size: int):
    return [lst[i:i+size] for i in range(0, len(lst), size)]
''')

# FILE 5: src/memory_manager.py
w('src/memory_manager.py', '''
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from loguru import logger
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
)
from langchain_core.messages import HumanMessage, AIMessage
from config import Config


class MemoryManager:

    def __init__(self):
        self._history = ChatMessageHistory()
        self._messages: List[dict] = []
        self._last_user_msg: str = ""
        self._db_path = (
            Path(Config.SESSIONS_PATH) / "chat_history.db"
        )
        self._init_db()

    def _init_db(self) -> None:
        Path(Config.SESSIONS_PATH).mkdir(
            parents=True, exist_ok=True
        )
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
        sources: List[dict] = None,
    ) -> None:
        ts = datetime.now().strftime("%H:%M")
        self._messages.append({
            "role": role,
            "content": content,
            "sources": sources or [],
            "timestamp": ts,
        })
        if role == "user":
            self._last_user_msg = content
            self._history.add_user_message(content)
        elif role == "assistant":
            self._history.add_ai_message(content)

    def get_history_messages(self) -> list:
        return self._history.messages

    def get_display_messages(self) -> List[dict]:
        return self._messages

    def clear_memory(self) -> None:
        self._history.clear()
        self._messages = []
        self._last_user_msg = ""

    def get_message_count(self) -> int:
        return len(self._messages)

    def save_session(self, name: str) -> str:
        sid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT INTO sessions VALUES (?,?,?)",
            (sid, name, now),
        )
        for msg in self._messages:
            conn.execute(
                "INSERT INTO messages "
                "(session_id,role,content,sources,timestamp)"
                " VALUES (?,?,?,?,?)",
                (
                    sid,
                    msg["role"],
                    msg["content"],
                    json.dumps(msg.get("sources", [])),
                    msg.get("timestamp", now),
                ),
            )
        conn.commit()
        conn.close()
        return sid

    def get_all_sessions(self) -> List[dict]:
        try:
            conn = sqlite3.connect(str(self._db_path))
            cur = conn.execute(
                "SELECT id,name,created_at FROM sessions "
                "ORDER BY created_at DESC"
            )
            sessions = [
                {"id": r[0], "name": r[1], "created": r[2]}
                for r in cur.fetchall()
            ]
            conn.close()
            return sessions
        except Exception:
            return []
''')

# FILE 6: src/rag_chain.py
w('src/rag_chain.py', '''
from typing import List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
)
from langchain_core.messages import HumanMessage, AIMessage
from config import Config


class RAGChain:
    """LCEL RAG chain. Compatible with langchain 1.2.15."""

    def __init__(self, embeddings_manager, memory_manager):
        self.em = embeddings_manager
        self.mm = memory_manager
        self._llm = None
        self._chain = None
        self._retriever = None
        self._initialize()

    def _initialize(self) -> None:
        key = Config.GOOGLE_API_KEY
        if not key or key == "your_google_api_key_here":
            return
        try:
            self._llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                google_api_key=key,
                temperature=Config.TEMPERATURE,
                max_output_tokens=Config.MAX_OUTPUT_TOKENS,
                convert_system_message_to_human=True,
            )
            self._retriever = self.em.get_retriever()
            if self._retriever:
                self._chain = self._build_chain()
                logger.info("RAG chain ready!")
        except Exception as e:
            logger.error(f"RAG init failed: {e}")

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a personal knowledge assistant.\\n"
                "Answer ONLY using the context below.\\n"
                "Always cite: [filename, Page X]\\n"
                "If not found say: "
                "I could not find this in your documents.\\n\\n"
                "Context:\\n{context}"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ])

        def retrieve(inputs: dict) -> dict:
            docs = self._retriever.invoke(
                inputs["question"]
            )
            parts = []
            for d in docs:
                fn = d.metadata.get(
                    "filename",
                    d.metadata.get("source", "Unknown")
                )
                pg = d.metadata.get("page", "N/A")
                parts.append(
                    f"[{fn} Page {pg}]\\n{d.page_content}"
                )
            inputs["context"] = "\\n\\n".join(parts)
            inputs["_docs"] = docs
            return inputs

        chain = (
            RunnableLambda(retrieve)
            | RunnablePassthrough.assign(
                answer=(
                    RunnableLambda(
                        lambda x: {
                            "context": x["context"],
                            "chat_history": x.get(
                                "chat_history", []
                            ),
                            "question": x["question"],
                        }
                    )
                    | prompt
                    | self._llm
                    | StrOutputParser()
                )
            )
        )
        return chain

    def rebuild_chain(self) -> None:
        self._retriever = self.em.get_retriever()
        if self._retriever and self._llm:
            self._chain = self._build_chain()
            logger.info("Chain rebuilt!")

    def reinitialize(self) -> None:
        self._llm = None
        self._chain = None
        self._retriever = None
        self._initialize()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
    )
    def get_response(self, question: str) -> dict:
        if not question or not question.strip():
            return {
                "answer": "Please enter a question.",
                "sources": [],
                "error": True,
            }
        if self._chain is None:
            return {
                "answer": (
                    "Please upload documents first!"
                ),
                "sources": [],
                "error": True,
            }
        try:
            history = []
            for m in self.mm.get_history_messages():
                if isinstance(m, HumanMessage):
                    history.append(
                        HumanMessage(content=m.content)
                    )
                elif isinstance(m, AIMessage):
                    history.append(
                        AIMessage(content=m.content)
                    )
            history = history[-10:]
            result = self._chain.invoke({
                "question": question,
                "chat_history": history,
            })
            answer = result.get("answer", "No answer")
            docs = result.get("_docs", [])
            return {
                "answer": answer,
                "sources": self._fmt(docs),
                "error": False,
            }
        except Exception as e:
            logger.error(f"Response error: {e}")
            err = str(e)
            if "API Key" in err or "INVALID_ARGUMENT" in err:
                return {
                    "answer": (
                        "API key error. "
                        "Re-enter your key in the sidebar."
                    ),
                    "sources": [],
                    "error": True,
                }
            return {
                "answer": f"Error: {err[:200]}",
                "sources": [],
                "error": True,
            }

    def _fmt(self, docs: List[Document]) -> List[dict]:
        seen, out = set(), []
        for d in docs:
            m = d.metadata
            fn = m.get("filename", m.get("source", "?"))
            pg = m.get("page", "N/A")
            k = f"{fn}_{pg}"
            if k not in seen:
                seen.add(k)
                out.append({
                    "filename": fn,
                    "page": pg,
                    "preview": d.page_content[:200] + "...",
                    "file_type": m.get("file_type", "doc"),
                })
        return out
''')

# FILE 7: src/document_processor.py
w('src/document_processor.py', '''
import os
import re
from pathlib import Path
from typing import List
import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config
from src.utils import sanitize_text


class DocumentProcessor:

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\\n\\n", "\\n", ". ", " ", ""],
        )

    def load_pdf(self, fp: str) -> List[Document]:
        docs = []
        try:
            import fitz
            doc = fitz.open(fp)
            for i in range(len(doc)):
                text = doc[i].get_text()
                if text.strip():
                    docs.append(Document(
                        page_content=sanitize_text(text),
                        metadata={
                            "source": fp,
                            "filename": Path(fp).name,
                            "page": i + 1,
                            "total_pages": len(doc),
                            "file_type": "pdf",
                        },
                    ))
            doc.close()
        except Exception:
            try:
                import PyPDF2
                with open(fp, "rb") as f:
                    r = PyPDF2.PdfReader(f)
                    for i, pg in enumerate(r.pages):
                        text = pg.extract_text() or ""
                        if text.strip():
                            docs.append(Document(
                                page_content=sanitize_text(text),
                                metadata={
                                    "source": fp,
                                    "filename": Path(fp).name,
                                    "page": i + 1,
                                    "total_pages": len(r.pages),
                                    "file_type": "pdf",
                                },
                            ))
            except Exception as e:
                logger.error(f"PDF failed: {e}")
        return docs

    def load_docx(self, fp: str) -> List[Document]:
        try:
            import docx2txt
            text = docx2txt.process(fp)
            if text.strip():
                return [Document(
                    page_content=sanitize_text(text),
                    metadata={
                        "source": fp,
                        "filename": Path(fp).name,
                        "file_type": "docx",
                    },
                )]
        except Exception as e:
            logger.error(f"DOCX failed: {e}")
        return []

    def load_txt(self, fp: str) -> List[Document]:
        for enc in ["utf-8", "latin-1", "cp1252", "ascii"]:
            try:
                with open(fp, "r", encoding=enc) as f:
                    text = f.read()
                return [Document(
                    page_content=sanitize_text(text),
                    metadata={
                        "source": fp,
                        "filename": Path(fp).name,
                        "file_type": "txt",
                    },
                )]
            except Exception:
                continue
        return []

    def load_markdown(self, fp: str) -> List[Document]:
        return self.load_txt(fp)

    def load_csv(self, fp: str) -> List[Document]:
        try:
            df = pd.read_csv(fp, encoding="utf-8")
            docs = []
            for i, row in df.iterrows():
                text = " | ".join([
                    f"{c}: {v}"
                    for c, v in row.items() if pd.notna(v)
                ])
                docs.append(Document(
                    page_content=sanitize_text(text),
                    metadata={
                        "source": fp,
                        "filename": Path(fp).name,
                        "file_type": "csv",
                        "row": i + 1,
                    },
                ))
            return docs
        except Exception as e:
            logger.error(f"CSV failed: {e}")
            return []

    def load_url(self, url: str) -> List[Document]:
        try:
            h = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=h, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            for t in soup(["script","style","nav","footer"]):
                t.decompose()
            text = soup.get_text(separator="\\n", strip=True)
            text = re.sub(r"\\n{3,}", "\\n\\n", text)
            return [Document(
                page_content=sanitize_text(text),
                metadata={
                    "source": url,
                    "filename": url,
                    "file_type": "url",
                },
            )]
        except Exception as e:
            logger.error(f"URL failed: {e}")
            return []

    def load_uploaded_file(self, uf) -> List[Document]:
        try:
            save = Path(Config.DOCUMENTS_PATH) / uf.name
            with open(save, "wb") as f:
                f.write(uf.getbuffer())
            return self._route(str(save))
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return []

    def chunk_documents(
        self, docs: List[Document]
    ) -> List[Document]:
        if not docs:
            return []
        chunks = self.splitter.split_documents(docs)
        for i, c in enumerate(chunks):
            c.metadata["chunk_index"] = i
            c.metadata["total_chunks"] = len(chunks)
        return chunks

    def _route(self, fp: str) -> List[Document]:
        ext = Path(fp).suffix.lower()
        m = {
            ".pdf": self.load_pdf,
            ".docx": self.load_docx,
            ".doc": self.load_docx,
            ".txt": self.load_txt,
            ".md": self.load_markdown,
            ".csv": self.load_csv,
        }
        fn = m.get(ext)
        return fn(fp) if fn else []
''')

# FILE 8: app.py
w('app.py', '''
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(override=True)

st.set_page_config(
    page_title="Personal Knowledge Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from config import Config
    from src.utils import validate_api_key, format_file_size
    from src.document_processor import DocumentProcessor
    from src.embeddings_manager import EmbeddingsManager
    from src.rag_chain import RAGChain
    from src.memory_manager import MemoryManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.code("pip install -r requirements.txt")
    st.stop()

st.markdown("""<style>
.hdr{background:linear-gradient(135deg,#6C63FF,#3B82F6);
padding:1.5rem;border-radius:12px;text-align:center;
color:white;margin-bottom:1rem;}
.umsg{background:linear-gradient(135deg,#6C63FF,#8B5CF6);
color:white;padding:1rem;border-radius:12px;margin:.5rem 0;}
.amsg{background:#1E1E2E;border:1px solid #6C63FF;
color:#FAFAFA;padding:1rem;border-radius:12px;margin:.5rem 0;}
.src{background:#262640;border-left:3px solid #6C63FF;
padding:.5rem;border-radius:6px;margin:.3rem 0;
font-size:.85rem;}
</style>""", unsafe_allow_html=True)


def init_session():
    defs = {
        "messages": [],
        "rag_chain": None,
        "embeddings_manager": None,
        "memory_manager": None,
        "vectorstore_ready": False,
        "api_key_valid": False,
        "stats": {
            "total_chunks": 0,
            "total_documents": 0,
            "storage_size": "0 KB",
            "indexed_files": [],
        },
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v


def init_managers():
    try:
        if st.session_state.memory_manager is None:
            st.session_state.memory_manager = MemoryManager()
        em = EmbeddingsManager()
        st.session_state.embeddings_manager = em
        st.session_state.rag_chain = RAGChain(
            em, st.session_state.memory_manager
        )
        if em.vectorstore_exists():
            st.session_state.vectorstore_ready = True
            st.session_state.stats = em.get_vectorstore_stats()
        return True
    except Exception as e:
        st.error(f"Init error: {e}")
        return False


init_session()

with st.sidebar:
    st.markdown("## 🧠 Knowledge Brain")
    st.caption("Personal RAG Assistant v3.0")
    st.divider()

    st.markdown("### 🔑 API Key")
    cur = Config.GOOGLE_API_KEY
    disp = (
        cur
        if (cur and cur != "your_google_api_key_here"
            and not cur.startswith(chr(34)))
        else ""
    )
    api_key = st.text_input(
        "Google API Key",
        value=disp,
        type="password",
        placeholder="AIzaSy...",
        key="api_input",
        help="Get FREE key: https://aistudio.google.com/app/apikey",
    )

    if st.button("Validate and Save", key="vbtn"):
        if not api_key:
            st.warning("Enter your API key first!")
        elif not api_key.startswith("AIza"):
            st.error("Key must start with AIza!")
        elif len(api_key) < 35:
            st.error("Key too short! Copy the full key.")
        else:
            with st.spinner("Validating..."):
                result = validate_api_key(api_key)
            if result["valid"]:
                Config.update_api_key(api_key)
                st.session_state.api_key_valid = True
                with st.spinner("Initializing AI..."):
                    init_managers()
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])

    if st.session_state.api_key_valid:
        st.success("API Key Active")
    else:
        st.info(
            "[Get FREE API Key](https://aistudio.google.com/app/apikey)"
        )

    st.divider()
    st.markdown("### Upload Documents")
    ups = st.file_uploader(
        "Choose files",
        type=["pdf","docx","txt","md","csv"],
        accept_multiple_files=True,
        key="uploader",
    )
    if ups:
        for f in ups:
            st.caption(
                f"📄 {f.name} ({format_file_size(f.size)})"
            )

    if ups and st.button("Process Documents", key="pbtn"):
        if not st.session_state.api_key_valid:
            st.error("Validate API key first!")
        else:
            prog = st.progress(0)
            stat = st.empty()
            try:
                p = DocumentProcessor()
                all_docs = []
                stat.text("Reading files...")
                prog.progress(15)
                for f in ups:
                    docs = p.load_uploaded_file(f)
                    all_docs.extend(docs)
                if not all_docs:
                    st.error("No text extracted!")
                else:
                    stat.text("Chunking...")
                    prog.progress(40)
                    chunks = p.chunk_documents(all_docs)
                    stat.text("Embedding...")
                    prog.progress(70)
                    em = st.session_state.embeddings_manager
                    em.create_vectorstore(chunks)
                    stat.text("Building chain...")
                    prog.progress(90)
                    st.session_state.rag_chain.rebuild_chain()
                    st.session_state.vectorstore_ready = True
                    st.session_state.stats = (
                        em.get_vectorstore_stats()
                    )
                    prog.progress(100)
                    stat.text("Done!")
                    st.success(
                        f"Processed {len(ups)} files! "
                        f"({len(chunks)} chunks)"
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.markdown("### Knowledge Base")
    s = st.session_state.stats
    if st.session_state.vectorstore_ready:
        st.success("Ready")
    else:
        st.info("No documents yet")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Docs", s.get("total_documents", 0))
    with c2:
        st.metric("Chunks", s.get("total_chunks", 0))
    st.caption(f"Size: {s.get('storage_size','0 KB')}")
    if s.get("indexed_files"):
        with st.expander("Files"):
            for f in s["indexed_files"]:
                st.caption(f"📄 {f}")
    if st.button("Clear Knowledge Base", key="ckb"):
        em = st.session_state.embeddings_manager
        if em:
            em.delete_all()
        st.session_state.vectorstore_ready = False
        st.session_state.stats = {
            "total_chunks": 0,
            "total_documents": 0,
            "storage_size": "0 KB",
            "indexed_files": [],
        }
        st.rerun()
    st.divider()
    if st.button("Clear Chat", key="cc"):
        if st.session_state.memory_manager:
            st.session_state.memory_manager.clear_memory()
        st.session_state.messages = []
        st.rerun()

st.markdown("""
<div class=\'hdr\'>
<h1>🧠 Personal Knowledge Brain</h1>
<p>Chat with your documents using AI-powered RAG</p>
</div>
""", unsafe_allow_html=True)

s = st.session_state.stats
ak = "API Active" if st.session_state.api_key_valid else "No API Key"
nd = s.get("total_documents", 0)
nc = s.get("total_chunks", 0)
rdy = "Ready" if st.session_state.vectorstore_ready else "Upload Docs"
st.info(f"{ak}  |  Docs: {nd}  |  Chunks: {nc}  |  {rdy}")

if not st.session_state.vectorstore_ready:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(
            "**Step 1**\\n\\n"
            "[Get FREE API Key](https://aistudio.google.com/app/apikey)"
        )
    with c2:
        st.info("**Step 2**\\n\\nUpload PDF DOCX TXT CSV in sidebar")
    with c3:
        st.info("**Step 3**\\n\\nAsk anything about your documents!")
else:
    msgs = st.session_state.messages
    if not msgs:
        st.info("Knowledge base ready! Ask anything below.")
    for msg in msgs:
        role = msg.get("role","user")
        content = msg.get("content","")
        ts = msg.get("timestamp","")
        srcs = msg.get("sources",[])
        if role == "user":
            st.markdown(
                f"<div class=\'umsg\'>"
                f"<b>You</b> <small>{ts}</small>"
                f"<br>{content}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class=\'amsg\'>"
                f"<b>AI</b> <small>{ts}</small>"
                f"<br>{content}</div>",
                unsafe_allow_html=True,
            )
            if srcs:
                with st.expander(f"Sources ({len(srcs)})"):
                    for src in srcs:
                        st.markdown(
                            f"<div class=\'src\'>"
                            f"<b>{src.get(\'filename\',\'?\')}"
                            f"</b> Page:{src.get(\'page\',\'?\')}"
                            f"<br><small>"
                            f"{src.get(\'preview\',\'\')[:150]}"
                            f"</small></div>",
                            unsafe_allow_html=True,
                        )
    q = st.chat_input("Ask anything about your documents...")
    if q:
        ts = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": q,
            "sources": [],
            "timestamp": ts,
        })
        st.session_state.memory_manager.add_message("user", q)
        with st.spinner("Searching knowledge base..."):
            try:
                res = st.session_state.rag_chain.get_response(q)
                ans = res.get("answer","No response")
                srcs = res.get("sources",[])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ans,
                    "sources": srcs,
                    "timestamp": ts,
                })
                st.session_state.memory_manager.add_message(
                    "assistant", ans, srcs
                )
            except Exception as e:
                st.error(f"Error: {e}")
        st.rerun()
''')

print()
print("="*50)
print("ALL FILES WRITTEN SUCCESSFULLY!")
print("="*50)