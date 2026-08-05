from __future__ import annotations

from pathlib import Path


BUILDER = Path(
    "tools/blender_sprite_factory/death_down_keyposes_builder_v01.py"
)
ADAPTER = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)


def replace_between(
    content: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError(f"{label}: markers not found")
    return content[:start] + replacement + content[end:]


def main() -> int:
    builder = BUILDER.read_text(encoding="utf-8")
    builder_replacement = '''def _unparent_preserving_world(obj: factory.bpy.types.Object) -> None:
    world_matrix = obj.matrix_world.copy()
    obj.parent = None
    obj.parent_type = "OBJECT"
    obj.matrix_world = world_matrix


def _create_gore_modules_v01(context: factory.BuildContext) -> None:
    required_names = (
        _GORE_DETACHED_FOREARM,
        _GORE_DETACHED_HAND,
        _GORE_STUMP_CAP,
        _GORE_DETACHED_CAP,
    )
    if any(factory.bpy.data.objects.get(name) is not None for name in required_names):
        raise RuntimeError("death_03 gore modules already exist")

    _, elbow, _, _, _ = context.silhouette.arm_points("L")
    stump = factory._ellipsoid(
        _GORE_STUMP_CAP,
        elbow,
        (0.115, 0.095, 0.115),
        context.materials["scarf"],
        segments=8,
        rings=5,
    )
    factory._register(context, stump, "arms", "upper_arm.L", "left")
    stump["death_gore_module"] = True
    stump["gore_role"] = "body_stump"
    _set_hidden(stump, True)

    detached_start = (0.92, -0.42, 0.24)
    detached_end = (1.38, -0.56, 0.20)
    detached_forearm = factory._cylinder_between(
        _GORE_DETACHED_FOREARM,
        detached_start,
        detached_end,
        context.silhouette.forearm_radius,
        8,
        context.materials["silver"],
    )
    factory._register(context, detached_forearm, "arms", "forearm.L", "left")
    _unparent_preserving_world(detached_forearm)
    detached_forearm["death_gore_module"] = True
    detached_forearm["detached_part_id"] = "left_forearm_and_hand"
    _set_hidden(detached_forearm, True)

    detached_hand = factory._ellipsoid(
        _GORE_DETACHED_HAND,
        (1.50, -0.60, 0.20),
        (0.15, 0.115, 0.15),
        context.materials["leather_dark"],
        segments=8,
        rings=5,
    )
    factory._register(context, detached_hand, "arms", "hand.L", "left")
    _unparent_preserving_world(detached_hand)
    detached_hand["death_gore_module"] = True
    detached_hand["detached_part_id"] = "left_forearm_and_hand"
    _set_hidden(detached_hand, True)

    detached_cap = factory._ellipsoid(
        _GORE_DETACHED_CAP,
        detached_start,
        (0.105, 0.085, 0.105),
        context.materials["scarf"],
        segments=8,
        rings=5,
    )
    factory._register(context, detached_cap, "arms", "forearm.L", "left")
    _unparent_preserving_world(detached_cap)
    detached_cap["death_gore_module"] = True
    detached_cap["gore_role"] = "detached_cut_cap"
    _set_hidden(detached_cap, True)


'''
    builder = replace_between(
        builder,
        "def _duplicate_detached_object(",
        "def create_death_down_keypose_actions_v01",
        builder_replacement,
        "builder gore module",
    )
    BUILDER.write_text(builder, encoding="utf-8")

    adapter = ADAPTER.read_text(encoding="utf-8")
    old_start = "    original_forearm = _required_object(_GORE_ORIGINAL_FOREARM)\n"
    old_end = "\n\ndef render_death_down_keyposes_v01(\n"
    replacement = '''    original_forearm = _required_object(_GORE_ORIGINAL_FOREARM)
    original_hand = _required_object(_GORE_ORIGINAL_HAND)
    detached_forearm = _required_object(_GORE_DETACHED_FOREARM)
    detached_hand = _required_object(_GORE_DETACHED_HAND)
    stump = _required_object(_GORE_STUMP_CAP)
    detached_cap = _required_object(_GORE_DETACHED_CAP)

    _set_hidden(original_forearm, True)
    _set_hidden(original_hand, True)
    for obj in (detached_forearm, detached_hand, stump, detached_cap):
        _set_hidden(obj, False)


'''
    adapter = replace_between(
        adapter,
        old_start,
        old_end,
        replacement,
        "adapter gore state",
    )
    ADAPTER.write_text(adapter, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
