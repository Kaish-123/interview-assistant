"""Image compression helpers for multimodal API payloads."""

from __future__ import annotations

import base64
import io
from typing import Any, Literal

from PIL import Image

ImageFormat = Literal["jpeg", "png"]


def _resize_max(image: Image.Image, max_size: int) -> Image.Image:
    width, height = image.size
    if width <= max_size and height <= max_size:
        return image
    ratio = min(max_size / width, max_size / height)
    new_size = (int(width * ratio), int(height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def compress_image_for_api(
    image: Image.Image,
    max_size: int = 1024,
    quality: int = 85,
) -> str:
    """
    Resize + JPEG-compress an image; return base64 (no data: prefix).
    Typical 60–80% payload reduction vs raw PNG for photos.
    """
    image = _resize_max(image, max_size)
    if image.mode in ("RGBA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "RGBA":
            background.paste(image, mask=image.split()[3])
        else:
            background.paste(image)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def compress_image_png(image: Image.Image, max_size: int = 1024) -> str:
    """Resize + PNG-compress (better for sharp screenshot text); return base64."""
    image = _resize_max(image, max_size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def image_to_data_url(
    image: Image.Image,
    *,
    fmt: ImageFormat = "png",
    max_size: int = 1280,
    quality: int = 85,
) -> str:
    """Return a data URL suitable for OpenAI image_url parts."""
    if fmt == "jpeg":
        b64 = compress_image_for_api(image, max_size=max_size, quality=quality)
        return f"data:image/jpeg;base64,{b64}"
    b64 = compress_image_png(image, max_size=max_size)
    return f"data:image/png;base64,{b64}"


def image_url_part(
    image: Image.Image,
    *,
    fmt: ImageFormat = "png",
    max_size: int = 1280,
    detail: str | None = None,
) -> dict[str, Any]:
    """Build an OpenAI multimodal image_url content part."""
    url = image_to_data_url(image, fmt=fmt, max_size=max_size)
    image_url: dict[str, Any] = {"url": url}
    if detail:
        image_url["detail"] = detail
    return {"type": "image_url", "image_url": image_url}
