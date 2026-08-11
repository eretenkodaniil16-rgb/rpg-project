# Combat AI Coordination v1

## Цель

Связать уже существующие `SquadTacticalPlanSystem` и `SquadPlanNpcAiSystem` с актуальным `Advanced Party Tactics v1`, чтобы несколько NPC одного `squad_id` действовали как отряд против любого поддерживаемого члена партии, а не принимали только независимые решения.

## Архитектура

Активный leaf runtime:

`game_ai_stealth_v2_ui_runtime.gd`
→ `game_combat_ai_coordination_v1_runtime.gd`
→ `game_advanced_party_tactics_v1_runtime.gd`
→ `game_combat_ai_targeting_v3_runtime.gd`

Новый слой не создаёт второй набор AI-профилей. `SquadPlanNpcAiSystem` является подклассом уже используемого Advanced AI и сохраняет существующие spell/target/tactical contracts.

`SquadTacticalPlanSystem` остаётся data-driven и читает `res://data/ai/squad_tactical_plans.json`.

## Что координируется

Для каждого `squad_id` выбирается один активный план. Затем каждому живому NPC выдаётся детерминированное назначение по его роли и индексу внутри squad.

Поддерживаются существующие планы:

- `suppress_and_flank` — ближники обходят, защитник фиксирует фронт, стрелок подавляет с тыла, маг контролирует цель;
- `coordinated_assault` — согласованное наступление с role-specific секторами;
- `orderly_withdrawal` — организованный отход;
- `sector_search` — разделение последней известной позиции на сектора;
- `rescue_bound_ally` — освобождение связанного союзника, когда есть реальный видимый bound-body context;
- `hold_chokepoint` — остаётся data-driven, но Combat AI Coordination v1 не синтезирует passage incident без реального environment-context.

## Generic party target

Координация использует выбранную `Combat AI Targeting v3` цель. Поэтому front/flank/rear/search objectives строятся относительно фактического выбранного члена партии, а не жёстко относительно главного героя.

## Tactical blackboard

Runtime хранит только временное боевое состояние:

- назначение NPC;
- рассчитанную tactical objective;
- зарезервированную конечную клетку;
- уже объявленный squad-plan;
- outcome назначения.

Состояние очищается после боя. Save schema не меняется и миграция старых сохранений не требуется.

## Cell reservations

Когда NPC планирует движение, выбранная конечная клетка резервируется для его `actor_id` внутри squad. Следующие союзники считают клетки других назначений недоступными и не пытаются закончить ход в одной точке.

Резервации сбрасываются при смене раунда.

## Ограничения v1

- Координация не даёт NPC всеведения. Targeting, LOS и shared memory продолжают ограничиваться существующими системами.
- Environment-specific passage/chokepoint план не активируется без конкретного события окружения.
- Система не телепортирует NPC и не отключает collision/path rules.
- Боевой план не записывается в сохранение: после загрузки активного боя он должен быть пересчитан из актуального состояния мира.

## Автоматическая проверка

`tests/smoke_combat_ai_coordination_v1.gd` проверяет реальный `vault_watch` mixed squad:

- `service_guard` получает flank;
- `caretaker` получает front/pin assignment;
- `training_marksman` получает suppression/rear assignment;
- `training_mage` получает caster control/rear assignment;
- общий план доходит до `SquadPlanNpcAiSystem` и способен переопределить независимый utility intent;
- tactical objectives расходятся по секторам;
- два NPC не резервируют одну конечную клетку;
- runtime state очищается.

## Ручная проверка Android

Проверить бой героя и Ирины против mixed squad минимум из четырёх ролей. Ожидается, что враги не складываются в одну точку, фронтовик удерживает направление, ближник пытается зайти сбоку, стрелок сохраняет rear/cover sector, маг занимает безопасный сектор и использует существующий spell selector. При потере цели squad должен перейти к shared-memory/search поведению, не получая информацию сквозь стены без существующего LOS/memory contract.
