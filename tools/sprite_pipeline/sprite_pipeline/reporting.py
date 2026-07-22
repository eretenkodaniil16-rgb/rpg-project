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
    payload = {
        "metadata": metadata,
        "ranked_candidates": [candidate.to_dict() for candidate in ranked],
        "selected_candidates": [candidate.to_dict() for candidate in selected],
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
        create_contact_sheet(selected, selected_dir / "contact_sheet.png")


def create_contact_sheet(candidates: list[RankedCandidate], output_path: Path) -> None:
    scale = 4
    card_width = 96 * scale + 24
    card_height = 96 * scale + 72
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
        draw.text((x, y + enlarged.height + 8), f"#{index + 1}  {candidate.final_score:.1f}/100", fill=(240, 240, 240, 255))
        draw.text((x, y + enlarged.height + 28), candidate.candidate_id, fill=(190, 190, 190, 255))
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
    lines = [
        "# Sprite pipeline report",
        "",
        f"- Character: `{metadata.get('character_id', '')}`",
        f"- Frame: `{metadata.get('frame_id', '')}`",
        f"- Started: `{metadata.get('started_at', '')}`",
        f"- Rounds: `{metadata.get('rounds_completed', 0)}`",
        f"- Minimum score: `{metadata.get('minimum_score', '')}`",
        "",
        "## Selected for human approval",
        "",
    ]
    if not selected:
        lines.append("No candidate survived hard rejects. Manual intervention is required.")
    else:
        for index, candidate in enumerate(selected, start=1):
            lines.extend([
                f"### {index}. `{candidate.candidate_id}` — {candidate.final_score:.1f}/100",
                "",
                candidate.summary,
                "",
                "Strengths: " + ("; ".join(candidate.strengths) if candidate.strengths else "none recorded"),
                "",
                "Required corrections: " + ("; ".join(candidate.corrections) if candidate.corrections else "none"),
                "",
            ])
    lines.extend([
        "## Full ranking",
        "",
        "| Candidate | Final | Visual | Technical | Hard reject |",
        "|---|---:|---:|---:|---|",
    ])
    for candidate in ranked:
        reject_text = ", ".join(candidate.hard_reject_reasons) if candidate.hard_reject_reasons else "—"
        lines.append(
            f"| `{candidate.candidate_id}` | {candidate.final_score:.1f} | {candidate.visual_score:.1f} | {candidate.technical_score:.1f} | {reject_text} |"
        )
    lines.append("")
    return "\n".join(lines)
