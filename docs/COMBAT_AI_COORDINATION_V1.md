# Combat AI Coordination v1

## Цель

Связать уже существующие `SquadTacticalPlanSystem` и `SquadPlanNpcAiSystem` с актуальным `Advanced Party Tactics v1`, чтобы несколько NPC одного `squad_id` действовали как отряд против любого поддерживаемого члена партии, а не принимали только независимые решения.

## Архитектура

Активный leaf runtime:

`game_ai_stealth_v2_ui_runtime.gd`
→ `game_combat_ai_coordination_v1_runtime.gd`
→ `game_advanced_party_tactics_v1_runtime.gd`
→ существующая цепочка, уже включающая `game_squad_tactical_plans_runtime.gd`
→ `game_combat_ai_targeting_v3_runtime.gd`

Ключевое ограничение: Combat AI Coordination v1 **не создаёт второй squad-blackboard и второй AI**. Исторический `game_squad_tactical_plans_runtime.gd` уже владеет `_squad_ai`, `_squad_plans`, назначениями, tactical objectives, outcome tracking и резервированием клеток. Новый runtime является только bridge-слоем: передаёт в этот существующий blackboard generic party-target context из Advanced Party Tactics v1 и возвращает его role-specific назначения в актуальный путь движения/действий.

`SquadPlanNpcAiSystem` является подклассом уже используемого Advanced AI, поэтому сохраняются существующие spell/target/tactical contracts. `SquadTacticalPlanSystem` остаётся data-driven и читает `res://data/ai/squad_tactical_plans.json`.

## Что координируется

Для каждого `squad_id` выбирается один активный план. Затем каждому живому NPC выдаётся детерминированное назначение по его роли и индексу внутри squad.

Поддерживаются существующие планы:

- `suppress_and_flank` — ближники обходят, защитник фиксирует фронт, стрелок подавляет с тыла, маг контролирует цель;
- `coordinated_assault` — согласованное наступление с role-specific секторами;
- `orderly_withdrawal` — организованный отход;
- `sector_search` — разделение последней известной позиции на сектора;
- `rescue_bound_ally` — освобождение связанного союзника, когда есть реальный видимый bound-body context;
- `hold_chokepoint` — остаётся data-driven и использует реальный environment/passage context существующей системы; новый bridge не синтезирует знание о проходе сам.

## Generic party target

Координация использует выбранную `Combat AI Targeting v3` цель. Поэтому front/flank/rear/search objectives строятся относительно фактического выбранного члена партии, а не жёстко относительно главного героя.

Если враг выбрал Ирину или будущего поддерживаемого спутника, тот же squad-plan продолжает работать без отдельной ветки AI для конкретного персонажа.

## Tactical blackboard

Единственный источник временного squad-state — унаследованный `game_squad_tactical_plans_runtime.gd`. В нём сохраняются:

- назначение NPC;
- рассчитанная tactical objective;
- зарезервированная конечная клетка;
- уже объявленный squad-plan;
- outcome назначения и failure count.

Combat AI Coordination v1 не дублирует эти структуры. Состояние очищается после боя. Save schema не меняется и миграция старых сохранений не требуется.

## Cell reservations

Когда NPC планирует generic party-target movement, новый bridge выставляет унаследованный `_active_planning_actor_id`. Поэтому существующая проверка `_combat_ai_cell_is_available()` учитывает клетки, уже зарезервированные другими членами того же squad. После выбора пути конечная клетка записывается в тот же унаследованный `_squad_reserved_cells`.

Резервации сбрасываются при смене раунда существующим squad runtime.

## Совместимость Advanced Party Tactics v1

Production runtime получает squad assignment через `_build_party_tactical_context_v1()` и позволяет squad-плану переопределять более слабое индивидуальное utility-решение.

Старый helper `choose_party_tactical_intent_v1_for_testing()` сохранён как изолированный тест нижнего слоя Rally / Take Cover / Regroup: из его тестового context удаляются только coordination keys. Это не влияет на production decision path; для самой координации существует отдельный integration smoke.

## Ограничения v1

- Координация не даёт NPC всеведения. Targeting, LOS и shared memory продолжают ограничиваться существующими системами.
- Новый bridge не создаёт фиктивный passage/chokepoint context.
- Система не телепортирует NPC и не отключает collision/path rules.
- Боевой план не записывается отдельной сущностью в сохранение: после загрузки он пересчитывается из актуального состояния мира существующей системой.

## Автоматическая проверка

`tests/smoke_load_combat_ai_coordination_v1.gd` напрямую загружает новый leaf и требует `Script.can_instantiate()`, чтобы parser error не мог ложно пройти как загруженный Resource.

`tests/smoke_combat_ai_coordination_v1.gd` проверяет реальный `vault_watch` mixed squad:

- `service_guard` получает flank;
- `caretaker` получает front/pin assignment;
- `training_marksman` получает suppression/rear assignment;
- `training_mage` получает caster control/rear assignment;
- общий план доходит до `SquadPlanNpcAiSystem` и способен переопределить независимый utility intent;
- tactical objectives расходятся по секторам;
- два NPC не резервируют одну конечную клетку;
- runtime state очищается.

Workflow также прогоняет регрессии Advanced Party Tactics v1, Combat AI Targeting v3, Advanced Combat AI, исторического squad tactical runtime, AI/Stealth v2 и controllable ally.

## Ручная проверка Android

Проверить бой героя и Ирины против mixed squad минимум из четырёх ролей. Ожидается, что враги не складываются в одну точку, фронтовик удерживает направление, ближник пытается зайти сбоку, стрелок сохраняет rear/cover sector, маг занимает безопасный сектор и использует существующий spell selector. При потере цели squad должен перейти к shared-memory/search поведению, не получая информацию сквозь стены без существующего LOS/memory contract.
