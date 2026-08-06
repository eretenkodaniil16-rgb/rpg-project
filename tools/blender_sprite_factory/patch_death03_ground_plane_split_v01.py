from __future__ import annotations

from pathlib import Path


ADAPTER = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)
TEST = Path("tools/blender_sprite_factory/tests/test_death_down_keyposes_v01.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    adapter = ADAPTER.read_text(encoding="utf-8")
    adapter = replace_once(
        adapter,
        '''def _upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 4:
        return (0.35, -0.30, 0.45)
    if frame_number == 5:
        return (0.42, -0.40, 0.55)
    return (0.0, 0.0, 0.0)
''',
        '''def _upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 4:
        return (0.35, 0.30, 0.45)
    if frame_number == 5:
        return (0.42, 0.40, 0.55)
    return (0.0, 0.0, 0.0)
''',
        "upper-body ground-plane offset",
    )
    ADAPTER.write_text(adapter, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test = replace_once(
        test,
        '''        self.assertIn("_detach_upper_body", source)
        self.assertIn("_restore_upper_body", source)''',
        '''        self.assertIn("_detach_upper_body", source)
        self.assertIn("return (0.35, 0.30, 0.45)", source)
        self.assertIn("return (0.42, 0.40, 0.55)", source)
        self.assertIn("_restore_upper_body", source)''',
        "ground-plane offset assertions",
    )
    TEST.write_text(test, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
