"""
Phase 1 Milestone 5 — context harness.

  python3 -m interview_copilot.packages.context.harness --file resume.txt
  python3 -m interview_copilot.packages.context.harness --folder ./docs
  python3 -m interview_copilot.packages.context.harness --demo-image
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from interview_copilot.packages.context import (
    collect_files_from_folder,
    compress_image_png,
    extract_text_from_file,
    load_document,
)
from interview_copilot.shared.config import get_settings
from interview_copilot.shared.logging import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Interview Copilot context harness")
    parser.add_argument("--file", type=str, help="Extract text from one file")
    parser.add_argument("--folder", type=str, help="List collectable files under folder")
    parser.add_argument("--demo-image", action="store_true", help="Compress a sample PNG")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings, force=True)

    print("Interview Copilot — Phase 1 Milestone 5 (Context)")
    if not args.file and not args.folder and not args.demo_image:
        parser.print_help()
        return

    if args.file:
        path = Path(args.file)
        result = load_document(path)
        print(f"  load: {result.message}")
        if result.ok:
            preview = result.text[:240].replace("\n", " ")
            print(f"  preview: {preview!r}…")

    if args.folder:
        files = collect_files_from_folder(args.folder)
        print(f"  folder files: {len(files)}")
        for p in files[:30]:
            print(f"    - {p}")
        if len(files) > 30:
            print(f"    … +{len(files) - 30} more")

    if args.demo_image:
        img = Image.new("RGB", (2000, 1200), color=(30, 30, 40))
        draw = ImageDraw.Draw(img)
        draw.text((40, 40), "Interview Copilot screenshot demo", fill=(240, 240, 240))
        b64 = compress_image_png(img, max_size=1280)
        print(f"  png base64 KB: {len(b64) // 1024}")


if __name__ == "__main__":
    main()
