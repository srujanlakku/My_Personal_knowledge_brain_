
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
