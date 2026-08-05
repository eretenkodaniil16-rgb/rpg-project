from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from sprite_pipeline.config import load_config
from sprite_pipeline.pipeline import SpritePipeline


class ManualValidationTests(unittest.TestCase):
    def test_manual_validation_writes_selected_contact_sheet_and_reports(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        config = load_config(
            repo_root / "tools/sprite_pipeline/configs/human_warrior_m01.json",
            repo_root,
        )
        pipeline = SpritePipeline(config)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_dir = root / "input"
            output_root = root / "runs"
            input_dir.mkdir()

            valid = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            draw = ImageDraw.Draw(valid)
            draw.rectangle((190, 70, 320, 449), fill=(80, 45, 25, 255))
            draw.rectangle((225, 85, 285, 165), fill=(225, 185, 155, 255))
            valid.save(input_dir / "candidate_valid.png")

            Image.new("RGBA", (256, 256), (255, 0, 255, 255)).save(
                input_dir / "candidate_opaque.png"
            )

            run_dir = pipeline.validate_directory(
                frame_id="walk_down_f01",
                input_dir=input_dir,
                output_root=output_root,
                top_k=1,
            )

            self.assertTrue((run_dir / "selected/contact_sheet.png").is_file())
            self.assertTrue((run_dir / "report.md").is_file())
            self.assertTrue((run_dir / "report.json").is_file())
            self.assertTrue((run_dir / "technical_report.json").is_file())
            self.assertTrue((run_dir / "rejected_raw/candidate_opaque.png").is_file())

            selected = list((run_dir / "selected").glob("rank_*.png"))
            self.assertEqual(len(selected), 1)

            payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "manual")
            self.assertEqual(payload["frame_id"], "walk_down_f01")
            self.assertEqual(payload["candidate_count"], 2)
            self.assertEqual(payload["passed_count"], 1)
            self.assertEqual(payload["rejected_count"], 1)
            self.assertEqual(len(payload["selected"]), 1)


if __name__ == "__main__":
    unittest.main()
