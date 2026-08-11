# Party Stealth v3

## Цель

Party Stealth v3 делает исследовательскую скрытность actor-agnostic: герой, Ирина и будущие `controllable_allies` имеют независимый результат Скрытности, а NPC запоминают и передают союзникам сведения о конкретной обнаруженной цели, а не о «группе вообще».

Этап является leaf-расширением над Combat AI Coordination v2. Он не создаёт вторую систему патруля, поиска, навигации или боевого AI.

## Состояние скрытности

`PartyStealthStateSystem` хранит состояния по стабильному `actor_id`:

- `hidden`;
- `stealth_total`.

Для героя используется стабильный ID `player_character`; для спутников — их `get_actor_id()`.

Состояние сохраняется в `GameState.story_flags.party_stealth_v3_state` как структурированный словарь. Это аддитивное поле: старые сохранения без него загружаются с прежним hero-state и видимыми спутниками. Legacy-поля героя `exploration_hidden` / `exploration_stealth_total` продолжают синхронизироваться для обратной совместимости.

## Восприятие NPC

Каждый exploration observer независимо проверяет каждого живого члена партии:

1. геометрическая видимость, двери и LOS;
2. если цель не скрыта — обычное визуальное обнаружение;
3. если цель скрыта — существующий `ExplorationStealthPerceptionSystem` сравнивает её собственный `stealth_total` с Восприятием наблюдателя;
4. активный Search работает только для конкретной ранее известной цели и имеет cooldown по паре `observer_id|target_id`.

Правила DC и дистанции не изменены. В частности, автоматическое приближение дистанции обнаружения 20→5 ft остаётся проектным house rule из AI/Stealth v2, а не официальным правилом D&D 5e.

## Target-specific memory

Память хранится отдельно:

- `observer_actor_id -> target_actor_id`;
- `squad_id -> target_actor_id` для разрешённого обмена sightings.

Запись содержит последнюю позицию, confidence, source (`visual`, `noise`, `combat_alert`) и последовательность. Обнаружение Ирины не создаёт запись о герое. Передача информации `vault_watch` также копирует только конкретный известный `target_actor_id`.

Persisted memory сериализует `Vector2` как числовые массивы, поэтому состояние совместимо с JSON save pipeline.

## Шум

Шаговый шум создаётся отдельно для каждого живого party target. Каждый noise event получает `source_actor_id`. NPC, который действительно услышал событие через существующий `StealthAlertSystem.actor_hears_noise`, запоминает позицию именно этого источника с пониженной confidence.

Существующий noise/room/door pipeline не заменён.

## Переход в бой

Если NPC обнаружил Ирину, а герой остаётся скрытым:

- скрытность снимается только с Ирины, если она была скрыта;
- target memory фиксирует Ирину;
- бой может начаться;
- hero exploration state не очищается;
- `_player_combat_state.hidden` сохраняется для героя;
- combat alert sync берёт `last_known_position` из последней target-specific memory наблюдателя и больше не записывает всем NPC текущую позицию героя автоматически.

Это устраняет прежний эффект «телепатического» раскрытия героя при обнаружении другого участника партии.

## Party follow

Существующий NavigationAgent/portal contract остаётся единственным follow pathfinder. Party Stealth v3 только добавляет защитный gate: когда лидер скрыт, а следующий waypoint видимого спутника находится в прямой зоне наблюдения NPC, follower удерживает позицию (`stealth_hold`) вместо автоматического выхода под обзор. Никакой телепортации или второго pathfinder нет.

Если сам follower уже скрыт, обычный path contract сохраняется.

## UI

Действие `СКРЫТЬСЯ` применяется к текущему exploration-controlled actor. В solo mode можно скрывать Ирину независимо от героя. HUD показывает только факт `СКРЫТ` для активного управляемого персонажа; внутренний числовой stealth total не раскрывается как диагностическая информация.

## Ограничения этапа

- система не выдаёт спутнику бесплатную Скрытность: каждый вход в hidden требует собственной проверки;
- fallback-модификатор будущего спутника — `get_exploration_stealth_modifier()`, а при отсутствии метода используется его Dexterity save modifier; полноценные skill proficiencies спутников можно подключить позже без изменения контракта;
- target-specific memory влияет на exploration alert/search и переход в бой; дальнейшая унификация всех combat-stealth реакций для нескольких управляемых персонажей остаётся отдельным этапом;
- состояние не вводит сетевой режим и не меняет save version.

## Проверки

`Validate Party Stealth v3` запускает Godot 4.7.1 Standard и проверяет:

- независимые hero/Irina/third-companion stealth states;
- target-specific observer memory;
- squad sharing без раскрытия соседней цели;
- JSON-safe persistence;
- actor-tagged noise;
- реальный `game.tscn` и переход в бой после обнаружения Ирины при скрытом герое;
- регрессии AI/Stealth v2, controllable ally, Targeting v3, Advanced Party Tactics и Coordination v1/v2.
