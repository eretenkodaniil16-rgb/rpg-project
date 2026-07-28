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
        arc_span = self.arc_end_degrees - self.arc_start_degrees
        if self.closed_around:
            if abs(arc_span - 360.0) > 0.001:
                raise ValueError(f"Closed sweep {self.name} must span 360 degrees")
        elif not 180.0 <= arc_span <= 300.0:
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
        if self.meshes[0].closed_around or self.meshes[1].closed_around:
            raise ValueError("Shell and nape must leave the face side open")
        if not self.meshes[2].closed_around:
            raise ValueError("Forelock must remain a closed strand")
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
            segments=20,
            wave_frequency=3,
            wave_amplitude=0.040,
            rings=(
                HairSweepRing(-0.38, 0.00, 0.05, 0.25, 0.20, 8.0),
                HairSweepRing(-0.23, 0.00, 0.02, 0.38, 0.30, 16.0),
                HairSweepRing(-0.06, 0.00, -0.02, 0.47, 0.40, 24.0),
                HairSweepRing(0.12, -0.01, -0.03, 0.48, 0.40, 36.0),
                HairSweepRing(0.28, -0.03, -0.01, 0.40, 0.32, 48.0),
                HairSweepRing(0.40, -0.04, 0.02, 0.25, 0.20, 62.0),
                HairSweepRing(0.47, -0.04, 0.04, 0.08, 0.06, 74.0),
            ),
            arc_start_degrees=-40.0,
            arc_end_degrees=220.0,
            closed_around=False,
        ),
        HairSweepMeshPart(
            name="hair_reference_nape",
            location=(0.0, 0.0, 4.22),
            segments=16,
            wave_frequency=3,
            wave_amplitude=0.030,
            rings=(
                HairSweepRing(-0.20, 0.00, 0.20, 0.10, 0.08),
                HairSweepRing(-0.10, 0.00, 0.20, 0.22, 0.14, 12.0),
                HairSweepRing(0.05, 0.00, 0.18, 0.31, 0.20, 24.0),
                HairSweepRing(0.18, 0.00, 0.15, 0.34, 0.22, 36.0),
                HairSweepRing(0.27, 0.00, 0.11, 0.27, 0.18, 48.0),
            ),
            arc_start_degrees=-25.0,
            arc_end_degrees=205.0,
            closed_around=False,
        ),
        HairSweepMeshPart(
            name="hair_reference_forelock",
            location=(-0.08, -0.43, 4.52),
            segments=10,
            wave_frequency=2,
            wave_amplitude=0.025,
            rings=(
                HairSweepRing(-0.22, -0.04, -0.035, 0.045, 0.030, 10.0),
                HairSweepRing(-0.08, -0.02, -0.020, 0.075, 0.045, 24.0),
                HairSweepRing(0.08, 0.00, 0.000, 0.105, 0.060, 38.0),
                HairSweepRing(0.20, 0.03, 0.015, 0.095, 0.055, 52.0),
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
