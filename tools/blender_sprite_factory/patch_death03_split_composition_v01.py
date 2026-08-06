from __future__ import annotations

from pathlib import Path


BUILDER = Path(
    "tools/blender_sprite_factory/death_down_keyposes_builder_v01.py"
)
ADAPTER = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    builder = BUILDER.read_text(encoding="utf-8")
    builder = replace_once(
        builder,
        '''        (0.30, 0.22, 0.095),
''',
        '''        (0.20, 0.15, 0.070),
''',
        "upper cut-cap dimensions",
    )
    builder = replace_once(
        builder,
        '''        (0.32, 0.23, 0.10),
''',
        '''        (0.22, 0.16, 0.075),
''',
        "lower cut-cap dimensions",
    )
    BUILDER.write_text(builder, encoding="utf-8")

    adapter = ADAPTER.read_text(encoding="utf-8")
    adapter = replace_once(
        adapter,
        '''    if frame_number == 4:
        return (0.78, -0.38, 0.18)
    if frame_number == 5:
        return (1.05, -0.52, 0.10)
''',
        '''    if frame_number == 4:
        return (0.55, -0.30, 0.45)
    if frame_number == 5:
        return (0.66, -0.40, 0.55)
''',
        "upper-body split composition",
    )
    ADAPTER.write_text(adapter, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
