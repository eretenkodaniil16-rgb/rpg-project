from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from .config import TechnicalSpec


@dataclass
class TechnicalResult:
    candidate_id: str
    source_path: str
    normalized_path: str | None
    passed: bool
    hard_reject_reasons: list[str]
    metrics: dict[str, float | int | str | list[int]]
    technical_score: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_and_validate(
    source_path: Path,
    output_path: Path,
    spec: TechnicalSpec,
    reference_path: Path | None = None,
) -> TechnicalResult:
    candidate_id = source_path.stem
    reasons: list[str] = []
    metrics: dict[str, float | int | str | list[int]] = {}

    try:
        image = Image.open(source_path)
        image.load()
    except Exception as exc:  # pragma: no cover - defensive I/O guard
        return TechnicalResult(
            candidate_id=candidate_id,
            source_path=str(source_path),
            normalized_path=None,
            passed=False,
            hard_reject_reasons=[f"invalid_png:{type(exc).__name__}"],
            metrics={},
            technical_score=0.0,
        )

    metrics["source_width"] = image.width
    metrics["source_height"] = image.height
    metrics["source_mode"] = image.mode

    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    alpha_extrema = alpha.getextrema()
    metrics["alpha_min"] = int(alpha_extrema[0])
    metrics["alpha_max"] = int(alpha_extrema[1])

    if alpha_extrema[0] == 255:
        reasons.append("opaque_background")

    alpha_values = alpha.histogram()
    semi_transparent = sum(alpha_values[1:255])
    total_pixels = rgba.width * rgba.height
    metrics["source_semitransparent_pixels"] = semi_transparent
    metrics["source_semitransparent_ratio"] = semi_transparent / max(total_pixels, 1)

    binary_alpha = alpha.point(lambda value: 255 if value >= spec.alpha_threshold else 0)
    bbox = binary_alpha.getbbox()
    if bbox is None:
        reasons.append("empty_sprite")
        return TechnicalResult(
            candidate_id=candidate_id,
            source_path=str(source_path),
            normalized_path=None,
            passed=False,
            hard_reject_reasons=reasons,
            metrics=metrics,
            technical_score=0.0,
        )

    metrics["source_bbox"] = list(bbox)
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]
    opaque_pixels = sum(binary_alpha.histogram()[255:])
    metrics["source_opaque_ratio"] = opaque_pixels / max(total_pixels, 1)

    if bbox_width >= rgba.width * 0.94 and bbox_height >= rgba.height * 0.94:
        reasons.append("background_or_full_canvas_content")

    cropped = rgba.crop(bbox)
    cropped.putalpha(binary_alpha.crop(bbox))

    target_height = spec.sprite_height_max
    scale = target_height / max(cropped.height, 1)
    target_width = max(1, round(cropped.width * scale))
    if target_width > spec.max_sprite_width:
        scale = spec.max_sprite_width / max(cropped.width, 1)
        target_width = spec.max_sprite_width
        target_height = max(1, round(cropped.height * scale))

    normalized_sprite = cropped.resize((target_width, target_height), Image.Resampling.NEAREST)
    normalized_sprite.putalpha(
        normalized_sprite.getchannel("A").point(lambda value: 255 if value >= spec.alpha_threshold else 0)
    )

    if target_height < spec.sprite_height_min or target_height > spec.sprite_height_max:
        reasons.append("sprite_height_out_of_range")
    if target_width > spec.max_sprite_width:
        reasons.append("sprite_width_out_of_range")

    left = (spec.canvas_width - target_width) // 2
    top = spec.baseline_y - target_height + 1
    if left < 0 or top < 0 or left + target_width > spec.canvas_width or top + target_height > spec.canvas_height:
        reasons.append("sprite_does_not_fit_canvas")

    normalized = Image.new("RGBA", (spec.canvas_width, spec.canvas_height), (0, 0, 0, 0))
    if not reasons or reasons == ["opaque_background"]:
        normalized.alpha_composite(normalized_sprite, (max(left, 0), max(top, 0)))

    normalized_alpha = normalized.getchannel("A")
    normalized_bbox = normalized_alpha.getbbox()
    if normalized_bbox is None:
        reasons.append("normalized_sprite_empty")
    else:
        metrics["normalized_bbox"] = list(normalized_bbox)
        metrics["normalized_width"] = normalized_bbox[2] - normalized_bbox[0]
        metrics["normalized_height"] = normalized_bbox[3] - normalized_bbox[1]
        metrics["normalized_baseline_y"] = normalized_bbox[3] - 1
        if normalized_bbox[3] - 1 != spec.baseline_y:
            reasons.append("baseline_mismatch")

    metrics["normalized_semitransparent_pixels"] = sum(normalized_alpha.histogram()[1:255])
    if metrics["normalized_semitransparent_pixels"] != 0:
        reasons.append("normalized_alpha_not_binary")

    local_similarity = 50.0
    face_similarity = 50.0
    if reference_path is not None and reference_path.exists() and normalized_bbox is not None:
        reference = _normalize_reference(reference_path, spec)
        local_similarity = _image_similarity(normalized, reference)
        face_similarity = _face_similarity(normalized, reference, spec.face_box)
    metrics["reference_similarity"] = round(local_similarity, 3)
    metrics["face_similarity"] = round(face_similarity, 3)

    background_rejects = {"opaque_background", "background_or_full_canvas_content"}
    fatal_reasons = [reason for reason in reasons if reason not in background_rejects]
    # Opaque outputs are rejected because the pipeline explicitly requests transparent PNG.
    if any(reason in background_rejects for reason in reasons):
        fatal_reasons.extend(reason for reason in reasons if reason in background_rejects)

    score = _technical_score(metrics, reasons, local_similarity, face_similarity)
    passed = len(fatal_reasons) == 0

    if passed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        normalized.save(output_path, format="PNG", optimize=True)
        normalized_path: str | None = str(output_path)
    else:
        normalized_path = None

    return TechnicalResult(
        candidate_id=candidate_id,
        source_path=str(source_path),
        normalized_path=normalized_path,
        passed=passed,
        hard_reject_reasons=sorted(set(reasons)),
        metrics=metrics,
        technical_score=round(score, 3),
    )


def _normalize_reference(reference_path: Path, spec: TechnicalSpec) -> Image.Image:
    image = Image.open(reference_path).convert("RGBA")
    alpha = image.getchannel("A").point(lambda value: 255 if value >= spec.alpha_threshold else 0)
    bbox = alpha.getbbox()
    if bbox is None:
        return Image.new("RGBA", (spec.canvas_width, spec.canvas_height), (0, 0, 0, 0))
    crop = image.crop(bbox)
    crop.putalpha(alpha.crop(bbox))
    height = spec.sprite_height_max
    scale = height / max(crop.height, 1)
    width = max(1, round(crop.width * scale))
    if width > spec.max_sprite_width:
        scale = spec.max_sprite_width / max(crop.width, 1)
        width = spec.max_sprite_width
        height = max(1, round(crop.height * scale))
    crop = crop.resize((width, height), Image.Resampling.NEAREST)
    crop.putalpha(crop.getchannel("A").point(lambda value: 255 if value >= spec.alpha_threshold else 0))
    result = Image.new("RGBA", (spec.canvas_width, spec.canvas_height), (0, 0, 0, 0))
    result.alpha_composite(crop, ((spec.canvas_width - width) // 2, spec.baseline_y - height + 1))
    return result


def _image_similarity(candidate: Image.Image, reference: Image.Image) -> float:
    candidate_rgb = _flatten_on_black(candidate)
    reference_rgb = _flatten_on_black(reference)
    diff = ImageChops.difference(candidate_rgb, reference_rgb)
    mean = sum(ImageStat.Stat(diff).mean) / 3.0
    return max(0.0, 100.0 * (1.0 - mean / 255.0))


def _face_similarity(
    candidate: Image.Image,
    reference: Image.Image,
    face_box: tuple[int, int, int, int],
) -> float:
    best = 0.0
    ref_face = _flatten_on_black(reference.crop(face_box))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            shifted_box = (
                face_box[0] + dx,
                face_box[1] + dy,
                face_box[2] + dx,
                face_box[3] + dy,
            )
            candidate_face = _flatten_on_black(candidate.crop(shifted_box))
            diff = ImageChops.difference(candidate_face, ref_face)
            mean = sum(ImageStat.Stat(diff).mean) / 3.0
            best = max(best, 100.0 * (1.0 - mean / 255.0))
    return max(0.0, min(100.0, best))


def _flatten_on_black(image: Image.Image) -> Image.Image:
    result = Image.new("RGB", image.size, (0, 0, 0))
    result.paste(image.convert("RGB"), mask=image.getchannel("A"))
    return result


def _technical_score(
    metrics: dict[str, float | int | str | list[int]],
    reasons: list[str],
    similarity: float,
    face_similarity: float,
) -> float:
    if reasons:
        penalty = min(70.0, 18.0 * len(set(reasons)))
    else:
        penalty = 0.0
    alpha_score = 100.0 if int(metrics.get("normalized_semitransparent_pixels", 0)) == 0 else 0.0
    size_score = 100.0
    height = int(metrics.get("normalized_height", 0))
    width = int(metrics.get("normalized_width", 0))
    if height <= 0 or width <= 0:
        size_score = 0.0
    base = 0.35 * alpha_score + 0.25 * size_score + 0.15 * similarity + 0.25 * face_similarity
    return max(0.0, min(100.0, base - penalty))
