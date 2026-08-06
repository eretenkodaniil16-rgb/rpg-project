extends SceneTree


class TestCharacter:
	extends RefCounted

	var current_health: int = 3
	var maximum_health: int = 12


class TestState:
	extends Node

	var player_character: TestCharacter = TestCharacter.new()
	var definitions: Dictionary = {}
	var counts: Dictionary = {}
	var flags: Dictionary = {}
	var transactions: InventoryTransactionSystem = InventoryTransactionSystem.new()

	func get_item_definition(item_id: String) -> Dictionary:
		var value: Variant = definitions.get(item_id, {})
		return (value as Dictionary).duplicate(true) if value is Dictionary else {}

	func get_item_count(item_id: String) -> int:
		return maxi(int(counts.get(item_id, 0)), 0)

	func remove_item(item_id: String, quantity: int = 1, _save_after: bool = false) -> bool:
		if quantity <= 0 or get_item_count(item_id) < quantity:
			return false
		var updated: int = get_item_count(item_id) - quantity
		if updated <= 0:
			counts.erase(item_id)
		else:
			counts[item_id] = updated
		return true

	func reserve_inventory_item(item_id: String, quantity: int = 1, reason_id: String = "", context: Dictionary = {}) -> Dictionary:
		return transactions.reserve(self, item_id, quantity, reason_id, context)

	func commit_inventory_transaction(transaction_id: String, save_after: bool = false) -> Dictionary:
		return transactions.commit(self, transaction_id, save_after)

	func rollback_inventory_transaction(transaction_id: String) -> Dictionary:
		return transactions.rollback(transaction_id)

	func set_flag(flag_id: String, value: Variant = true) -> void:
		flags[flag_id] = value


class DyingTarget:
	extends Node

	var dying: bool = true
	var stabilized: bool = false

	func can_be_stabilized_with_healers_kit() -> bool:
		return dying and not stabilized

	func stabilize_with_healers_kit() -> Dictionary:
		if not can_be_stabilized_with_healers_kit():
			return {"success": false, "message": "Цель не нуждается в стабилизации."}
		dying = false
		stabilized = true
		return {"success": true, "message": "Цель стабилизирована."}


func _init() -> void:
	var state := TestState.new()
	state.definitions = _load_definitions()
	state.counts = {
		"potion_of_healing": 2,
		"healers_kit": 1,
		"caretaker_field_note": 1
	}
	var system := ItemUseSystem.new()

	var potion: Dictionary = state.get_item_definition("potion_of_healing")
	assert(system.has_use_action(potion))
	assert(system.get_inventory_label(potion) == "ВЫПИТЬ")
	assert(system.build_action_label(potion) == "ВЫПИТЬ: ЗЕЛЬЕ ЛЕЧЕНИЯ")

	var prepared_potion: Dictionary = system.prepare_use(state, "potion_of_healing")
	assert(bool(prepared_potion.get("success", false)))
	assert(state.get_item_count("potion_of_healing") == 2)
	assert(state.transactions.get_available_count(state, "potion_of_healing") == 1)
	var potion_result: Dictionary = system.execute_prepared_use(
		state,
		prepared_potion,
		null,
		{"healing_roll_override": 7}
	)
	assert(bool(potion_result.get("success", false)))
	assert(int(potion_result.get("amount", 0)) == 7)
	assert(state.player_character.current_health == 10)
	assert(state.get_item_count("potion_of_healing") == 1)

	state.player_character.current_health = state.player_character.maximum_health
	var full_health: Dictionary = system.prepare_use(state, "potion_of_healing")
	assert(not bool(full_health.get("success", false)))
	assert(state.get_item_count("potion_of_healing") == 1)

	state.player_character.current_health = 6
	var cancelled: Dictionary = system.prepare_use(state, "potion_of_healing")
	assert(bool(cancelled.get("success", false)))
	system.cancel_prepared_use(state, cancelled)
	assert(state.get_item_count("potion_of_healing") == 1)
	assert(not state.transactions.has_active_transactions())

	var dying_target := DyingTarget.new()
	var prepared_kit: Dictionary = system.prepare_use(state, "healers_kit", dying_target)
	assert(bool(prepared_kit.get("success", false)))
	var kit_result: Dictionary = system.execute_prepared_use(state, prepared_kit, dying_target)
	assert(bool(kit_result.get("success", false)))
	assert(dying_target.stabilized)
	assert(state.get_item_count("healers_kit") == 0)
	var repeated_kit: Dictionary = system.prepare_use(state, "healers_kit", dying_target)
	assert(not bool(repeated_kit.get("success", false)))

	var prepared_note: Dictionary = system.prepare_use(state, "caretaker_field_note")
	assert(bool(prepared_note.get("success", false)))
	var note_result: Dictionary = system.execute_prepared_use(state, prepared_note)
	assert(bool(note_result.get("success", false)))
	assert(bool(state.flags.get("caretaker_field_note_read", false)))
	assert(state.get_item_count("caretaker_field_note") == 1)

	dying_target.free()
	state.free()
	print("Item use preparation, rollback, healing, stabilization and story flag tests passed.")
	quit(0)


func _load_definitions() -> Dictionary:
	var file: FileAccess = FileAccess.open("res://data/items/item_use_definitions.json", FileAccess.READ)
	assert(file != null)
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	assert(parsed is Dictionary)
	return parsed as Dictionary
