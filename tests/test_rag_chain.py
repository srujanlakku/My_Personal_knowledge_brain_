"""
Tests for the RAGChain module.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.rag_chain import RAGChain


class TestRAGChain:
    """Test suite for RAGChain."""

    def _create_rag(self, mock_llm_class):
        """Helper to create a RAGChain with mocked dependencies."""
        mock_embeddings = MagicMock()
        mock_retriever = MagicMock()
        mock_embeddings.get_retriever.return_value = mock_retriever
        mock_memory = MagicMock()
        mock_memory.get_chat_history.return_value = []
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(content="Test answer")
        mock_llm_class.return_value = mock_llm_instance

        rag = RAGChain(
            embeddings_manager=mock_embeddings,
            memory_manager=mock_memory,
            google_api_key="test_key_12345678901234567890",
        )
        return rag, mock_embeddings, mock_memory, mock_retriever

    @patch("src.rag_chain.ChatGoogleGenerativeAI")
    def test_validate_question(self, mock_llm):
        """Test question validation."""
        rag, _, _, _ = self._create_rag(mock_llm)

        # Empty question
        result = rag.validate_question("")
        assert result["valid"] is False
        assert "enter a question" in result["message"].lower()

        # Valid question
        result = rag.validate_question("What is AI?")
        assert result["valid"] is True

        # Too long
        result = rag.validate_question("x" * 600)
        assert result["valid"] is False
        assert "too long" in result["message"].lower()

    @patch("src.rag_chain.ChatGoogleGenerativeAI")
    def test_format_sources(self, mock_llm):
        """Test source formatting."""
        from langchain.schema import Document

        rag, _, _, _ = self._create_rag(mock_llm)

        docs = [
            Document(
                page_content="Test content one",
                metadata={"source": "doc1.pdf", "page": 1, "file_type": "pdf"},
            ),
            Document(
                page_content="Test content two",
                metadata={"source": "doc1.pdf", "page": 2, "file_type": "pdf"},
            ),
            Document(
                page_content="Another doc",
                metadata={"source": "doc2.txt", "page": 1, "file_type": "txt"},
            ),
        ]

        formatted = rag.format_sources(docs)
        assert len(formatted) == 2  # doc1 deduplicated
        assert formatted[0]["name"] == "doc1.pdf"
        assert formatted[1]["name"] == "doc2.txt"
        assert "preview" in formatted[0]

    @patch("src.rag_chain.ChatGoogleGenerativeAI")
    def test_empty_question_handling(self, mock_llm):
        """Test empty input handling."""
        rag, _, _, _ = self._create_rag(mock_llm)

        response = rag.get_response("")
        assert "answer" in response
        assert response["sources"] == []
        assert response["tokens_used"] == 0
