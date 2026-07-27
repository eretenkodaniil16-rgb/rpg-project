from __future__ import annotations

import unittest

from head_profile import (
    HUMAN_WARRIOR_M01_HEAD_V01,
    HUMAN_WARRIOR_M01_HEAD_V02,
    HUMAN_WARRIOR_M01_HEAD_V03,
    load_head_profile,
)


class HeadProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile("human_warrior_m01")

    def test_profile_is_versioned_separately_from_accepted_body(self) -> None:
        self.assertEqual(self.profile.revision, "v03")
        self.assertEqual(self.profile.proxy_revision, "v06")
        self.profile.assert_valid()

    def test_previous_head_revisions_remain_reproducible(self) -> None:
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V01.revision, "v01")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V01.proxy_revision, "v04")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V02.revision, "v02")
        self.assertEqual(HUMAN_WARRIOR_M01_HEAD_V02.proxy_revision, "v05")
        HUMAN_WARRIOR_M01_HEAD_V01.assert_valid()
        HUMAN_WARRIOR_M01_HEAD_V02.assert_valid()

    def test_cranium_size_is_locked_to_head_v02(self) -> None:
        self.assertEqual(
            HUMAN_WARRIOR_M01_HEAD_V03.head_base.scale,
            HUMAN_WARRIOR_M01_HEAD_V02.head_base.scale,
        )
        self.assertEqual(
            HUMAN_WARRIOR_M01_HEAD_V03.head_base.location,
            HUMAN_WARRIOR_M01_HEAD_V02.head_base.location,
        )

    def test_adult_jaw_is_narrower_but_taller_than_v02(self) -> None:
        profile = self.profile
        previous = HUMAN_WARRIOR_M01_HEAD_V02
        self.assertLess(profile.jaw.scale[0], previous.jaw.scale[0])
        self.assertGreater(profile.jaw.scale[2], previous.jaw.scale[2])
        self.assertLess(profile.jaw.location[2], previous.jaw.location[2])
        self.assertGreater(profile.head_base.scale[0], profile.jaw.scale[0])

    def test_hair_cap_is_reduced_instead_of_rescaling_the_head(self) -> None:
        profile = self.profile
        previous = HUMAN_WARRIOR_M01_HEAD_V02
        self.assertLess(profile.hair_cap.scale[0], previous.hair_cap.scale[0])
        self.assertLess(profile.hair_cap.scale[1], previous.hair_cap.scale[1])
        self.assertLess(profile.hair_cap.scale[2], previous.hair_cap.scale[2])

    def test_medium_wavy_hair_has_distinct_front_side_back_and_nape_masses(self) -> None:
        profile = self.profile
        names = {
            part.name
            for part in (
                profile.hair_back_masses
                + profile.hair_front_locks
                + profile.hair_side_locks
            )
        }
        self.assertIn("hair_lock_crown_front", names)
        self.assertIn("hair_lock_front_center", names)
        self.assertIn("hair_lock_crown_back", names)
        self.assertIn("hair_lock_side_left", names)
        self.assertIn("hair_lock_side_right", names)
        self.assertIn("hair_back_left", names)
        self.assertIn("hair_back_right", names)
        self.assertIn("hair_nape_left", names)
        self.assertIn("hair_nape_right", names)

    def test_rear_crown_restores_height_without_changing_cranium(self) -> None:
        profile = self.profile
        front_crown = next(
            part
            for part in profile.hair_front_locks
            if part.name == "hair_lock_crown_front"
        )
        back_crown = next(
            part
            for part in profile.hair_back_masses
            if part.name == "hair_lock_crown_back"
        )
        front_top = front_crown.location[2] + front_crown.scale[2]
        back_top = back_crown.location[2] + back_crown.scale[2]
        self.assertLessEqual(abs(front_top - back_top), 0.05)
        self.assertLessEqual(front_crown.location[1], -0.37)
        self.assertGreaterEqual(back_crown.location[1], 0.44)
        cap_front = profile.hair_cap.location[1] - profile.hair_cap.scale[1]
        cap_back = profile.hair_cap.location[1] + profile.hair_cap.scale[1]
        self.assertGreaterEqual(
            front_crown.location[1] + front_crown.scale[1],
            cap_front,
        )
        self.assertLessEqual(
            back_crown.location[1] - back_crown.scale[1],
            cap_back,
        )

    def test_face_plane_is_not_hidden_by_forehead_lock(self) -> None:
        profile = self.profile
        eye_top = max(
            part.location[2] + part.dimensions[2] * 0.5
            for part in profile.eyes
        )
        front_hairline = min(
            part.location[2] - part.scale[2]
            for part in profile.hair_front_locks
        )
        self.assertGreaterEqual(front_hairline, eye_top)
        self.assertGreater(profile.hair_cap.location[1], profile.head_base.location[1])

    def test_stern_brows_and_centered_eyes_are_explicit(self) -> None:
        profile = self.profile
        left_brow, right_brow = profile.brows
        self.assertLess(left_brow.rotation_y_degrees, 0.0)
        self.assertGreater(right_brow.rotation_y_degrees, 0.0)
        self.assertLess(abs(left_brow.rotation_y_degrees), 8.0)
        left_eye, right_eye = profile.eyes
        self.assertAlmostEqual(left_eye.location[0], -right_eye.location[0])
        self.assertLess(profile.mouth.location[2], left_eye.location[2])

    def test_face_features_have_separate_pixel_row_budgets(self) -> None:
        profile = self.profile
        brow_bottom = min(
            part.location[2] - part.dimensions[2] * 0.5
            for part in profile.brows
        )
        eye_top = max(
            part.location[2] + part.dimensions[2] * 0.5
            for part in profile.eyes
        )
        eye_bottom = min(
            part.location[2] - part.dimensions[2] * 0.5
            for part in profile.eyes
        )
        mouth_top = profile.mouth.location[2] + profile.mouth.dimensions[2] * 0.5
        self.assertGreaterEqual(brow_bottom - eye_top, 0.12)
        self.assertGreaterEqual(eye_bottom - mouth_top, 0.20)
        self.assertLess(
            max(part.dimensions[0] for part in profile.brows),
            max(part.dimensions[0] for part in HUMAN_WARRIOR_M01_HEAD_V02.brows),
        )
        self.assertLess(self.profile.mouth.dimensions[0], HUMAN_WARRIOR_M01_HEAD_V02.mouth.dimensions[0])

    def test_unknown_character_cannot_reuse_head_identity_silently(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head profile"):
            load_head_profile("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
