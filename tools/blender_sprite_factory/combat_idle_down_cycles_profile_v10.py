from __future__ import annotations

from dataclasses import dataclass, replace

from combat_idle_down_profile_v01 import CombatIdleDownPoseV01
from combat_idle_down_weapon_variants_profile_v05 import WeaponStanceVariantV05
from combat_idle_down_weapon_variants_profile_v09 import load_weapon_stance_profile_v09


@dataclass(frozen=True)
class CombatIdleCycleFrameV10:
    pose: CombatIdleDownPoseV01
    hand_left_x_degrees: float
    hand_left_z_degrees: float
    chest_lift_z: float


@dataclass(frozen=True)
class CombatIdleCycleV10:
    cycle_id: str
    display_name: str
    animation_id: str
    grip_mode: str
    weapon_variant_id: str
    source_animation_id: str
    source_revision: str
    weapon_id: str
    fps: int
    loop: bool
    frames: tuple[CombatIdleCycleFrameV10, ...]


@dataclass(frozen=True)
class CombatIdleCyclesProfileV10:
    character_id: str
    revision: str
    direction: str
    cycles: tuple[CombatIdleCycleV10, ...]


FRAME_ORDER = (1, 2, 3, 4)
PHASE_ORDER = ("base", "inhale", "settle", "exhale")
COMBAT_IDLE_CYCLE_FPS = 4


def _frame(
    source: WeaponStanceVariantV05,
    *,
    frame: int,
    phase: str,
    chest_lift_z: float,
    spine_pitch_delta: float = 0.0,
    chest_yaw_delta: float = 0.0,
    head_yaw_delta: float = 0.0,
    upper_arm_left_x_delta: float = 0.0,
    upper_arm_left_z_delta: float = 0.0,
    forearm_left_x_delta: float = 0.0,
    forearm_left_z_delta: float = 0.0,
    upper_arm_right_x_delta: float = 0.0,
    upper_arm_right_z_delta: float = 0.0,
    forearm_right_x_delta: float = 0.0,
    forearm_right_z_delta: float = 0.0,
    cloth_left_delta: float = 0.0,
    cloth_center_delta: float = 0.0,
    cloth_right_delta: float = 0.0,
) -> CombatIdleCycleFrameV10:
    pose = source.pose
    return CombatIdleCycleFrameV10(
        pose=replace(
            pose,
            frame=frame,
            phase=phase,
            spine_pitch_x_degrees=pose.spine_pitch_x_degrees + spine_pitch_delta,
            chest_yaw_z_degrees=pose.chest_yaw_z_degrees + chest_yaw_delta,
            head_yaw_z_degrees=pose.head_yaw_z_degrees + head_yaw_delta,
            upper_arm_left_x_degrees=(
                pose.upper_arm_left_x_degrees + upper_arm_left_x_delta
            ),
            upper_arm_left_z_degrees=(
                pose.upper_arm_left_z_degrees + upper_arm_left_z_delta
            ),
            forearm_left_x_degrees=pose.forearm_left_x_degrees + forearm_left_x_delta,
            forearm_left_z_degrees=pose.forearm_left_z_degrees + forearm_left_z_delta,
            upper_arm_right_x_degrees=(
                pose.upper_arm_right_x_degrees + upper_arm_right_x_delta
            ),
            upper_arm_right_z_degrees=(
                pose.upper_arm_right_z_degrees + upper_arm_right_z_delta
            ),
            forearm_right_x_degrees=(
                pose.forearm_right_x_degrees + forearm_right_x_delta
            ),
            forearm_right_z_degrees=(
                pose.forearm_right_z_degrees + forearm_right_z_delta
            ),
            cloth_left_x_degrees=pose.cloth_left_x_degrees + cloth_left_delta,
            cloth_center_x_degrees=pose.cloth_center_x_degrees + cloth_center_delta,
            cloth_right_x_degrees=pose.cloth_right_x_degrees + cloth_right_delta,
        ),
        hand_left_x_degrees=source.hand_left_x_degrees,
        hand_left_z_degrees=source.hand_left_z_degrees,
        chest_lift_z=chest_lift_z,
    )


def _build_profile() -> CombatIdleCyclesProfileV10:
    stance_profile = load_weapon_stance_profile_v09("human_warrior_m01")
    onehand_source = stance_profile.variants[1]
    twohand_source = stance_profile.variants[3]

    onehand_cycle = CombatIdleCycleV10(
        cycle_id="onehand_ready",
        display_name="Одноручная боевая стойка — дыхательный цикл",
        animation_id="combat_idle_onehand_ready_cycle_v10",
        grip_mode="one_handed",
        weapon_variant_id="onehand_ready",
        source_animation_id=onehand_source.animation_id,
        source_revision="v09",
        weapon_id=onehand_source.weapon_id,
        fps=COMBAT_IDLE_CYCLE_FPS,
        loop=True,
        frames=(
            _frame(onehand_source, frame=1, phase="base", chest_lift_z=0.0),
            _frame(
                onehand_source,
                frame=2,
                phase="inhale",
                chest_lift_z=0.032,
                spine_pitch_delta=0.55,
                chest_yaw_delta=0.20,
                head_yaw_delta=-0.10,
                upper_arm_left_x_delta=-0.35,
                upper_arm_left_z_delta=0.85,
                forearm_left_x_delta=-0.20,
                forearm_left_z_delta=0.65,
                cloth_left_delta=0.55,
                cloth_center_delta=0.35,
                cloth_right_delta=0.45,
            ),
            _frame(
                onehand_source,
                frame=3,
                phase="settle",
                chest_lift_z=0.008,
                spine_pitch_delta=0.10,
                upper_arm_left_z_delta=0.20,
                forearm_left_z_delta=0.15,
                cloth_left_delta=0.15,
                cloth_center_delta=0.10,
                cloth_right_delta=0.10,
            ),
            _frame(
                onehand_source,
                frame=4,
                phase="exhale",
                chest_lift_z=-0.016,
                spine_pitch_delta=-0.40,
                chest_yaw_delta=-0.15,
                head_yaw_delta=0.08,
                upper_arm_left_x_delta=0.20,
                upper_arm_left_z_delta=-0.45,
                forearm_left_x_delta=0.15,
                forearm_left_z_delta=-0.35,
                cloth_left_delta=-0.40,
                cloth_center_delta=-0.25,
                cloth_right_delta=-0.30,
            ),
        ),
    )
    twohand_cycle = CombatIdleCycleV10(
        cycle_id="twohand_center_high",
        display_name="Двуручная центральная высокая — дыхательный цикл",
        animation_id="combat_idle_twohand_center_high_cycle_v10",
        grip_mode="two_handed",
        weapon_variant_id="twohand_center_high",
        source_animation_id=twohand_source.animation_id,
        source_revision="v06",
        weapon_id=twohand_source.weapon_id,
        fps=COMBAT_IDLE_CYCLE_FPS,
        loop=True,
        frames=(
            _frame(twohand_source, frame=1, phase="base", chest_lift_z=0.0),
            _frame(
                twohand_source,
                frame=2,
                phase="inhale",
                chest_lift_z=0.030,
                spine_pitch_delta=0.50,
                upper_arm_left_x_delta=0.20,
                upper_arm_right_x_delta=0.20,
                forearm_left_x_delta=0.15,
                forearm_right_x_delta=0.15,
                cloth_left_delta=0.45,
                cloth_center_delta=0.30,
                cloth_right_delta=0.45,
            ),
            _frame(
                twohand_source,
                frame=3,
                phase="settle",
                chest_lift_z=0.007,
                spine_pitch_delta=0.08,
                cloth_left_delta=0.12,
                cloth_center_delta=0.08,
                cloth_right_delta=0.12,
            ),
            _frame(
                twohand_source,
                frame=4,
                phase="exhale",
                chest_lift_z=-0.014,
                spine_pitch_delta=-0.35,
                upper_arm_left_x_delta=-0.18,
                upper_arm_right_x_delta=-0.18,
                forearm_left_x_delta=-0.12,
                forearm_right_x_delta=-0.12,
                cloth_left_delta=-0.35,
                cloth_center_delta=-0.22,
                cloth_right_delta=-0.35,
            ),
        ),
    )
    return CombatIdleCyclesProfileV10(
        character_id="human_warrior_m01",
        revision="v10",
        direction="down",
        cycles=(onehand_cycle, twohand_cycle),
    )


HUMAN_WARRIOR_M01_COMBAT_IDLE_CYCLES_V10 = _build_profile()


def _lower_body_signature(pose: CombatIdleDownPoseV01) -> tuple[float, ...]:
    return (
        pose.pelvis_x,
        pose.pelvis_z,
        pose.pelvis_roll_z_degrees,
        pose.thigh_left_x_degrees,
        pose.thigh_right_x_degrees,
        pose.thigh_left_z_degrees,
        pose.thigh_right_z_degrees,
        pose.shin_left_x_degrees,
        pose.shin_right_x_degrees,
        pose.foot_left_x_degrees,
        pose.foot_right_x_degrees,
    )


def load_combat_idle_cycles_profile_v10(
    character_id: str,
) -> CombatIdleCyclesProfileV10:
    profile = HUMAN_WARRIOR_M01_COMBAT_IDLE_CYCLES_V10
    if character_id != profile.character_id:
        raise KeyError(f"No combat idle cycles v10 profile for character_id={character_id}")
    if profile.revision != "v10" or profile.direction != "down":
        raise ValueError("Combat idle cycles v10 identity drifted")
    if tuple(cycle.cycle_id for cycle in profile.cycles) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Combat idle cycles v10 selected stance order drifted")

    stance_profile = load_weapon_stance_profile_v09(character_id)
    sources = {
        "onehand_ready": stance_profile.variants[1],
        "twohand_center_high": stance_profile.variants[3],
    }
    for cycle in profile.cycles:
        source = sources[cycle.cycle_id]
        if cycle.fps != COMBAT_IDLE_CYCLE_FPS or not cycle.loop:
            raise ValueError(f"Cycle {cycle.cycle_id} must be a looping four-frame idle")
        if tuple(frame.pose.frame for frame in cycle.frames) != FRAME_ORDER:
            raise ValueError(f"Cycle {cycle.cycle_id} frame order drifted")
        if tuple(frame.pose.phase for frame in cycle.frames) != PHASE_ORDER:
            raise ValueError(f"Cycle {cycle.cycle_id} phase order drifted")
        if cycle.frames[0].pose.numeric_channels() != source.pose.numeric_channels():
            raise ValueError(f"Cycle {cycle.cycle_id} no longer starts from the approved pose")
        if cycle.frames[0].hand_left_x_degrees != source.hand_left_x_degrees:
            raise ValueError(f"Cycle {cycle.cycle_id} changed the approved left-hand base")
        if cycle.frames[0].hand_left_z_degrees != source.hand_left_z_degrees:
            raise ValueError(f"Cycle {cycle.cycle_id} changed the approved left-hand base")
        source_lower_body = _lower_body_signature(source.pose)
        for frame in cycle.frames:
            if _lower_body_signature(frame.pose) != source_lower_body:
                raise ValueError(f"Cycle {cycle.cycle_id} moved the planted lower body")
            if abs(frame.chest_lift_z) > 0.04:
                raise ValueError(f"Cycle {cycle.cycle_id} exceeds the restrained breath lift")
            if frame.hand_left_x_degrees != source.hand_left_x_degrees:
                raise ValueError(f"Cycle {cycle.cycle_id} changed left-hand grip rotation")
            if frame.hand_left_z_degrees != source.hand_left_z_degrees:
                raise ValueError(f"Cycle {cycle.cycle_id} changed left-hand grip rotation")

        if cycle.cycle_id == "onehand_ready":
            for frame in cycle.frames:
                pose = frame.pose
                if (
                    pose.upper_arm_right_x_degrees
                    != source.pose.upper_arm_right_x_degrees
                    or pose.upper_arm_right_z_degrees
                    != source.pose.upper_arm_right_z_degrees
                    or pose.forearm_right_x_degrees
                    != source.pose.forearm_right_x_degrees
                    or pose.forearm_right_z_degrees
                    != source.pose.forearm_right_z_degrees
                    or pose.hand_right_x_degrees
                    != source.pose.hand_right_x_degrees
                    or pose.hand_right_z_degrees
                    != source.pose.hand_right_z_degrees
                ):
                    raise ValueError("One-hand v10 sword arm must remain rotation-stable")
        else:
            for frame in cycle.frames:
                pose = frame.pose
                if pose.upper_arm_left_x_degrees != pose.upper_arm_right_x_degrees:
                    raise ValueError("Two-hand v10 upper-arm X rotations lost symmetry")
                if pose.forearm_left_x_degrees != pose.forearm_right_x_degrees:
                    raise ValueError("Two-hand v10 forearm X rotations lost symmetry")
                if pose.upper_arm_left_z_degrees != pose.upper_arm_right_z_degrees:
                    raise ValueError("Two-hand v10 upper-arm Z rotations lost locked source")
                if pose.forearm_left_z_degrees != -pose.forearm_right_z_degrees:
                    raise ValueError("Two-hand v10 forearm Z rotations lost center symmetry")
    return profile
