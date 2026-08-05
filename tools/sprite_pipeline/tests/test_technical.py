from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from sprite_pipeline.config import TechnicalSpec
from sprite_pipeline.technical import normalize_and_validate


class TechnicalValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = TechnicalSpec(
            canvas_width=96,
            canvas_height=96,
            sprite_height_min=76,
            sprite_height_max=80,
            max_sprite_width=88,
            baseline_y=91,
            alpha_threshold=16,
            face_box=(31, 7, 65, 39),
        )

    def test_transparent_candidate_is_normalized_to_gameplay_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "candidate.png"
            output = root / "normalized.png"
            image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.rectangle((382, 120, 641, 919), fill=(80, 45, 25, 255))
            draw.rectangle((470, 155, 553, 305), fill=(225, 185, 155, 255))
            image.save(source)

            result = normalize_and_validate(source, output, self.spec)

            self.assertTrue(result.passed, result.hard_reject_reasons)
            self.assertTrue(output.exists())
            normalized = Image.open(output).convert("RGBA")
            self.assertEqual(normalized.size, (96, 96))
            bbox = normalized.getchannel("A").getbbox()
            self.assertIsNotNone(bbox)
            assert bbox is not None
            self.assertEqual(bbox[3] - 1, 91)
            self.assertGreaterEqual(bbox[3] - bbox[1], 76)
            self.assertLessEqual(bbox[3] - bbox[1], 80)
            self.assertEqual(sum(normalized.getchannel("A").histogram()[1:255]), 0)

    def test_opaque_background_is_hard_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "opaque.png"
            output = root / "normalized.png"
            Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)).save(source)

            result = normalize_and_validate(source, output, self.spec)

            self.assertFalse(result.passed)
            self.assertIn("opaque_background", result.hard_reject_reasons)
            self.assertFalse(output.exists())

    def test_empty_transparent_image_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "empty.png"
            output = root / "normalized.png"
            Image.new("RGBA", (96, 96), (0, 0, 0, 0)).save(source)

            result = normalize_and_validate(source, output, self.spec)

            self.assertFalse(result.passed)
            self.assertIn("empty_sprite", result.hard_reject_reasons)


if __name__ == "__main__":
    unittest.main()
