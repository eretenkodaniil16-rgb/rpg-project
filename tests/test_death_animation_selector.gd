extends SceneTree

const SELECTOR_SCRIPT: Script = preload("res://scripts/systems/death_animation_selector.gd")

var _failed: bool = false


func _init() -> void:
	var selector: DeathAnimationSelector = SELECTOR_SCRIPT.new(17) as DeathAnimationSelector
	var entries: Array[Dictionary] = [
		{"death_variant_id": "death_01_base", "set_id": "death_01_base", "weight": 1.0},
		{"death_variant_id": "death_02_base", "set_id": "death_02_base", "weight": 1.0},
		{"death_variant_id": "death_03_base", "set_id": "death_03_base", "weight": 1.0}
	]

	_expect(
		selector.select_variant(entries, "", 0.0) == "death_01_base",
		"Equal-weight roll 0.0 must select death_01_base."
	)
	_expect(
		selector.select_variant(entries, "", 0.34) == "death_02_base",
		"Equal-weight middle roll must select death_02_base."
	)
	_expect(
		selector.select_variant(entries, "", 0.99) == "death_03_base",
		"Equal-weight high roll must select death_03_base."
	)
	_expect(
		selector.select_variant(entries, "death_01_base", 0.0) == "death_02_base",
		"Immediate repetition was not removed from the candidate pool."
	)
	_expect(
		selector.select_variant(entries, "death_01_base", 0.99) == "death_03_base",
		"No-repeat selection did not retain all other variants."
	)
	for previous_variant_id: String in ["death_01_base", "death_02_base", "death_03_base"]:
		for roll: float in [0.0, 0.25, 0.50, 0.75, 0.99]:
			_expect(
				selector.select_variant(entries, previous_variant_id, roll) != previous_variant_id,
				"Selector immediately repeated %s." % previous_variant_id
			)

	var weighted_entries: Array[Dictionary] = [
		{"death_variant_id": "light", "set_id": "light", "weight": 1.0},
		{"death_variant_id": "heavy", "set_id": "heavy", "weight": 3.0}
	]
	_expect(
		selector.select_variant(weighted_entries, "", 0.24) == "light",
		"Weighted lower quartile did not select the light entry."
	)
	_expect(
		selector.select_variant(weighted_entries, "", 0.25) == "heavy",
		"Weighted threshold did not select the heavy entry."
	)

	_expect(
		selector.resolve_available_variant("missing", entries) == "death_01_base",
		"Unavailable persisted variant did not fall back to death_01_base."
	)
	var entries_without_fallback: Array[Dictionary] = [entries[1], entries[2]]
	_expect(
		selector.resolve_available_variant("missing", entries_without_fallback).is_empty(),
		"Missing requested and fallback variants must request the static visual fallback."
	)
	var invalid_entries: Array[Dictionary] = [
		{"death_variant_id": "", "set_id": "bad", "weight": 1.0},
		{"death_variant_id": "zero", "set_id": "zero", "weight": 0.0}
	]
	_expect(
		selector.select_variant(invalid_entries).is_empty(),
		"Invalid selector entries were not rejected."
	)

	_test_player_character_persistence()
	if _failed:
		quit(1)
		return
	print("Death animation selector and persistence tests passed.")
	quit(0)


func _test_player_character_persistence() -> void:
	var character := PlayerCharacter.new()
	character.maximum_health = 12
	character.current_health = 0
	character.last_death_variant_id = "death_03_base"
	character.death_visual_state = {
		"death_variant_id": "death_03_base",
		"direction_id": "up",
		"corpse_state": "corpse_hold",
		"frame_index": 7
	}
	var restored := PlayerCharacter.from_dict(character.to_dict())
	_expect(
		restored.last_death_variant_id == "death_03_base",
		"Last death variant was not serialized."
	)
	_expect(
		restored.death_visual_state == character.death_visual_state,
		"Corpse visual state did not survive serialization."
	)

	var old_save := PlayerCharacter.from_dict({
		"name": "Старое сохранение",
		"maximum_health": 12,
		"current_health": 0
	})
	_expect(
		old_save.last_death_variant_id.is_empty() and old_save.death_visual_state.is_empty(),
		"Legacy save without death fields did not receive safe defaults."
	)
	var living_save: Dictionary = character.to_dict()
	living_save["current_health"] = 1
	var living := PlayerCharacter.from_dict(living_save)
	_expect(
		living.death_visual_state.is_empty(),
		"A living character retained stale corpse visual state."
	)


func _expect(condition: bool, message: String) -> void:
	if condition:
		return
	push_error(message)
	_failed = true
