
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
            separators=["\n\n", "\n", ". ", " ", ""],
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
            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
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
