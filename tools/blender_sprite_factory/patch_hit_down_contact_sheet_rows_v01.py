from __future__ import annotations

from pathlib import Path


PATH = Path("tools/blender_sprite_factory/blender_sprite_factory_hit_down_keyposes_v01.py")
OLD = '''                    column_index * tile_width,
                    row_index * tile_height,
'''
NEW = '''                    column_index * tile_width,
                    (len(profiles) - 1 - row_index) * tile_height,
'''


def main() -> int:
    content = PATH.read_text(encoding="utf-8")
    count = content.count(OLD)
    if count != 1:
        raise RuntimeError(f"expected one contact-sheet row placement, found {count}")
    PATH.write_text(content.replace(OLD, NEW, 1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
