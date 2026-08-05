from __future__ import annotations

import ast
import importlib.util
from dataclasses import fields
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
PROFILE_PATH = FACTORY_DIR / "attack_sword_twohand_down_overhead_profile_v21.py"
ADAPTER_PATH = (
    FACTORY_DIR / "blender_sprite_factory_attack_sword_twohand_down_overhead_v21.py"
)
WORKFLOW_PATH = (
    ROOT / ".github/workflows/validate-human-warrior-attack-twohand-overhead-v21.yml"
)


def _load_profile() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_down_overhead_profile_v21",
        PROFILE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("overhead profile could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pose_values(pose: object) -> tuple[float, ...]:
    return tuple(
        float(getattr(pose, item.name))
        for item in fields(type(pose))
        if item.name not in ("frame", "phase")
    )


def test_overhead_sources_parse() -> None:
    ast.parse(PROFILE_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_overhead_cycle_starts_and_ends_at_exact_guard() -> None:
    profile = _load_profile()
    poses = profile.TWOHAND_OVERHEAD_POSES
    assert tuple(item.frame for item in poses) == tuple(range(1, 9))
    assert tuple(item.phase for item in poses) == (
        "guard",
        "windup",
        "anticipation",
        "contact",
        "follow_through",
        "rebound",
        "recovery",
        "settle",
    )
    assert not any(_pose_values(poses[0]))
    assert not any(_pose_values(poses[7]))


def test_overhead_cycle_has_no_sideways_body_twist() -> None:
    profile = _load_profile()
    for pose in profile.TWOHAND_OVERHEAD_POSES[1:7]:
        assert pose.pelvis_x == 0.0
        assert pose.pelvis_roll_z_degrees == 0.0
        assert pose.chest_yaw_z_degrees == 0.0
        assert pose.head_yaw_z_degrees == 0.0
        assert pose.upper_arm_left_x_degrees == pose.upper_arm_right_x_degrees
        assert pose.forearm_left_x_degrees == pose.forearm_right_x_degrees
        assert pose.hand_left_x_degrees == pose.hand_right_x_degrees
        assert pose.upper_arm_left_z_degrees == -pose.upper_arm_right_z_degrees
        assert pose.forearm_left_z_degrees == -pose.forearm_right_z_degrees
        assert pose.hand_left_z_degrees == -pose.hand_right_z_degrees


def test_overhead_cycle_moves_from_raise_to_vertical_contact() -> None:
    profile = _load_profile()
    anticipation = profile.TWOHAND_OVERHEAD_POSES[2]
    contact = profile.TWOHAND_OVERHEAD_POSES[3]
    follow = profile.TWOHAND_OVERHEAD_POSES[4]
    assert anticipation.upper_arm_left_x_degrees <= -30.0
    assert contact.upper_arm_left_x_degrees >= 36.0
    assert follow.upper_arm_left_x_degrees > contact.upper_arm_left_x_degrees
    assert contact.spine_pitch_x_degrees < 0.0
    assert follow.spine_pitch_x_degrees < contact.spine_pitch_x_degrees


def test_overhead_profile_preserves_onehand_and_sources() -> None:
    profile = _load_profile()
    result = profile.load_attack_sword_twohand_down_overhead_profile_v21(
        "human_warrior_m01"
    )
    assert result.grips[0].action_id == "attack_sword_01_onehand_down_v20"
    assert result.grips[1].action_id == profile.OVERHEAD_ACTION_ID
    assert result.grips[1].trajectory_id == profile.OVERHEAD_TRAJECTORY_ID
    assert result.grips[1].stance_variant_id == "twohand_center_high"
    assert result.grips[1].weapon_cycle_id == "twohand_center_high"


def test_overhead_adapter_keeps_review_isolated() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "load_attack_sword_twohand_down_overhead_profile_v21",
        "_apply_overhead_contract",
        "_restore_overhead_contract",
        "guard_settle_pixel_identical",
        '"onehand_cycle_changed": False',
        '"approved_down_v20_replaced": False',
        '"runtime_connected": False',
        '"root_translation_used": False',
        '"mirroring_used": False',
        '"negative_scale_used": False',
        '"weapon_geometry_changed": False',
    )
    for marker in required:
        assert marker in source


def test_overhead_workflow_targets_review_entrypoint() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "blender_sprite_factory_attack_sword_twohand_down_overhead_v21.py" in source
    assert "human_warrior_m01_proxy_v25_twohand_down_overhead_v21" in source
