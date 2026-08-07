from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


class SocialMediaRAGChain:
    """
    A streamlined class implementing RAG (Retrieval-Augmented Generation) for social media support using LCEL.

    This class creates a complete RAG pipeline that enhances LLM responses with retrieved knowledge.
    It retrieves relevant documents from a vector store based on user queries, formats them as context,
    and generates accurate, contextually-informed responses for social media platform support questions.
    """

    def __init__(
        self,
        vectorstore: VectorStore,
        llm: Optional[BaseLanguageModel] = None,
        temperature: float = 0.0,
        k: int = 4,
        return_source_documents: bool = True,
        similarity_threshold: float = 0.8,
        prompt_template: Optional[str] = None,
    ):
        """
        Initialize the RAG chain with LCEL.

        Args:
            vectorstore (VectorStore): The vector store for document retrieval
            llm (Optional[BaseLanguageModel]): The language model to use (defaults to ChatOpenAI model="gpt-4o")
            temperature (float): Temperature setting for the LLM (default: 0.0 for deterministic responses)
            k (int): Number of documents to retrieve from the vector store (default: 4)
            return_source_documents (bool): Whether to return source documents with responses (default: True)
            similarity_threshold (float): Threshold for document relevance (default: 0.8)
                                         Lower scores in FAISS indicate higher similarity, so documents with
                                         scores <= this threshold will be considered relevant
        Note:
            self.prompt: The `prompt_template` should be set or customized here to suit your use case.
        """
        self.vectorstore = vectorstore
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=temperature)
        self.k = k
        self.return_source_documents = return_source_documents
        self.similarity_threshold = similarity_threshold
        self.prompt = PromptTemplate.from_template(
            prompt_template or "write your prompt here with {context} and {question}"
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.k})
        self.chain = self._create_chain()

    def _create_chain(self):
        """
        Create the LCEL RAG chain.

        Note:
           This is an internal method called during initialization.
        """
        def format_context(question: str) -> str:
            docs = self.get_relevant_documents(question)
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {"context": format_context, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return chain

    def _get_scored_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve documents filtered by similarity score threshold."""
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=self.k)
        return [
            doc
            for doc, score in docs_with_scores
            if score <= self.similarity_threshold
        ]

    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the chain with a user question.

        Args:
            question (str): The user's question about social media platform usage

        Returns:
            Dict[str, Any]: Dictionary containing:
                - "answer": The generated response text
                - "sources": List of unique source names
                - "source_documents": List of relevant Document objects (if return_source_documents is True)
                - "error": Error message (if an exception occurs)
        """
        try:
            relevant_docs = self._get_scored_relevant_documents(question)

            if not relevant_docs:
                return {
                    "answer": "I'm sorry, I don't have enough information to answer this question confidently.",
                    "source_documents": [],
                }

            answer = self.chain.invoke(question)
            sources = list(
                dict.fromkeys(
                    doc.metadata.get("source", "unknown") for doc in relevant_docs
                )
            )

            result: Dict[str, Any] = {
                "answer": answer,
                "sources": sources,
            }

            if self.return_source_documents:
                result["source_documents"] = relevant_docs

            return result

        except Exception as e:
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "error": str(e),
                "source_documents": [],
            }

    def get_relevant_documents(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents for a query without generating an answer.

        Args:
            query (str): The query string to find relevant documents
            k (Optional[int]): Number of documents to retrieve (defaults to self.k if None)

        Returns:
            List[Document]: List of relevant Document objects from the vector store
        """
        num_docs = k if k is not None else self.k
        return self.vectorstore.similarity_search(query, k=num_docs)
