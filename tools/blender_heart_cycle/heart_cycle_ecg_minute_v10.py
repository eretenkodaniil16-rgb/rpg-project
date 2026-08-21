from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import heart_cycle_ecg_minute_v09_compat as compat


v09 = compat.v09

V10_REVISION = "heart_cycle_ecg_minute_v10"
V10_MODEL_REVISION = v09.MODEL_REVISION.replace("_ecg_minute_v09", "_ecg_minute_v10")
V10_BLEND_NAME = f"{V10_MODEL_REVISION}.blend"
V10_VIDEO_NAME = "heart_cycle_ecg_minute_v10_1080p30_review.mp4"
V10_MANIFEST_NAME = "heart_cycle_ecg_minute_v10_manifest.json"

_BASE_UPDATE_HEADER = v09._update_header
_BASE_BUILD_ECG_OVERLAY = v09._build_ecg_overlay
_BASE_BUILD_INTRO_OUTRO = v09._build_intro_outro
_BASE_BUILD_MODEL = v09.build_model
_BASE_WRITE_MANIFEST = v09._write_manifest


def _text_object(name: str):
    obj = bpy.data.objects.get(name)
    if obj is None or not hasattr(obj.data, "size"):
        return None
    return obj


def _set_text(name: str, *, size: float | None = None, y: float | None = None) -> None:
    obj = _text_object(name)
    if obj is None:
        return
    if size is not None:
        obj.data.size = size
    if y is not None:
        obj.location.y = y


def _update_header_v10() -> None:
    _BASE_UPDATE_HEADER()

    # Global header: approximately 20–25% larger than v09.
    _set_text("Infographic_Title", size=0.040)
    _set_text("Infographic_Subtitle", size=0.0180)

    # Phase card typography is enlarged while vertical positions are redistributed
    # to preserve separation from the ECG electrical-event label above it.
    for obj in bpy.data.objects:
        if not hasattr(obj.data, "size"):
            continue
        if obj.name.startswith("Info_PhaseIndex_"):
            obj.location.y = 0.079
            obj.data.size = 0.0195
        elif obj.name.startswith("Info_PhaseTitle_"):
            obj.location.y = 0.044
            obj.data.size = 0.0330
        elif obj.name.startswith("Info_PhaseBody_"):
            obj.location.y = -0.035
            obj.data.size = 0.0200
        elif obj.name.startswith("Info_PhaseDuration_"):
            obj.location.y = -0.204
            obj.data.size = 0.0195
        elif obj.name.startswith("Info_PhaseValves_"):
            obj.location.y = -0.241
            obj.data.size = 0.0180


def _build_ecg_overlay_v10(build):
    created = _BASE_BUILD_ECG_OVERLAY(build)

    # ECG wave labels and the phase-specific electrical event are deliberately
    # larger for phone/tablet viewing.
    _set_text("ECG_LabelP_v09", size=0.027)
    _set_text("ECG_LabelQRS_v09", size=0.0245)
    _set_text("ECG_LabelT_v09", size=0.027)
    _set_text("ECG_Scale_v09", size=0.0170, y=0.144)

    for idx in range(1, 10):
        _set_text(
            f"ECG_PhaseElectrical_{idx:02d}_v09",
            size=0.0195,
            y=0.113,
        )

    return created


def _build_intro_outro_v10(build):
    created = _BASE_BUILD_INTRO_OUTRO(build)

    # Intro/outro text is enlarged by roughly 18–22%; the card already has
    # enough vertical room for these sizes without covering the heart model.
    _set_text("Minute_IntroTitle_v09", size=0.0430)
    _set_text("Minute_IntroBody_v09", size=0.0250)
    _set_text("Minute_IntroHint_v09", size=0.0195)

    _set_text("Minute_OutroTitle_v09", size=0.0370)
    _set_text("Minute_OutroBody_v09", size=0.0235)
    _set_text("Minute_OutroHint_v09", size=0.0195)

    return created


def _build_model_v10(resolution: int):
    build = _BASE_BUILD_MODEL(resolution)
    scene = bpy.context.scene
    scene["model_revision"] = V10_MODEL_REVISION
    scene["minute_revision"] = V10_REVISION
    scene["text_readability_profile"] = "large_1080p_mobile_v10"
    scene["target_master"] = "1920x1080 @ 30 fps"
    return build


def _write_manifest_v10(output_root: Path, args) -> Path:
    legacy_path = _BASE_WRITE_MANIFEST(output_root, args)
    payload = json.loads(legacy_path.read_text(encoding="utf-8"))
    payload["revision"] = V10_REVISION
    payload["model_revision"] = V10_MODEL_REVISION
    payload.setdefault("render", {})["readability_profile"] = "large_1080p_mobile_v10"
    payload["render"]["target_master"] = [1920, 1080, 30]
    payload["render"]["native_30fps"] = True
    payload["typography"] = {
        "header_scale": "~1.24x",
        "phase_title_scale": "~1.22x",
        "phase_body_scale": "~1.21x",
        "ecg_event_scale": "~1.18x",
        "intro_outro_scale": "~1.20x",
        "layout_reflowed_for_larger_text": True,
    }
    payload.setdefault("files", {})["blend"] = V10_BLEND_NAME
    payload["files"]["video_target"] = V10_VIDEO_NAME

    target = output_root / V10_MANIFEST_NAME
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if legacy_path != target:
        legacy_path.unlink(missing_ok=True)
    return target


# Override the v09 globals used by its already-tested main/render pipeline.
v09.MINUTE_REVISION = V10_REVISION
v09.MODEL_REVISION = V10_MODEL_REVISION
v09.DEFAULT_BLEND_NAME = V10_BLEND_NAME
v09.DEFAULT_VIDEO_NAME = V10_VIDEO_NAME
v09._update_header = _update_header_v10
v09._build_ecg_overlay = _build_ecg_overlay_v10
v09._build_intro_outro = _build_intro_outro_v10
v09.build_model = _build_model_v10
v09._write_manifest = _write_manifest_v10


if __name__ == "__main__":
    raise SystemExit(v09.main())
