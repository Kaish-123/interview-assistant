"""Context package — document text extraction + image compression for LLM payloads."""

from interview_copilot.packages.context.documents import DocumentLoadResult, load_document
from interview_copilot.packages.context.extract import (
    ExtractError,
    extract_text_from_file,
)
from interview_copilot.packages.context.folder import collect_files_from_folder
from interview_copilot.packages.context.images import (
    compress_image_for_api,
    compress_image_png,
    image_to_data_url,
    image_url_part,
)

__all__ = [
    "DocumentLoadResult",
    "ExtractError",
    "collect_files_from_folder",
    "compress_image_for_api",
    "compress_image_png",
    "extract_text_from_file",
    "image_to_data_url",
    "image_url_part",
    "load_document",
]
