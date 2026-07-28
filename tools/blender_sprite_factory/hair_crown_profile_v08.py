from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HairCrownSlice:
    y: float
    points_xz: tuple[tuple[float, float], ...]

    def assert_valid(self, expected_points: int) -> None:
        if len(self.points_xz) != expected_points:
            raise ValueError("Every crown slice must use the same point count")
        if len(set(self.points_xz)) != len(self.points_xz):
            raise ValueError("Crown slice points must be unique")
        x_values = [point[0] for point in self.points_xz]
        z_values = [point[1] for point in self.points_xz]
        if min(x_values) >= -0.30 or max(x_values) <= 0.30:
            raise ValueError("Crown slice must span both physical sides of the head")
        if max(z_values) - min(z_values) < 0.35:
            raise ValueError("Crown slice needs a readable vertical silhouette")


@dataclass(frozen=True)
class HairCrownProfileV08:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairCrownSlice, ...]

    def assert_valid(self) -> None:
        if self.revision != "v08" or self.proxy_revision != "v11":
            raise ValueError("Crown profile must match head v08 / proxy v11")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Unexpected crown mesh identity")
        if len(self.slices) != 3:
            raise ValueError("Reference crown must use front, middle and back slices")
        point_count = len(self.slices[0].points_xz)
        if point_count != 8:
            raise ValueError("Reference crown needs eight coarse contour points")
        for item in self.slices:
            item.assert_valid(point_count)
        y_values = [item.y for item in self.slices]
        if y_values != sorted(y_values):
            raise ValueError("Crown slices must run from face side to back side")
        if self.slices[0].y > -0.40:
            raise ValueError("Front crown slice must remain ahead of the cranium")
        if self.slices[-1].y < 0.20:
            raise ValueError("Back crown slice must cover the rear silhouette")

        front = self.slices[0].points_xz
        top_points = sorted(front, key=lambda point: point[1], reverse=True)[:3]
        if len({point[1] for point in top_points}) < 3:
            raise ValueError("Front crown top must remain asymmetrical")
        if min(point[1] for point in front) <= 4.20:
            raise ValueError("Front crown must not cover the readable eye line")
        if min(point[1] for point in self.slices[-1].points_xz) > 4.25:
            raise ValueError("Back crown needs sufficient medium-length drop")


HUMAN_WARRIOR_M01_HAIR_CROWN_V08 = HairCrownProfileV08(
    revision="v08",
    proxy_revision="v11",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairCrownSlice(
            y=-0.485,
            points_xz=(
                (-0.430, 4.430),
                (-0.420, 4.690),
                (-0.275, 4.925),
                (-0.075, 5.035),
                (0.125, 4.990),
                (0.305, 4.885),
                (0.435, 4.650),
                (0.400, 4.430),
            ),
        ),
        HairCrownSlice(
            y=-0.050,
            points_xz=(
                (-0.475, 4.380),
                (-0.460, 4.680),
                (-0.305, 4.945),
                (-0.100, 5.010),
                (0.120, 4.975),
                (0.340, 4.855),
                (0.470, 4.600),
                (0.430, 4.380),
            ),
        ),
        HairCrownSlice(
            y=0.285,
            points_xz=(
                (-0.410, 4.205),
                (-0.440, 4.545),
                (-0.295, 4.815),
                (-0.080, 4.925),
                (0.150, 4.895),
                (0.335, 4.720),
                (0.420, 4.435),
                (0.380, 4.205),
            ),
        ),
    ),
)


def load_hair_crown_profile_v08() -> HairCrownProfileV08:
    HUMAN_WARRIOR_M01_HAIR_CROWN_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_CROWN_V08
