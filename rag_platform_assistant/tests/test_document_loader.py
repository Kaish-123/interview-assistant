import os
import uuid

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from src.document_loader import SocialMediaDocumentLoader
from langchain_core.documents import Document


class TestSocialMediaDocumentLoader:

    def test_load_documents(self, temp_dir):
        temp_dir_path = Path(temp_dir)
        test_file_path = temp_dir_path / "test_doc.txt"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("This is a test document content.")

        loader = SocialMediaDocumentLoader(temp_dir)
        docs = loader.load_documents()

        assert len(docs) == 1
        assert docs[0].metadata["source"] == "test_doc.txt"
        assert docs[0].page_content == "This is a test document content."

    def test_process_documents(self):
        long_content = "This is the first sentence.\n\n" + \
                    "This is a second paragraph with more text. " * 50 + \
                    "\n\nThis is the final paragraph."
        input_doc = Document(
            page_content=long_content,
            metadata={"source": "test_doc.txt"}
        )

        loader = SocialMediaDocumentLoader(
            "test_dir",
            chunk_size=1000,
            chunk_overlap=200
        )

        result = loader.process_documents([input_doc])

        assert len(result) > 1
        assert all(len(chunk.page_content) <= 1000 for chunk in result)
        assert all("source" in chunk.metadata and chunk.metadata["source"] == "test_doc.txt" for chunk in result)
        assert any("This is the first sentence" in chunk.page_content for chunk in result)
        assert any("This is the final paragraph" in chunk.page_content for chunk in result)

        overlaps = False
        for i in range(len(result) - 1):
            chunk1, chunk2 = result[i].page_content, result[i + 1].page_content
            common_text = set(chunk1.split()).intersection(set(chunk2.split()))
            if len(common_text) > 0:
                overlaps = True
                break
        assert overlaps, "Chunks should have overlapping content"

    def test_load_and_process(self, temp_dir, mock_text_file):
        import re
        doc_id = uuid.uuid4().hex[:6]
        chunk1_content = f"Dynamic chunk 1 - {doc_id}"
        chunk2_content = f"Dynamic chunk 2 - {uuid.uuid4().hex[:6]}"
        test_source = f"file_{uuid.uuid4().hex[:4]}.txt"

        with patch.object(SocialMediaDocumentLoader, 'load_documents') as mock_load:
            with patch.object(SocialMediaDocumentLoader, 'process_documents') as mock_process:
                mock_load.return_value = [
                    Document(page_content="Dynamically loaded document", metadata={"source": test_source})
                ]
                mock_process.return_value = [
                    Document(page_content=chunk1_content, metadata={"source": test_source}),
                    Document(page_content=chunk2_content, metadata={"source": test_source})
                ]

                loader = SocialMediaDocumentLoader(temp_dir)
                result = loader.load_and_process()

                mock_load.assert_called_once()
                mock_process.assert_called_once_with(mock_load.return_value)

                assert len(result) == 2

                assert re.match(r"Dynamic chunk 1 - \w{6}", result[0].page_content)
                assert re.match(r"Dynamic chunk 2 - \w{6}", result[1].page_content)

                assert all(doc.metadata["source"] == test_source for doc in result)
