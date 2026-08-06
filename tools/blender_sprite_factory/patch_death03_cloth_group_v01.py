from __future__ import annotations

from pathlib import Path


BUILDER = Path("tools/blender_sprite_factory/death_down_keyposes_builder_v01.py")
TEST = Path("tools/blender_sprite_factory/tests/test_death_down_keyposes_v01.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    builder = BUILDER.read_text(encoding="utf-8")
    builder = replace_once(
        builder,
        '''        "hand.L",
        "hand.R",
    }
)''',
        '''        "hand.L",
        "hand.R",
        "cloth.L",
        "cloth.C",
        "cloth.R",
    }
)''',
        "upper-body cloth bone set",
    )
    BUILDER.write_text(builder, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test = replace_once(
        test,
        '''        self.assertIn("_GORE_UPPER_BODY_BONES", source)
        self.assertIn('scene["death_down_action_count"] = len(actions)', source)''',
        '''        self.assertIn("_GORE_UPPER_BODY_BONES", source)
        self.assertIn('"cloth.L"', source)
        self.assertIn('"cloth.C"', source)
        self.assertIn('"cloth.R"', source)
        self.assertIn('scene["death_down_action_count"] = len(actions)', source)''',
        "cloth-group static assertions",
    )
    TEST.write_text(test, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
