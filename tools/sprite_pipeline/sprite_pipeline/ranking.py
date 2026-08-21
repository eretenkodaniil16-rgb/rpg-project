from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .openai_backend import VisualGrade
from .technical import TechnicalResult


@dataclass
class RankedCandidate:
    candidate_id: str
    normalized_path: str
    hard_reject: bool
    hard_reject_reasons: list[str]
    technical_score: float
    visual_score: float
    final_score: float
    scores: dict[str, float]
    summary: str
    strengths: list[str]
    corrections: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def rank_candidates(
    technical_results: Iterable[TechnicalResult],
    visual_grades: dict[str, VisualGrade],
    weights: dict[str, float],
) -> list[RankedCandidate]:
    ranked: list[RankedCandidate] = []
    for technical in technical_results:
        if not technical.passed or technical.normalized_path is None:
            continue
        grade = visual_grades.get(technical.candidate_id)
        if grade is None:
            continue
        visual_score = sum(
            max(0.0, min(100.0, float(grade.scores.get(key, 0.0)))) * weight
            for key, weight in weights.items()
        )
        hard_reject_reasons = sorted(set([
            *technical.hard_reject_reasons,
            *grade.hard_reject_reasons,
        ]))
        hard_reject = bool(grade.hard_reject or hard_reject_reasons)
        final_score = 0.0 if hard_reject else 0.85 * visual_score + 0.15 * technical.technical_score
        ranked.append(RankedCandidate(
            candidate_id=technical.candidate_id,
            normalized_path=technical.normalized_path,
            hard_reject=hard_reject,
            hard_reject_reasons=hard_reject_reasons,
            technical_score=round(technical.technical_score, 3),
            visual_score=round(visual_score, 3),
            final_score=round(final_score, 3),
            scores={key: round(float(value), 3) for key, value in grade.scores.items()},
            summary=grade.summary,
            strengths=grade.strengths,
            corrections=grade.corrections,
        ))
    ranked.sort(key=lambda item: (item.hard_reject, -item.final_score, item.candidate_id))
    return ranked


def select_top(
    ranked: list[RankedCandidate],
    top_k: int,
    minimum_score: float,
) -> list[RankedCandidate]:
    accepted = [
        candidate
        for candidate in ranked
        if not candidate.hard_reject and candidate.final_score >= minimum_score
    ]
    if accepted:
        return accepted[:top_k]
    fallback = [candidate for candidate in ranked if not candidate.hard_reject]
    return fallback[:top_k]
