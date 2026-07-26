from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from factory_config import FactoryConfig, MaterialSlot, load_factory_config


TEXTURE_SIZE = 16


def generate_all(config: FactoryConfig) -> list[Path]:
    config.texture_root.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for slot in config.material_slots.values():
        image = _make_texture(slot)
        image.save(slot.texture_path, format="PNG", optimize=False)
        generated.append(slot.texture_path)
    return generated


def _make_texture(slot: MaterialSlot) -> Image.Image:
    base = _hex_rgb(slot.base_color)
    dark = _mix(base, (0, 0, 0), 0.28)
    darker = _mix(base, (0, 0, 0), 0.46)
    light = _mix(base, (255, 246, 232), 0.24)
    image = Image.new("RGBA", (TEXTURE_SIZE, TEXTURE_SIZE), (*base, 255))
    draw = ImageDraw.Draw(image)

    if slot.slot_id == "skin":
        _skin(draw, dark, light)
    elif slot.slot_id == "hair":
        _hair(draw, dark, darker, light)
    elif slot.slot_id == "scarf":
        _cloth(draw, dark, light)
    elif slot.slot_id in {"leather_dark", "leather_mid", "boots"}:
        _leather(draw, dark, darker, light)
    elif slot.slot_id == "chainmail":
        _chainmail(draw, dark, darker, light)
    elif slot.slot_id in {"silver", "dark_steel"}:
        _metal(draw, dark, darker, light)
    else:
        raise ValueError(f"Нет pilot texture pattern для {slot.slot_id}")
    return image


def _skin(draw: ImageDraw.ImageDraw, dark: tuple[int, int, int], light: tuple[int, int, int]) -> None:
    for x, y in ((2, 3), (10, 2), (5, 11), (13, 9)):
        draw.point((x, y), fill=(*light, 255))
    for x, y in ((1, 12), (8, 7), (14, 14), (4, 5)):
        draw.point((x, y), fill=(*dark, 255))


def _hair(
    draw: ImageDraw.ImageDraw,
    dark: tuple[int, int, int],
    darker: tuple[int, int, int],
    light: tuple[int, int, int],
) -> None:
    for offset in range(-16, 32, 5):
        draw.line((offset, 0, offset - 8, 15), fill=(*dark, 255), width=2)
        draw.point((offset % 16, 4), fill=(*light, 255))
    for x, y in ((2, 13), (7, 8), (12, 3), (15, 12)):
        draw.point((x, y), fill=(*darker, 255))


def _cloth(
    draw: ImageDraw.ImageDraw,
    dark: tuple[int, int, int],
    light: tuple[int, int, int],
) -> None:
    for value in range(0, 16, 4):
        draw.line((0, value, 15, value + 3), fill=(*dark, 255), width=1)
        draw.line((value, 0, value + 3, 15), fill=(*light, 255), width=1)


def _leather(
    draw: ImageDraw.ImageDraw,
    dark: tuple[int, int, int],
    darker: tuple[int, int, int],
    light: tuple[int, int, int],
) -> None:
    for x, y in (
        (1, 1),
        (4, 6),
        (7, 2),
        (10, 9),
        (13, 4),
        (2, 13),
        (8, 14),
        (15, 12),
    ):
        draw.rectangle((x, y, min(15, x + 1), min(15, y + 1)), fill=(*dark, 255))
    for x, y in ((5, 4), (12, 1), (3, 10), (11, 14)):
        draw.point((x, y), fill=(*darker, 255))
    for x, y in ((2, 4), (8, 7), (14, 9), (6, 12)):
        draw.point((x, y), fill=(*light, 255))


def _chainmail(
    draw: ImageDraw.ImageDraw,
    dark: tuple[int, int, int],
    darker: tuple[int, int, int],
    light: tuple[int, int, int],
) -> None:
    for row, y in enumerate(range(1, 16, 4)):
        offset = 0 if row % 2 == 0 else 2
        for x in range(-2 + offset, 16, 4):
            draw.rectangle((x, y, x + 2, y + 2), outline=(*dark, 255))
            draw.point((x + 1, y), fill=(*light, 255))
            draw.point((x + 1, y + 2), fill=(*darker, 255))


def _metal(
    draw: ImageDraw.ImageDraw,
    dark: tuple[int, int, int],
    darker: tuple[int, int, int],
    light: tuple[int, int, int],
) -> None:
    for offset in range(-16, 32, 7):
        draw.line((offset, 15, offset + 15, 0), fill=(*dark, 255), width=2)
        draw.line((offset + 2, 15, offset + 17, 0), fill=(*light, 255), width=1)
    draw.line((0, 15, 15, 15), fill=(*darker, 255), width=1)


def _hex_rgb(value: str) -> tuple[int, int, int]:
    raw = value.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _mix(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    return tuple(
        max(0, min(255, round(a * (1.0 - amount) + b * amount)))
        for a, b in zip(first, second)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic 16x16 pilot textures.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
    )
    parser.add_argument(
        "--config",
        default="tools/blender_sprite_factory/configs/human_warrior_m01.json",
    )
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    config = load_factory_config((repo_root / args.config).resolve(), repo_root)
    generated = generate_all(config)
    for path in generated:
        print(config.relative_to_repo(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
