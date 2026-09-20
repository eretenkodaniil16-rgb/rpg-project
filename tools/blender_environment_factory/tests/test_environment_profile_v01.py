from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from environment_profile_v01 import load_environment_profile


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    REPO_ROOT
    / "tools/blender_environment_factory/configs/cold_ancient_stone_v01.json"
)


class EnvironmentProfileV01Tests(unittest.TestCase):
    def test_profile_locks_real_game_and_character_contracts(self) -> None:
        profile = load_environment_profile(CONFIG_PATH, REPO_ROOT)

        self.assertEqual(profile.tile_size, 64)
        self.assertEqual(profile.character_sprite_canvas, 96)
        self.assertEqual(profile.elevation_degrees, 47.0)
        self.assertEqual(profile.raw_render_scale, 3)
        self.assertEqual(profile.stage, "review_candidate")
        self.assertEqual(profile.payload["game_contract"]["runtime_filter"], "NEAREST")
        self.assertFalse(
            profile.payload["game_contract"]["local_light_baked_into_floor"]
        )
        self.assertEqual(
            profile.payload["seam_contract"]["mode"],
            "per_variant_opposite_edge_harmonization",
        )
        self.assertTrue(
            profile.payload["seam_contract"][
                "arbitrary_adjacency_requires_opaque_edges"
            ]
        )

    def test_profile_contains_complete_first_review_set(self) -> None:
        profile = load_environment_profile(CONFIG_PATH, REPO_ROOT)

        self.assertEqual(len(profile.assets), 33)
        self.assertEqual(len(profile.assets_of_kind("floor")), 8)
        self.assertEqual(len(profile.assets_of_kind("decal")), 6)
        self.assertEqual(len(profile.assets_of_kind("transition")), 4)
        self.assertEqual(len(profile.assets_of_kind("wall_edge")), 4)
        self.assertEqual(len(profile.assets_of_kind("wall_corner")), 4)
        self.assertEqual(len(profile.assets_of_kind("door")), 4)
        self.assertEqual(len(profile.assets_of_kind("stairs")), 1)
        self.assertEqual(len(profile.assets_of_kind("arcane")), 2)
        self.assertEqual(
            {asset.state for asset in profile.assets_of_kind("door")},
            {"closed", "open"},
        )

    def test_profile_rejects_accidental_96_pixel_combat_grid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_value:
            temp_dir = Path(temp_dir_value)
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            payload["game_contract"]["combat_cell_size"] = 96
            payload["paths"]["run_root"] = "runs"
            atlas = temp_dir / payload["paths"]["character_idle_atlas"]
            atlas.parent.mkdir(parents=True)
            Image.new("RGBA", (96, 384), (0, 0, 0, 0)).save(atlas)
            config = temp_dir / "profile.json"
            config.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "текущей сеткой 64"):
                load_environment_profile(config, temp_dir)


if __name__ == "__main__":
    unittest.main()
