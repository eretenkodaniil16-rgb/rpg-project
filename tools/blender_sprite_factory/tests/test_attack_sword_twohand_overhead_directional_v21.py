from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
PROFILE_PATH = (
    FACTORY_DIR / "attack_sword_twohand_overhead_directional_profile_v21.py"
)
BUILDER_PATH = (
    FACTORY_DIR / "attack_sword_twohand_overhead_directional_builder_v21.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21.py"
)
WORKFLOW_PATH = (
    ROOT
    / ".github/workflows/validate-human-warrior-twohand-overhead-directional-v21.yml"
)


def _load_profile_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_overhead_directional_profile_v21",
        PROFILE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("directional overhead profile could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_overhead_sources_parse() -> None:
    ast.parse(PROFILE_PATH.read_text(encoding="utf-8"))
    ast.parse(BUILDER_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_directional_overhead_profile_has_four_views_of_one_cycle() -> None:
    module = _load_profile_module()
    profile = module.load_attack_sword_twohand_overhead_directional_profile_v21(
        "human_warrior_m01"
    )
    assert profile.directions == ("down", "left", "right", "up")
    assert len(profile.actions) == 4
    assert {action.grip_id for action in profile.actions} == {
        "twohand_center_high"
    }
    assert {action.source_action_id for action in profile.actions} == {
        "attack_sword_01_twohand_down_overhead_v21"
    }
    assert profile.frame_order == tuple(range(1, 9))
    assert len(module.DOWN_FRAME_SHA256) == 8
    assert module.DOWN_FRAME_SHA256[1] == module.DOWN_FRAME_SHA256[8]


def test_directional_overhead_builder_copies_without_rekeying() -> None:
    source = BUILDER_PATH.read_text(encoding="utf-8")
    required = (
        "source_action.copy()",
        'action["directional_copy_of_overhead_local_motion"] = True',
        'action["local_action_curves_changed"] = False',
        'action["root_translation_used"] = False',
        'action["mirroring_used"] = False',
        'action["negative_scale_used"] = False',
        "len(created_names) != TOTAL_ACTION_COUNT - 1",
    )
    for marker in required:
        assert marker in source


def test_directional_overhead_adapter_uses_character_local_trajectory() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "_local_overhead_target_direction",
        'context.config.directions["down"]',
        "context.rig.matrix_world.to_3x3().inverted() @ target_world",
        "context.rig.matrix_world.to_3x3() @ target_local",
        "directional_adapter._direction_calibrations",
        "PROJECTION_BY_FRAME[3] = F03_SCREEN_PROJECTION",
        '"same_local_action_curves_for_all_directions": True',
        '"character_local_weapon_trajectory_shared": True',
        '"approved_down_pass04_pixels_preserved": True',
        '"mirroring_used": False',
        '"negative_scale_used": False',
        '"weapon_geometry_changed": False',
    )
    for marker in required:
        assert marker in source


def test_directional_overhead_adapter_checks_down_pixel_identity() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    assert "frame_hashes != DOWN_FRAME_SHA256" in source
    assert "changed approved pass04 down pixels" in source
    assert "guard_sha != settle_sha" in source
    assert "TOTAL_RENDERED_FRAME_COUNT = TOTAL_RENDERED_FRAME_COUNT" in source


def test_directional_overhead_workflow_targets_new_adapter() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21.py"
        in source
    )
    assert "twohand_overhead_directional_v21_32_frames" in source
