from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
from head_profile_v04 import DetailedBoxPart, DetailedEllipsoidPart
from head_profile_v06 import (
    HeadDetailProfileV06,
    load_head_detail_profile_v06,
    load_head_profile_v06,
)


BASE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile.py"
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v05.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v06.py"
_ORIGINAL_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _register_ellipsoid(
    context: factory.BuildContext,
    item: DetailedEllipsoidPart,
    module_id: str,
) -> None:
    factory._register(
        context,
        factory._ellipsoid(
            item.part.name,
            item.part.location,
            item.part.scale,
            context.materials[item.material_slot],
            segments=item.density.segments,
            rings=item.density.rings,
        ),
        module_id,
        "head",
    )


def _register_box(
    context: factory.BuildContext,
    item: DetailedBoxPart,
    module_id: str,
) -> None:
    part = item.part
    factory._register(
        context,
        factory._box(
            part.name,
            part.location,
            part.dimensions,
            context.materials[item.material_slot],
            item.bevel,
            rotation=(0.0, math.radians(part.rotation_y_degrees), 0.0),
        ),
        module_id,
        "head",
    )


def _density_for_hair(
    detail: HeadDetailProfileV06,
    scale: tuple[float, float, float],
) -> tuple[int, int]:
    largest_axis = max(scale)
    if largest_axis >= 0.28:
        density = detail.hair_primary_density
    elif largest_axis >= 0.16:
        density = detail.hair_secondary_density
    else:
        density = detail.hair_tertiary_density
    return density.segments, density.rings


def _build_head_and_hair_v06(context: factory.BuildContext) -> None:
    head = context.head
    detail = load_head_detail_profile_v06(context.config.character_id)

    factory._register(
        context,
        factory._ellipsoid(
            head.head_base.name,
            head.head_base.location,
            head.head_base.scale,
            context.materials["skin"],
            segments=detail.cranium_density.segments,
            rings=detail.cranium_density.rings,
        ),
        "head",
        "head",
    )
    factory._register(
        context,
        factory._ellipsoid(
            head.jaw.name,
            head.jaw.location,
            head.jaw.scale,
            context.materials["skin"],
            segments=detail.jaw_density.segments,
            rings=detail.jaw_density.rings,
        ),
        "head",
        "head",
    )
    for ear in head.ears:
        factory._register(
            context,
            factory._ellipsoid(
                ear.name,
                ear.location,
                ear.scale,
                context.materials["skin"],
                segments=detail.ear_density.segments,
                rings=detail.ear_density.rings,
            ),
            "head",
            "head",
        )

    for item in detail.face_skin_masses:
        _register_ellipsoid(context, item, "head")

    factory._register(
        context,
        factory._frustum(
            "head_nose",
            head.nose.location,
            radius_bottom=head.nose.radius_bottom,
            radius_top=head.nose.radius_top,
            depth=head.nose.depth,
            vertices=detail.nose_vertices,
            material=context.materials["skin"],
            rotation=(math.radians(90.0), 0.0, 0.0),
        ),
        "head",
        "head",
    )

    factory._register(
        context,
        factory._ellipsoid(
            head.hair_cap.name,
            head.hair_cap.location,
            head.hair_cap.scale,
            context.materials["hair"],
            segments=detail.hair_cap_density.segments,
            rings=detail.hair_cap_density.rings,
        ),
        "hair",
        "head",
    )
    hair_parts = head.hair_back_masses + head.hair_front_locks + head.hair_side_locks
    for hair_part in hair_parts:
        segments, rings = _density_for_hair(detail, hair_part.scale)
        factory._register(
            context,
            factory._ellipsoid(
                hair_part.name,
                hair_part.location,
                hair_part.scale,
                context.materials["hair"],
                segments=segments,
                rings=rings,
            ),
            "hair",
            "head",
        )
    for item in detail.hair_detail_masses:
        _register_ellipsoid(context, item, "hair")

    for face_part in head.brows + head.eyes + (head.mouth,):
        _register_box(context, DetailedBoxPart(face_part, "hair"), "head")
    for item in detail.face_dark_details:
        _register_box(context, item, "head")


def _write_run_manifest_v06(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = _ORIGINAL_WRITE_RUN_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    detail = load_head_detail_profile_v06(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["base_head_profile"] = {
        "path": context.config.relative_to_repo(BASE_HEAD_PROFILE_PATH),
        "sha256": hashlib.sha256(BASE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v05",
        "proxy_revision": "v08",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_builder_adapter"] = {
        "path": context.config.relative_to_repo(SCRIPT_PATH),
        "sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
    }
    payload["head_geometry"] = {
        "cranium_segments": detail.cranium_density.segments,
        "cranium_rings": detail.cranium_density.rings,
        "jaw_segments": detail.jaw_density.segments,
        "jaw_rings": detail.jaw_density.rings,
        "hair_cap_segments": detail.hair_cap_density.segments,
        "hair_cap_rings": detail.hair_cap_density.rings,
        "hair_primary_segments": detail.hair_primary_density.segments,
        "hair_primary_rings": detail.hair_primary_density.rings,
        "hair_secondary_segments": detail.hair_secondary_density.segments,
        "hair_secondary_rings": detail.hair_secondary_density.rings,
        "hair_tertiary_segments": detail.hair_tertiary_density.segments,
        "hair_tertiary_rings": detail.hair_tertiary_density.rings,
        "nose_vertices": detail.nose_vertices,
        "separate_face_skin_parts": len(detail.face_skin_masses),
        "separate_face_dark_parts": (
            len(context.head.brows)
            + len(context.head.eyes)
            + 1
            + len(detail.face_dark_details)
        ),
        "separate_hair_parts": (
            1
            + len(context.head.hair_back_masses)
            + len(context.head.hair_front_locks)
            + len(context.head.hair_side_locks)
            + len(detail.hair_detail_masses)
        ),
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v06
    factory._build_head_and_hair = _build_head_and_hair_v06
    factory._write_run_manifest = _write_run_manifest_v06
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
