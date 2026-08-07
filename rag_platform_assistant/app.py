import os
import logging
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

from src.document_loader import SocialMediaDocumentLoader
from src.vector_store import SocialMediaVectorStore
from src.rag_chain import SocialMediaRAGChain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found. Please add it to your .env file.")

DATA_DIR = Path("data")
FAISS_INDEX_DIR = Path("faiss_index")


def initialize_rag_system() -> SocialMediaRAGChain:
    """
    Initialize the RAG system by loading an existing vector store or creating a new one.

    Steps:
        1. Create a SocialMediaVectorStore instance.
        2. Attempt to load an existing vector store from disk.
        3. If no store exists:
            - Create a SocialMediaDocumentLoader and process documentation.
            - Load and process documents from DATA_DIR.
            - Create a new vector store from the documents.
            - Save the vector store to disk.
        4. Create and return a SocialMediaRAGChain initialized with the vector store.

    Returns:
        SocialMediaRAGChain: A RAG chain ready to answer questions.
    """
    try:
        vector_store = SocialMediaVectorStore(
            index_path=str(FAISS_INDEX_DIR),
            index_name="support_docs",
        )

        loaded_vectorstore = vector_store.load_vectorstore()

        if loaded_vectorstore is None:
            logger.info("No existing vector store found. Creating a new one...")
            document_loader = SocialMediaDocumentLoader(
                data_dir=str(DATA_DIR),
                chunk_size=1000,
                chunk_overlap=200,
            )
            documents = document_loader.load_and_process()

            if not documents:
                logger.error("No documents found in data directory")
                st.error(
                    "No documentation files found. Please add .txt files to the data/ directory."
                )
                st.stop()

            vector_store.create_vectorstore(documents)
            vector_store.save_vectorstore()

        rag_chain = SocialMediaRAGChain(
            vectorstore=vector_store.vectorstore,
            llm=None,
            temperature=0.0,
            k=4,
            return_source_documents=True,
            similarity_threshold=0.7,
        )

        return rag_chain

    except NotImplementedError as e:
        st.warning(f"Feature NotImplemented: {e}")
        st.stop()


def format_sources(sources):
    """
    Format the source document names for display in the UI.

    Args:
        sources (List[str]): List of source document names.

    Returns:
        str: Formatted source string for display in the UI.
    """
    try:
        if not sources:
            return "No sources found"

        sources_text = "Sources:\n"
        for i, source in enumerate(sources, 1):
            source_name = source.replace(".html.txt", "").replace("-", " ").title()
            sources_text += f"{i}. {source_name}\n"

        return sources_text
    except NotImplementedError as e:
        st.warning(f"Feature NotImplemented: {e}")
        st.stop()


sample_queries = [
    "How do I reset my password?",
    "How can I recover my account if I forgot my email?",
    "How can I report someone who is harassing me?",
    "What should I do if my account was hacked?",
    "How do I block or unblock someone?",
    "How do I change my username?",
]


def main():
    st.set_page_config(page_title="Social Media App Support Agent", layout="wide")

    st.title("Social Media App Support Agent")
    st.markdown(
        "Get help with your social media platform questions. "
        "Ask anything about platform features and policies."
    )

    if "rag_chain" not in st.session_state:
        with st.spinner("Initializing support agent..."):
            st.session_state.rag_chain = initialize_rag_system()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                if "don't have enough information" not in message["content"].lower():
                    with st.expander("View Sources"):
                        st.markdown(message["sources"])

    st.sidebar.title("Options")
    selected_query = st.sidebar.selectbox("Sample Questions", sample_queries)
    user_input = st.chat_input("Ask a question about the platform...")

    prompt = user_input or selected_query

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.rag_chain.query(prompt)
            st.markdown(response["answer"])

            sources_text = "No sources found"
            if "sources" in response and response["sources"]:
                sources_text = format_sources(response["sources"])
                with st.expander("View Sources"):
                    st.markdown(sources_text)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response["answer"],
                "sources": sources_text,
            }
        )
    else:
        st.warning("Please select or type a question to proceed.")

    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as e:
        st.warning(f"Feature NotImplemented: {e}")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
