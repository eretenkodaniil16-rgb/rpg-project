from __future__ import annotations

import re
from dataclasses import dataclass


_HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-F]{6}$")
_QUANTIZATION_COMPATIBLE_COLORS = frozenset(
    {
        "#060102",
        "#0B0602",
        "#1A120A",
        "#26180B",
        "#3C2411",
    }
)


def _relative_luminance(color_hex: str) -> float:
    raw = color_hex.lstrip("#")
    channels = tuple(int(raw[index : index + 2], 16) / 255.0 for index in (0, 2, 4))
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


@dataclass(frozen=True)
class HairPaletteV10:
    revision: str
    proxy_revision: str
    shadow: str
    base: str
    mid: str
    highlight: str
    separator: str

    @property
    def facet_colors(self) -> tuple[str, str, str, str]:
        return (self.shadow, self.base, self.mid, self.highlight)

    @property
    def all_colors(self) -> tuple[str, str, str, str, str]:
        return (*self.facet_colors, self.separator)

    def assert_valid(self) -> None:
        if self.revision != "v10" or self.proxy_revision != "v13":
            raise ValueError("Hair palette must match head v10 / proxy v13")
        if any(_HEX_COLOR_PATTERN.fullmatch(color) is None for color in self.all_colors):
            raise ValueError("Hair palette colors must use uppercase #RRGGBB notation")
        if not set(self.all_colors).issubset(_QUANTIZATION_COMPATIBLE_COLORS):
            raise ValueError("Hair palette must use colors already present in the render quantization palette")
        luminance = tuple(_relative_luminance(color) for color in self.facet_colors)
        if not luminance[0] < luminance[1] < luminance[2] < luminance[3]:
            raise ValueError("Hair tones must progress from shadow to restrained highlight")
        if _relative_luminance(self.separator) > luminance[0]:
            raise ValueError("Lock separators must remain darker than the main hair shadow")
        if luminance[-1] >= 0.20:
            raise ValueError("Hair highlight is too bright and may merge with pale skin at 96x96")


HUMAN_WARRIOR_M01_HAIR_PALETTE_V10 = HairPaletteV10(
    revision="v10",
    proxy_revision="v13",
    shadow="#0B0602",
    base="#1A120A",
    mid="#26180B",
    highlight="#3C2411",
    separator="#060102",
)


def load_hair_palette_v10() -> HairPaletteV10:
    HUMAN_WARRIOR_M01_HAIR_PALETTE_V10.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_PALETTE_V10
