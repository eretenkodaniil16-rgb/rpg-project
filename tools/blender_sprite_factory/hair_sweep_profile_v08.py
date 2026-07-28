from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HairSweepRing:
    z: float
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    phase_degrees: float = 0.0
    arc_start_degrees: float | None = None
    arc_end_degrees: float | None = None

    def resolved_arc(self, part_start: float, part_end: float) -> tuple[float, float]:
        start = part_start if self.arc_start_degrees is None else self.arc_start_degrees
        end = part_end if self.arc_end_degrees is None else self.arc_end_degrees
        return start, end


@dataclass(frozen=True)
class HairSweepMeshPart:
    name: str
    location: tuple[float, float, float]
    segments: int
    wave_frequency: int
    wave_amplitude: float
    rings: tuple[HairSweepRing, ...]
    arc_start_degrees: float = 0.0
    arc_end_degrees: float = 360.0
    closed_around: bool = True

    def ring_arc(self, ring: HairSweepRing) -> tuple[float, float]:
        return ring.resolved_arc(self.arc_start_degrees, self.arc_end_degrees)

    def assert_valid(self) -> None:
        if self.segments < 8 or len(self.rings) < 4:
            raise ValueError(f"Invalid sweep density for {self.name}")
        if self.wave_frequency < 1 or not 0.0 <= self.wave_amplitude <= 0.12:
            raise ValueError(f"Invalid sweep wave for {self.name}")
        if any(ring.radius_x <= 0.0 or ring.radius_y <= 0.0 for ring in self.rings):
            raise ValueError(f"Invalid sweep radius for {self.name}")
        z_values = [ring.z for ring in self.rings]
        if z_values != sorted(z_values) or len(z_values) != len(set(z_values)):
            raise ValueError(f"Sweep rings must have unique ascending z: {self.name}")

        for ring in self.rings:
            arc_start, arc_end = self.ring_arc(ring)
            arc_span = arc_end - arc_start
            if self.closed_around:
                if abs(arc_span - 360.0) > 0.001:
                    raise ValueError(f"Closed sweep {self.name} must span 360 degrees")
            elif not 180.0 <= arc_span < 360.0:
                raise ValueError(f"Open sweep {self.name} needs a rear/side arc")


@dataclass(frozen=True)
class HairSweepProfileV08:
    revision: str
    proxy_revision: str
    meshes: tuple[HairSweepMeshPart, ...]
    profile_accent_names: frozenset[str]
    detail_accent_names: frozenset[str]
    accent_rotations_degrees: tuple[tuple[str, tuple[float, float, float]], ...]

    def assert_valid(self) -> None:
        if self.revision != "v08" or self.proxy_revision != "v11":
            raise ValueError("Sweep profile must match head v08 / proxy v11")
        if [part.name for part in self.meshes] != [
            "hair_reference_shell",
            "hair_reference_nape",
            "hair_reference_forelock",
        ]:
            raise ValueError("Reference hair needs shell, nape and forelock meshes")
        for part in self.meshes:
            part.assert_valid()

        shell, nape, forelock = self.meshes
        if shell.closed_around or nape.closed_around:
            raise ValueError("Shell and nape must leave the face side open")
        if not forelock.closed_around:
            raise ValueError("Forelock must remain a closed strand")

        shell_spans = [
            shell.ring_arc(ring)[1] - shell.ring_arc(ring)[0]
            for ring in shell.rings
        ]
        if shell_spans != sorted(shell_spans):
            raise ValueError("Crown opening must narrow monotonically towards the top")
        if shell_spans[0] > 240.0 or shell_spans[-1] < 350.0:
            raise ValueError("Shell needs an open lower hairline and nearly closed crown")

        rotation_names = [name for name, _rotation in self.accent_rotations_degrees]
        if len(rotation_names) != len(set(rotation_names)):
            raise ValueError("Hair rotation targets must be unique")
        if not self.profile_accent_names.issubset(rotation_names):
            raise ValueError("Every profile accent needs a real rotation")


HUMAN_WARRIOR_M01_HAIR_SWEEP_V08 = HairSweepProfileV08(
    revision="v08",
    proxy_revision="v11",
    meshes=(
        HairSweepMeshPart(
            name="hair_reference_shell",
            location=(0.0, 0.0, 4.55),
            segments=24,
            wave_frequency=3,
            wave_amplitude=0.032,
            rings=(
                HairSweepRing(
                    -0.38, 0.00, 0.08, 0.29, 0.24, 8.0, -20.0, 200.0
                ),
                HairSweepRing(
                    -0.23, 0.00, 0.04, 0.40, 0.34, 16.0, -30.0, 210.0
                ),
                HairSweepRing(
                    -0.06, 0.00, -0.03, 0.49, 0.43, 24.0, -45.0, 225.0
                ),
                HairSweepRing(
                    0.12, -0.01, -0.07, 0.50, 0.45, 36.0, -60.0, 240.0
                ),
                HairSweepRing(
                    0.28, -0.03, -0.09, 0.43, 0.38, 48.0, -72.0, 252.0
                ),
                HairSweepRing(
                    0.40, -0.04, -0.09, 0.30, 0.25, 62.0, -82.0, 262.0
                ),
                HairSweepRing(
                    0.49, -0.04, -0.08, 0.12, 0.10, 74.0, -88.0, 268.0
                ),
            ),
            arc_start_degrees=-20.0,
            arc_end_degrees=200.0,
            closed_around=False,
        ),
        HairSweepMeshPart(
            name="hair_reference_nape",
            location=(0.0, 0.0, 4.22),
            segments=18,
            wave_frequency=3,
            wave_amplitude=0.026,
            rings=(
                HairSweepRing(
                    -0.18, 0.00, 0.22, 0.11, 0.09, 0.0, -10.0, 190.0
                ),
                HairSweepRing(
                    -0.06, 0.00, 0.20, 0.24, 0.15, 12.0, -20.0, 200.0
                ),
                HairSweepRing(
                    0.08, 0.00, 0.18, 0.34, 0.22, 24.0, -30.0, 210.0
                ),
                HairSweepRing(
                    0.22, 0.00, 0.14, 0.37, 0.24, 36.0, -40.0, 220.0
                ),
                HairSweepRing(
                    0.32, 0.00, 0.10, 0.31, 0.20, 48.0, -50.0, 230.0
                ),
            ),
            arc_start_degrees=-10.0,
            arc_end_degrees=190.0,
            closed_around=False,
        ),
        HairSweepMeshPart(
            name="hair_reference_forelock",
            location=(-0.07, -0.47, 4.54),
            segments=12,
            wave_frequency=2,
            wave_amplitude=0.020,
            rings=(
                HairSweepRing(-0.26, -0.02, -0.010, 0.040, 0.025, 8.0),
                HairSweepRing(-0.12, -0.015, 0.000, 0.060, 0.035, 20.0),
                HairSweepRing(0.03, 0.00, 0.010, 0.095, 0.055, 34.0),
                HairSweepRing(0.18, 0.03, 0.025, 0.115, 0.065, 48.0),
                HairSweepRing(0.28, 0.05, 0.035, 0.090, 0.055, 62.0),
            ),
        ),
    ),
    profile_accent_names=frozenset(
        {
            "hair_front_hairline_left",
            "hair_front_hairline_right",
            "hair_side_mass_left",
            "hair_side_mass_right",
        }
    ),
    detail_accent_names=frozenset(
        {
            "hair_temple_curl_left",
            "hair_temple_curl_right",
            "hair_back_texture_left",
            "hair_back_texture_right",
        }
    ),
    accent_rotations_degrees=(
        ("hair_front_hairline_left", (12.0, -8.0, 0.0)),
        ("hair_front_hairline_right", (15.0, 10.0, 0.0)),
        ("hair_side_mass_left", (11.0, 0.0, -5.0)),
        ("hair_side_mass_right", (12.0, 0.0, 4.0)),
        ("hair_temple_curl_left", (10.0, -8.0, 0.0)),
        ("hair_temple_curl_right", (12.0, 10.0, 0.0)),
    ),
)


def load_hair_sweep_profile_v08() -> HairSweepProfileV08:
    HUMAN_WARRIOR_M01_HAIR_SWEEP_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_SWEEP_V08
