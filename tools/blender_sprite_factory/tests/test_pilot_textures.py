from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image

from factory_config import load_factory_config
from generate_pilot_textures import _make_texture


class PilotTextureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]
        cls.config = load_factory_config(
            cls.repo_root
            / "tools/blender_sprite_factory/configs/human_warrior_m01.json",
            cls.repo_root,
        )

    def test_all_texture_slots_are_small_opaque_pixel_textures(self) -> None:
        for slot in self.config.material_slots.values():
            with self.subTest(slot=slot.slot_id):
                with Image.open(slot.texture_path) as image:
                    rgba = image.convert("RGBA")
                    raw = rgba.tobytes()
                    pixels = {
                        tuple(raw[index : index + 4])
                        for index in range(0, len(raw), 4)
                    }
                    self.assertEqual(rgba.size, (16, 16))
                    self.assertEqual(rgba.mode, "RGBA")
                    self.assertEqual({alpha for _, _, _, alpha in pixels}, {255})
                    self.assertGreater(len(pixels), 1)
                    self.assertLessEqual(len(pixels), 12)

    def test_committed_textures_match_deterministic_generator(self) -> None:
        for slot in self.config.material_slots.values():
            with self.subTest(slot=slot.slot_id):
                generated = _make_texture(slot)
                with Image.open(slot.texture_path) as committed:
                    self.assertEqual(
                        generated.tobytes(),
                        committed.convert("RGBA").tobytes(),
                    )


if __name__ == "__main__":
    unittest.main()
