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


def _opaque_component_sizes(alpha: Image.Image) -> list[int]:
    pixels = alpha.load()
    visited: set[tuple[int, int]] = set()
    sizes: list[int] = []
    for y in range(CELL_SIZE):
        for x in range(CELL_SIZE):
            if pixels[x, y] == 0 or (x, y) in visited:
                continue
            pending = [(x, y)]
            visited.add((x, y))
            size = 0
            while pending:
                current_x, current_y = pending.pop()
                size += 1
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < CELL_SIZE and 0 <= next_y < CELL_SIZE):
                        continue
                    if pixels[next_x, next_y] == 0 or (next_x, next_y) in visited:
                        continue
                    visited.add((next_x, next_y))
                    pending.append((next_x, next_y))
            sizes.append(size)
    return sorted(sizes, reverse=True)


class HumanWarriorAnimationAssetsV01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    def test_manifest_contract(self) -> None:
        self.assertEqual(self.manifest["character_id"], "human_warrior_m01")
        self.assertEqual(self.manifest["revision"], "animation_assets_v01")
        self.assertEqual(self.manifest["art_status"], "approved")
        self.assertTrue(self.manifest["runtime_connected"])
        self.assertEqual(self.manifest["cell_size"], CELL_SIZE)
        self.assertEqual(self.manifest["baseline_y"], 91)
        self.assertEqual(self.manifest["direction_order"], list(DIRECTION_ORDER))
        self.assertEqual(len(self.manifest["sets"]), 13)

        runtime = dict(self.manifest["runtime"])
        self.assertEqual(
            runtime["visual_controller"],
            "res://scripts/game/player.gd",
        )
        self.assertEqual(
            runtime["animation_event"],
            "AnimatedSprite2D.frame_changed",
        )
        self.assertEqual(runtime["contact_frame_number"], 4)
        self.assertTrue(runtime["movement_locked_during_attack"])
        self.assertTrue(runtime["repeat_attack_locked"])
        self.assertEqual(runtime["hit_reaction_damage_threshold"], 1)
        self.assertTrue(runtime["hit_reaction_movement_locked"])
        self.assertTrue(runtime["hit_reaction_facing_locked"])
        self.assertTrue(runtime["death_priority_over_hit"])
        self.assertTrue(runtime["death_priority_over_attack_and_movement"])
        self.assertTrue(runtime["death_confirmed_state_only"])
        self.assertEqual(runtime["death_transition_minimum_seconds"], 0.8)

        death_runtime = dict(self.manifest["death_runtime"])
        self.assertEqual(
            death_runtime["selection_policy"],
            "weighted_without_immediate_repeat",
        )
        self.assertEqual(death_runtime["fallback_variant_id"], "death_01_base")
        self.assertEqual(death_runtime["duration_seconds"], 0.8)
        self.assertEqual(death_runtime["corpse_hold_frame"], 8)
        self.assertTrue(death_runtime["final_pose_persistent"])
        self.assertTrue(death_runtime["weapon_agnostic"])
        self.assertTrue(death_runtime["confirmed_dead_only"])
        self.assertEqual(
            [entry["death_variant_id"] for entry in death_runtime["variants"]],
            ["death_01_base", "death_02_base", "death_03_base"],
        )
        self.assertEqual(
            [entry["weight"] for entry in death_runtime["variants"]],
            [1.0, 1.0, 1.0],
        )

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
            settle_contract = dict(
                spec.get("first_last_identical_by_direction", {})
            )
            final_hold_contract = dict(
                spec.get("final_hold_identical_by_direction", {})
            )

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

                if settle_contract:
                    self.assertEqual(
                        cells[0].tobytes() == cells[-1].tobytes(),
                        bool(settle_contract[direction]),
                        f"settle contract: {set_id}/{direction}",
                    )
                if final_hold_contract:
                    self.assertFalse(bool(spec["loop"]))
                    self.assertEqual(frame_count, 8)
                    self.assertEqual(float(spec["fps"]), 10.0)
                    self.assertEqual(int(spec["corpse_hold_frame"]), 8)
                    self.assertEqual(
                        cells[-2].tobytes() == cells[-1].tobytes(),
                        bool(final_hold_contract[direction]),
                        f"final hold contract: {set_id}/{direction}",
                    )

                if set_id == "death_03_base":
                    for frame_number in (6, 7, 8):
                        component_sizes = _opaque_component_sizes(
                            cells[frame_number - 1].getchannel("A")
                        )
                        self.assertGreaterEqual(
                            len(component_sizes),
                            2,
                            f"weapon separation: {set_id}/{direction}/f{frame_number:02d}",
                        )
                        self.assertGreaterEqual(component_sizes[1], 120)
                        self.assertGreaterEqual(
                            component_sizes[1] / component_sizes[0],
                            0.20,
                        )

    def test_lock_hashes_match(self) -> None:
        hashes = dict(self.lock["existing_atlas_sha256"])
        for attack in self.lock["attack_atlases"].values():
            hashes[Path(str(attack["path"])).name] = str(attack["sha256"])
        for hit in self.lock["hit_atlases"].values():
            hashes[Path(str(hit["path"])).name] = str(hit["sha256"])
        for death in self.lock["death_atlases"].values():
            hashes[Path(str(death["path"])).name] = str(death["sha256"])
            self.assertEqual(death["size"], [768, 384])
            self.assertEqual(
                death["source_run_manifest_sha256"],
                "857f0dc53619611edf40a481768a5fbfec51ae98149fca6768c336e29a0688f3",
            )
        self.assertEqual(len(hashes), 13)
        for name, expected in hashes.items():
            self.assertEqual(
                hashlib.sha256((ATLAS_DIR / name).read_bytes()).hexdigest(),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
