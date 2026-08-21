from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .ranking import RankedCandidate


def write_reports(
    run_dir: Path,
    metadata: dict[str, Any],
    ranked: list[RankedCandidate],
    selected: list[RankedCandidate],
) -> None:
    minimum_score = float(metadata.get("minimum_score", 0.0))
    payload = {
        "metadata": metadata,
        "ranked_candidates": [candidate.to_dict() for candidate in ranked],
        "selected_candidates": [
            {
                **candidate.to_dict(),
                "meets_threshold": candidate.final_score >= minimum_score and not candidate.hard_reject,
            }
            for candidate in selected
        ],
    }
    (run_dir / "report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "report.md").write_text(
        _markdown_report(metadata, ranked, selected),
        encoding="utf-8",
    )

    selected_dir = run_dir / "selected"
    selected_dir.mkdir(parents=True, exist_ok=True)
    for index, candidate in enumerate(selected, start=1):
        source = Path(candidate.normalized_path)
        target = selected_dir / f"rank_{index:02d}_{candidate.candidate_id}.png"
        shutil.copy2(source, target)
    if selected:
        create_contact_sheet(selected, selected_dir / "contact_sheet.png", minimum_score)


def create_contact_sheet(
    candidates: list[RankedCandidate],
    output_path: Path,
    minimum_score: float,
) -> None:
    scale = 4
    card_width = 96 * scale + 24
    card_height = 96 * scale + 92
    sheet = Image.new("RGBA", (card_width * len(candidates), card_height), (24, 24, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for index, candidate in enumerate(candidates):
        sprite = Image.open(candidate.normalized_path).convert("RGBA")
        enlarged = sprite.resize((sprite.width * scale, sprite.height * scale), Image.Resampling.NEAREST)
        x = index * card_width + 12
        y = 12
        checker = _checkerboard(enlarged.size)
        sheet.alpha_composite(checker, (x, y))
        sheet.alpha_composite(enlarged, (x, y))
        meets_threshold = candidate.final_score >= minimum_score and not candidate.hard_reject
        status = "PASS" if meets_threshold else "BELOW THRESHOLD"
        status_color = (220, 245, 220, 255) if meets_threshold else (255, 205, 125, 255)
        draw.text((x, y + enlarged.height + 8), f"#{index + 1}  {candidate.final_score:.1f}/100", fill=(240, 240, 240, 255))
        draw.text((x, y + enlarged.height + 28), status, fill=status_color)
        draw.text((x, y + enlarged.height + 48), candidate.candidate_id, fill=(190, 190, 190, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output_path, format="PNG", optimize=True)


def _checkerboard(size: tuple[int, int], cell: int = 24) -> Image.Image:
    image = Image.new("RGBA", size, (220, 220, 220, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, min(x + cell - 1, size[0] - 1), min(y + cell - 1, size[1] - 1)), fill=(185, 185, 185, 255))
    return image


def _markdown_report(
    metadata: dict[str, Any],
    ranked: list[RankedCandidate],
    selected: list[RankedCandidate],
) -> str:
    minimum_score = float(metadata.get("minimum_score", 0.0))
    lines = [
        "# Отчёт гибридного sprite pipeline",
        "",
        f"- Персонаж: `{metadata.get('character_id', '')}`",
        f"- Кадр: `{metadata.get('frame_id', '')}`",
        f"- Запущено: `{metadata.get('started_at', '')}`",
        f"- Выполнено раундов: `{metadata.get('rounds_completed', 0)}`",
        f"- Проходной балл: `{minimum_score:.1f}`",
        "",
        "## Кандидаты для согласования",
        "",
    ]
    if not selected:
        lines.append("Ни один кандидат не пережил hard reject. Требуется ручная или модульная правка.")
    else:
        for index, candidate in enumerate(selected, start=1):
            meets_threshold = candidate.final_score >= minimum_score and not candidate.hard_reject
            status = "ПРОШЁЛ АВТОМАТИЧЕСКИЙ ПОРОГ" if meets_threshold else "НИЖЕ ПОРОГА — ТОЛЬКО РУЧНОЕ РАССМОТРЕНИЕ"
            lines.extend([
                f"### {index}. `{candidate.candidate_id}` — {candidate.final_score:.1f}/100",
                "",
                f"**Статус:** {status}",
                "",
                candidate.summary,
                "",
                "Сильные стороны: " + ("; ".join(candidate.strengths) if candidate.strengths else "не зафиксированы"),
                "",
                "Требуемые исправления: " + ("; ".join(candidate.corrections) if candidate.corrections else "нет"),
                "",
            ])
    lines.extend([
        "## Полный рейтинг",
        "",
        "| Кандидат | Итог | Vision | Техника | Статус | Hard reject |",
        "|---|---:|---:|---:|---|---|",
    ])
    for candidate in ranked:
        reject_text = ", ".join(candidate.hard_reject_reasons) if candidate.hard_reject_reasons else "—"
        if candidate.hard_reject:
            status = "REJECT"
        elif candidate.final_score >= minimum_score:
            status = "PASS"
        else:
            status = "BELOW"
        lines.append(
            f"| `{candidate.candidate_id}` | {candidate.final_score:.1f} | {candidate.visual_score:.1f} | {candidate.technical_score:.1f} | {status} | {reject_text} |"
        )
    lines.append("")
    return "\n".join(lines)
