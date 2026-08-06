from __future__ import annotations

from pathlib import Path


ADAPTER = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = ADAPTER.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''    if frame_number == 4:
        return (0.58, -0.12, 0.10)
    if frame_number == 5:
        return (0.86, -0.18, 0.04)
''',
        '''    if frame_number == 4:
        return (0.78, -0.38, 0.18)
    if frame_number == 5:
        return (1.05, -0.52, 0.10)
''',
        "death_03 upper-body offsets",
    )
    text = replace_once(
        text,
        '''                        fixed_scale=down_calibration.scale,
                        fixed_center_x=down_calibration.source_center_x,
''',
        '''                        fixed_scale=down_calibration.scale,
                        fixed_center_x=(
                            None
                            if split_states
                            else down_calibration.source_center_x
                        ),
''',
        "death_03 detached-frame centering",
    )
    ADAPTER.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
