from __future__ import annotations

from pathlib import Path


PATH = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)
OLD = '''def _upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 4:
        return (0.45, -0.30, 0.45)
    if frame_number == 5:
        return (0.54, -0.40, 0.55)
    return (0.0, 0.0, 0.0)
'''
NEW = '''def _upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 4:
        return (0.35, -0.30, 0.45)
    if frame_number == 5:
        return (0.42, -0.40, 0.55)
    return (0.0, 0.0, 0.0)
'''


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count != 1:
        raise RuntimeError(f"expected one upper-body offset block, found {count}")
    PATH.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
