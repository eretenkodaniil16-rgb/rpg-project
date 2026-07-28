from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_head_v07 as previous_adapter
from hair_sweep_builder_v08 import replace_hair_with_reference_sweeps
from hair_sweep_profile_v08 import load_hair_sweep_profile_v08
from head_profile_v08 import load_head_detail_profile_v08, load_head_profile_v08


BASE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile.py"
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v07.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v08.py"
HAIR_SWEEP_PROFILE_PATH = SCRIPT_DIR / "hair_sweep_profile_v08.py"
HAIR_SWEEP_BUILDER_PATH = SCRIPT_DIR / "hair_sweep_builder_v08.py"
_ORIGINAL_WRITE_RUN_MANIFEST = factory._write_run_manifest

# Compatibility markers retained for the preceding proxy_v11 implementation:
# _apply_reference_hair_palette(context)
# _apply_reference_hair_rotations(context)
# "approved_reference_constant_color_ramp"
# "approved_reference_consolidated_five_zone"


def _build_head_and_hair_v08(context: factory.BuildContext) -> None:
    previous_adapter.load_head_detail_profile_v07 = load_head_detail_profile_v08
    previous_adapter._build_head_and_hair_v07(context)
    replace_hair_with_reference_sweeps(context)


def _write_run_manifest_v08(
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
    detail = load_head_detail_profile_v08(context.config.character_id)
    sweep = load_hair_sweep_profile_v08()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["base_head_profile"] = {
        "path": context.config.relative_to_repo(BASE_HEAD_PROFILE_PATH),
        "sha256": hashlib.sha256(BASE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v07",
        "proxy_revision": "v10",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_sweep_profile"] = {
        "path": context.config.relative_to_repo(HAIR_SWEEP_PROFILE_PATH),
        "revision": sweep.revision,
        "sha256": hashlib.sha256(HAIR_SWEEP_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_sweep_builder"] = {
        "path": context.config.relative_to_repo(HAIR_SWEEP_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_SWEEP_BUILDER_PATH.read_bytes()).hexdigest(),
    }
    payload["head_builder_adapter"] = {
        "path": context.config.relative_to_repo(SCRIPT_PATH),
        "sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
    }
    actual_hair_parts = sum(
        1
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    )
    payload["head_geometry"] = {
        "cranium_segments": detail.cranium_density.segments,
        "cranium_rings": detail.cranium_density.rings,
        "jaw_segments": detail.jaw_density.segments,
        "jaw_rings": detail.jaw_density.rings,
        "nose_vertices": detail.nose_vertices,
        "separate_face_skin_parts": len(detail.face_skin_masses),
        "separate_face_dark_parts": (
            len(context.head.brows)
            + len(context.head.eyes)
            + 1
            + len(detail.face_dark_details)
        ),
        "separate_hair_parts": actual_hair_parts,
        "sweep_mesh_parts": len(sweep.meshes),
        "sweep_mesh_vertices": sum(
            part.segments * len(part.rings) for part in sweep.meshes
        ),
    }
    payload["hair_structure"] = {
        "strategy": "approved_reference_profile_sweep_meshes",
        "zones": ["top", "front", "sides", "back", "nape"],
        "sweep_meshes": {
            part.name: {
                "segments": part.segments,
                "rings": len(part.rings),
                "wave_frequency": part.wave_frequency,
                "wave_amplitude": part.wave_amplitude,
            }
            for part in sweep.meshes
        },
        "face_geometry_locked_to_revision": "v07",
        "material_palette": ["#0B0602", "#1A120A", "#26180B", "#582A15", "#7C4924"],
        "material_strategy": "approved_reference_emission_color_ramp",
        "rotations_degrees": {
            name: list(rotation) for name, rotation in sweep.accent_rotations_degrees
        },
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v08
    factory._build_head_and_hair = _build_head_and_hair_v08
    factory._write_run_manifest = _write_run_manifest_v08
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
