from __future__ import annotations

import unittest
from pathlib import Path


class WalkSideHistoricalEntrypointsV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.repo_root = cls.tool_root.parents[1]
        cls.launcher = (cls.tool_root / "run_blender_sprite_pilot.ps1").read_text(
            encoding="ascii"
        )
        cls.workflow = (
            cls.repo_root / ".github/workflows/validate-blender-sprite-factory.yml"
        ).read_text(encoding="utf-8")

    def test_historical_side_adapters_remain_available(self) -> None:
        for adapter_name, render_name, builder_name in (
            (
                "blender_sprite_factory_walk_left_v01.py",
                "render_pilot_walk_left_v01",
                "create_walk_left_actions_v01",
            ),
            (
                "blender_sprite_factory_walk_right_v01.py",
                "render_pilot_walk_right_v01",
                "create_walk_right_actions_v01",
            ),
        ):
            adapter = self.tool_root / adapter_name
            self.assertTrue(adapter.is_file())
            source = adapter.read_text(encoding="utf-8")
            self.assertIn(render_name, source)
            self.assertIn(builder_name, source)

    def test_windows_launcher_advances_to_walk_up_v01_adapter(self) -> None:
        self.assertIn(
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_walk_up_v01.py"',
            self.launcher,
        )

    def test_ci_uses_walk_up_v01_real_blender_render(self) -> None:
        self.assertIn("render-walk-up-v01:", self.workflow)
        self.assertIn(
            "--python tools/blender_sprite_factory/blender_sprite_factory_walk_up_v01.py",
            self.workflow,
        )
        self.assertIn(
            "human_warrior_m01_proxy_v25_appearance_v03_walk_down_v04_walk_left_v01_walk_right_v01_walk_up_v01_",
            self.workflow,
        )


if __name__ == "__main__":
    unittest.main()
