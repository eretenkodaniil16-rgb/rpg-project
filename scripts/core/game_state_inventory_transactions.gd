extends "res://scripts/core/game_state_stealth_alerts.gd"

signal inventory_transaction_reserved(transaction_id: String, item_id: String, quantity: int)
signal inventory_transaction_committed(transaction_id: String, item_id: String, quantity: int)
signal inventory_transaction_rolled_back(transaction_id: String, item_id: String, quantity: int)

const INVENTORY_TRANSACTION_SYSTEM_SCRIPT: Script = preload("res://scripts/systems/inventory_transaction_system.gd")

var _inventory_transactions: InventoryTransactionSystem = (
	INVENTORY_TRANSACTION_SYSTEM_SCRIPT.new() as InventoryTransactionSystem
)


func new_game() -> void:
	_inventory_transactions.clear()
	super.new_game()


func load_game() -> bool:
	_inventory_transactions.clear()
	return super.load_game()


func can_reserve_inventory_item(item_id: String, quantity: int = 1) -> bool:
	return _inventory_transactions.can_reserve(self, item_id, quantity)


func get_inventory_available_count(item_id: String) -> int:
	return _inventory_transactions.get_available_count(self, item_id)


func reserve_inventory_item(
	item_id: String,
	quantity: int = 1,
	reason_id: String = "",
	context: Dictionary = {}
) -> Dictionary:
	var result: Dictionary = _inventory_transactions.reserve(
		self,
		item_id,
		quantity,
		reason_id,
		context
	)
	if bool(result.get("success", false)):
		inventory_transaction_reserved.emit(
			str(result.get("transaction_id", "")),
			item_id,
			maxi(int(result.get("quantity", quantity)), 1)
		)
	return result


func commit_inventory_transaction(transaction_id: String, save_after: bool = false) -> Dictionary:
	var result: Dictionary = _inventory_transactions.commit(self, transaction_id, save_after)
	if bool(result.get("success", false)):
		inventory_transaction_committed.emit(
			transaction_id,
			str(result.get("item_id", "")),
			maxi(int(result.get("quantity", 1)), 1)
		)
	return result


func rollback_inventory_transaction(transaction_id: String) -> Dictionary:
	var result: Dictionary = _inventory_transactions.rollback(transaction_id)
	if bool(result.get("success", false)):
		inventory_transaction_rolled_back.emit(
			transaction_id,
			str(result.get("item_id", "")),
			maxi(int(result.get("quantity", 1)), 1)
		)
	return result


func clear_inventory_transactions() -> void:
	_inventory_transactions.clear()


func has_active_inventory_transactions() -> bool:
	return _inventory_transactions.has_active_transactions()


func get_active_inventory_transactions_for_testing() -> Array[Dictionary]:
	return _inventory_transactions.get_active_transactions()
