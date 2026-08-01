from __future__ import annotations

import ast
import unittest
from pathlib import Path


class WalkDirectionalWeaponRenderV16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.source = (
            cls.tool_root
            / "blender_sprite_factory_walk_directional_weapon_render_v16.py"
        ).read_text(encoding="utf-8")

    def test_adapter_parses_and_keeps_v15_as_animation_source(self) -> None:
        ast.parse(self.source)
        self.assertIn(
            "previous_adapter.create_walk_directional_weapon_actions_v15",
            self.source,
        )
        self.assertIn('"source_animation_stage": "walk_directional_weapon_v15"', self.source)
        self.assertNotIn("factory._new_action", self.source)

    def test_manifest_writer_restores_unpatched_base_writer(self) -> None:
        self.assertIn(
            "BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest",
            self.source,
        )
        self.assertIn("active_writer = factory._write_run_manifest", self.source)
        self.assertIn(
            "factory._write_run_manifest = BASE_WRITE_RUN_MANIFEST",
            self.source,
        )
        self.assertIn("finally:", self.source)
        self.assertIn("factory._write_run_manifest = active_writer", self.source)
        self.assertIn('"base_manifest_writer_restored": True', self.source)

    def test_render_reuses_calibration_directories_and_safe_framing(self) -> None:
        self.assertIn("raw_dir.mkdir(exist_ok=True)", self.source)
        self.assertIn("frame_dir.mkdir(exist_ok=True)", self.source)
        self.assertIn("TWOHAND_RIGHT_RENDER_SCALE_FACTOR = 0.975", self.source)
        self.assertIn(
            'grip_id == "twohand_center_high" and direction == "right"',
            self.source,
        )
        self.assertNotIn("scale.x = -1", self.source)
        self.assertNotIn("scale[0] = -1", self.source)


if __name__ == "__main__":
    unittest.main()
