from __future__ import annotations

import base64
import json
import os
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from .config import GenerationSpec


@dataclass
class VisualGrade:
    candidate_id: str
    hard_reject: bool
    hard_reject_reasons: list[str]
    scores: dict[str, float]
    summary: str
    strengths: list[str]
    corrections: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "hard_reject": self.hard_reject,
            "hard_reject_reasons": self.hard_reject_reasons,
            "scores": self.scores,
            "summary": self.summary,
            "strengths": self.strengths,
            "corrections": self.corrections,
        }


class OpenAIBackend:
    def __init__(self, generation: GenerationSpec) -> None:
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY не задан")
        self._generation = generation
        self._client = OpenAI()

    def edit_images(
        self,
        reference_paths: list[Path],
        prompt: str,
        output_dir: Path,
        count: int,
        prefix: str,
    ) -> list[Path]:
        if not reference_paths:
            raise ValueError("Для редактирования нужен хотя бы один исходный PNG")
        missing = [str(path) for path in reference_paths if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Не найдены reference-файлы: {missing}")
        safe_count = max(1, min(int(count), 10))
        output_dir.mkdir(parents=True, exist_ok=True)

        with ExitStack() as stack:
            opened = [stack.enter_context(path.open("rb")) for path in reference_paths]
            image_argument: Any = opened[0] if len(opened) == 1 else opened
            result = self._client.images.edit(
                model=self._generation.image_model,
                image=image_argument,
                prompt=prompt,
                n=safe_count,
                size=self._generation.size,
                quality=self._generation.quality,
                input_fidelity=self._generation.input_fidelity,
                background="transparent",
                output_format="png",
            )

        paths: list[Path] = []
        for index, item in enumerate(result.data, start=1):
            encoded = getattr(item, "b64_json", None)
            if not encoded:
                continue
            path = output_dir / f"{prefix}_{index:02d}.png"
            path.write_bytes(base64.b64decode(encoded))
            paths.append(path)
        if not paths:
            raise RuntimeError("Images API не вернул ни одного PNG")
        return paths

    def grade_candidate(
        self,
        candidate_id: str,
        candidate_path: Path,
        reference_paths: list[Path],
        frame_prompt: str,
        hard_reject_labels: tuple[str, ...],
    ) -> VisualGrade:
        content: list[dict[str, Any]] = [
            {
                "type": "input_text",
                "text": _grader_prompt(candidate_id, frame_prompt, hard_reject_labels),
            }
        ]
        for index, path in enumerate(reference_paths, start=1):
            content.append({"type": "input_text", "text": f"REFERENCE {index}: {path.name}"})
            content.append({
                "type": "input_image",
                "image_url": _data_url(path),
                "detail": "high",
            })
        content.append({"type": "input_text", "text": f"CANDIDATE: {candidate_path.name}"})
        content.append({
            "type": "input_image",
            "image_url": _data_url(candidate_path),
            "detail": "high",
        })

        response = self._client.responses.create(
            model=self._generation.grader_model,
            input=[{"role": "user", "content": content}],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "sprite_candidate_grade",
                    "strict": True,
                    "schema": _grade_schema(),
                }
            },
        )
        raw = json.loads(response.output_text)
        scores = {key: float(value) for key, value in raw["scores"].items()}
        return VisualGrade(
            candidate_id=candidate_id,
            hard_reject=bool(raw["hard_reject"]),
            hard_reject_reasons=[str(item) for item in raw["hard_reject_reasons"]],
            scores=scores,
            summary=str(raw["summary"]),
            strengths=[str(item) for item in raw["strengths"]],
            corrections=[str(item) for item in raw["corrections"]],
        )


def _data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _grader_prompt(candidate_id: str, frame_prompt: str, reject_labels: tuple[str, ...]) -> str:
    labels = ", ".join(reject_labels)
    return f"""
Ты — строгий арт-директор и технический контролёр игрового pixel-art проекта.

Сравни CANDIDATE с приложенными REFERENCE. Первый reference задаёт личность, лицо и общий стиль. Направленный idle задаёт масштаб, перспективу и физические стороны экипировки. Оцени только соответствие, не пытайся оправдать изменения генератора.

Кандидат: {candidate_id}

Требуемая фаза:
{frame_prompt}

Критерии оцениваются от 0 до 100:
- identity_face: тот же взрослый мужчина, форма головы, скрытые глаза, нос, подбородок, волосы;
- equipment_sides: большой серебряный наплечник на физической левой руке, меньший тёмный на правой, меч/ножны/сумки не перепутаны;
- perspective: единый gameplay top-down 3/4, камера 45–50° сверху;
- proportions: размер головы, ширина плеч, телосложение, масштаб и базовая линия;
- pose: точность конкретной фазы движения и возможность бесшовного цикла;
- palette_style: кожа, бордовый шарф, кожа/кольчуга/сталь, чёткий pixel-art без размытия.

Немедленный hard reject применяется при любом из классов: {labels}.
Hard reject важнее итогового балла. В corrections перечисляй только конкретные локальные исправления. Не предлагай полный редизайн или новую генерацию персонажа.
""".strip()


def _grade_schema() -> dict[str, Any]:
    score_properties = {
        key: {"type": "number", "minimum": 0, "maximum": 100}
        for key in (
            "identity_face",
            "equipment_sides",
            "perspective",
            "proportions",
            "pose",
            "palette_style",
        )
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "hard_reject",
            "hard_reject_reasons",
            "scores",
            "summary",
            "strengths",
            "corrections",
        ],
        "properties": {
            "hard_reject": {"type": "boolean"},
            "hard_reject_reasons": {"type": "array", "items": {"type": "string"}},
            "scores": {
                "type": "object",
                "additionalProperties": False,
                "required": list(score_properties),
                "properties": score_properties,
            },
            "summary": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "corrections": {"type": "array", "items": {"type": "string"}},
        },
    }
