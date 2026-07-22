from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TechnicalSpec:
    canvas_width: int
    canvas_height: int
    sprite_height_min: int
    sprite_height_max: int
    max_sprite_width: int
    baseline_y: int
    alpha_threshold: int
    face_box: tuple[int, int, int, int]


@dataclass(frozen=True)
class GenerationSpec:
    image_model: str
    grader_model: str
    size: str
    quality: str
    input_fidelity: str
    initial_candidates: int
    top_k: int
    minimum_score: float
    max_rounds: int


@dataclass(frozen=True)
class FrameSpec:
    frame_id: str
    direction: str
    source_reference: str
    prompt_file: str
    additional_references: tuple[str, ...]


@dataclass(frozen=True)
class PipelineConfig:
    schema_version: int
    character_id: str
    ready: bool
    master_prompt_file: str
    technical: TechnicalSpec
    generation: GenerationSpec
    weights: dict[str, float]
    hard_reject_labels: tuple[str, ...]
    frames: dict[str, FrameSpec]
    manifest_path: Path
    repo_root: Path

    @property
    def pipeline_root(self) -> Path:
        return self.manifest_path.parent.parent

    def resolve_repo_path(self, relative_path: str) -> Path:
        return (self.repo_root / relative_path).resolve()

    def resolve_pipeline_path(self, relative_path: str) -> Path:
        return (self.pipeline_root / relative_path).resolve()

    def load_prompt(self, frame_id: str) -> str:
        frame = self.frame(frame_id)
        master = self.resolve_pipeline_path(self.master_prompt_file).read_text(encoding="utf-8")
        pose = self.resolve_pipeline_path(frame.prompt_file).read_text(encoding="utf-8")
        return f"{master.strip()}\n\nКОНКРЕТНАЯ ФАЗА КАДРА\n\n{pose.strip()}\n"

    def frame(self, frame_id: str) -> FrameSpec:
        try:
            return self.frames[frame_id]
        except KeyError as exc:
            available = ", ".join(sorted(self.frames))
            raise ValueError(f"Неизвестный frame_id '{frame_id}'. Доступны: {available}") from exc

    def reference_paths(self, frame_id: str, extra_reference: str | None = None) -> list[Path]:
        frame = self.frame(frame_id)
        raw_paths = [frame.source_reference, *frame.additional_references]
        if extra_reference:
            raw_paths.append(extra_reference)
        result: list[Path] = []
        for raw_path in raw_paths:
            path = self.resolve_repo_path(raw_path)
            if path not in result:
                result.append(path)
        return result


def load_config(manifest_path: Path, repo_root: Path) -> PipelineConfig:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require_keys(raw, [
        "schema_version",
        "character_id",
        "ready",
        "master_prompt_file",
        "technical",
        "generation",
        "weights",
        "hard_reject_labels",
        "frames",
    ], "manifest")

    technical_raw = _as_dict(raw["technical"], "technical")
    generation_raw = _as_dict(raw["generation"], "generation")
    frames_raw = _as_dict(raw["frames"], "frames")

    technical = TechnicalSpec(
        canvas_width=_positive_int(technical_raw, "canvas_width"),
        canvas_height=_positive_int(technical_raw, "canvas_height"),
        sprite_height_min=_positive_int(technical_raw, "sprite_height_min"),
        sprite_height_max=_positive_int(technical_raw, "sprite_height_max"),
        max_sprite_width=_positive_int(technical_raw, "max_sprite_width"),
        baseline_y=_non_negative_int(technical_raw, "baseline_y"),
        alpha_threshold=_bounded_int(technical_raw, "alpha_threshold", 0, 255),
        face_box=_int_tuple(technical_raw.get("face_box"), 4, "technical.face_box"),
    )
    if technical.sprite_height_min > technical.sprite_height_max:
        raise ValueError("sprite_height_min не может быть больше sprite_height_max")
    if technical.baseline_y >= technical.canvas_height:
        raise ValueError("baseline_y должен находиться внутри холста")

    generation = GenerationSpec(
        image_model=_non_empty_string(generation_raw, "image_model"),
        grader_model=_non_empty_string(generation_raw, "grader_model"),
        size=_non_empty_string(generation_raw, "size"),
        quality=_non_empty_string(generation_raw, "quality"),
        input_fidelity=_non_empty_string(generation_raw, "input_fidelity"),
        initial_candidates=_bounded_int(generation_raw, "initial_candidates", 1, 10),
        top_k=_bounded_int(generation_raw, "top_k", 1, 5),
        minimum_score=_bounded_float(generation_raw, "minimum_score", 0.0, 100.0),
        max_rounds=_bounded_int(generation_raw, "max_rounds", 1, 2),
    )
    if generation.top_k > generation.initial_candidates:
        raise ValueError("top_k не может быть больше initial_candidates")

    weights_raw = _as_dict(raw["weights"], "weights")
    weights = {str(key): float(value) for key, value in weights_raw.items()}
    required_weights = {
        "identity_face",
        "equipment_sides",
        "perspective",
        "proportions",
        "pose",
        "palette_style",
    }
    missing_weights = required_weights.difference(weights)
    if missing_weights:
        raise ValueError(f"В weights отсутствуют критерии: {sorted(missing_weights)}")
    if any(value < 0.0 for value in weights.values()):
        raise ValueError("Веса критериев не могут быть отрицательными")
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.0001:
        raise ValueError(f"Сумма weights должна быть 1.0, получено {weight_sum}")

    frames: dict[str, FrameSpec] = {}
    for frame_id, value in frames_raw.items():
        frame_raw = _as_dict(value, f"frames.{frame_id}")
        frame = FrameSpec(
            frame_id=str(frame_id),
            direction=_non_empty_string(frame_raw, "direction"),
            source_reference=_non_empty_string(frame_raw, "source_reference"),
            prompt_file=_non_empty_string(frame_raw, "prompt_file"),
            additional_references=tuple(_string_list(frame_raw.get("additional_references", []), f"frames.{frame_id}.additional_references")),
        )
        frames[frame.frame_id] = frame
    if not frames:
        raise ValueError("Manifest должен содержать хотя бы один кадр")

    reject_labels = tuple(_string_list(raw["hard_reject_labels"], "hard_reject_labels"))
    if not reject_labels:
        raise ValueError("hard_reject_labels не может быть пустым")

    return PipelineConfig(
        schema_version=int(raw["schema_version"]),
        character_id=str(raw["character_id"]),
        ready=bool(raw["ready"]),
        master_prompt_file=str(raw["master_prompt_file"]),
        technical=technical,
        generation=generation,
        weights=weights,
        hard_reject_labels=reject_labels,
        frames=frames,
        manifest_path=manifest_path.resolve(),
        repo_root=repo_root.resolve(),
    )


def _require_keys(data: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"В {label} отсутствуют обязательные поля: {missing}")


def _as_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} должен быть объектом JSON")
    return value


def _non_empty_string(data: dict[str, Any], key: str) -> str:
    value = str(data.get(key, "")).strip()
    if not value:
        raise ValueError(f"Поле '{key}' не может быть пустым")
    return value


def _positive_int(data: dict[str, Any], key: str) -> int:
    value = int(data.get(key, 0))
    if value <= 0:
        raise ValueError(f"Поле '{key}' должно быть положительным")
    return value


def _non_negative_int(data: dict[str, Any], key: str) -> int:
    value = int(data.get(key, -1))
    if value < 0:
        raise ValueError(f"Поле '{key}' не может быть отрицательным")
    return value


def _bounded_int(data: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = int(data.get(key, minimum - 1))
    if value < minimum or value > maximum:
        raise ValueError(f"Поле '{key}' должно находиться в диапазоне {minimum}..{maximum}")
    return value


def _bounded_float(data: dict[str, Any], key: str, minimum: float, maximum: float) -> float:
    value = float(data.get(key, minimum - 1.0))
    if value < minimum or value > maximum:
        raise ValueError(f"Поле '{key}' должно находиться в диапазоне {minimum}..{maximum}")
    return value


def _int_tuple(value: Any, length: int, label: str) -> tuple[int, ...]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} должен быть массивом из {length} целых чисел")
    return tuple(int(item) for item in value)


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} должен быть массивом строк")
    result = [str(item).strip() for item in value]
    if any(not item for item in result):
        raise ValueError(f"{label} содержит пустую строку")
    return result
