# cold_ancient_stone_v01

Утверждённый runtime-пакет холодного древнего камня для Godot 4.7.1.

- `modules/` — 33 нормализованных PNG, сохранённых для точных неполных краёв и stateful-дверей;
- `atlases/` — шесть детерминированных атласов для `TileMapLayer`;
- `tilesets/cold_ancient_stone_v01.tres` — `TileSet` с source ID `0…5` и custom data `visual_id`;
- `cold_ancient_stone_v01.approved.json` — provenance, хэши, canvas и координаты атласов.

PNG и manifest не редактируются вручную. Их воспроизводит `tools/environment_integration/build_environment_atlases_v01.py`; `TileSet` воспроизводит `tools/environment_integration/create_environment_tileset_v01.gd`. Полный runtime-контракт описан в `docs/GODOT_ENVIRONMENT_INTEGRATION_V01.md`.
