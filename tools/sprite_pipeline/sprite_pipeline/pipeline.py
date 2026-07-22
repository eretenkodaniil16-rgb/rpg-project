from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config import PipelineConfig
from .openai_backend import OpenAIBackend, VisualGrade
from .ranking import RankedCandidate, rank_candidates, select_top
from .reporting import write_reports
from .technical import TechnicalResult, normalize_and_validate


class SpritePipeline:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def run(
        self,
        frame_id: str,
        output_root: Path,
        candidates: int | None = None,
        top_k: int | None = None,
        max_rounds: int | None = None,
        extra_reference: str | None = None,
    ) -> Path:
        if not self.config.ready:
            raise RuntimeError(
                "Reference pack ещё не утверждён: в manifest установлено ready=false. "
                "Добавьте финальные PNG и только затем включите pipeline."
            )
        frame = self.config.frame(frame_id)
        reference_paths = self.config.reference_paths(frame_id, extra_reference)
        _require_files(reference_paths)
        prompt = self.config.load_prompt(frame_id)

        candidate_count = max(1, min(candidates or self.config.generation.initial_candidates, 10))
        selected_count = max(1, min(top_k or self.config.generation.top_k, 5))
        round_limit = max(1, min(max_rounds or self.config.generation.max_rounds, 2))
        backend = OpenAIBackend(self.config.generation)

        started_at = datetime.now(timezone.utc)
        run_dir = output_root / self.config.character_id / frame_id / started_at.strftime("%Y%m%dT%H%M%SZ")
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (run_dir / "manifest.snapshot.json").write_text(
            self.config.manifest_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        all_technical: list[TechnicalResult] = []
        all_grades: dict[str, VisualGrade] = {}
        ranked: list[RankedCandidate] = []
        best_for_refinement: RankedCandidate | None = None
        rounds_completed = 0

        for round_number in range(1, round_limit + 1):
            rounds_completed = round_number
            raw_dir = run_dir / "raw" / f"round_{round_number:02d}"
            normalized_dir = run_dir / "normalized" / f"round_{round_number:02d}"

            round_references = list(reference_paths)
            round_prompt = prompt
            round_count = candidate_count
            if round_number > 1:
                if best_for_refinement is None:
                    break
                round_references = [Path(best_for_refinement.normalized_path), *reference_paths]
                round_references = _deduplicate_paths(round_references)[:16]
                round_count = max(2, min(4, candidate_count // 2))
                correction_text = "\n".join(f"- {item}" for item in best_for_refinement.corrections)
                round_prompt = (
                    f"{prompt}\n\n"
                    "ЭТО ВТОРОЙ ЛОКАЛЬНЫЙ ПРОХОД РЕДАКТИРОВАНИЯ. "
                    "Первое изображение — лучший кандидат предыдущего прохода. "
                    "Не перегенерируй персонажа. Исправь только перечисленные дефекты:\n"
                    f"{correction_text or '- сохранить предыдущий кандидат без новых изменений'}"
                )

            generated = backend.edit_images(
                round_references,
                round_prompt,
                raw_dir,
                round_count,
                prefix=f"r{round_number:02d}_{frame_id}",
            )
            reference_for_local = reference_paths[0]
            for source_path in generated:
                normalized_path = normalized_dir / source_path.name
                technical = normalize_and_validate(
                    source_path,
                    normalized_path,
                    self.config.technical,
                    reference_path=reference_for_local,
                )
                all_technical.append(technical)
                if not technical.passed or technical.normalized_path is None:
                    continue
                try:
                    grade = backend.grade_candidate(
                        technical.candidate_id,
                        Path(technical.normalized_path),
                        reference_paths,
                        prompt,
                        self.config.hard_reject_labels,
                    )
                except Exception as exc:
                    grade = VisualGrade(
                        candidate_id=technical.candidate_id,
                        hard_reject=True,
                        hard_reject_reasons=[f"grader_error:{type(exc).__name__}"],
                        scores={key: 0.0 for key in self.config.weights},
                        summary="Visual grader failed; candidate cannot be auto-approved.",
                        strengths=[],
                        corrections=[str(exc)],
                    )
                all_grades[technical.candidate_id] = grade

            ranked = rank_candidates(all_technical, all_grades, self.config.weights)
            non_rejected = [candidate for candidate in ranked if not candidate.hard_reject]
            best_for_refinement = non_rejected[0] if non_rejected else None
            if best_for_refinement is not None and best_for_refinement.final_score >= self.config.generation.minimum_score:
                break

        selected = select_top(ranked, selected_count, self.config.generation.minimum_score)
        metadata = {
            "schema_version": 1,
            "character_id": self.config.character_id,
            "frame_id": frame.frame_id,
            "direction": frame.direction,
            "started_at": started_at.isoformat(),
            "rounds_completed": rounds_completed,
            "initial_candidates": candidate_count,
            "top_k": selected_count,
            "minimum_score": self.config.generation.minimum_score,
            "image_model": self.config.generation.image_model,
            "grader_model": self.config.generation.grader_model,
            "reference_paths": [str(path) for path in reference_paths],
        }
        write_reports(run_dir, metadata, ranked, selected)
        _write_technical_report(run_dir, all_technical)
        return run_dir

    def validate_directory(
        self,
        frame_id: str,
        input_dir: Path,
        output_root: Path,
    ) -> Path:
        frame = self.config.frame(frame_id)
        source_reference = self.config.resolve_repo_path(frame.source_reference)
        if not source_reference.exists():
            source_reference = None
        started_at = datetime.now(timezone.utc)
        run_dir = output_root / self.config.character_id / frame_id / f"validate_{started_at.strftime('%Y%m%dT%H%M%SZ')}"
        normalized_dir = run_dir / "normalized"
        run_dir.mkdir(parents=True, exist_ok=False)

        results: list[TechnicalResult] = []
        for source_path in sorted(input_dir.glob("*.png")):
            results.append(normalize_and_validate(
                source_path,
                normalized_dir / source_path.name,
                self.config.technical,
                reference_path=source_reference,
            ))
        if not results:
            raise RuntimeError(f"В {input_dir} не найдено PNG-файлов")
        _write_technical_report(run_dir, results)
        return run_dir


def _require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Reference pack неполон. Отсутствуют файлы:\n- " + "\n- ".join(missing)
        )


def _deduplicate_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def _write_technical_report(run_dir: Path, results: list[TechnicalResult]) -> None:
    payload = [result.to_dict() for result in results]
    (run_dir / "technical_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rejected_dir = run_dir / "rejected_raw"
    for result in results:
        if result.passed:
            continue
        source = Path(result.source_path)
        if source.exists():
            rejected_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, rejected_dir / source.name)
