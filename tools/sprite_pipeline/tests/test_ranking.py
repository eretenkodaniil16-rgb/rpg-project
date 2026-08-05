from __future__ import annotations

import unittest

from sprite_pipeline.openai_backend import VisualGrade
from sprite_pipeline.ranking import rank_candidates, select_top
from sprite_pipeline.technical import TechnicalResult


class RankingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.weights = {
            "identity_face": 0.30,
            "equipment_sides": 0.20,
            "perspective": 0.15,
            "proportions": 0.15,
            "pose": 0.10,
            "palette_style": 0.10,
        }

    def _technical(self, candidate_id: str, score: float = 100.0) -> TechnicalResult:
        return TechnicalResult(
            candidate_id=candidate_id,
            source_path=f"raw/{candidate_id}.png",
            normalized_path=f"normalized/{candidate_id}.png",
            passed=True,
            hard_reject_reasons=[],
            metrics={},
            technical_score=score,
        )

    def _grade(self, candidate_id: str, value: float, hard_reject: bool = False) -> VisualGrade:
        return VisualGrade(
            candidate_id=candidate_id,
            hard_reject=hard_reject,
            hard_reject_reasons=["face_identity_changed"] if hard_reject else [],
            scores={key: value for key in self.weights},
            summary="summary",
            strengths=["stable"],
            corrections=[],
        )

    def test_higher_visual_score_ranks_first(self) -> None:
        technical = [self._technical("a", 90), self._technical("b", 100)]
        grades = {"a": self._grade("a", 94), "b": self._grade("b", 86)}

        ranked = rank_candidates(technical, grades, self.weights)

        self.assertEqual([candidate.candidate_id for candidate in ranked], ["a", "b"])
        self.assertGreater(ranked[0].final_score, ranked[1].final_score)

    def test_hard_reject_never_becomes_selected(self) -> None:
        technical = [self._technical("good"), self._technical("reject")]
        grades = {
            "good": self._grade("good", 88),
            "reject": self._grade("reject", 100, hard_reject=True),
        }

        ranked = rank_candidates(technical, grades, self.weights)
        selected = select_top(ranked, top_k=2, minimum_score=85)

        self.assertEqual([candidate.candidate_id for candidate in selected], ["good"])
        rejected = next(candidate for candidate in ranked if candidate.candidate_id == "reject")
        self.assertEqual(rejected.final_score, 0.0)

    def test_best_non_rejected_is_returned_as_fallback_below_threshold(self) -> None:
        technical = [self._technical("a"), self._technical("b")]
        grades = {"a": self._grade("a", 81), "b": self._grade("b", 79)}

        ranked = rank_candidates(technical, grades, self.weights)
        selected = select_top(ranked, top_k=1, minimum_score=85)

        self.assertEqual(selected[0].candidate_id, "a")


if __name__ == "__main__":
    unittest.main()
