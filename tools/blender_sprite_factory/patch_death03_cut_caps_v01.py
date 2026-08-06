from __future__ import annotations

from pathlib import Path


PATH = Path("tools/blender_sprite_factory/death_down_keyposes_builder_v01.py")
REPLACEMENTS = (
    (
        '''        (0.20, 0.15, 0.070),''',
        '''        (0.12, 0.09, 0.045),''',
        "upper cut-cap radii",
    ),
    (
        '''        (0.22, 0.16, 0.075),''',
        '''        (0.13, 0.10, 0.050),''',
        "lower cut-cap radii",
    ),
)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    for old, new, label in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"{label}: expected one match, found {count}")
        text = text.replace(old, new, 1)
    PATH.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
