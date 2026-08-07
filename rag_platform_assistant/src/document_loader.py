from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader


class SocialMediaDocumentLoader:
    """
    Loads and processes social media documentation files for use in AI support agents.

    This class reads text files from a directory and splits documents into optimally
    sized chunks for efficient vector embedding and retrieval. It assumes the documents
    are already pre-cleaned.
    """

    def __init__(self, data_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the SocialMediaDocumentLoader with specified parameters.

        Args:
            data_dir (str): Directory path where documentation files are stored.
            chunk_size (int, optional): Maximum size of each text chunk. Default is 1000.
            chunk_overlap (int, optional): Overlap between consecutive chunks. Default is 200.
        """
        self.data_dir = Path(data_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def load_documents(self, file_pattern: str = "*.txt") -> List[Document]:
        """
        Loads raw documents from files matching a pattern in the specified directory.

        Args:
            file_pattern (str, optional): Glob pattern to match files. Defaults to "*.txt".

        Returns:
            List[Document]: List of Document objects where each Document contains:
                - page_content (str): Raw text content of the file
                - metadata (dict): Must include 'source' (str) with the filename

        Note:
            Each document's metadata will include the source filename.
        """
        documents: List[Document] = []

        if not self.data_dir.exists():
            return documents

        for file_path in sorted(self.data_dir.glob(file_pattern)):
            if not file_path.is_file():
                continue
            try:
                loader = TextLoader(str(file_path), encoding="utf-8")
                loaded_docs = loader.load()
                for doc in loaded_docs:
                    doc.metadata["source"] = file_path.name
                documents.extend(loaded_docs)
            except Exception:
                continue

        return documents

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Processes documents by splitting into optimally sized chunks.

        Args:
            documents (List[Document]): List of Document objects to process.

        Returns:
            List[Document]: List of processed Document objects split into chunks.

        Raises:
            ValueError: If the documents list is empty, raises ValueError with the exact message:
                "Empty document list"
            RuntimeError: If an error occurs during document processing, raises RuntimeError with
                the exact error message from the underlying exception
        """
        if not documents:
            raise ValueError("Empty document list")

        try:
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            raise RuntimeError(str(e)) from e

    def load_and_process(self, file_pattern: str = "*.txt") -> List[Document]:
        """
        Performs end-to-end document loading and processing in a single operation.

        This method chains the two main operations (loading and processing) for convenience.

        Args:
            file_pattern (str, optional): Glob pattern to match files. Defaults to "*.txt".

        Returns:
            List[Document]: List of processed Document objects ready for indexing.
                Returns processed chunks from all successfully loaded documents.

        Raises:
            ValueError: If no documents could be loaded, raises ValueError with the exact message:
                "No documents found"
        """
        documents = self.load_documents(file_pattern=file_pattern)
        if not documents:
            raise ValueError("No documents found")

        return self.process_documents(documents)
