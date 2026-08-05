# Hybrid Sprite Pipeline

Инструмент поддерживает два независимых режима:

- **API mode** — создаёт варианты через OpenAI API, технически фильтрует, оценивает vision-grader и показывает лучшие кандидаты;
- **Manual mode** — бесплатно проверяет PNG, полученные в ChatGPT или другом редакторе, и формирует пакет для ручного художественного согласования.

Финальное художественное решение всегда принимает пользователь. Pipeline никогда не объединяет PR и не переносит кандидат в `approved` автоматически.

## Manual mode без API

Кандидаты загружаются в фиксированную папку выбранного кадра:

```text
art_pipeline_submissions/human_warrior_m01/walk_down_f01/
```

Поддерживаются папки `walk_down_f01`–`walk_down_f06`. Рекомендуемые имена:

```text
candidate_01.png
candidate_02.png
candidate_03.png
candidate_04.png
```

Далее:

1. Откройте **Actions → Validate manual sprite candidates → Run workflow**.
2. Выберите ветку с pipeline и нужный `frame_id`.
3. Укажите `top_k` — сколько технически сильнейших кандидатов показать для художественной проверки.
4. Скачайте artifact `sprite-review-manual-...`.
5. Откройте `selected/contact_sheet.png` и `report.md`.

API-ключ для manual mode не требуется.

Manual mode проверяет:

- настоящий alpha;
- отсутствие непрозрачного или встроенного фона;
- непустой силуэт;
- нормализацию nearest-neighbor в `96×96`;
- высоту `76–80 px`;
- ширину не более `88 px`;
- единую нижнюю базовую линию;
- бинарный alpha без полупрозрачной каймы;
- техническое сходство с направленным idle и областью лица.

Он не может автоматически подтвердить лицо, физические стороны экипировки, перспективу и точность позы. Эти пункты остаются на ручном художественном согласовании.

## API mode

1. Image Edit API получает исходный idle и master-reference.
2. Создаётся до 8 кандидатов первого прохода.
3. Каждый PNG проходит те же локальные технические проверки.
4. Vision-grader сравнивает прошедшие варианты с reference pack по шести критериям.
5. Любая критическая ошибка отклоняет кандидат независимо от общего балла.
6. Если никто не набрал 85/100, выполняется один дополнительный локальный проход над лучшим неотклонённым вариантом.
7. В artifact попадают полный отчёт и только лучшие нормализованные PNG для согласования.

Для API mode нужен repository secret `OPENAI_API_KEY`. Подписка ChatGPT не заменяет отдельный API-биллинг.

## Требуемые эталоны

Перед запуском должны существовать:

```text
art/reference_packs/human_warrior_m01/approved/human_warrior_m01_master.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_down.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_left.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_right.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_up.png
```

И manifest должен содержать:

```json
"ready": true
```

## Локальный запуск на Windows

```powershell
py -3.12 -m venv .tools\sprite-pipeline-venv
.tools\sprite-pipeline-venv\Scripts\python -m pip install -r tools\sprite_pipeline\requirements.txt
```

Бесплатная техническая проверка:

```powershell
.tools\sprite-pipeline-venv\Scripts\python tools\sprite_pipeline\run_pipeline.py validate `
  --frame-id walk_down_f01 `
  --input-dir C:\sprites\candidates `
  --top-k 3
```

API-генерация:

```powershell
$env:OPENAI_API_KEY="..."
.tools\sprite-pipeline-venv\Scripts\python tools\sprite_pipeline\run_pipeline.py run --frame-id walk_down_f01
```

## Результаты

```text
art_pipeline_runs/<character_id>/<frame_id>/<timestamp>/
├── normalized/
├── rejected_raw/
├── selected/
│   ├── rank_01_*.png
│   ├── rank_02_*.png
│   └── contact_sheet.png
├── technical_report.json
├── report.json
└── report.md
```

В API mode дополнительно создаются `raw/`, `prompt.txt` и snapshot manifest. `art_pipeline_runs/` игнорируется Git и не должен попадать в историю репозитория.

## Художественные критерии API grader

| Критерий | Вес |
|---|---:|
| Лицо и личность | 30% |
| Физические стороны экипировки | 20% |
| Перспектива | 15% |
| Пропорции | 15% |
| Требуемая фаза движения | 10% |
| Палитра и pixel-art стиль | 10% |

Hard reject:

- создан другой персонаж или полностью перегенерирован дизайн;
- изменилось лицо;
- появились крупные видимые/анимешные глаза;
- перепутаны физические стороны наплечников, меча, ножен или сумок;
- изменён угол камеры;
- изменены голова, телосложение или пропорции;
- фон непрозрачный либо шахматная сетка встроена в PNG;
- есть размытие или нежелательный антиалиасинг;
- поза не соответствует выбранному кадру.

## Ограничения

- Технический фильтр не заменяет художественное утверждение.
- Автонормализация исправляет размер, alpha и базовую линию, но не исправляет анатомию или лицо.
- После двух неудачных API-проходов pipeline прекращает генерацию.
- Кандидаты не считаются игровыми ресурсами до проверки в Godot на реальном размере.
