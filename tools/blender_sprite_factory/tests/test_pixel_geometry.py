from __future__ import annotations

import unittest

from pixel_geometry import alpha_bbox, anchor_rgba_to_baseline


class PixelGeometryTests(unittest.TestCase):
    def test_observed_one_pixel_drift_is_anchored_to_contract_baseline(self) -> None:
        width = 96
        height = 96
        pixels = self._canvas(width, height)
        self._set_pixel(pixels, width, x=47, y=5, rgba=(0.2, 0.3, 0.4, 1.0))
        self._set_pixel(pixels, width, x=48, y=82, rgba=(0.5, 0.6, 0.7, 1.0))
        original_bbox = alpha_bbox(pixels, width, height, 0.5)
        self.assertIsNotNone(original_bbox)
        self.assertEqual(height - 1 - original_bbox[1], 90)

        anchored, bbox = anchor_rgba_to_baseline(
            pixels,
            width,
            height,
            baseline_y=91,
            threshold=0.5,
        )

        self.assertEqual(bbox, (47, 4, 48, 81))
        self.assertEqual(height - 1 - bbox[1], 91)
        self.assertEqual(alpha_bbox(anchored, width, height, 0.5), bbox)
        self.assertEqual(
            self._pixel_at(anchored, width, x=47, y=4),
            [0.2, 0.3, 0.4, 1.0],
        )
        self.assertEqual(
            self._pixel_at(anchored, width, x=48, y=81),
            [0.5, 0.6, 0.7, 1.0],
        )

    def test_canvas_already_on_baseline_is_not_shifted(self) -> None:
        width = 4
        height = 5
        pixels = self._canvas(width, height)
        self._set_pixel(pixels, width, x=1, y=1, rgba=(1.0, 0.0, 0.0, 1.0))

        anchored, bbox = anchor_rgba_to_baseline(
            pixels,
            width,
            height,
            baseline_y=3,
            threshold=0.5,
        )

        self.assertEqual(anchored, pixels)
        self.assertEqual(bbox, (1, 1, 1, 1))

    def test_anchor_rejects_vertical_cropping(self) -> None:
        width = 3
        height = 4
        pixels = self._canvas(width, height)
        self._set_pixel(pixels, width, x=1, y=0, rgba=(1.0, 1.0, 1.0, 1.0))
        self._set_pixel(pixels, width, x=1, y=3, rgba=(1.0, 1.0, 1.0, 1.0))

        with self.assertRaisesRegex(ValueError, "would crop visible pixels"):
            anchor_rgba_to_baseline(
                pixels,
                width,
                height,
                baseline_y=2,
                threshold=0.5,
            )

    @staticmethod
    def _canvas(width: int, height: int) -> list[float]:
        return [0.0] * (width * height * 4)

    @staticmethod
    def _set_pixel(
        pixels: list[float],
        width: int,
        x: int,
        y: int,
        rgba: tuple[float, float, float, float],
    ) -> None:
        start = (y * width + x) * 4
        pixels[start : start + 4] = rgba

    @staticmethod
    def _pixel_at(
        pixels: list[float],
        width: int,
        x: int,
        y: int,
    ) -> list[float]:
        start = (y * width + x) * 4
        return pixels[start : start + 4]


if __name__ == "__main__":
    unittest.main()
