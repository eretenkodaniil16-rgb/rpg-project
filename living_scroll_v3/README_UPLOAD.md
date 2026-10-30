# The Living Scroll V3 — мобильная загрузка и Blender CI

Этот проект изолирован в ветке `art/living-scroll-v3-blender`; основная ветка `main` не изменяется.

## Загрузить проект с телефона

1. Скачайте архив **the_living_scroll_v3_blender_project.zip** из чата.
2. Откройте ветку: https://github.com/eretenkodaniil16-rgb/rpg-project/tree/art/living-scroll-v3-blender
3. В GitHub нажмите **Add file → Upload files**. При необходимости включите в браузере «Версия для ПК».
4. Выберите ZIP **целиком**, без распаковки и переименования, и загрузите в **корень репозитория на этой ветке**.
5. Нажмите **Commit changes** и убедитесь, что целевая ветка — `art/living-scroll-v3-blender`, а не `main`.

## Что произойдёт

GitHub Actions автоматически запустит workflow `.github/workflows/living-scroll-v3-ci.yml` после загрузки именно файла `the_living_scroll_v3_blender_project.zip`. Он:

- Проверит целостность ZIP и защитится от распаковки вне рабочей директории.
- Распакует художественные ассеты и исходники в `living_scroll_v3/`.
- Установит Blender **5.2.0 LTS** с официального сайта, проверив SHA256.
- Создаст маскированные слои и выполнит шесть тестовых кадров.
- Сохранит `living_scroll_v3.blend` и PNG-превью в **Actions → Artifacts**.

Workflow производит **только smoke render** (шесть кадров), не полный MP4. Переход к полному 12-секундному рендеру — отдельный шаг после визуальной проверки превью.

## Ограничения

- Не добавляйте архив в `main`. Он относительно большой (~17 MB), а проект пока экспериментальный.
- Репозиторий `rpg-project` публичный: загруженный архив и его изображения будут доступны всем.
- Архив должен иметь в корне `blender_scene.py`, `build_layers.py`, `assets/lotus_master.png` и `assets/landscape_master.png`.
- На мобильном приложении GitHub опции Upload files может не быть. Откройте github.com в браузере и включите desktop site.
- Отчёт о **фактической успешности рендера** можно делать только по результату запуска Actions, а не по наличию workflow.

Посмотреть запускаемые задачи: https://github.com/eretenkodaniil16-rgb/rpg-project/actions/workflows/living-scroll-v3-ci.yml
