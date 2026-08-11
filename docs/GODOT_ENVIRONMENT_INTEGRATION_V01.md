# Godot Environment Integration v01

## Статус

Утверждённый набор `cold_ancient_stone_v01` интегрирован в игровую сцену караульного поста как чисто визуальный слой. Источник зафиксирован SHA-256 профиля `a589602410f3cdaac775ee3e690d701c24926e1754b847aec3161af0e4edffb9`; в runtime попадают только 33 нормализованных PNG-модуля, шесть атласов и один Godot `TileSet`.

Интеграция не меняет боевую сетку, коллизии, навигацию, AI, line of sight, состояние дверей, схему сохранений или идентификаторы столкновений. Главной платформой остаётся Android, поэтому используются Nearest-фильтрация, статические атласы и ограниченное число клеток.

## Контракты масштаба

| Контракт | Значение |
| --- | ---: |
| Клетка боя и пола | `64×64 px` |
| Canvas персонажа | `96×96 px` |
| Модули стены и двери | `64×96 px` |
| Углы стены | `96×96 px` |
| Локальные границы караулки | `(-200, -315), 1190×630 px` |
| Seed раскладки пола | `1729` |
| Фильтрация | `Nearest` |

Размер комнаты не кратен 64. Полный центр пола занимает `18×9 = 162` клеток; остатки `38 px` справа и `54 px` снизу закрываются cropped-регионами без растягивания. Поэтому визуальные границы совпадают с существующим механическим `Rect2` до пикселя.

## Runtime-архитектура

`scenes/game/game.tscn` подключает `guard_post_environment_integration.gd`, который наследует существующий `guard_post_party_visibility.gd`. Сначала полностью запускается прежняя механика, затем дочерний `GuardPostEnvironmentPresentation` пытается установить утверждённый визуальный пакет.

Данные комнаты находятся в `data/environment/guard_post_environment_v01.json`. Восемь `TileMapLayer` разделяют пол, переходы влажности, декали и стены:

| Слой | Назначение | Z |
| --- | --- | ---: |
| `FloorLayer` | Детерминированные варианты каменного пола | `0` |
| `TransitionLayer` | Переходы сухого и влажного камня | `0` |
| `DecalLayer` | Трещины, пыль, сырость и рунические инкрустации | `0` |
| `NorthWallLayer` | Северная внешняя стена | `50` |
| `SouthForegroundLayer` | Южная стена поверх персонажей | `50` |
| `LeftWallLayer` / `RightWallLayer` | Боковые внешние стены | `50` |
| `PartitionWallLayer` | Две внутренние перегородки с дверными проёмами | `50` |

Неполные края пола и стен, углы и две двери создаются небольшими `Sprite2D`, потому что их точная геометрия не укладывается в целую клетку. Углы имеют Z `51`, двери — `52`, прежний room fog остаётся на Z `60`.

Распределение восьми вариантов пола вычисляется только из координаты клетки и seed. Оно одинаково между запусками и не записывается в save snapshot. Текущая караулка использует 245 TileMap-клеток при лимите v01 в 260; суммарный размер исходных runtime PNG и атласов — 42 764 байта.

## Двери и fallback

Каждая дверь длиной 128 px собирается из двух утверждённых модулей. `EnvironmentDoorSprite` читает текущее состояние существующего `StealthDoor` и меняет текстуру между `closed` и `open`; `broken` использует открытую форму с отдельной модуляцией. Коллизия и правила прохода по-прежнему принадлежат старому узлу двери.

Legacy-пол, ковёр, debug-стены и прежний door decorator скрываются только после успешной загрузки JSON, `TileSet` и всех обязательных текстур. При отсутствующем или повреждённом ресурсе установка прекращается, прежние визуалы остаются видимыми, а механика продолжает работать.

## Demo и ручная проверка

Сцена `scenes/game/environment/cold_ancient_stone_demo_v01.tscn` показывает комнату `6×6`, стены, сырость, трещины, руны, лестницу и утверждённый кадр человека-воина для проверки масштаба. Лестница в v01 является только review-объектом и не добавляет интерактивность или переход уровня.

Headless-композиция точной игровой раскладки:

```bash
python3 tools/environment_integration/render_environment_layout_review_v01.py
```

`capture_environment_review_v01.gd` снимает demo и production-сцену через viewport, но требует графический renderer; dummy renderer в headless-режиме не создаёт пригодный кадр.

## Воспроизводимость ресурсов

После утверждения Blender run модули и атласы пересобираются так:

```bash
python3 tools/environment_integration/build_environment_atlases_v01.py \
  --source-run art/blender_environment_runs/cold_ancient_stone_v01/local_20260811_environment_v01_render_final \
  --output-root assets/environment/approved/cold_ancient_stone_v01 \
  --approved-on 2026-08-11

godot --headless --path . \
  --script res://tools/environment_integration/create_environment_tileset_v01.gd
```

Promotion проверяет профиль, число артефактов, SHA-256 каждого PNG, RGBA-режим и canvas. Approved manifest дополнительно фиксирует координаты атласов и контракт `TileSet`: шесть source ID, custom data `visual_id`, `64×64`, без collision/navigation.

## Автоматические проверки

```bash
python3 tools/environment_integration/validate_environment_integration_v01.py

godot --headless --path . \
  --script res://tests/smoke_godot_environment_integration_v01.gd

godot --headless --path . --script res://tests/smoke_movement_wall_integrity.gd
godot --headless --path . --script res://tests/smoke_player_visibility_save_runtime.gd
godot --headless --path . --script res://tests/smoke_guard_post_presentation_and_parley.gd
```

Профильный workflow повторяет статическую проверку, чистый импорт Godot 4.7.1, runtime smoke и три регрессии. Smoke отдельно проверяет 33 модуля, шесть атласов, custom `visual_id`, восемь слоёв, точное число основных клеток, Nearest, fallback, сохранение механических коллизий, смену вида дверей, одинаковый floor signature после пересоздания сцены и demo `6×6`.

## Отложено после v01

- интерактивная лестница и переход уровня;
- локальное динамическое освещение и тени;
- дополнительные биомы и autotile-правила;
- профилирование на целевых Android-устройствах и корректировка бюджетов по измерениям.
