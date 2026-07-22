# human_warrior_m01 reference pack

Этот каталог хранит только утверждённые художественные эталоны, которые используются генератором и визуальным контролёром. Каталог исключён из импорта Godot через родительский `.gdignore`.

Перед включением pipeline нужно добавить:

```text
art/reference_packs/human_warrior_m01/approved/human_warrior_m01_master.png
```

`human_warrior_m01_master.png` должен быть исходным изображением, по которому окончательно утверждены:

- лицо, возраст и выражение;
- форма головы, носа и подбородка;
- волосы;
- палитра кожи;
- общий painterly pixel-art стиль;
- физические стороны асимметричной брони, оружия и сумок.

Направленные gameplay-idle берутся из:

```text
assets/characters/human/warrior_m01/gameplay/frames/
```

После окончательного утверждения четырёх idle-файлов нужно изменить `ready` на `true` в:

```text
tools/sprite_pipeline/configs/human_warrior_m01.json
```

Нельзя помещать в `approved` промежуточные генерации. Кандидаты хранятся только во временных `art_pipeline_runs/` или GitHub Actions artifacts.
