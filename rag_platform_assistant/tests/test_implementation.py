import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from src.document_loader import SocialMediaDocumentLoader
from src.vector_store import SocialMediaVectorStore
from src.rag_chain import SocialMediaRAGChain


@pytest.fixture
def sample_doc():
    return Document(page_content="Test content about password reset.", metadata={"source": "test.txt"})


@pytest.fixture
def tmp_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test1.txt").write_text("Content about resetting password on X platform.")
    (data_dir / "test2.txt").write_text("Content about blocking users on X.")
    return data_dir


class TestDocumentLoader:
    def test_load_documents(self, tmp_data_dir):
        loader = SocialMediaDocumentLoader(data_dir=str(tmp_data_dir))
        docs = loader.load_documents()
        assert len(docs) == 2
        assert all("source" in doc.metadata for doc in docs)
        assert docs[0].metadata["source"] in ("test1.txt", "test2.txt")

    def test_process_documents_empty_raises(self, tmp_data_dir):
        loader = SocialMediaDocumentLoader(data_dir=str(tmp_data_dir))
        with pytest.raises(ValueError, match="Empty document list"):
            loader.process_documents([])

    def test_process_documents_splits(self, tmp_data_dir):
        loader = SocialMediaDocumentLoader(data_dir=str(tmp_data_dir), chunk_size=20, chunk_overlap=5)
        docs = loader.load_documents()
        processed = loader.process_documents(docs)
        assert len(processed) >= len(docs)

    def test_load_and_process_no_docs_raises(self, tmp_path):
        loader = SocialMediaDocumentLoader(data_dir=str(tmp_path / "empty"))
        with pytest.raises(ValueError, match="No documents found"):
            loader.load_and_process()

    def test_load_and_process(self, tmp_data_dir):
        loader = SocialMediaDocumentLoader(data_dir=str(tmp_data_dir))
        docs = loader.load_and_process()
        assert len(docs) > 0


class TestVectorStore:
    def test_create_vectorstore_empty_returns_none(self):
        store = SocialMediaVectorStore(embedding_model=MagicMock())
        result = store.create_vectorstore([])
        assert result is None

    @patch("src.vector_store.FAISS.from_documents")
    def test_create_vectorstore_success(self, mock_from_docs, sample_doc):
        mock_vs = MagicMock()
        mock_from_docs.return_value = mock_vs
        store = SocialMediaVectorStore(embedding_model=MagicMock())
        result = store.create_vectorstore([sample_doc])
        assert result is mock_vs
        assert store.vectorstore is mock_vs

    def test_save_vectorstore_no_store_returns_false(self):
        store = SocialMediaVectorStore(embedding_model=MagicMock())
        assert store.save_vectorstore() is False

    def test_load_vectorstore_missing_returns_none(self, tmp_path):
        store = SocialMediaVectorStore(
            embedding_model=MagicMock(),
            index_path=str(tmp_path),
        )
        assert store.load_vectorstore() is None

    def test_get_embedding_for_text(self):
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 1536
        store = SocialMediaVectorStore(embedding_model=mock_embeddings)
        result = store.get_embedding_for_text("hello")
        assert len(result) == 1536


class TestRAGChain:
    def test_get_relevant_documents_filters_by_threshold(self, sample_doc):
        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = [
            (sample_doc, 0.5),
            (Document(page_content="irrelevant", metadata={"source": "other.txt"}), 1.5),
        ]
        chain = SocialMediaRAGChain(
            vectorstore=mock_vs,
            llm=MagicMock(),
            similarity_threshold=0.8,
        )
        docs = chain.get_relevant_documents("password reset")
        assert len(docs) == 1
        assert docs[0].metadata["source"] == "test.txt"

    def test_query_no_relevant_docs(self):
        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = []
        chain = SocialMediaRAGChain(vectorstore=mock_vs, llm=MagicMock())
        result = chain.query("unknown topic xyz")
        assert "don't have enough information" in result["answer"]
        assert result["source_documents"] == []

    def test_query_success(self, sample_doc):
        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = [(sample_doc, 0.3)]
        mock_llm = MagicMock()
        chain = SocialMediaRAGChain(
            vectorstore=mock_vs,
            llm=mock_llm,
            similarity_threshold=0.8,
        )
        chain.chain = MagicMock()
        chain.chain.invoke.return_value = "Reset your password via settings."
        result = chain.query("How do I reset my password?")
        assert result["answer"] == "Reset your password via settings."
        assert "test.txt" in result["sources"]
        assert len(result["source_documents"]) == 1

    def test_query_error_handling(self):
        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.side_effect = RuntimeError("API failure")
        chain = SocialMediaRAGChain(vectorstore=mock_vs, llm=MagicMock())
        result = chain.query("test question")
        assert "encountered an error" in result["answer"]
        assert result["error"] == "API failure"
