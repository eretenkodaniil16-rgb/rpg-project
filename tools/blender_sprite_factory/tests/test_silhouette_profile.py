from __future__ import annotations

import unittest

from silhouette_profile import load_silhouette_profile


class SilhouetteProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_silhouette_profile("human_warrior_m01")

    def test_profile_is_versioned_and_self_validating(self) -> None:
        self.assertEqual(self.profile.revision, "v03")
        self.profile.assert_valid()

    def test_torso_is_shallower_without_narrowing_the_character_axis(self) -> None:
        profile = self.profile
        self.assertLess(profile.ribcage_depth_scale, 0.80)
        self.assertLess(
            profile.chest_armor_dimensions[1],
            profile.chest_armor_dimensions[0] * 0.35,
        )

    def test_idle_legs_form_an_outward_depth_staggered_stance(self) -> None:
        left = self.profile.leg_points("L")
        right = self.profile.leg_points("R")
        self.assertGreater(left[2][0], left[0][0])
        self.assertLess(right[2][0], right[0][0])
        self.assertGreater(abs(left[0][1] - right[0][1]), 0.20)
        self.assertGreater(self.profile.boot_x, 0.55)
        self.assertGreater(self.profile.boot_outward_degrees, 7.0)

    def test_arms_bend_forward_and_stay_on_their_physical_sides(self) -> None:
        left = self.profile.arm_points("L")
        right = self.profile.arm_points("R")
        self.assertTrue(all(point[0] > 0.0 for point in left))
        self.assertTrue(all(point[0] < 0.0 for point in right))
        self.assertLess(left[3][1], left[2][1])
        self.assertLess(right[3][1], right[2][1])

    def test_asymmetric_shoulders_and_flared_cloth_remain_explicit(self) -> None:
        profile = self.profile
        left_extent = max(
            part.location[0] + part.scale[0]
            for part in profile.left_pauldron_plates
        )
        right_extent = abs(
            profile.right_pauldron.location[0]
            - profile.right_pauldron.scale[0]
        )
        self.assertGreater(left_extent, right_extent * 1.10)
        self.assertTrue(
            all(
                panel.radius_bottom > panel.radius_top
                for panel in profile.cloth_panels
            )
        )

    def test_lower_cloth_expands_in_width_and_depth_for_true_side_views(self) -> None:
        profile = self.profile
        left_extent = max(
            part.location[0] + part.scale[0]
            for part in profile.left_pauldron_plates
        )
        cloth_width_extent = max(
            abs(panel.location[0])
            + panel.radius_bottom * panel.cross_section_scale[0]
            for panel in profile.cloth_panels
        )
        self.assertGreater(cloth_width_extent, left_extent * 0.90)
        self.assertTrue(
            all(
                panel.cross_section_scale[1] > panel.cross_section_scale[0]
                for panel in profile.cloth_panels
            )
        )
        self.assertGreater(
            max(
                panel.location[1]
                + panel.radius_bottom * panel.cross_section_scale[1]
                for panel in profile.cloth_panels
            ),
            1.0,
        )

    def test_unknown_character_cannot_reuse_this_body_profile_silently(self) -> None:
        with self.assertRaisesRegex(KeyError, "No silhouette profile"):
            load_silhouette_profile("dwarf_warrior_m01")


if __name__ == "__main__":
    unittest.main()
