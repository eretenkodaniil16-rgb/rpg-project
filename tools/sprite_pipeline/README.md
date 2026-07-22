# Hybrid Sprite Pipeline

Инструмент создаёт несколько вариантов локального редактирования утверждённого спрайта, отбраковывает технический брак, выполняет визуальную оценку и передаёт пользователю только лучшие кандидаты. Финальное художественное решение всегда принимает пользователь.

## Что автоматизировано

1. Image Edit API получает исходный idle и master-reference.
2. Создаётся до 8 кандидатов первого прохода.
3. Каждый PNG проверяется локально:
   - настоящий alpha;
   - отсутствие непрозрачного фона;
   - непустой силуэт;
   - нормализация nearest-neighbor в `96×96`;
   - высота `76–80 px`;
   - ширина не более `88 px`;
   - единая нижняя базовая линия;
   - бинарный alpha без полупрозрачной каймы;
   - техническое сходство с направленным idle и областью лица.
4. Vision-grader сравнивает прошедшие варианты с reference pack по шести критериям.
5. Любая критическая ошибка отклоняет кандидат независимо от общего балла.
6. Если никто не набрал 85/100, выполняется один дополнительный локальный проход над лучшим неотклонённым вариантом.
7. В artifact попадают полный отчёт и только два лучших нормализованных PNG для согласования.

Pipeline никогда не объединяет PR и не переносит кандидат в `approved` автоматически.

## Требуемые эталоны

Перед первым запуском должны существовать:

```text
art/reference_packs/human_warrior_m01/approved/human_warrior_m01_master.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_down.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_left.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_right.png
assets/characters/human/warrior_m01/gameplay/frames/human_warrior_m01_idle_up.png
```

После проверки файлов измените:

```json
"ready": true
```

в `configs/human_warrior_m01.json`.

Пока `ready=false`, платная генерация намеренно блокируется.

## GitHub Actions с телефона

1. Откройте репозиторий → **Settings** → **Secrets and variables** → **Actions**.
2. Создайте repository secret `OPENAI_API_KEY`.
3. Откройте **Actions** → **Generate sprite candidates** → **Run workflow**.
4. Выберите ветку с утверждёнными reference-файлами и нужный `frame_id`.
5. После завершения скачайте artifact `sprite-review-...`.
6. Для согласования откройте `selected/contact_sheet.png` и `report.md`.

API-ключ нельзя записывать в `.env`, workflow, issue, PR, лог или изображение. OpenAI SDK читает его только из переменной окружения.

## Локальный запуск на Windows

```powershell
py -3.12 -m venv .tools\sprite-pipeline-venv
.tools\sprite-pipeline-venv\Scripts\python -m pip install -r tools\sprite_pipeline\requirements.txt
$env:OPENAI_API_KEY="..."
.tools\sprite-pipeline-venv\Scripts\python tools\sprite_pipeline\run_pipeline.py run --frame-id walk_down_f01
```

Техническая проверка уже полученных PNG не требует API-ключа:

```powershell
.tools\sprite-pipeline-venv\Scripts\python tools\sprite_pipeline\run_pipeline.py validate --frame-id walk_down_f01 --input-dir C:\sprites\candidates
```

## Результаты

Локально создаётся:

```text
art_pipeline_runs/<character_id>/<frame_id>/<timestamp>/
├── raw/
├── normalized/
├── rejected_raw/
├── selected/
│   ├── rank_01_*.png
│   ├── rank_02_*.png
│   └── contact_sheet.png
├── prompt.txt
├── technical_report.json
├── report.json
└── report.md
```

`art_pipeline_runs/` игнорируется Git и не должен попадать в историю репозитория.

## Система оценки

| Критерий | Вес |
|---|---:|
| Лицо и личность | 30% |
| Физические стороны экипировки | 20% |
| Перспектива | 15% |
| Пропорции | 15% |
| Требуемая фаза движения | 10% |
| Палитра и pixel-art стиль | 10% |

Hard reject:

- модель создала другого персонажа или полностью перегенерировала дизайн;
- изменилось лицо;
- появились крупные видимые/анимешные глаза;
- перепутаны физические стороны наплечников, меча, ножен или сумок;
- изменён угол камеры;
- изменены голова, телосложение или пропорции;
- фон непрозрачный либо шахматная сетка встроена в PNG;
- есть размытие или нежелательный антиалиасинг;
- поза не соответствует выбранному кадру.

## Ограничения

- Нейросетевой grader не заменяет художественное утверждение.
- Автонормализация исправляет размер, alpha и базовую линию, но не исправляет анатомию или лицо.
- После двух неудачных проходов pipeline прекращает генерацию. Следующий шаг — ручная или модульная pixel-art правка, а не бесконечная перегенерация.
- Кандидаты не считаются игровыми ресурсами до проверки в Godot на реальном размере.

Официальные API-источники:

- https://developers.openai.com/api/reference/resources/images/methods/edit
- https://developers.openai.com/api/docs/guides/images-vision
- https://developers.openai.com/api/docs/guides/structured-outputs
