import os
import pytest
from unittest.mock import patch, MagicMock
from src.vector_store import SocialMediaVectorStore


class TestSocialMediaVectorStore:

    def test_create_vectorstore(self, sample_documents, mock_embeddings):
        with patch('src.vector_store.FAISS') as MockFAISS:
            mock_vs = MagicMock()
            MockFAISS.from_documents.return_value = mock_vs

            vs = SocialMediaVectorStore(embedding_model=mock_embeddings)
            result = vs.create_vectorstore(sample_documents)

            MockFAISS.from_documents.assert_called_once_with(
                sample_documents,
                mock_embeddings
            )

            assert result is mock_vs
            assert vs.vectorstore is mock_vs

            result = vs.create_vectorstore([])
            assert result is None

    def test_save_vectorstore(self, mock_embeddings):
        vs = SocialMediaVectorStore(embedding_model=mock_embeddings)

        assert vs.save_vectorstore() is False

        with patch('os.makedirs') as mock_makedirs:
            mock_faiss = MagicMock()
            vs.vectorstore = mock_faiss

            result = vs.save_vectorstore()

            mock_makedirs.assert_called_once_with("faiss_index", exist_ok=True)
            mock_faiss.save_local.assert_called_once_with(
                folder_path="faiss_index",
                index_name="support_docs"
            )
            assert result is True

            mock_faiss.save_local.side_effect = Exception("Save error")
            result = vs.save_vectorstore()
            assert result is False

    def test_load_vectorstore(self, mock_embeddings):
        vs = SocialMediaVectorStore(embedding_model=mock_embeddings)

        with patch('os.path.exists') as mock_exists:
            with patch('src.vector_store.FAISS') as MockFAISS:
                mock_exists.return_value = True
                mock_vs = MagicMock()
                MockFAISS.load_local.return_value = mock_vs

                result = vs.load_vectorstore()

                mock_exists.assert_called_once_with(os.path.join("faiss_index", "support_docs.faiss"))

                MockFAISS.load_local.assert_called_once_with(
                    folder_path="faiss_index",
                    embeddings=mock_embeddings,
                    index_name="support_docs",
                    allow_dangerous_deserialization=True
                )

                assert result is mock_vs
                assert vs.vectorstore is mock_vs

                mock_exists.return_value = False
                result = vs.load_vectorstore()
                assert result is None

    def test_get_embedding_for_text(self, mock_embeddings):
        vs = SocialMediaVectorStore(embedding_model=mock_embeddings)

        mock_embeddings.embed_query.reset_mock()
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3, 0.4]

        embedding = vs.get_embedding_for_text("Test query")

        mock_embeddings.embed_query.assert_called_once_with("Test query")
        assert embedding == [0.1, 0.2, 0.3, 0.4]

        mock_embeddings.embed_query.side_effect = Exception("Embedding error")
        with pytest.raises(Exception):
            vs.get_embedding_for_text("Test query")
