# Human Warrior Runtime Animation v02

## Статус

`human_warrior_m01` подключён к runtime Godot 4.7.1 через утверждённые атласы из:

`res://assets/characters/human/warrior_m01/gameplay/approved/atlases/`

Реализация не изменяет PNG, боевые формулы, инициативу, расход действий, боеприпасы, mitigation или формат сохранений.

## Наборы

| Состояние | Одноручный меч | Двуручный меч |
| --- | --- | --- |
| Exploration idle/walk | обычные `idle` / `walk` | обычные `idle` / `walk` |
| Combat idle | `combat_idle_onehand` | `combat_idle_twohand` |
| Combat walk | `walk_onehand` | `walk_twohand` |
| Attack | `attack_sword_01_onehand` | `attack_sword_01_twohand` |

Каждый набор содержит направления `down / left / right / up`. Ячейка — `96×96`, baseline — `y=91`, фильтрация — nearest-neighbor.

## Поддерживаемые visual_id оружия

Одноручная sword-анимация применяется только для:

- `longsword`;
- `shortsword`;
- `scimitar`.

Двуручная sword-анимация применяется для:

- `greatsword`.

Для булав, топоров, копий, посохов, неподдерживаемой расы/класса и отсутствующих ресурсов сохраняется процедурный lunge-fallback. Это предотвращает показ меча при фактически экипированном оружии другого типа.

## Синхронизация атаки и урона

1. CombatSystem заранее рассчитывает попадание и значение урона, но не изменяет HP цели.
2. `Player.start_melee_attack_animation()` включает локальный action-lock и запускает нужное направление.
3. `AnimatedSprite2D.frame_changed` служит animation event.
4. На кадре `f04` вызывается contact callback, который применяет существующий `AttackResult` через `receive_player_attack`.
5. Кадры `f05–f08` проигрываются уже после контакта.
6. `AnimatedSprite2D.animation_finished` снимает action-lock и возвращает персонажа в соответствующий `combat_idle`.

У одноручных `left/up` сохраняется отдельный кадр settle `f08`; принудительной подмены на `f01` нет.

## Блокировки

Во время `attack_sword_01`:

- перемещение равно нулю;
- повторный запуск melee-атаки отклоняется;
- смена walk/idle не перезаписывает attack-анимацию;
- завершение игрового действия ожидает `f08`.

Глобальный `GameState.input_locked` для этого не используется: блокировка локальна и не вмешивается в диалоги, меню и сохранения.

## Fallback

При отсутствии manifest, atlas, animation set или неподдерживаемом персонаже:

- `Polygon2D` остаётся рабочим визуалом;
- используется прежний lunge Tween;
- contact callback вызывается на вершине выпада, а не сразу при нажатии;
- после возврата Tween локальная блокировка снимается.

## Проверки

`tests/test_human_warrior_runtime_animation_v02.gd` проверяет:

- 8 наборов и 32 directional animation;
- реальные клетки `96×96`;
- переходы idle/walk/combat idle;
- выбор направления перед атакой;
- одноручный и двуручный attack;
- contact event строго на `f04`;
- сохранение lock до завершения `f08`;
- запрет повторной атаки;
- блокировку движения;
- возврат в matching combat idle;
- fallback для другого оружия и неподдерживаемого персонажа.

Перед объединением необходимо дополнительно проверить на Windows и Android:

- визуальное совпадение точки контакта с моментом уменьшения HP;
- отсутствие движения во время атаки;
- корректный возврат в стойку для четырёх направлений;
- отсутствие масштабирования, blur и смещения baseline.
