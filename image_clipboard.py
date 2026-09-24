"""macOS multi-image clipboard helpers for Interview Assistant."""

from __future__ import annotations

import base64
import io
import os
import re
import subprocess
import tempfile
import uuid

from PIL import Image, ImageGrab

IMAGE_FILE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".heic", ".tiff", ".tif",
}
CLIPBOARD_IMAGE_DIR = os.path.join(tempfile.gettempdir(), "interview_assistant_clipboard")


def _is_image_path(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_FILE_EXTENSIONS


def user_message_display_text(msg: dict) -> str:
    """Text as shown in the chat log for a user message."""
    content = msg.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif part.get("type") == "image_url":
                parts.append("[Image]")
        return "\n".join(p.strip() for p in parts if p.strip()).strip()
    return str(content).strip()


def message_has_images(msg: dict) -> bool:
    content = msg.get("content", "")
    if not isinstance(content, list):
        return False
    return any(
        isinstance(part, dict) and part.get("type") == "image_url"
        for part in content
    )


def normalize_question_display(text: str) -> str:
    text = re.sub(r"^QUESTION:\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\[📎 Image \d+\]", "[Image]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def question_display_matches_message(ui_text: str, msg: dict) -> bool:
    """True when a QUESTION: line in the chat log belongs to this user message."""
    ui_norm = normalize_question_display(ui_text)
    msg_norm = normalize_question_display(user_message_display_text(msg))

    if ui_norm and msg_norm and ui_norm == msg_norm:
        return True

    if ui_norm in ("[Screenshot attached]", "[Image]") and message_has_images(msg):
        return True

    if ui_norm and msg_norm and (ui_norm in msg_norm or msg_norm in ui_norm):
        return True

    if message_has_images(msg) and not ui_norm and not msg_norm:
        return True

    return False


def extract_pil_images_from_message_content(content) -> list[Image.Image]:
    """Decode base64 image_url parts from a chat message into PIL images."""
    images: list[Image.Image] = []
    if not isinstance(content, list):
        return images
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "image_url":
            continue
        url = part.get("image_url", {}).get("url", "")
        if not url.startswith("data:image"):
            continue
        try:
            _header, b64data = url.split(",", 1)
            img = Image.open(io.BytesIO(base64.b64decode(b64data)))
            img.load()
            images.append(img)
        except Exception as exc:
            print(f"⚠️ Could not decode image: {exc}")
    return images


def _nsimage_from_path(path: str):
    try:
        import AppKit
    except ImportError:
        return None
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return None
    return AppKit.NSImage.alloc().initWithContentsOfFile_(path)


def _nsimages_from_paths(file_paths: list[str]) -> list:
    images = []
    for path in file_paths:
        ns = _nsimage_from_path(path)
        if ns is not None:
            images.append(ns)
    return images


def _nsimage_to_pil(ns_image) -> Image.Image | None:
    try:
        tiff = ns_image.TIFFRepresentation()
        if tiff is None:
            return None
        return Image.open(io.BytesIO(bytes(tiff)))
    except Exception:
        return None


def save_pil_images_to_temp(pil_images: list[Image.Image]) -> list[str]:
    """Write PNGs to a temp folder (unique batch — avoids stale Finder/clipboard URLs)."""
    os.makedirs(CLIPBOARD_IMAGE_DIR, exist_ok=True)
    batch = uuid.uuid4().hex[:10]
    paths: list[str] = []
    for i, pil in enumerate(pil_images, 1):
        path = os.path.join(CLIPBOARD_IMAGE_DIR, f"copy_{batch}_{i}.png")
        if pil.mode not in ("RGB", "RGBA"):
            pil = pil.convert("RGBA")
        pil.save(path, format="PNG")
        paths.append(path)
    return paths


def _escape_applescript_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _copy_images_via_osascript(file_paths: list[str]) -> bool:
    """Fallback when PyObjC pasteboard write fails (common in bundled .app builds)."""
    valid = [os.path.abspath(p) for p in file_paths if p and os.path.isfile(p)]
    if not valid:
        return False

    load_lines = []
    for path in valid:
        esc = _escape_applescript_string(path)
        load_lines.append(
            f'set imageURL to current application\'s NSURL\'s fileURLWithPath:"{esc}"\n'
            f"set theImage to current application's NSImage's alloc()'s initWithContentsOfURL:imageURL\n"
            f"if theImage is not missing value then imageArray's addObject:theImage"
        )
    body = "\n".join(load_lines)
    script = f'''
use framework "Foundation"
use framework "AppKit"
set imageArray to current application's NSMutableArray's alloc()'s init()
{body}
set pb to current application's NSPasteboard's generalPasteboard()
pb's clearContents()
pb's writeObjects:imageArray
return "ok"
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"Clipboard osascript failed: {result.stderr.strip()}")
            return False
        return (result.stdout or "").strip() == "ok"
    except Exception as exc:
        print(f"Clipboard osascript error: {exc}")
        return False


def _set_text_via_osascript(text: str) -> bool:
    if not text:
        return False
    esc = _escape_applescript_string(text)
    script = f'set the clipboard to "{esc}"'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception as exc:
        print(f"Clipboard text osascript error: {exc}")
        return False


def _copy_via_appkit(text: str, file_paths: list[str]) -> bool:
    try:
        import AppKit
    except ImportError:
        return False

    try:
        pb = AppKit.NSPasteboard.generalPasteboard()
        pb.clearContents()

        ns_images = _nsimages_from_paths(file_paths)
        wrote_images = bool(ns_images) and bool(pb.writeObjects_(ns_images))

        if text:
            pb.setString_forType_(text, AppKit.NSPasteboardTypeString)

        return wrote_images
    except Exception as exc:
        print(f"Clipboard AppKit copy failed: {exc}")
        return False


def copy_text_and_images_to_clipboard(
    text: str,
    pil_images: list[Image.Image],
    file_paths: list[str] | None = None,
) -> bool:
    """Put question text + all images on the macOS clipboard (no Finder needed)."""
    paths = list(file_paths or [])
    if pil_images and not paths:
        try:
            paths = save_pil_images_to_temp(pil_images)
        except Exception as exc:
            print(f"Could not save temp images: {exc}")
            paths = []

    text = (text or "").strip()
    has_images = bool(paths)

    if not has_images and not text:
        return False

    # 1) AppKit + on-disk PNGs (most reliable for large screenshots)
    if has_images and _copy_via_appkit(text, paths):
        return True

    # 2) osascript image copy, then add text without wiping images if possible
    if has_images and _copy_images_via_osascript(paths):
        if text:
            try:
                import AppKit
                pb = AppKit.NSPasteboard.generalPasteboard()
                pb.setString_forType_(text, AppKit.NSPasteboardTypeString)
            except Exception:
                pass
        return True

    # 3) text-only fallback (images failed entirely)
    if text:
        try:
            import AppKit
            pb = AppKit.NSPasteboard.generalPasteboard()
            pb.clearContents()
            pb.setString_forType_(text, AppKit.NSPasteboardTypeString)
            return True
        except Exception:
            return _set_text_via_osascript(text)

    return False


def read_images_from_clipboard() -> list[Image.Image]:
    """Read every image currently on the clipboard (macOS multi-image aware)."""
    images: list[Image.Image] = []
    try:
        import AppKit

        pb = AppKit.NSPasteboard.generalPasteboard()
        ns_images = pb.readObjectsForClasses_options_([AppKit.NSImage], None)
        if ns_images:
            for ns in ns_images:
                pil = _nsimage_to_pil(ns)
                if pil is not None:
                    images.append(pil)
            if images:
                return images

        urls = pb.readObjectsForClasses_options_([AppKit.NSURL], None)
        if urls:
            seen: set[str] = set()
            for url in urls:
                path = url.path()
                if not path or path in seen or not _is_image_path(path):
                    continue
                seen.add(path)
                try:
                    images.append(Image.open(path))
                except Exception:
                    pass
            if images:
                return images
    except Exception as exc:
        print(f"AppKit clipboard read: {exc}")

    try:
        data = ImageGrab.grabclipboard()
        if isinstance(data, Image.Image):
            return [data]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, Image.Image):
                    images.append(item)
                elif isinstance(item, str) and _is_image_path(item) and os.path.isfile(item):
                    try:
                        images.append(Image.open(item))
                    except Exception:
                        pass
    except Exception:
        pass
    return images
