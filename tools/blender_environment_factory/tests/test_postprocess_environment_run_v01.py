from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from environment_profile_v01 import load_environment_profile
from postprocess_environment_run_v01 import process_run


REAL_REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_CONFIG_PATH = (
    REAL_REPO_ROOT
    / "tools/blender_environment_factory/configs/cold_ancient_stone_v01.json"
)


class PostprocessEnvironmentRunV01Tests(unittest.TestCase):
    def test_synthetic_blender_run_produces_valid_review_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_value:
            repo_root = Path(temp_dir_value)
            config_path = self._prepare_fake_repo(repo_root)
            profile = load_environment_profile(config_path, repo_root)
            run_dir = profile.run_root / "unit_test_run"
            self._write_synthetic_raw_run(profile, run_dir)

            manifest_path = process_run(repo_root, config_path, run_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["validation"]["asset_count"], 33)
            self.assertTrue(manifest["validation"]["floor_variants_unique"])
            self.assertTrue(
                manifest["validation"]["floor_self_repeat_seam_safe"]
            )
            self.assertTrue(
                manifest["validation"]["arbitrary_floor_adjacency_opaque"]
            )
            self.assertTrue(manifest["approval"]["manual_review_required"])
            self.assertFalse(manifest["approval"]["approved"])
            self.assertFalse(manifest["approval"]["runtime_integrated"])

            for relative in manifest["review"].values():
                self.assertTrue((run_dir / relative).is_file(), relative)
            with Image.open(run_dir / manifest["review"]["room_preview"]) as preview:
                self.assertEqual(preview.size, (608, 608))
            with Image.open(
                run_dir / manifest["review"]["room_preview_2x"]
            ) as preview_2x:
                self.assertEqual(preview_2x.size, (1216, 1216))

            floors = [
                entry for entry in manifest["artifacts"] if entry["kind"] == "floor"
            ]
            self.assertEqual(len(floors), 8)
            floor_images = []
            try:
                floor_images = [Image.open(run_dir / entry["path"]) for entry in floors]
                for image in floor_images:
                    self.assertEqual(image.size, (64, 64))
                    self.assertEqual(self._column(image, 0), self._column(image, 63))
                    self.assertEqual(self._row(image, 0), self._row(image, 63))
                    self.assertTrue(
                        all(pixel[3] == 255 for pixel in self._column(image, 0))
                    )
            finally:
                for image in floor_images:
                    image.close()

    def _prepare_fake_repo(self, repo_root: Path) -> Path:
        payload = json.loads(REAL_CONFIG_PATH.read_text(encoding="utf-8"))
        payload["paths"]["run_root"] = "art/test_environment_runs"
        atlas_path = repo_root / payload["paths"]["character_idle_atlas"]
        atlas_path.parent.mkdir(parents=True)
        atlas = Image.new("RGBA", (96, 384), (0, 0, 0, 0))
        draw = ImageDraw.Draw(atlas)
        draw.rectangle((34, 20, 61, 90), fill=(129, 147, 157, 255))
        atlas.save(atlas_path)
        config_path = repo_root / "profile.json"
        config_path.write_text(json.dumps(payload), encoding="utf-8")
        return config_path

    def _write_synthetic_raw_run(self, profile, run_dir: Path) -> None:
        raw_dir = run_dir / "raw"
        source_dir = run_dir / "source"
        raw_dir.mkdir(parents=True)
        source_dir.mkdir()
        (source_dir / "fake.blend").write_bytes(b"BLENDER-v01-test")
        entries = []
        palette = [value.lstrip("#") for value in profile.palette_hex]
        for index, asset in enumerate(profile.assets):
            raw_size = (
                asset.canvas_width * profile.raw_render_scale,
                asset.canvas_height * profile.raw_render_scale,
            )
            image = Image.new("RGBA", raw_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            color_hex = palette[(4 + index) % len(palette)]
            color = tuple(int(color_hex[offset : offset + 2], 16) for offset in (0, 2, 4))
            if asset.kind == "floor":
                draw.rectangle((0, 0, raw_size[0] - 1, raw_size[1] - 1), fill=(*color, 255))
                center_color_hex = palette[(9 + index) % len(palette)]
                center_color = tuple(
                    int(center_color_hex[offset : offset + 2], 16)
                    for offset in (0, 2, 4)
                )
                inset = 18 + index
                draw.rectangle(
                    (inset, inset, raw_size[0] - inset - 1, raw_size[1] - inset - 1),
                    fill=(*center_color, 255),
                )
            else:
                inset = 18
                draw.rounded_rectangle(
                    (inset, inset, raw_size[0] - inset - 1, raw_size[1] - inset - 1),
                    radius=12,
                    fill=(*color, 255),
                )
            raw_path = raw_dir / f"{asset.asset_id}_raw.png"
            image.save(raw_path)
            entries.append(
                {
                    "asset_id": asset.asset_id,
                    "kind": asset.kind,
                    "canvas": [asset.canvas_width, asset.canvas_height],
                    "raw_canvas": [raw_size[0], raw_size[1]],
                    "raw_path": raw_path.relative_to(run_dir).as_posix(),
                    "anchor": [asset.canvas_width // 2, asset.canvas_height - 8],
                }
            )
        manifest = {
            "schema_version": 1,
            "factory_id": "blender_environment_factory_v01",
            "profile_id": profile.profile_id,
            "profile_sha256": profile.profile_sha256,
            "stage": "review_candidate",
            "run_id": "unit_test_run",
            "blender_version": "5.2.0",
            "source_blend": "source/fake.blend",
            "camera": {
                "projection": "ORTHOGRAPHIC",
                "elevation_degrees": 47.0,
                "raw_render_scale": 3,
            },
            "game_contract": profile.payload["game_contract"],
            "lighting_contract": {
                "neutral_only": True,
                "local_light_baked_into_floor": False,
                "arcane_emission_has_light_spill": False,
            },
            "artifacts": entries,
        }
        (run_dir / "raw_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    @staticmethod
    def _column(image: Image.Image, x: int):
        pixels = image.load()
        return tuple(pixels[x, y] for y in range(image.height))

    @staticmethod
    def _row(image: Image.Image, y: int):
        pixels = image.load()
        return tuple(pixels[x, y] for x in range(image.width))


if __name__ == "__main__":
    unittest.main()
