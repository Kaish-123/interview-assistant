"""Phase 1 Milestone 5 — context package tests."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest
from PIL import Image

from interview_copilot.packages.context.documents import load_document
from interview_copilot.packages.context.extract import ExtractError, extract_text_from_file
from interview_copilot.packages.context.folder import collect_files_from_folder
from interview_copilot.packages.context.images import (
    compress_image_for_api,
    compress_image_png,
    image_to_data_url,
    image_url_part,
)


def test_extract_txt(tmp_path: Path):
    p = tmp_path / "resume.txt"
    p.write_text("Jane Doe\nSoftware Engineer\n", encoding="utf-8")
    text = extract_text_from_file(p)
    assert "Jane Doe" in text


def test_extract_skips_binary(tmp_path: Path):
    p = tmp_path / "pic.png"
    Image.new("RGB", (10, 10), color="red").save(p)
    with pytest.raises(ExtractError, match="Skipped"):
        extract_text_from_file(p)


def test_extract_docx_stdlib_fallback(tmp_path: Path):
    # Minimal docx (zip + word/document.xml) without python-docx
    docx = tmp_path / "cv.docx"
    wns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    document = Element(f"{wns}document")
    body = SubElement(document, f"{wns}body")
    para = SubElement(body, f"{wns}p")
    run = SubElement(para, f"{wns}r")
    t = SubElement(run, f"{wns}t")
    t.text = "DOCX Hello Candidate"
    xml_bytes = tostring(document, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("word/document.xml", xml_bytes)
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
    text = extract_text_from_file(docx)
    assert "DOCX Hello Candidate" in text


def test_pdf_dispatch_uses_pdf_extractor(tmp_path: Path, monkeypatch):
    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(b"%PDF-1.4 minimal")
    monkeypatch.setattr(
        "interview_copilot.packages.context.extract._extract_pdf",
        lambda path: "PDF Resume Content",
    )
    assert extract_text_from_file(pdf) == "PDF Resume Content"


def test_pdf_real_optional(tmp_path: Path):
    """Optional integration when reportlab is installed."""
    pytest.importorskip("pypdf")
    try:
        from reportlab.pdfgen import canvas  # type: ignore
    except Exception:
        pytest.skip("reportlab not installed")

    pdf_path = tmp_path / "r.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "PDF Resume Text")
    c.save()
    text = extract_text_from_file(pdf_path)
    assert "PDF Resume Text" in text or "Resume" in text


def test_collect_files_from_folder(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.py").write_text("print(1)\n", encoding="utf-8")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "c.md").write_text("# hi", encoding="utf-8")
    (tmp_path / "skip.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x", encoding="utf-8")

    files = collect_files_from_folder(tmp_path)
    names = {Path(f).name for f in files}
    assert names == {"a.txt", "b.py", "c.md"}
    assert "skip.png" not in names
    assert "config" not in names


def test_load_document_ok_and_empty(tmp_path: Path):
    p = tmp_path / "jd.txt"
    p.write_text("Looking for Python engineer", encoding="utf-8")
    result = load_document(p)
    assert result.ok
    assert "Looking for Python" in result.text
    assert "loaded" in result.message.lower() or "📄" in result.message

    empty = tmp_path / "empty.txt"
    empty.write_text("   \n", encoding="utf-8")
    bad = load_document(empty)
    assert not bad.ok


def test_image_compress_jpeg_and_png():
    img = Image.new("RGBA", (2000, 1500), color=(255, 0, 0, 128))
    jpeg_b64 = compress_image_for_api(img, max_size=512, quality=70)
    png_b64 = compress_image_png(img, max_size=512)
    assert len(jpeg_b64) > 100
    assert len(png_b64) > 100
    # JPEG path should usually be smaller than PNG for solid-ish fills after resize
    url = image_to_data_url(img, fmt="png", max_size=640)
    assert url.startswith("data:image/png;base64,")
    part = image_url_part(img, fmt="jpeg", max_size=640, detail="low")
    assert part["type"] == "image_url"
    assert part["image_url"]["detail"] == "low"
    assert part["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_engine_load_document(tmp_path: Path):
    from dataclasses import replace
    from unittest.mock import MagicMock

    from interview_copilot.packages.llm.engine import InterviewLLMEngine
    from interview_copilot.shared.config.settings import build_settings

    settings = replace(build_settings(), openai_api_key="sk-test")
    engine = InterviewLLMEngine(settings=settings, client=MagicMock())
    p = tmp_path / "resume.txt"
    p.write_text("Expert in distributed systems", encoding="utf-8")
    ok, msg = engine.load_document(str(p))
    assert ok
    assert any(
        "Attached document" in str(m.get("content", ""))
        for m in engine.messages
        if m.get("role") == "system"
    )
