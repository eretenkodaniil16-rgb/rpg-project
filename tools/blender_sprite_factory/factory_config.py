from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
EXPECTED_DIRECTIONS = {
    "down": 0.0,
    "left": -90.0,
    "right": 90.0,
    "up": 180.0,
}


@dataclass(frozen=True)
class TechnicalContract:
    canvas_width: int
    canvas_height: int
    sprite_height_min: int
    sprite_height_max: int
    max_sprite_width: int
    baseline_y: int
    alpha_threshold: int

    @property
    def pilot_sprite_height(self) -> int:
        return (self.sprite_height_min + self.sprite_height_max) // 2


@dataclass(frozen=True)
class MaterialSlot:
    slot_id: str
    base_color: str
    texture_path: Path
    roughness: float


@dataclass(frozen=True)
class FactoryConfig:
    schema_version: int
    character_id: str
    stage: str
    repo_root: Path
    manifest_path: Path
    recommended_blender_lts: tuple[int, int]
    minimum_blender: tuple[int, int]
    master_reference: Path
    idle_reference_root: Path
    texture_root: Path
    run_root: Path
    camera: dict[str, float | int | bool | str]
    directions: dict[str, float]
    required_bones: tuple[str, ...]
    required_modules: tuple[str, ...]
    physical_sides: dict[str, str]
    animations: dict[str, dict[str, object]]
    materials_status: str
    material_slots: dict[str, MaterialSlot]
    quantization_palette: tuple[str, ...]
    technical: TechnicalContract

    def assert_blender_version(self, version: tuple[int, int, int]) -> None:
        if tuple(version[:2]) < self.minimum_blender:
            minimum = ".".join(str(value) for value in self.minimum_blender)
            actual = ".".join(str(value) for value in version[:2])
            raise RuntimeError(
                f"Blender {actual} не поддерживается; требуется Blender {minimum} или новее."
            )

    def relative_to_repo(self, path: Path) -> str:
        return path.resolve().relative_to(self.repo_root).as_posix()


def load_factory_config(manifest_path: Path, repo_root: Path) -> FactoryConfig:
    safe_root = repo_root.resolve()
    safe_manifest = manifest_path.resolve()
    _assert_within(safe_root, safe_manifest, "factory manifest")
    raw = _read_json(safe_manifest)
    _require_keys(
        raw,
        [
            "schema_version",
            "character_id",
            "stage",
            "shared_sprite_manifest",
            "target_blender",
            "paths",
            "camera",
            "directions",
            "rig",
            "modules",
            "animations",
            "materials",
        ],
        "factory manifest",
    )

    schema_version = _positive_int(raw, "schema_version")
    if schema_version != 1:
        raise ValueError(f"Неподдерживаемая schema_version: {schema_version}")

    character_id = _non_empty_string(raw, "character_id")
    stage = _non_empty_string(raw, "stage")
    target_blender = _as_dict(raw["target_blender"], "target_blender")
    recommended_lts = _version_pair(
        _non_empty_string(target_blender, "recommended_lts"),
        "target_blender.recommended_lts",
    )
    minimum_blender = _version_pair(
        _non_empty_string(target_blender, "minimum_supported"),
        "target_blender.minimum_supported",
    )
    if recommended_lts < minimum_blender:
        raise ValueError("recommended_lts не может быть старее minimum_supported")

    shared_manifest_path = _resolve_repo_path(
        safe_root,
        _non_empty_string(raw, "shared_sprite_manifest"),
        "shared_sprite_manifest",
    )
    shared_raw = _read_json(shared_manifest_path)
    if str(shared_raw.get("character_id", "")).strip() != character_id:
        raise ValueError("character_id не совпадает с общим sprite manifest")
    technical = _load_technical_contract(shared_raw)

    paths = _as_dict(raw["paths"], "paths")
    master_reference = _resolve_repo_path(
        safe_root,
        _non_empty_string(paths, "master_reference"),
        "paths.master_reference",
    )
    idle_reference_root = _resolve_repo_path(
        safe_root,
        _non_empty_string(paths, "idle_reference_root"),
        "paths.idle_reference_root",
    )
    texture_root = _resolve_repo_path(
        safe_root,
        _non_empty_string(paths, "texture_root"),
        "paths.texture_root",
    )
    run_root = _resolve_repo_path(
        safe_root,
        _non_empty_string(paths, "run_root"),
        "paths.run_root",
    )

    camera_raw = _as_dict(raw["camera"], "camera")
    camera = _validate_camera(camera_raw, technical)
    directions = _validate_directions(_as_dict(raw["directions"], "directions"))

    rig = _as_dict(raw["rig"], "rig")
    required_bones = _unique_strings(rig.get("required_bones"), "rig.required_bones")
    _validate_bone_contract(required_bones)

    modules = _as_dict(raw["modules"], "modules")
    required_modules = _unique_strings(modules.get("required"), "modules.required")
    physical_sides_raw = _as_dict(modules.get("physical_sides"), "modules.physical_sides")
    physical_sides = {
        str(module_id): str(side).strip().lower()
        for module_id, side in physical_sides_raw.items()
    }
    _validate_physical_sides(physical_sides)

    animations = _validate_animations(_as_dict(raw["animations"], "animations"))
    materials = _as_dict(raw["materials"], "materials")
    materials_status = _non_empty_string(materials, "status")
    slots_raw = _as_dict(materials.get("slots"), "materials.slots")
    material_slots = _load_material_slots(slots_raw, texture_root)
    quantization_palette = _unique_strings(
        materials.get("quantization_palette"),
        "materials.quantization_palette",
    )
    for color in quantization_palette:
        _validate_hex(color, "materials.quantization_palette")

    return FactoryConfig(
        schema_version=schema_version,
        character_id=character_id,
        stage=stage,
        repo_root=safe_root,
        manifest_path=safe_manifest,
        recommended_blender_lts=recommended_lts,
        minimum_blender=minimum_blender,
        master_reference=master_reference,
        idle_reference_root=idle_reference_root,
        texture_root=texture_root,
        run_root=run_root,
        camera=camera,
        directions=directions,
        required_bones=required_bones,
        required_modules=required_modules,
        physical_sides=physical_sides,
        animations=animations,
        materials_status=materials_status,
        material_slots=material_slots,
        quantization_palette=quantization_palette,
        technical=technical,
    )


def validate_required_files(config: FactoryConfig) -> list[Path]:
    expected = [
        config.master_reference,
        config.idle_reference_root / f"{config.character_id}_idle_down.png",
        config.idle_reference_root / f"{config.character_id}_idle_left.png",
        config.idle_reference_root / f"{config.character_id}_idle_right.png",
        config.idle_reference_root / f"{config.character_id}_idle_up.png",
    ]
    expected.extend(slot.texture_path for slot in config.material_slots.values())
    return [path for path in expected if not path.is_file()]


def _load_technical_contract(shared_raw: dict[str, Any]) -> TechnicalContract:
    technical = _as_dict(shared_raw.get("technical"), "shared technical")
    contract = TechnicalContract(
        canvas_width=_positive_int(technical, "canvas_width"),
        canvas_height=_positive_int(technical, "canvas_height"),
        sprite_height_min=_positive_int(technical, "sprite_height_min"),
        sprite_height_max=_positive_int(technical, "sprite_height_max"),
        max_sprite_width=_positive_int(technical, "max_sprite_width"),
        baseline_y=_non_negative_int(technical, "baseline_y"),
        alpha_threshold=_bounded_int(technical, "alpha_threshold", 0, 255),
    )
    if contract.canvas_width != 96 or contract.canvas_height != 96:
        raise ValueError("Blender pilot ожидает общий gameplay-холст 96×96")
    if contract.sprite_height_min > contract.sprite_height_max:
        raise ValueError("Некорректный диапазон высоты спрайта")
    if not contract.sprite_height_min <= 78 <= contract.sprite_height_max:
        raise ValueError("Утверждённый pilot target 78 px должен входить в общий диапазон")
    if contract.baseline_y >= contract.canvas_height:
        raise ValueError("baseline_y должен находиться внутри холста")
    return contract


def _validate_camera(
    raw: dict[str, Any],
    technical: TechnicalContract,
) -> dict[str, float | int | bool | str]:
    _require_keys(
        raw,
        [
            "projection",
            "elevation_degrees",
            "horizontal_distance_units",
            "target_height_units",
            "orthographic_scale",
            "raw_render_scale",
            "transparent_background",
        ],
        "camera",
    )
    projection = _non_empty_string(raw, "projection").upper()
    if projection != "ORTHOGRAPHIC":
        raise ValueError("Gameplay factory использует только ортографическую камеру")
    elevation = float(raw["elevation_degrees"])
    if not 45.0 <= elevation <= 50.0:
        raise ValueError("elevation_degrees должен сохранять утверждённые 45–50°")
    raw_render_scale = _bounded_int(raw, "raw_render_scale", 1, 4)
    return {
        "projection": projection,
        "elevation_degrees": elevation,
        "horizontal_distance_units": _positive_float(raw, "horizontal_distance_units"),
        "target_height_units": _positive_float(raw, "target_height_units"),
        "orthographic_scale": _positive_float(raw, "orthographic_scale"),
        "raw_render_scale": raw_render_scale,
        "transparent_background": bool(raw["transparent_background"]),
        "render_width": technical.canvas_width * raw_render_scale,
        "render_height": technical.canvas_height * raw_render_scale,
    }


def _validate_directions(raw: dict[str, Any]) -> dict[str, float]:
    if set(raw) != set(EXPECTED_DIRECTIONS):
        raise ValueError(
            f"directions должны содержать ровно {sorted(EXPECTED_DIRECTIONS)}"
        )
    directions = {key: float(value) for key, value in raw.items()}
    for direction, expected_rotation in EXPECTED_DIRECTIONS.items():
        if directions[direction] != expected_rotation:
            raise ValueError(
                f"Направление {direction} должно физически поворачивать модель "
                f"на {expected_rotation}°, а не зеркалить её"
            )
    return directions


def _validate_bone_contract(bones: tuple[str, ...]) -> None:
    mandatory = {
        "root",
        "pelvis",
        "spine",
        "chest",
        "neck",
        "head",
        "upper_arm.L",
        "upper_arm.R",
        "thigh.L",
        "thigh.R",
        "foot.L",
        "foot.R",
    }
    missing = sorted(mandatory.difference(bones))
    if missing:
        raise ValueError(f"В rig.required_bones отсутствуют обязательные кости: {missing}")


def _validate_physical_sides(physical_sides: dict[str, str]) -> None:
    expected = {
        "large_silver_pauldron": "left",
        "small_dark_pauldron": "right",
        "sword_scabbard": "left",
        "pouch": "right",
    }
    if physical_sides != expected:
        raise ValueError(
            "Физические стороны экипировки human_warrior_m01 изменять нельзя"
        )


def _validate_animations(raw: dict[str, Any]) -> dict[str, dict[str, object]]:
    if set(raw) != {"idle", "walk_down"}:
        raise ValueError("Пилот должен содержать idle и один полный walk_down")
    result: dict[str, dict[str, object]] = {}
    expected_frames = {"idle": [1], "walk_down": [1, 2, 3, 4, 5, 6]}
    for animation_id, value in raw.items():
        spec = _as_dict(value, f"animations.{animation_id}")
        frames = spec.get("frames")
        if frames != expected_frames[animation_id]:
            raise ValueError(
                f"animations.{animation_id}.frames должен быть {expected_frames[animation_id]}"
            )
        fps = _positive_int(spec, "fps")
        result[animation_id] = {"frames": tuple(frames), "fps": fps}
    return result


def _load_material_slots(
    raw: dict[str, Any],
    texture_root: Path,
) -> dict[str, MaterialSlot]:
    required = {
        "skin",
        "hair",
        "scarf",
        "leather_dark",
        "leather_mid",
        "chainmail",
        "silver",
        "dark_steel",
        "boots",
    }
    if set(raw) != required:
        raise ValueError(f"materials.slots должны содержать ровно {sorted(required)}")
    result: dict[str, MaterialSlot] = {}
    for slot_id, value in raw.items():
        spec = _as_dict(value, f"materials.slots.{slot_id}")
        base_color = _non_empty_string(spec, "base_color").upper()
        _validate_hex(base_color, f"materials.slots.{slot_id}.base_color")
        texture_name = _non_empty_string(spec, "texture")
        if Path(texture_name).name != texture_name or Path(texture_name).suffix.lower() != ".png":
            raise ValueError(
                f"materials.slots.{slot_id}.texture должен быть безопасным именем PNG"
            )
        roughness = float(spec.get("roughness", -1.0))
        if not 0.0 <= roughness <= 1.0:
            raise ValueError(
                f"materials.slots.{slot_id}.roughness должен быть от 0 до 1"
            )
        result[slot_id] = MaterialSlot(
            slot_id=slot_id,
            base_color=base_color,
            texture_path=(texture_root / texture_name).resolve(),
            roughness=roughness,
        )
    return result


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Не найден JSON: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _as_dict(raw, str(path))


def _resolve_repo_path(repo_root: Path, relative: str, label: str) -> Path:
    path = (repo_root / relative).resolve()
    _assert_within(repo_root, path, label)
    return path


def _assert_within(root: Path, path: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} выходит за пределы репозитория: {path}") from exc


def _version_pair(value: str, label: str) -> tuple[int, int]:
    parts = value.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"{label} должен иметь вид major.minor")
    return int(parts[0]), int(parts[1])


def _require_keys(data: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"В {label} отсутствуют обязательные поля: {missing}")


def _as_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} должен быть JSON-объектом")
    return value


def _non_empty_string(data: dict[str, Any], key: str) -> str:
    value = str(data.get(key, "")).strip()
    if not value:
        raise ValueError(f"Поле {key} не может быть пустым")
    return value


def _unique_strings(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} должен быть непустым массивом")
    result = tuple(str(item).strip() for item in value)
    if any(not item for item in result):
        raise ValueError(f"{label} содержит пустое значение")
    if len(result) != len(set(result)):
        raise ValueError(f"{label} содержит дубли")
    return result


def _validate_hex(value: str, label: str) -> None:
    if not HEX_COLOR.fullmatch(value):
        raise ValueError(f"{label} должен быть цветом #RRGGBB")


def _positive_int(data: dict[str, Any], key: str) -> int:
    value = int(data.get(key, 0))
    if value <= 0:
        raise ValueError(f"{key} должен быть положительным целым")
    return value


def _non_negative_int(data: dict[str, Any], key: str) -> int:
    value = int(data.get(key, -1))
    if value < 0:
        raise ValueError(f"{key} не может быть отрицательным")
    return value


def _bounded_int(data: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = int(data.get(key, minimum - 1))
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} должен быть от {minimum} до {maximum}")
    return value


def _positive_float(data: dict[str, Any], key: str) -> float:
    value = float(data.get(key, 0.0))
    if value <= 0.0:
        raise ValueError(f"{key} должен быть положительным числом")
    return value
