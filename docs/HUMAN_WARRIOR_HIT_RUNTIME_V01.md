# Human Warrior Hit Runtime v01

## Статус

Утверждённые directional `hit_01` для `human_warrior_m01` подключены к production-сцене Godot 4.7.1.

Поддерживаются:

- `onehand_ready`;
- `twohand_center_high`;
- `down / left / right / up`;
- 6 кадров при 15 FPS;
- длительность 0,4 секунды;
- non-loop playback.

## Approved-ресурсы

```text
res://assets/characters/human/warrior_m01/gameplay/approved/atlases/human_warrior_m01_hit_01_onehand_v01.png
res://assets/characters/human/warrior_m01/gameplay/approved/atlases/human_warrior_m01_hit_01_twohand_v01.png
```

Оба атласа имеют размер `576×384`: шесть колонок и четыре directional-строки `down / left / right / up`.

## Условие запуска

Единая production-точка — `apply_damage_to_player` в damage/fall runtime.

Последовательность:

1. SRD-система рассчитывает resistance, immunity, temporary HP и итоговый `applied`;
2. HP персонажа изменяется существующим кодом;
3. при `applied <= 0` визуальная реакция не запускается;
4. при оставшемся HP выше нуля вызывается `Player.play_hit_reaction`;
5. при переходе к 0 HP или смерти активный hit отменяется и сохраняется приоритет `death`;
6. сохранение и обновление HUD выполняются прежним damage runtime.

Боевые формулы, concentration, death saves и формат сохранений не меняются.

## Visual state machine

Hit использует существующий `_action_animation_locked`:

- движение блокируется;
- facing не меняется;
- новая атака не может начаться;
- idle/walk не перезаписывают hit;
- после шестого кадра персонаж возвращается в matching combat idle;
- завершение обрабатывается deferred-вызовом после `AnimatedSprite2D.animation_finished`.

Если урон получен во время другой локальной action-анимации, сохраняется одна queued hit-реакция с максимальным значением damage. Она запускается после завершения текущего action, если персонаж остаётся жив.

## Выбор хвата

- `longsword / shortsword / scimitar` в combat mode → `hit_01_onehand_*`;
- `greatsword` в combat mode → `hit_01_twohand_*`;
- неподдерживаемое оружие, exploration mode или неподдерживаемый персонаж → короткий процедурный recoil fallback.

Fallback не создаёт новые узлы каждый кадр и не требует отдельного сохранения.

## Death priority

Текущий этап ещё не содержит художественную death-анимацию. Тем не менее контракт приоритета уже установлен:

- летальный damage не запускает hit;
- активный hit отменяется при переходе к 0 HP;
- следующий death-этап сможет занять visual state без конкуренции с hit.

## Автоматические проверки

`tests/test_human_warrior_hit_runtime_v01.gd` проверяет:

- 8 directional hit-анимаций;
- 6 кадров, 15 FPS, non-loop;
- onehand и twohand выбор;
- блокировку движения и facing;
- возврат в matching combat idle;
- fallback неподдерживаемого оружия;
- отсутствие реакции на нулевой damage;
- запуск через production `apply_damage_to_player`;
- отсутствие hit при летальном damage;
- очистку active state при death priority.

Asset-validator дополнительно проверяет:

- 10 approved-атласов;
- размеры, binary alpha и baseline `y=91`;
- edge/settle contracts;
- SHA-256 атласов;
- runtime manifest contract.

## Ручная проверка перед merge

На Windows и Android проверить:

1. получение обычного melee damage во всех четырёх направлениях;
2. onehand и twohand стойки;
3. отсутствие реакции при полном блокировании damage;
4. отсутствие движения и разворота во время hit;
5. возврат в ту же боевую стойку;
6. переход к 0 HP без проигрывания hit поверх death/game-over состояния;
7. fallback с булавой или другим неподдерживаемым оружием;
8. отсутствие blur, baseline drift и смены физических сторон асимметрии.
