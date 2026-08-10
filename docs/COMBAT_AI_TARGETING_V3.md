# Combat AI Targeting v3

## Цель

Combat AI Targeting v3 убирает зависимость боевого ИИ от конкретного управляемого персонажа. Герой, Ирина и будущие подконтрольные союзники рассматриваются как участники одной партии через общий боевой контракт.

## Контракт цели партии

Управляемый союзник поддерживает полноценную тактику ИИ, если предоставляет:

- `get_actor_id()` — стабильный идентификатор;
- `get_combat_name()` — отображаемое имя;
- `get_current_health()` / `get_maximum_health()`;
- `get_armor_class()`;
- `get_saving_throw_modifier(ability_id)`;
- `get_combatant_state()`;
- `set_current_health(value)` для применения урона;
- опционально `can_receive_enemy_attack()`, `is_dodging()` и `enter_dying()`.

Герой адаптируется к этому же контракту через `GameState.player_character` и `_player_combat_state`. Никакой `character_id` конкретного спутника не используется для выбора тактики.

## Target adapter

`CombatAiPartyTargetAdapter` — stateless слой между AI и представлением конкретного персонажа. Он нормализует HP, КД, спасброски, состояния и доступность цели.

Это позволяет добавлять будущих спутников без новых веток `if target == companion_x` в Combat AI.

## Target discovery и utility scoring

Runtime получает героя и все узлы группы `controllable_allies`, удаляет дубликаты и передаёт доступные видимые цели в существующий `NpcTacticalTargetingSystem`.

Сохраняются:

- hysteresis предыдущей цели;
- target claims и штраф за чрезмерную концентрацию врагов на одной цели;
- оценка дистанции и готовности атаки;
- оценка уязвимости по HP;
- роль melee/ranged/caster.

Цель с поддерживаемым контрактом получает `full_tactics_supported = true`, поэтому caster и ranged AI больше не штрафуют союзника только за то, что он не является главным героем.

## Полноценный non-player target pipeline

Для выбранного союзника Combat AI v3 поддерживает:

- тактическое перемещение через существующий grid/environment planner;
- обычные melee/ranged атаки;
- Dodge и Rally;
- Shove с проверкой характеристик и состоянием `prone`;
- выбор заклинания через существующий `NpcSpellSelectionSystem`;
- spell attack против КД конкретного союзника;
- saving throw spell против спасброска конкретного союзника;
- состояния через его `CombatantState`;
- AoE с подсчётом всех членов партии в области;
- friendly-fire оценку против союзников NPC;
- исключение персонажей с 0 HP и погибших из обычного target selection.

Для героя сохраняется прежний проверенный Advanced AI pipeline. Это уменьшает риск регрессий существующего боя, пока новый actor-agnostic путь расширяет поддержку всех остальных членов партии.

## Точки расширения

Новый спутник должен войти в группу `controllable_allies` и реализовать контракт цели. После этого он автоматически появляется в utility-targeting без изменения AI runtime.

Если в будущем появятся существа с нестандартной моделью HP/защиты, расширять следует `CombatAiPartyTargetAdapter`, а не создавать отдельный combat AI для конкретного персонажа.

## Проверки

- `tests/test_combat_ai_party_target_adapter.gd`;
- `tests/smoke_combat_ai_targeting_v3.gd`;
- регрессии AI/Stealth v2;
- Advanced Combat AI;
- controllable ally runtime;
- squad tactical plans;
- импорт проекта Godot 4.7.1.
