extends SceneTree


class InventoryState:
	extends Node

	var counts: Dictionary = {}

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


func _init() -> void:
	var state := InventoryState.new()
	state.counts = {"arrow": 2, "javelin": 1}
	var transactions := InventoryTransactionSystem.new()

	assert(transactions.get_available_count(state, "arrow") == 2)
	var first: Dictionary = transactions.reserve(state, "arrow", 1, "test_shot")
	assert(bool(first.get("success", false)))
	assert(state.get_item_count("arrow") == 2)
	assert(transactions.get_available_count(state, "arrow") == 1)

	var overbooked: Dictionary = transactions.reserve(state, "arrow", 2, "duplicate_shot")
	assert(not bool(overbooked.get("success", false)))
	assert(transactions.get_active_transactions().size() == 1)

	var rollback: Dictionary = transactions.rollback(str(first.get("transaction_id", "")))
	assert(bool(rollback.get("success", false)))
	assert(state.get_item_count("arrow") == 2)
	assert(transactions.get_available_count(state, "arrow") == 2)

	var committed_reservation: Dictionary = transactions.reserve(state, "arrow", 2, "confirmed_volley")
	assert(bool(committed_reservation.get("success", false)))
	var commit: Dictionary = transactions.commit(
		state,
		str(committed_reservation.get("transaction_id", "")),
		false
	)
	assert(bool(commit.get("success", false)))
	assert(state.get_item_count("arrow") == 0)
	assert(not transactions.has_active_transactions())

	var thrown: Dictionary = transactions.reserve(state, "javelin", 1, "confirmed_throw")
	assert(bool(thrown.get("success", false)))
	assert(transactions.can_reserve(state, "javelin", 1) == false)
	assert(bool(transactions.commit(state, str(thrown.get("transaction_id", "")), false).get("success", false)))
	assert(state.get_item_count("javelin") == 0)

	print("Inventory reservation, rollback, commit and overbooking tests passed.")
	quit(0)
