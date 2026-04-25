"""
Tests for the EmbeddingsManager module.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.embeddings_manager import EmbeddingsManager


class TestEmbeddingsManager:
    """Test suite for EmbeddingsManager."""

    @patch("src.embeddings_manager.GoogleGenerativeAIEmbeddings")
    @patch("src.embeddings_manager.Chroma")
    def test_vectorstore_creation(self, mock_chroma, mock_embeddings, tmp_path):
        """Test ChromaDB initialization."""
        mock_embed_instance = MagicMock()
        mock_embeddings.return_value = mock_embed_instance
        mock_chroma.return_value = MagicMock()

        manager = EmbeddingsManager(
            google_api_key="test_key_12345678901234567890",
            vector_store_path=str(tmp_path / "vectorstore"),
        )
        assert manager.embeddings is not None
        assert manager.vector_store_path.exists()

    @patch("src.embeddings_manager.GoogleGenerativeAIEmbeddings")
    @patch("src.embeddings_manager.Chroma")
    def test_get_stats(self, mock_chroma, mock_embeddings, tmp_path):
        """Test statistics return format."""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance._collection.count.return_value = 10
        mock_chroma_instance._collection.get.return_value = {
            "metadatas": [
                {"source": "doc1.pdf"},
                {"source": "doc1.pdf"},
                {"source": "doc2.txt"},
            ]
        }
        mock_chroma.return_value = mock_chroma_instance

        manager = EmbeddingsManager(
            google_api_key="test_key_12345678901234567890",
            vector_store_path=str(tmp_path / "vectorstore"),
        )
        stats = manager.get_vectorstore_stats()
        assert "total_chunks" in stats
        assert "total_documents" in stats
        assert "storage_size" in stats
        assert "indexed_files" in stats

    @patch("src.embeddings_manager.GoogleGenerativeAIEmbeddings")
    @patch("src.embeddings_manager.Chroma")
    def test_vectorstore_exists(self, mock_chroma, mock_embeddings, tmp_path):
        """Test detection logic."""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance._collection.count.return_value = 5
        mock_chroma.return_value = mock_chroma_instance

        manager = EmbeddingsManager(
            google_api_key="test_key_12345678901234567890",
            vector_store_path=str(tmp_path / "vectorstore"),
        )
        assert manager.vectorstore_exists() is True

        mock_chroma_instance._collection.count.return_value = 0
        assert manager.vectorstore_exists() is False

    @patch("src.embeddings_manager.GoogleGenerativeAIEmbeddings")
    @patch("src.embeddings_manager.Chroma")
    def test_reset_vectorstore(self, mock_chroma, mock_embeddings, tmp_path):
        """Test vectorstore reset."""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance._collection.get.return_value = {"ids": ["1", "2"]}
        mock_chroma.return_value = mock_chroma_instance

        manager = EmbeddingsManager(
            google_api_key="test_key_12345678901234567890",
            vector_store_path=str(tmp_path / "vectorstore"),
        )
        result = manager.reset_vectorstore()
        assert result is True
