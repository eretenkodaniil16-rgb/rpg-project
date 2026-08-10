# Combat AI Targeting v3

## Цель

Combat AI Targeting v3 убирает зависимость выбора боевой цели от конкретного управляемого персонажа. Герой, Ирина и будущие подконтрольные союзники рассматриваются как участники одной партии через общий боевой контракт.

## Контракт цели партии

Управляемый союзник поддерживается actor-agnostic targeting/runtime, если предоставляет:

- `get_actor_id()` — стабильный идентификатор;
- `get_combat_name()` — отображаемое имя;
- `get_current_health()` / `get_maximum_health()`;
- `get_armor_class()`;
- `get_saving_throw_modifier(ability_id)`;
- `get_combatant_state()`;
- `set_current_health(value)` для применения урона;
- опционально `can_receive_enemy_attack()`, `is_dodging()` и `enter_dying()`.

Герой адаптируется к тому же набору характеристик через `GameState.player_character` и `_player_combat_state`. Никакой `character_id` конкретного спутника не используется для выбора боевой цели.

## Target adapter

`CombatAiPartyTargetAdapter` — stateless слой между AI и представлением конкретного персонажа. Он нормализует HP, КД, спасброски, состояния и доступность цели.

Это позволяет добавлять будущих спутников без новых веток `if target == companion_x` в Combat AI.

## Target discovery и utility scoring

Runtime получает героя и все поддерживаемые узлы группы `controllable_allies`, удаляет дубликаты и передаёт доступные видимые цели в существующий `NpcTacticalTargetingSystem`.

Сохраняются:

- hysteresis предыдущей цели;
- target claims и штраф за чрезмерную концентрацию врагов на одной цели;
- оценка дистанции и готовности атаки;
- оценка уязвимости по HP;
- роль melee/ranged/caster.

Цель с поддерживаемым контрактом получает `full_tactics_supported = true` на уровне выбора цели: caster и ranged AI больше не штрафуют союзника только за то, что он не является главным героем.

## Actor-agnostic non-player target pipeline

Для выбранного союзника Combat AI Targeting v3 поддерживает:

- перемещение к рабочей дистанции через существующий grid/environment planner;
- обычные melee/ranged атаки через реальный `CombatNpc` attack call-site;
- fallback в Dodge, когда полезная атака недоступна;
- Shove с проверкой характеристик и состоянием `prone`;
- выбор заклинания через существующий `NpcSpellSelectionSystem`;
- spell attack против КД конкретного союзника;
- saving throw spell против спасброска конкретного союзника;
- состояния через его `CombatantState`;
- AoE с подсчётом всех членов партии в области;
- friendly-fire оценку против союзников NPC;
- исключение персонажей с 0 HP и погибших из обычного target selection.

Для героя сохраняется прежний проверенный Advanced AI pipeline. Это намеренное ограничение v3: система универсализирует цель и боевое разрешение без переписывания уже работающей герой-ориентированной Advanced AI ветки.

## Граница версии

Targeting v3 не объявляет полную тактическую идентичность hero и non-player веток. Продвинутые intent'ы вроде Rally, Regroup и target-aware Take Cover пока остаются в существующем hero Advanced AI pipeline. Их перенос на общий party-target context следует выполнять отдельным этапом после стабилизации универсального target contract.

Это позволяет не смешивать в одном изменении две независимые задачи: отвязку боевой цели от Ирины и переработку всей системы Advanced AI.

## Точки расширения

Новый спутник должен войти в группу `controllable_allies` и реализовать контракт цели. После этого он автоматически появляется в utility-targeting без изменения AI runtime.

Если в будущем появятся существа с нестандартной моделью HP/защиты, расширять следует `CombatAiPartyTargetAdapter`, а не создавать отдельный combat AI для конкретного персонажа.

## Проверки

- `tests/test_combat_ai_party_target_adapter.gd`;
- `tests/smoke_combat_ai_targeting_v3.gd`, включая второй искусственный союзник, weapon call-site, single-target spell, AoE и downed exclusion;
- регрессии AI/Stealth v2;
- Advanced Combat AI;
- controllable ally runtime;
- squad tactical plans;
- импорт проекта Godot 4.7.1;
- общая валидация проекта и Android build workflow.
