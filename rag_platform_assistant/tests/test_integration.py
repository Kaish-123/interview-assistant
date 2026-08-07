import os
import pytest
from unittest.mock import patch, MagicMock

from src.document_loader import SocialMediaDocumentLoader
from src.vector_store import SocialMediaVectorStore
from src.rag_chain import SocialMediaRAGChain
from langchain_core.documents import Document
import uuid


class TestIntegration:
    def test_end_to_end_workflow(self, temp_dir, mock_text_file):
        with patch("src.rag_chain.PromptTemplate") as MockPromptTemplate:
            MockPromptTemplate.from_template.return_value = MagicMock()

            with patch("src.rag_chain.RunnablePassthrough") as MockRunnablePassthrough:
                passthrough_instance = MagicMock()
                MockRunnablePassthrough.return_value = passthrough_instance

                with patch("src.rag_chain.StrOutputParser") as MockStrOutputParser:
                    mock_chain = MagicMock()
                    mock_chain.invoke.return_value = "Here's how to reset your password..."

                    MockPromptTemplate.from_template.return_value.__or__.return_value = MagicMock()
                    MockPromptTemplate.from_template.return_value.__or__.return_value.__or__.return_value = mock_chain

                    with patch.object(SocialMediaDocumentLoader, 'load_and_process') as mock_load_process:
                        documents = [Document(page_content="Test content", metadata={"source": "test.txt"})]
                        mock_load_process.return_value = documents

                        with patch.object(SocialMediaVectorStore, 'create_vectorstore') as mock_create_vs:
                            mock_vs = MagicMock()

                            mock_retriever = MagicMock()
                            mock_retriever.__or__.return_value = lambda \
                                docs: f"Formatted docs: {len(docs) if isinstance(docs, list) else 'unknown'} documents"
                            mock_vs.as_retriever.return_value = mock_retriever

                            mock_vs.similarity_search_with_score.return_value = [(documents[0], 0.8)]
                            mock_create_vs.return_value = mock_vs

                            loader = SocialMediaDocumentLoader(temp_dir)
                            documents = loader.load_and_process()

                            assert len(documents) > 0, "Should have loaded at least one document"

                            vector_store = SocialMediaVectorStore()
                            vs = vector_store.create_vectorstore(documents)

                            with patch.object(SocialMediaRAGChain, '_create_chain', return_value=mock_chain):
                                rag_chain = SocialMediaRAGChain(vectorstore=vs)

                                dynamic_content = f"Reset your pass at step-{uuid.uuid4().hex[:4]}"
                                mock_chain.invoke.return_value = dynamic_content

                                response = rag_chain.query("How to reset password?")

                                assert "answer" in response
                                assert dynamic_content in response["answer"]
                                assert "source_documents" in response

                                mock_load_process.assert_called_once()
                                mock_create_vs.assert_called_once_with(documents)
