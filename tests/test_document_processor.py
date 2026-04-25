"""
Tests for the DocumentProcessor module.
"""
import os
import tempfile
from pathlib import Path

import pytest

from src.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""

    @pytest.fixture
    def processor(self):
        """Create a DocumentProcessor fixture."""
        return DocumentProcessor(chunk_size=100, chunk_overlap=20)

    def test_load_txt_basic(self, processor, tmp_path):
        """Test loading a simple text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world\nThis is a test.\n", encoding="utf-8")

        docs = processor.load_txt(str(test_file))
        assert len(docs) == 1
        assert "Hello world" in docs[0].page_content
        assert docs[0].metadata["file_type"] == "txt"

    def test_load_txt_encoding(self, processor, tmp_path):
        """Test loading files with different encodings."""
        # UTF-8 file
        utf8_file = tmp_path / "utf8.txt"
        utf8_file.write_text("Hello UTF-8: café", encoding="utf-8")
        docs = processor.load_txt(str(utf8_file))
        assert len(docs) == 1
        assert "café" in docs[0].page_content

        # Latin-1 file
        latin_file = tmp_path / "latin.txt"
        latin_file.write_text("Hello Latin: café", encoding="latin-1")
        docs = processor.load_txt(str(latin_file))
        assert len(docs) == 1

    def test_chunk_documents(self, processor):
        """Verify chunk sizes and overlap."""
        from langchain.schema import Document

        long_text = "Word " * 500
        docs = [Document(page_content=long_text, metadata={"source": "test"})]
        chunks = processor.chunk_documents(docs)

        assert len(chunks) > 1
        assert all(len(c.page_content) <= processor.chunk_size + 50 for c in chunks)
        for chunk in chunks:
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata

    def test_validate_file_size(self, processor, tmp_path):
        """Test file size limits."""
        # Create a file under the limit
        small_file = tmp_path / "small.txt"
        small_file.write_text("Small content")
        info = small_file.stat()
        assert info.st_size < processor.max_file_size_bytes

        # The processor should skip files over limit during folder scan
        # (not directly tested here as it's handled in process_all_documents)

    def test_supported_extensions(self, processor):
        """Test file type detection."""
        assert ".pdf" in processor.supported_extensions
        assert ".docx" in processor.supported_extensions
        assert ".txt" in processor.supported_extensions
        assert ".md" in processor.supported_extensions
        assert ".csv" in processor.supported_extensions
        assert ".exe" not in processor.supported_extensions

    def test_load_markdown(self, processor, tmp_path):
        """Test loading a markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Header 1\n\nSome content\n\n## Header 2\n\nMore content\n",
            encoding="utf-8",
        )
        docs = processor.load_markdown(str(md_file))
        assert len(docs) == 1
        assert docs[0].metadata["section_count"] == 2
        assert docs[0].metadata["file_type"] == "md"

    def test_load_csv(self, processor, tmp_path):
        """Test loading a CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
        docs = processor.load_csv(str(csv_file))
        assert len(docs) == 1
        assert "Alice" in docs[0].page_content
        assert "Bob" in docs[0].page_content
        assert docs[0].metadata["row_count"] == 2

    def test_empty_file(self, processor, tmp_path):
        """Test handling empty files."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")
        docs = processor.load_txt(str(empty_file))
        assert len(docs) == 1
        assert docs[0].page_content == ""
