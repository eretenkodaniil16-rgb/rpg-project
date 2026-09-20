# Blender Environment Factory v01

Воспроизводимый review-конвейер первого набора окружения:

```text
параметрическая Blender-сцена → neutral 47° ortho raw-render
→ Nearest 64 px → фиксированная палитра → seam-проверка
→ 6×6 review room → ручное утверждение → отдельная Godot-интеграция
```

Blender остаётся только производственным инструментом. Android получает
обычные PNG/атласы после отдельного утверждения; `.blend`, Eevee, источники
света и Python не попадают в runtime.

## Зафиксированные размеры

- фактическая клетка боя и карты: **64×64 px**;
- холст gameplay-спрайта человека-воина: **96×96 px**;
- raw-render: трёхкратный;
- камера: orthographic top-down 3/4, 47°;
- фильтрация экспорта и Godot runtime: `Nearest`.

Размеры намеренно различаются. `96×96` — безопасный холст высокого персонажа,
а не размер клетки: текущая механика рассчитывает 5 футов как 64 пикселя.

## Состав v01

- 8 вариантов холодного каменного пола;
- 6 декалей: трещины, пыль и сырость;
- 4 направленных перехода сухой → влажный;
- 4 стены на рёбрах и 4 угла;
- дверь `x/y` в состояниях `closed/open`;
- короткая лестница;
- 2 арканные инкрустации;
- контрольная комната 6×6 с approved `human_warrior_m01`.

Всего профиль содержит 33 стабильных `asset_id`.

## Требования

- Blender 5.2.0 LTS (минимум 4.5);
- Windows 10/11 для локального launcher;
- Python с `Pillow>=11.1.0,<13.0.0` для нормализации и review-листов.

## Запуск на Windows

Из корня репозитория:

```text
RUN_BLENDER_ENVIRONMENT_FACTORY_V01.cmd
```

Или напрямую:

```powershell
.\tools\blender_environment_factory\run_blender_environment_factory_v01.ps1
```

При нестандартной установке Blender:

```powershell
.\tools\blender_environment_factory\run_blender_environment_factory_v01.ps1 `
  -BlenderExe "D:\Programs\Blender\blender.exe"
```

Только построить и сохранить `.blend`, без PNG:

```powershell
.\tools\blender_environment_factory\run_blender_environment_factory_v01.ps1 `
  -Mode build
```

Каждый запуск создаёт новый каталог и никогда не перезаписывает старый.

## Результат

```text
art/blender_environment_runs/cold_ancient_stone_v01/<run_id>/
├── source/cold_ancient_stone_v01_source_v01.blend
├── raw/*.png
├── raw_manifest.json
├── exports/
│   ├── floors/
│   ├── overlays/
│   ├── walls/
│   ├── doors/
│   └── structures/
├── review/
│   ├── cold_stone_floor_variants_v01.png
│   ├── environment_modules_contact_sheet_v01.png
│   ├── cold_ancient_stone_room_6x6_v01.png
│   └── cold_ancient_stone_room_6x6_v01_2x.png
└── run_manifest.json
```

Run-каталоги игнорируются Git. До ручного утверждения ничего не копируется в
`assets/environment/` и не подключается к сценам Godot.

## Локальные проверки без Blender

```powershell
$env:PYTHONPATH="tools\blender_environment_factory"
py -m unittest discover `
  -s tools\blender_environment_factory\tests `
  -p "test_*.py" -v
py tools\blender_environment_factory\validate_environment_factory_v01.py
```

Они проверяют профиль, реальные размеры проекта, детерминированность
геометрии, полный каталог, палитру, прозрачные границы и произвольную
совместимость краёв восьми вариантов пола. Перспективу и художественное
качество подтверждает только настоящий Blender render.
