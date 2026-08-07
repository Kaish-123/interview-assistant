import os
from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings


class SocialMediaVectorStore:
    """A class for managing a FAISS vector store for social media support documentation."""

    def __init__(
        self,
        embedding_model: Optional[Embeddings] = None,
        index_path: str = "faiss_index",
        index_name: str = "support_docs",
    ):
        """
        Initialize the SocialMediaVectorStore.

        Args:
            embedding_model (Optional[Embeddings]): Embedding model to use. Defaults to
                OpenAIEmbeddings(model="text-embedding-ada-002") if not provided.
            index_path (str): Directory path to store the FAISS index. Default is "faiss_index".
            index_name (str): Name of the index file. Default is "support_docs".
        """
        self.embedding_model = embedding_model or OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        self.index_path = index_path
        self.index_name = index_name
        self.vectorstore: Optional[FAISS] = None

    def create_vectorstore(self, documents: List[Document]) -> FAISS:
        """
        Create a new FAISS vector store from the provided documents.

        Args:
            documents (List[Document]): List of Document objects to embed and store.

        Returns:
            FAISS: The created FAISS vector store object, or None if documents list is empty.

        Raises:
            Exception: If creation fails, raises Exception with the original error message.

        Note:
            This method initializes or overwrites the self.vectorstore instance variable.
        """
        if not documents:
            return None

        try:
            self.vectorstore = FAISS.from_documents(documents, self.embedding_model)
            return self.vectorstore
        except Exception as e:
            raise Exception(str(e)) from e

    def save_vectorstore(self) -> bool:
        """
        Save the current vector store to disk.

        Returns:
            bool: True if save was successful, False otherwise.

        Note:
            Returns False if no vector store is available to save.
            Silently handles any exceptions during directory creation or saving.
        """
        if self.vectorstore is None:
            return False

        try:
            os.makedirs(self.index_path, exist_ok=True)
            self.vectorstore.save_local(
                folder_path=self.index_path,
                index_name=self.index_name,
            )
            return True
        except Exception:
            return False

    def load_vectorstore(self) -> Optional[FAISS]:
        """
        Load a previously saved vector store from disk.

        Returns:
            Optional[FAISS]: The loaded FAISS vector store, or None if loading fails.

        Note:
            Returns None if the index file does not exist on disk.
            Silently handles any exceptions during the loading process.
            On success, initializes or overwrites self.vectorstore.
        """
        faiss_file = os.path.join(self.index_path, f"{self.index_name}.faiss")
        if not os.path.exists(faiss_file):
            return None

        try:
            self.vectorstore = FAISS.load_local(
                folder_path=self.index_path,
                embeddings=self.embedding_model,
                index_name=self.index_name,
                allow_dangerous_deserialization=True,
            )
            return self.vectorstore
        except Exception:
            return None

    def get_embedding_for_text(self, text: str) -> List[float]:
        """
        Get the embedding vector for a piece of text.

        Args:
            text (str): The text to embed.

        Returns:
            List[float]: The embedding vector with shape [1536].

        Raises:
            Exception: If embedding generation fails, raises Exception with the error message.
        """
        try:
            return self.embedding_model.embed_query(text)
        except Exception as e:
            raise Exception(str(e)) from e
