# Blender Sprite Factory

Воспроизводимый пилот конвейера:

```text
модульная 3D-модель → риг и Actions → 4 настоящих направления
→ прозрачные PNG 96×96 → ручная пиксельная проверка → Godot
```

3D используется только при производстве графики. В игру попадают обычные
`AnimatedSprite2D`-кадры, поэтому runtime Android не получает Blender, меши,
кости или 3D-материалы.

## Что создаёт пилот

- риг из 21 кости;
- 14 независимых модулей тела и экипировки;
- `human_warrior_m01_idle`;
- шестикадровый `human_warrior_m01_walk_down`;
- ортографическую камеру под углом 47°;
- реальный поворот модели на 0°, −90°, +90° и 180°, без зеркалирования;
- заменяемые texture slots с интерполяцией `Closest`;
- четыре `idle`-кадра и шесть `walk_down`-кадров;
- бинарный alpha, высоту 78 px и базовую линию `y=91`;
- `.blend`, отдельные PNG, сравнительный contact sheet и машинный
  `run_manifest.json`.

Это proxy-пилот. Он проверяет технологию, силуэт, перспективу, стороны
экипировки и повторяемость. Он не считается финальной моделью или готовым
игровым спрайтом.

## Требования

- Windows 10/11 x64;
- [Blender 5.2 LTS](https://www.blender.org/download/lts/) — рекомендуемая
  закреплённая версия;
- минимум Blender 4.5;
- репозиторий `rpg-project`.

API-ключ, платные сервисы и отдельный Python для рендера не нужны. Скрипт
использует Python, встроенный в Blender.

## Самый простой запуск на Windows

1. Установить Blender 5.2 LTS в стандартную папку.
2. Обновить локальную копию ветки с factory.
3. Дважды нажать:

```text
02_RUN_BLENDER_SPRITE_PILOT.cmd
```

Скрипт ищет `blender.exe` в `PATH`, переменной `BLENDER_EXE` и стандартных
папках Blender 4.5–5.2. Путь репозитория может содержать кириллицу.

Ручной PowerShell-запуск:

```powershell
.\tools\blender_sprite_factory\run_blender_sprite_pilot.ps1
```

Если Blender установлен нестандартно:

```powershell
.\tools\blender_sprite_factory\run_blender_sprite_pilot.ps1 `
  -BlenderExe "D:\Programs\Blender\blender.exe"
```

Только создать `.blend`, без рендера:

```powershell
.\tools\blender_sprite_factory\run_blender_sprite_pilot.ps1 -Mode build
```

## Результат

Каждый запуск получает новый каталог и не перезаписывает предыдущий:

```text
art/blender_pipeline_runs/human_warrior_m01/<run_id>/
├── source/
│   └── human_warrior_m01_proxy_v01.blend
├── raw/
├── frames/
│   ├── human_warrior_m01_idle_down_proxy_v01.png
│   ├── human_warrior_m01_idle_left_proxy_v01.png
│   ├── human_warrior_m01_idle_right_proxy_v01.png
│   ├── human_warrior_m01_idle_up_proxy_v01.png
│   └── human_warrior_m01_walk_down_f01–f06_proxy_v01.png
├── contact_sheet.png
└── run_manifest.json
```

`art/blender_pipeline_runs/` игнорируется Git. Кадры не попадают в игру
автоматически.

`contact_sheet.png` использует нейтральный сине-серый фон, отсутствующий в
палитре персонажа. Ряды сверху вниз:

1. четыре новых proxy-idle;
2. четыре утверждённых idle-эталона;
3. шесть новых кадров `walk_down`.

Так тёмная сталь и контур не сливаются с фоном, а пропорции можно сравнить с
каноном без отдельного монтажа.

## Что прислать для следующей итерации

Достаточно прикрепить:

```text
contact_sheet.png
```

Если скрипт завершился ошибкой, дополнительно скопировать последние строки
окна PowerShell. `.blend` нужен только если требуется ручная локальная правка
модели.

Первая художественная проверка оценивает только:

1. высоту камеры и читаемость top-down 3/4;
2. пропорции и общий силуэт;
3. неизменные физические стороны наплечников, меча и подсумка;
4. стабильность четырёх направлений;
5. отсутствие дрожания базовой линии в `walk_down`.

Лицо, точная форма брони и финальная палитра дорабатываются после принятия
этого технического среза — по одной группе проблем за итерацию.

## Texture slots

Технические текстуры находятся в:

```text
art/blender_sources/human_warrior_m01/textures/pilot_v01/
```

Смена PNG с тем же именем меняет поверхность без изменения рига и Actions.
Изменение силуэта — например другой наплечник или шлем — требует замены
соответствующего отдельного меша, а не только текстуры.

## Локальные проверки без Blender

```powershell
py -m pip install "Pillow>=11.1.0,<13.0.0"
$env:PYTHONPATH="tools\blender_sprite_factory"
py -m unittest discover -s tools\blender_sprite_factory\tests -p "test_*.py" -v
py tools\blender_sprite_factory\validate_factory.py
```

CI проверяет контракт, ссылки на reference pack, texture slots, синтаксис и
детерминированность текстур. Настоящий визуальный рендер всё равно обязателен:
статическая проверка не может подтвердить Blender API, лицо или перспективу.
