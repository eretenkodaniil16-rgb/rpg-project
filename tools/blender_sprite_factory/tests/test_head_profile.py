from __future__ import annotations

import unittest

from head_profile import HUMAN_WARRIOR_M01_HEAD_V01, load_head_profile


class HeadProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_head_profile("human_warrior_m01")

    def test_profile_is_versioned_separately_from_accepted_body(self) -> None:
        self.assertEqual(self.profile.revision, "v02")
        self.assertEqual(self.profile.proxy_revision, "v05")
        self.profile.assert_valid()

    def test_readability_pass_strengthens_jaw_without_rescaling_cranium(self) -> None:
        profile = self.profile
        previous = HUMAN_WARRIOR_M01_HEAD_V01
        self.assertEqual(profile.head_base.scale, previous.head_base.scale)
        self.assertGreater(profile.jaw.scale[0], previous.jaw.scale[0])
        self.assertGreater(profile.jaw.scale[2], previous.jaw.scale[2])
        self.assertEqual(previous.revision, "v01")
        self.assertEqual(previous.proxy_revision, "v04")

    def test_adult_head_tapers_to_a_separate_jaw(self) -> None:
        profile = self.profile
        self.assertGreater(profile.head_base.scale[0], profile.jaw.scale[0])
        self.assertGreater(profile.head_base.location[2], profile.jaw.location[2])
        self.assertLess(profile.jaw.location[1], profile.head_base.location[1])

    def test_face_plane_is_not_hidden_by_front_hair(self) -> None:
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
        self.assertGreater(
            profile.hair_cap.location[1],
            profile.head_base.location[1],
        )

    def test_medium_wavy_hair_has_front_side_and_back_masses(self) -> None:
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
        self.assertIn("hair_lock_crown_back", names)
        self.assertIn("hair_lock_side_left", names)
        self.assertIn("hair_lock_side_right", names)
        self.assertIn("hair_back_mass", names)
        self.assertGreater(
            max(part.location[1] for part in profile.hair_back_masses),
            0.15,
        )

    def test_front_and_back_crown_keep_turnaround_height(self) -> None:
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
        self.assertLessEqual(abs(front_top - back_top), 0.02)
        self.assertLessEqual(front_crown.location[1], -0.55)
        self.assertGreaterEqual(back_crown.location[1], 0.55)

    def test_stern_brows_and_centered_eyes_are_explicit(self) -> None:
        profile = self.profile
        left_brow, right_brow = profile.brows
        self.assertLess(left_brow.rotation_y_degrees, 0.0)
        self.assertGreater(right_brow.rotation_y_degrees, 0.0)
        left_eye, right_eye = profile.eyes
        self.assertAlmostEqual(left_eye.location[0], -right_eye.location[0])
        self.assertLess(profile.mouth.location[2], left_eye.location[2])

    def test_face_features_have_a_final_pixel_visibility_budget(self) -> None:
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
        mouth_top = (
            profile.mouth.location[2]
            + profile.mouth.dimensions[2] * 0.5
        )
        self.assertGreaterEqual(brow_bottom - eye_top, 0.07)
        self.assertGreaterEqual(eye_bottom - mouth_top, 0.18)
        self.assertGreaterEqual(
            min(part.dimensions[0] for part in profile.eyes),
            0.08,
        )
        self.assertGreaterEqual(profile.mouth.dimensions[0], 0.18)

    def test_unknown_character_cannot_reuse_head_identity_silently(self) -> None:
        with self.assertRaisesRegex(KeyError, "No head profile"):
            load_head_profile("elf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
