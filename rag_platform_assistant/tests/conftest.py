import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document


@pytest.fixture
def temp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def mock_text_file(temp_dir):
    path = f"{temp_dir}/sample.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("Sample text content for testing.")
    return path


@pytest.fixture
def sample_documents():
    return [
        Document(page_content="Test content 1", metadata={"source": "doc1.txt"}),
        Document(page_content="Test content 2", metadata={"source": "doc2.txt"}),
    ]


@pytest.fixture
def mock_embeddings():
    mock = MagicMock()
    mock.embed_query.return_value = [0.1] * 1536
    return mock


@pytest.fixture
def mock_vectorstore():
    return MagicMock()


@pytest.fixture
def mock_llm():
    return MagicMock()
