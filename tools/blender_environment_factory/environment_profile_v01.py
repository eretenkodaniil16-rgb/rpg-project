from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ASSET_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
SUPPORTED_KINDS = frozenset(
    {
        "floor",
        "decal",
        "transition",
        "wall_edge",
        "wall_corner",
        "door",
        "stairs",
        "arcane",
    }
)
FLOOR_KINDS = frozenset({"floor"})
OVERLAY_KINDS = frozenset({"decal", "transition", "arcane"})
EDGE_OBJECT_KINDS = frozenset({"wall_edge", "wall_corner", "door"})


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    kind: str
    seed: int
    canvas_width: int
    canvas_height: int
    shape: str = ""
    orientation: str = ""
    state: str = ""

    @property
    def is_floor(self) -> bool:
        return self.kind in FLOOR_KINDS

    @property
    def is_overlay(self) -> bool:
        return self.kind in OVERLAY_KINDS

    @property
    def is_edge_object(self) -> bool:
        return self.kind in EDGE_OBJECT_KINDS

    @property
    def canvas(self) -> tuple[int, int]:
        return self.canvas_width, self.canvas_height


@dataclass(frozen=True)
class EnvironmentProfile:
    source_path: Path
    repo_root: Path
    payload: dict[str, Any]
    assets: tuple[AssetSpec, ...]

    @property
    def profile_id(self) -> str:
        return str(self.payload["profile_id"])

    @property
    def schema_version(self) -> int:
        return int(self.payload["schema_version"])

    @property
    def stage(self) -> str:
        return str(self.payload["stage"])

    @property
    def tile_size(self) -> int:
        return int(self.payload["game_contract"]["combat_cell_size"])

    @property
    def character_sprite_canvas(self) -> int:
        return int(self.payload["game_contract"]["character_sprite_canvas"])

    @property
    def elevation_degrees(self) -> float:
        return float(self.payload["camera"]["elevation_degrees"])

    @property
    def raw_render_scale(self) -> int:
        return int(self.payload["camera"]["raw_render_scale"])

    @property
    def floor_view_height(self) -> float:
        return float(self.payload["camera"]["floor_view_height_units"])

    @property
    def object_view_height(self) -> float:
        return float(self.payload["camera"]["object_view_height_units"])

    @property
    def run_root(self) -> Path:
        return (self.repo_root / str(self.payload["paths"]["run_root"])).resolve()

    @property
    def character_idle_atlas(self) -> Path:
        return (
            self.repo_root / str(self.payload["paths"]["character_idle_atlas"])
        ).resolve()

    @property
    def palette_hex(self) -> tuple[str, ...]:
        return tuple(str(value).upper() for value in self.payload["palette"])

    @property
    def profile_sha256(self) -> str:
        canonical = json.dumps(
            self.payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def assets_of_kind(self, *kinds: str) -> tuple[AssetSpec, ...]:
        selected = frozenset(kinds)
        return tuple(asset for asset in self.assets if asset.kind in selected)

    def asset(self, asset_id: str) -> AssetSpec:
        for asset in self.assets:
            if asset.asset_id == asset_id:
                return asset
        raise KeyError(f"Неизвестный environment asset_id: {asset_id}")

    def relative_to_repo(self, path: Path) -> str:
        return path.resolve().relative_to(self.repo_root).as_posix()

    def assert_blender_version(self, version: tuple[int, ...]) -> None:
        minimum = _version_tuple(
            str(self.payload["target_blender"]["minimum_supported"])
        )
        normalized = tuple(version[: len(minimum)])
        if normalized < minimum:
            raise RuntimeError(
                f"Blender {minimum} или новее обязателен; получен {normalized}"
            )


def load_environment_profile(
    config_path: Path,
    repo_root: Path,
) -> EnvironmentProfile:
    source_path = config_path.resolve()
    root = repo_root.resolve()
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Environment profile должен быть JSON-объектом")
    assets = tuple(_parse_assets(payload.get("assets", [])))
    profile = EnvironmentProfile(
        source_path=source_path,
        repo_root=root,
        payload=payload,
        assets=assets,
    )
    _validate_profile(profile)
    return profile


def _parse_assets(raw_assets: object) -> Iterable[AssetSpec]:
    if not isinstance(raw_assets, list):
        raise ValueError("assets должен быть JSON-массивом")
    for raw in raw_assets:
        if not isinstance(raw, dict):
            raise ValueError("Каждый environment asset должен быть объектом")
        canvas = raw.get("canvas")
        if not isinstance(canvas, list) or len(canvas) != 2:
            raise ValueError(f"Некорректный canvas у {raw.get('asset_id', '?')}")
        yield AssetSpec(
            asset_id=str(raw.get("asset_id", "")),
            kind=str(raw.get("kind", "")),
            seed=int(raw.get("seed", 0)),
            canvas_width=int(canvas[0]),
            canvas_height=int(canvas[1]),
            shape=str(raw.get("shape", "")),
            orientation=str(raw.get("orientation", "")),
            state=str(raw.get("state", "")),
        )


def _validate_profile(profile: EnvironmentProfile) -> None:
    if profile.schema_version != 1:
        raise ValueError(f"Неподдерживаемая schema_version: {profile.schema_version}")
    if profile.stage != "review_candidate":
        raise ValueError("Environment v01 должен оставаться review_candidate")
    if profile.tile_size != 64:
        raise ValueError("Игровой экспорт обязан совпадать с текущей сеткой 64 px")
    if profile.character_sprite_canvas != 96:
        raise ValueError("Контракт холста персонажа должен оставаться 96 px")
    if not 45.0 <= profile.elevation_degrees <= 50.0:
        raise ValueError("Камера окружения должна оставаться в диапазоне 45–50°")
    if profile.raw_render_scale < 2:
        raise ValueError("Raw render должен быть минимум вдвое крупнее экспорта")
    if profile.payload["game_contract"].get("runtime_filter") != "NEAREST":
        raise ValueError("Runtime filter окружения должен быть NEAREST")
    if not bool(
        profile.payload["game_contract"].get("walls_and_doors_use_cell_edges")
    ):
        raise ValueError("Стены и двери должны оставаться на рёбрах клеток")
    if bool(profile.payload["game_contract"].get("local_light_baked_into_floor")):
        raise ValueError("Локальный свет нельзя запекать в базовый пол")
    if not bool(profile.payload["lighting"].get("neutral_only")):
        raise ValueError("Pilot lighting должен оставаться нейтральным")

    seam = profile.payload.get("seam_contract", {})
    if seam.get("mode") != "per_variant_opposite_edge_harmonization":
        raise ValueError("Floor seam contract не должен возвращать общий бордюр")
    if int(seam.get("sample_inset_px", 0)) not in range(1, 5):
        raise ValueError("Floor seam sample inset должен быть в диапазоне 1–4 px")
    if not bool(seam.get("arbitrary_adjacency_requires_opaque_edges")):
        raise ValueError("Произвольное соседство floor variants требует opaque edges")

    if len(profile.palette_hex) < 16 or len(profile.palette_hex) > 32:
        raise ValueError("Палитра должна содержать от 16 до 32 цветов")
    if len(set(profile.palette_hex)) != len(profile.palette_hex):
        raise ValueError("Палитра не должна содержать дубликаты")
    for value in profile.palette_hex:
        if not re.fullmatch(r"#[0-9A-F]{6}", value):
            raise ValueError(f"Некорректный цвет палитры: {value}")

    if len(profile.assets) != 33:
        raise ValueError(f"Environment v01 ожидает 33 asset-спецификации, получено {len(profile.assets)}")
    ids: set[str] = set()
    for asset in profile.assets:
        if not ASSET_ID_PATTERN.fullmatch(asset.asset_id):
            raise ValueError(f"Некорректный asset_id: {asset.asset_id}")
        if asset.asset_id in ids:
            raise ValueError(f"Повторяющийся asset_id: {asset.asset_id}")
        ids.add(asset.asset_id)
        if asset.kind not in SUPPORTED_KINDS:
            raise ValueError(f"Неподдерживаемый kind {asset.kind}: {asset.asset_id}")
        if asset.seed <= 0:
            raise ValueError(f"Seed должен быть положительным: {asset.asset_id}")
        if asset.canvas_width not in (64, 96) or asset.canvas_height not in (64, 96):
            raise ValueError(f"Некорректный canvas: {asset.asset_id} {asset.canvas}")
        if asset.kind == "floor" and asset.canvas != (64, 64):
            raise ValueError(f"Floor export должен быть 64×64: {asset.asset_id}")
        if asset.kind == "decal" and asset.shape not in {"crack", "dust", "damp"}:
            raise ValueError(f"Некорректный decal shape: {asset.asset_id}")
        if asset.kind == "door" and asset.state not in {"closed", "open"}:
            raise ValueError(f"Некорректное состояние двери: {asset.asset_id}")

    expected_counts = {
        "floor": 8,
        "decal": 6,
        "transition": 4,
        "wall_edge": 4,
        "wall_corner": 4,
        "door": 4,
        "stairs": 1,
        "arcane": 2,
    }
    actual_counts = {
        kind: len(profile.assets_of_kind(kind)) for kind in expected_counts
    }
    if actual_counts != expected_counts:
        raise ValueError(
            f"Некорректный состав набора: {actual_counts}, ожидается {expected_counts}"
        )

    if not profile.character_idle_atlas.is_file():
        raise FileNotFoundError(
            f"Не найден approved idle atlas: {profile.character_idle_atlas}"
        )
    _validate_preview(profile)


def _validate_preview(profile: EnvironmentProfile) -> None:
    preview = profile.payload.get("preview")
    if not isinstance(preview, dict):
        raise ValueError("preview должен быть объектом")
    room_size = preview.get("room_size_cells")
    if room_size != [6, 6]:
        raise ValueError("Контрольная комната v01 должна быть 6×6 клеток")
    rows = preview.get("floor_rows")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("preview.floor_rows должен содержать 6 строк")
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError("Каждая строка preview.floor_rows должна содержать 6 значений")
        if any(int(value) < 1 or int(value) > 8 for value in row):
            raise ValueError("Preview floor index должен быть в диапазоне 1–8")
    for decal in preview.get("decals", []):
        if not isinstance(decal, dict):
            raise ValueError("Preview decal должен быть объектом")
        asset_id = str(decal.get("asset_id", ""))
        if profile.asset(asset_id).kind == "floor":
            raise ValueError("Floor нельзя использовать как preview decal")


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = tuple(int(part) for part in value.split("."))
    if not numbers:
        raise ValueError(f"Некорректная версия Blender: {value}")
    return numbers
