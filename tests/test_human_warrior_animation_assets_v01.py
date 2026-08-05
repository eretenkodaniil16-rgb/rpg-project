from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "data/visuals/human_warrior_m01_animation_assets_v01.json"
LOCK_PATH = REPO_ROOT / "data/visuals/human_warrior_m01_animation_assets_v01.lock.json"
ATLAS_DIR = REPO_ROOT / "assets/characters/human/warrior_m01/gameplay/approved/atlases"
CELL_SIZE = 96
DIRECTION_ORDER = ("down", "left", "right", "up")
ZERO_EDGE_COUNTS = {"left": 0, "right": 0, "top": 0, "bottom": 0}


def _edge_alpha_counts(alpha: Image.Image) -> dict[str, int]:
    pixels = alpha.load()
    return {
        "left": sum(pixels[0, y] > 0 for y in range(CELL_SIZE)),
        "right": sum(pixels[CELL_SIZE - 1, y] > 0 for y in range(CELL_SIZE)),
        "top": sum(pixels[x, 0] > 0 for x in range(CELL_SIZE)),
        "bottom": sum(pixels[x, CELL_SIZE - 1] > 0 for x in range(CELL_SIZE)),
    }


class HumanWarriorAnimationAssetsV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    def test_manifest_contract(self) -> None:
        self.assertEqual(self.manifest["character_id"], "human_warrior_m01")
        self.assertEqual(self.manifest["revision"], "animation_assets_v01")
        self.assertEqual(self.manifest["art_status"], "approved")
        self.assertFalse(self.manifest["runtime_connected"])
        self.assertEqual(self.manifest["cell_size"], CELL_SIZE)
        self.assertEqual(self.manifest["baseline_y"], 91)
        self.assertEqual(self.manifest["direction_order"], list(DIRECTION_ORDER))
        self.assertEqual(len(self.manifest["sets"]), 8)

    def test_all_atlases(self) -> None:
        for set_id, spec in self.manifest["sets"].items():
            path = REPO_ROOT / str(spec["sheet_path"]).removeprefix("res://")
            self.assertTrue(path.is_file(), f"missing atlas: {set_id}")
            image = Image.open(path).convert("RGBA")
            frame_count = int(spec["frame_count"])
            self.assertEqual(
                image.size,
                (CELL_SIZE * frame_count, CELL_SIZE * len(DIRECTION_ORDER)),
            )
            self.assertTrue(set(image.getchannel("A").getdata()).issubset({0, 255}))
            edge_exceptions = dict(spec.get("edge_alpha_exceptions", {}))

            for row, direction in enumerate(DIRECTION_ORDER):
                cells: list[Image.Image] = []
                for column in range(frame_count):
                    frame_number = column + 1
                    cell = image.crop(
                        (
                            column * CELL_SIZE,
                            row * CELL_SIZE,
                            (column + 1) * CELL_SIZE,
                            (row + 1) * CELL_SIZE,
                        )
                    )
                    cells.append(cell)
                    alpha = cell.getchannel("A")
                    bbox = alpha.getbbox()
                    self.assertIsNotNone(
                        bbox,
                        f"empty cell: {set_id}/{direction}/f{frame_number:02d}",
                    )
                    assert bbox is not None
                    self.assertEqual(
                        bbox[3] - 1,
                        91,
                        f"baseline: {set_id}/{direction}/f{frame_number:02d}",
                    )
                    if bool(spec.get("edge_alpha_required", False)):
                        frame_key = f"{direction}/f{frame_number:02d}"
                        expected_edges = dict(
                            edge_exceptions.get(frame_key, ZERO_EDGE_COUNTS)
                        )
                        self.assertEqual(
                            _edge_alpha_counts(alpha),
                            expected_edges,
                            f"edge alpha: {set_id}/{frame_key}",
                        )
                if bool(spec.get("first_last_identical", False)):
                    self.assertEqual(cells[0].tobytes(), cells[-1].tobytes())

    def test_lock_hashes_match(self) -> None:
        hashes = dict(self.lock["existing_atlas_sha256"])
        for attack in self.lock["attack_atlases"].values():
            hashes[Path(str(attack["path"])).name] = str(attack["sha256"])
        self.assertEqual(len(hashes), 8)
        for name, expected in hashes.items():
            self.assertEqual(
                hashlib.sha256((ATLAS_DIR / name).read_bytes()).hexdigest(),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
