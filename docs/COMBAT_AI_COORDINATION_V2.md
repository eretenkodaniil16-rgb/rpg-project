# Combat AI Coordination v2

## Цель

Сделать уже существующую squad-координацию адаптивной к изменению боя, не создавая второй AI или второй tactical blackboard.

Активная цепочка:

`game_ai_stealth_v2_ui_runtime.gd`
→ `game_combat_ai_coordination_v2_runtime.gd`
→ `game_combat_ai_coordination_v1_runtime.gd`
→ `game_advanced_party_tactics_v1_runtime.gd`
→ `game_combat_ai_targeting_v3_runtime.gd`

`SquadTacticalPlanSystem` и `SquadPlanNpcAiSystem` остаются единственным источником squad-plan, assignment и outcome state.

## Dynamic replanning

До v2 активный plan сохранялся до конца `duration_rounds`, пока оставался формально валиден. v2 переоценивает контекст при каждом запросе, но использует два стабилизатора:

- `interrupt_priority` — более срочный план может немедленно прервать менее срочный;
- hysteresis — планы одинакового приоритета переключаются только после минимального времени commitment и достаточного выигрыша score.

Параметры находятся в `data/ai/squad_tactical_plans.json`:

- `min_commitment_rounds`;
- `switch_score_margin`;
- `same_round_switch_score_margin`.

Активный plan хранит `previous_plan_id`, `replan_count`, `last_switch_round` и `switch_reason`, поэтому смена решения диагностируема без отдельного runtime-state.

## Новые планы

### casualty_regroup

Короткая реакция на новую потерю союзника:

- melee собираются ближе к центру живой группы;
- defender прикрывает направление угрозы у точки потери;
- ranged занимает rear-sector и продолжает прикрытие;
- caster получает squad-level Rally assignment.

Это не постоянная паника: plan длится один раунд и не повторяется только из-за старого трупа.

### protect_wounded_ally

Если живой член squad падает до критического здоровья, но отряд ещё не находится в состоянии общего разгрома:

- melee/defender формируют экран между раненым и выбранной party target;
- ranged/caster отходят за раненого относительно направления угрозы;
- focus хранится по стабильному `actor_id` и текущей позиции.

В v2 **не добавляется новое лечение NPC**. Если у конкретного caster позже появится поддерживаемое healing spell/action, оно должно подключаться через существующий spell/action selector отдельным этапом. Текущий план защищает и перегруппировывает раненого, не симулируя несуществующее лечение.

## Withdrawal

`orderly_withdrawal` остаётся более приоритетным, чем защита одного раненого. При двух и более потерях, критически низком среднем HP или morale squad должен перейти к организованному отходу, а не продолжать локальную защиту.

## Search / reacquisition

`Suppress and Flank` и `Coordinated Assault` теперь считаются валидными только при фактической видимости цели. Если LOS потерян, но существует допустимая target memory, plan немедленно переключается на `sector_search`.

Когда цель снова обнаружена, `sector_search` становится невалидным и squad возвращается к подходящему наступательному plan без ожидания конца старой duration.

Это не даёт NPC всеведения: источник памяти и LOS по-прежнему определяется существующими Targeting v3 / Advanced Party Tactics / Stealth systems.

## Wounded context

`game_combat_ai_coordination_v2_runtime.gd` агрегирует по живому squad:

- `wounded_ally_count` — HP ratio ≤ 0.50;
- `critical_ally_count` — HP ratio ≤ 0.25;
- `lowest_health_ratio`;
- `wounded_ally_actor_id`;
- `wounded_ally_position`;
- последнюю casualty record из существующего `NpcCasualtyAwarenessSystem`.

Никаких данных конкретно про Ирину или героя здесь нет.

## Tactical objectives

Добавлены objective types:

- `squad_center`;
- `casualty_front`;
- `casualty_rear`;
- `wounded_front`;
- `wounded_rear`.

Front-sector строится между anchor и текущей угрозой. Rear-sector — за anchor относительно угрозы. Боковой offset зависит от role slot (`left` / `right`). Все конечные клетки продолжают проходить через существующий path planner и reservation contract v1.

## Совместимость

- save schema не меняется;
- active squad-plan остаётся transient и пересчитывается после загрузки;
- actor IDs, target memory и существующие AI data contracts сохраняются;
- `squad_tactical_plans.json` повышен до schema version 2 только для новых plan/replanning data;
- старые тестовые helper v1 продолжают использоваться как regression boundary.

## Автоматические проверки

`tests/test_squad_tactical_replanning_v2.gd` проверяет:

- стабильный plan на одинаковом контексте;
- priority interrupt после casualty;
- protection критически раненого;
- emergency withdrawal;
- мгновенный переход attack → sector search → attack;
- same-round hysteresis и score-margin switch на следующем раунде.

`tests/smoke_combat_ai_coordination_v2.gd` на реальном `game.tscn`:

- запускает mixed `vault_watch` squad;
- реально снижает HP `training_marksman` и требует `protect_wounded_ally`;
- проверяет defender screen objective вокруг раненого;
- проверяет возврат к attack plan после восстановления HP;
- проверяет casualty regroup и caster Rally assignment;
- проверяет casualty-driven withdrawal;
- проверяет sector search и reacquisition.

Специализированный workflow также прогоняет Coordination v1, Advanced Party Tactics v1, Targeting v3, Advanced Combat AI, исторический squad tactical smoke, AI/Stealth v2 и controllable ally.

## Ручная проверка Android

В бою героя и Ирины против mixed squad проверить:

1. обычное наступление распределяет роли как v1;
2. тяжело раненый враг не остаётся изолированным — группа формирует защитный сектор;
3. после смерти союзника группа кратко перегруппировывается, но не зацикливается на трупе;
4. при тяжёлых потерях squad организованно отходит;
5. при потере LOS группа разделяет поиск по секторам;
6. после повторного обнаружения цели squad возвращается к атакующей координации;
7. NPC не телепортируются, не занимают одну клетку и не получают информацию через стены вне существующих LOS/memory правил.