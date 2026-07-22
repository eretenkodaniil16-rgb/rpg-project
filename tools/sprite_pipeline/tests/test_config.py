from __future__ import annotations

import unittest
from pathlib import Path

from sprite_pipeline.config import load_config


class PipelineConfigTests(unittest.TestCase):
    def _config(self):
        repo_root = Path(__file__).resolve().parents[3]
        manifest = repo_root / "tools/sprite_pipeline/configs/human_warrior_m01.json"
        return load_config(manifest, repo_root)

    def test_human_warrior_manifest_is_bounded_and_locked(self) -> None:
        config = self._config()

        self.assertEqual(config.character_id, "human_warrior_m01")
        self.assertFalse(config.ready)
        self.assertEqual(
            list(config.frames),
            [
                "walk_down_f01",
                "walk_down_f02",
                "walk_down_f03",
                "walk_down_f04",
                "walk_down_f05",
                "walk_down_f06",
            ],
        )
        self.assertEqual(config.technical.canvas_width, 96)
        self.assertEqual(config.technical.canvas_height, 96)
        self.assertGreaterEqual(config.technical.sprite_height_min, 76)
        self.assertLessEqual(config.technical.sprite_height_max, 80)
        self.assertLessEqual(config.generation.initial_candidates, 10)
        self.assertLessEqual(config.generation.max_rounds, 2)
        self.assertAlmostEqual(sum(config.weights.values()), 1.0)
        self.assertIn("identity_face", config.weights)
        self.assertIn("physical_equipment_sides_swapped", config.hard_reject_labels)

    def test_master_and_pose_prompts_are_combined(self) -> None:
        config = self._config()

        prompt = config.load_prompt("walk_down_f01")

        self.assertIn("ЭТО НЕ НОВАЯ ГЕНЕРАЦИЯ", prompt)
        self.assertIn("контакт физической левой ноги", prompt)
        self.assertIn("ФИЗИЧЕСКОЙ ЛЕВОЙ", prompt)

    def test_extra_reference_cannot_escape_repository(self) -> None:
        config = self._config()

        with self.assertRaisesRegex(ValueError, "выходит за разрешённый каталог"):
            config.reference_paths("walk_down_f01", "../../../../etc/passwd")

    def test_prompt_path_cannot_escape_pipeline_root(self) -> None:
        config = self._config()

        with self.assertRaisesRegex(ValueError, "выходит за разрешённый каталог"):
            config.resolve_pipeline_path("../../../README.md")


if __name__ == "__main__":
    unittest.main()
