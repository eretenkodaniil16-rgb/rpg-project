from __future__ import annotations

import unittest
from pathlib import Path


class WalkHistoricalEntrypointsTests(unittest.TestCase):
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

    def test_historical_direction_and_combat_adapters_remain_available(self) -> None:
        for adapter_name, render_name in (
            ("blender_sprite_factory_walk_left_v01.py", "render_pilot_walk_left_v01"),
            ("blender_sprite_factory_walk_right_v01.py", "render_pilot_walk_right_v01"),
            ("blender_sprite_factory_walk_up_v01.py", "render_pilot_walk_up_v01"),
            (
                "blender_sprite_factory_combat_idle_down_v01.py",
                "render_pilot_combat_idle_down_v01",
            ),
            (
                "blender_sprite_factory_combat_idle_down_variants_v02.py",
                "render_pilot_combat_idle_down_variants_v02",
            ),
            (
                "blender_sprite_factory_combat_idle_down_variants_v03.py",
                "render_pilot_combat_idle_down_variants_v03",
            ),
            (
                "blender_sprite_factory_combat_idle_down_variants_v04.py",
                "render_pilot_combat_idle_down_variants_v04",
            ),
            (
                "blender_sprite_factory_combat_idle_down_weapon_variants_v05.py",
                "render_weapon_stance_variants_v05",
            ),
            (
                "blender_sprite_factory_combat_idle_down_weapon_variants_v06.py",
                "render_weapon_stance_variants_v06",
            ),
            (
                "blender_sprite_factory_combat_idle_down_weapon_variants_v07.py",
                "render_weapon_stance_variants_v07",
            ),
            (
                "blender_sprite_factory_combat_idle_down_weapon_variants_v08.py",
                "render_weapon_stance_variants_v08",
            ),
            (
                "blender_sprite_factory_combat_idle_down_weapon_variants_v09.py",
                "render_weapon_stance_variants_v09",
            ),
            (
                "blender_sprite_factory_combat_idle_down_cycles_v10.py",
                "render_combat_idle_cycles_v10",
            ),
            (
                "blender_sprite_factory_combat_idle_directional_v11.py",
                "render_combat_idle_directional_v11",
            ),
            (
                "blender_sprite_factory_combat_idle_directional_weapon_v12.py",
                "render_combat_idle_directional_weapon_v12",
            ),
            (
                "blender_sprite_factory_combat_idle_directional_weapon_v13.py",
                "render_combat_idle_directional_weapon_v13",
            ),
        ):
            adapter = self.tool_root / adapter_name
            self.assertTrue(adapter.is_file())
            self.assertIn(render_name, adapter.read_text(encoding="utf-8"))
        self.assertTrue(
            (self.tool_root / "blender_sprite_factory_walk_up_v02.py").is_file()
        )

    def test_windows_launcher_advances_to_directional_cycles_v14_adapter(self) -> None:
        self.assertIn(
            '$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_combat_idle_directional_cycles_v14.py"',
            self.launcher,
        )
        self.assertIn(
            "Artist-approved directional source: blender_sprite_factory_combat_idle_directional_weapon_v12.py",
            self.launcher,
        )
        self.assertIn(
            "Rejected boundary-touch experiment: blender_sprite_factory_combat_idle_directional_weapon_v13.py",
            self.launcher,
        )

    def test_ci_uses_directional_cycles_v14_real_blender_render(self) -> None:
        self.assertIn("render-combat-idle-directional-cycles-v14:", self.workflow)
        self.assertIn(
            "--python tools/blender_sprite_factory/blender_sprite_factory_combat_idle_directional_cycles_v14.py",
            self.workflow,
        )
        self.assertIn(
            "human_warrior_m01_proxy_v25_appearance_v03_walk_down_v04_walk_left_v01_walk_right_v01_walk_up_v02_combat_idle_directional_cycles_v14_",
            self.workflow,
        )
        for marker in (
            "render-combat-idle-down-v01 (technical baseline)",
            "render-combat-idle-down-weapon-variants-v06",
            "render-combat-idle-down-weapon-variants-v07",
            "render-combat-idle-down-weapon-variants-v08",
            "render-combat-idle-down-weapon-variants-v09",
            "render-combat-idle-down-cycles-v10",
            "render-combat-idle-directional-v11",
            "render-combat-idle-directional-weapon-v12",
            "render-combat-idle-directional-weapon-v13",
        ):
            self.assertIn(marker, self.workflow)


if __name__ == "__main__":
    unittest.main()
