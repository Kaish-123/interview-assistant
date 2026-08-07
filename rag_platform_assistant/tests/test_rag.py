import uuid
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from src.rag_chain import SocialMediaRAGChain


class TestSocialMediaRAGChain:

    def test_query_success(self, mock_vectorstore, mock_llm):
        with patch('src.rag_chain.PromptTemplate.from_template') as mock_prompt_template, \
                patch('src.rag_chain.StrOutputParser'), \
                patch('src.rag_chain.RunnablePassthrough'):
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = "Here's how to reset your password..."

            with patch.object(SocialMediaRAGChain, '_create_chain', return_value=mock_chain):
                rag_chain = SocialMediaRAGChain(vectorstore=mock_vectorstore, llm=mock_llm, similarity_threshold=0.8)

                doc1_source = f"{uuid.uuid4().hex[:6]}.txt"
                doc2_source = f"{uuid.uuid4().hex[:6]}.txt"

                docs = [
                    Document(page_content="Reset instructions", metadata={"source": doc1_source}),
                    Document(page_content="Recovery guide", metadata={"source": doc2_source}),
                ]

                mock_vectorstore.similarity_search_with_score.return_value = [
                    (docs[0], 0.6),
                    (docs[1], 0.7)
                ]

                result = rag_chain.query("How do I reset my password?")

                mock_vectorstore.similarity_search_with_score.assert_called_once()
                mock_chain.invoke.assert_called_once_with("How do I reset my password?")

                assert "answer" in result
                assert result["answer"] == "Here's how to reset your password..."
                assert "sources" in result
                assert set(result["sources"]) == {doc1_source, doc2_source}
                assert "source_documents" in result
                assert len(result["source_documents"]) == 2

    def test_query_no_relevant_docs(self, mock_vectorstore, mock_llm):
        fname = f"unrelated_{uuid.uuid4().hex[:6]}.txt"
        unrelated_doc = Document(
            page_content="Some unrelated technical information",
            metadata={"source": fname}
        )

        with patch('src.rag_chain.PromptTemplate') as MockPromptTemplate, \
                patch('src.rag_chain.RunnablePassthrough') as MockRunnablePassthrough, \
                patch('src.rag_chain.StrOutputParser') as MockStrOutputParser:
            MockPromptTemplate.from_template.return_value = MagicMock()

            chain = SocialMediaRAGChain(
                vectorstore=mock_vectorstore,
                llm=mock_llm,
                similarity_threshold=0.1
            )

            mock_vectorstore.similarity_search_with_score.return_value = [
                (unrelated_doc, 0.2)
            ]

            result = chain.query("How do I reset my password?")

            mock_vectorstore.similarity_search_with_score.assert_called_once_with(
                "How do I reset my password?",
                k=4
            )
            assert "I don't have enough information" in result["answer"]
            assert "source_documents" in result
            assert len(result["source_documents"]) == 0
            assert "sources" not in result

    def test_query_exception_handling(self, mock_vectorstore, mock_llm):
        with patch('src.rag_chain.PromptTemplate'), \
                patch('src.rag_chain.RunnablePassthrough'), \
                patch('src.rag_chain.StrOutputParser'):
            chain = SocialMediaRAGChain(vectorstore=mock_vectorstore, llm=mock_llm)

            mock_vectorstore.similarity_search_with_score.side_effect = Exception("Test error")
            result = chain.query("How do I reset my password?")
            assert "I encountered an error" in result["answer"]
            assert "error" in result
            assert result["error"] == "Test error"
            assert "source_documents" in result
            assert result["source_documents"] == []

    def test_get_relevant_documents(self, mock_vectorstore, mock_llm):
        with patch('src.rag_chain.PromptTemplate') as MockPromptTemplate:
            with patch('src.rag_chain.RunnablePassthrough') as MockRunnablePassthrough:
                with patch('src.rag_chain.StrOutputParser') as MockStrOutputParser:
                    MockPromptTemplate.from_template.return_value = MagicMock()

                    chain = SocialMediaRAGChain(
                        vectorstore=mock_vectorstore,
                        llm=mock_llm
                    )

                    mock_docs = [Document(page_content="Test content", metadata={"source": "test.txt"})]
                    mock_vectorstore.similarity_search.return_value = mock_docs

                    docs = chain.get_relevant_documents("password reset")

                    mock_vectorstore.similarity_search.assert_called_once_with("password reset", k=4)
                    assert docs == mock_docs

                    mock_vectorstore.similarity_search.reset_mock()
                    chain.get_relevant_documents("password reset", k=10)
                    mock_vectorstore.similarity_search.assert_called_once_with("password reset", k=10)
