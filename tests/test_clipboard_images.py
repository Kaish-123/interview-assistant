"""Tests for bulk image copy/paste helpers."""

from __future__ import annotations

import base64
import io
import os
import sys
import unittest

from PIL import Image

from image_clipboard import (
    copy_text_and_images_to_clipboard,
    extract_pil_images_from_message_content,
    question_display_matches_message,
    read_images_from_clipboard,
    save_pil_images_to_temp,
)


def _tiny_png_b64() -> str:
    img = Image.new("RGB", (8, 8), color=(10, 120, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


class QuestionMatchingTests(unittest.TestCase):
    def test_screenshot_line_matches_message(self):
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Please analyze this screenshot."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_tiny_png_b64()}"}},
            ],
        }
        self.assertTrue(
            question_display_matches_message("QUESTION: [Screenshot attached]", msg)
        )

    def test_two_screenshot_questions_match_in_order(self):
        """Each [Screenshot attached] line must pair with the next image message."""
        b64 = _tiny_png_b64()
        img_part = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        msg1 = {"role": "user", "content": [{"type": "text", "text": "first"}, img_part]}
        msg2 = {"role": "user", "content": [{"type": "text", "text": "second"}, img_part, img_part]}

        displays = ["QUESTION: [Screenshot attached]", "QUESTION: [Screenshot attached]"]
        user_msgs = [msg1, msg2]
        ui_idx = 0
        pairs = []
        for msg in user_msgs:
            if ui_idx >= len(displays):
                break
            if question_display_matches_message(displays[ui_idx], msg):
                pairs.append((ui_idx, msg))
                ui_idx += 1

        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0][1], msg1)
        self.assertEqual(pairs[1][1], msg2)
        self.assertEqual(len(extract_pil_images_from_message_content(msg2["content"])), 2)

    def test_image_placeholder_matches(self):
        b64 = _tiny_png_b64()
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is this?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }
        ui = "QUESTION: What is this?\n[Image]"
        self.assertTrue(question_display_matches_message(ui, msg))


class ExtractImagesTests(unittest.TestCase):
    def test_extract_multiple_images(self):
        b64 = _tiny_png_b64()
        content = [
            {"type": "text", "text": "two pics"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]
        images = extract_pil_images_from_message_content(content)
        self.assertEqual(len(images), 2)


@unittest.skipUnless(sys.platform == "darwin", "macOS clipboard tests")
class ClipboardRoundTripTests(unittest.TestCase):
    def test_copy_and_read_three_images(self):
        imgs = [
            Image.new("RGB", (12, 12), color=(255, 0, 0)),
            Image.new("RGB", (12, 12), color=(0, 255, 0)),
            Image.new("RGB", (12, 12), color=(0, 0, 255)),
        ]
        paths = save_pil_images_to_temp(imgs)
        self.assertEqual(len(paths), 3)
        self.assertEqual(len({os.path.basename(p).split("_")[1] for p in paths}), 1)
        ok = copy_text_and_images_to_clipboard("question text", imgs, paths)
        self.assertTrue(ok)
        read_back = read_images_from_clipboard()
        self.assertEqual(len(read_back), 3)

    def test_unique_batch_paths_on_second_copy(self):
        imgs = [Image.new("RGB", (8, 8), color=(1, 2, 3))]
        paths1 = save_pil_images_to_temp(imgs)
        paths2 = save_pil_images_to_temp(imgs)
        self.assertNotEqual(paths1[0], paths2[0])


@unittest.skipUnless(sys.platform == "darwin", "macOS osascript tests")
class OsascriptCopyTests(unittest.TestCase):
    def test_osascript_multi_image_copy(self):
        from image_clipboard import _copy_images_via_osascript, save_pil_images_to_temp

        imgs = [Image.new("RGB", (32, 32), color=(i * 70, 40, 10)) for i in range(3)]
        paths = save_pil_images_to_temp(imgs)
        self.assertTrue(_copy_images_via_osascript(paths))


if __name__ == "__main__":
    unittest.main()
