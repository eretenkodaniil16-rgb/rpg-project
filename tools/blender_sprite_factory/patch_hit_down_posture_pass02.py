from __future__ import annotations

from pathlib import Path


PROFILE_PATH = Path("tools/blender_sprite_factory/hit_down_keyposes_profile_v01.py")
TEST_PATH = Path("tools/blender_sprite_factory/tests/test_hit_down_keyposes_v01.py")


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}, found {count}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        PROFILE_PATH,
        'revision="hit_down_keyposes_v01",',
        'revision="hit_down_keyposes_v01_pass02",',
    )
    replacements = {
        "spine_pitch_x_degrees=7.0,": "spine_pitch_x_degrees=-7.0,",
        "head_pitch_x_degrees=8.0,": "head_pitch_x_degrees=-8.0,",
        "spine_pitch_x_degrees=12.0,": "spine_pitch_x_degrees=-12.0,",
        "head_pitch_x_degrees=14.0,": "head_pitch_x_degrees=-14.0,",
        "spine_pitch_x_degrees=4.0,": "spine_pitch_x_degrees=-4.0,",
        "head_pitch_x_degrees=5.0,": "head_pitch_x_degrees=-5.0,",
    }
    for old, new in replacements.items():
        replace_once(PROFILE_PATH, old, new)

    replace_once(
        TEST_PATH,
        'self.assertEqual(self.profile.revision, "hit_down_keyposes_v01")',
        'self.assertEqual(self.profile.revision, "hit_down_keyposes_v01_pass02")',
    )
    replace_once(
        TEST_PATH,
        "self.assertGreater(peak.spine_pitch_x_degrees, impact.spine_pitch_x_degrees)",
        "self.assertGreater(abs(peak.spine_pitch_x_degrees), abs(impact.spine_pitch_x_degrees))",
    )
    replace_once(
        TEST_PATH,
        "self.assertGreater(peak.head_pitch_x_degrees, impact.head_pitch_x_degrees)",
        "self.assertGreater(abs(peak.head_pitch_x_degrees), abs(impact.head_pitch_x_degrees))",
    )
    replace_once(
        TEST_PATH,
        "self.assertLess(recovery.spine_pitch_x_degrees, impact.spine_pitch_x_degrees)",
        "self.assertLess(abs(recovery.spine_pitch_x_degrees), abs(impact.spine_pitch_x_degrees))",
    )
    replace_once(
        TEST_PATH,
        "self.assertLess(recovery.head_pitch_x_degrees, impact.head_pitch_x_degrees)",
        "self.assertLess(abs(recovery.head_pitch_x_degrees), abs(impact.head_pitch_x_degrees))",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
