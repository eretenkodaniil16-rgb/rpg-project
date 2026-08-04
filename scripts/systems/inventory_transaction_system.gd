class_name InventoryTransactionSystem
extends RefCounted

const STATUS_RESERVED: String = "reserved"
const STATUS_COMMITTED: String = "committed"
const STATUS_ROLLED_BACK: String = "rolled_back"

var _transactions: Dictionary = {}
var _sequence: int = 0


func can_reserve(state: Node, item_id: String, quantity: int = 1) -> bool:
	if state == null or item_id.is_empty() or quantity <= 0:
		return false
	if not state.has_method("get_item_count"):
		return false
	return get_available_count(state, item_id) >= quantity


func get_available_count(state: Node, item_id: String) -> int:
	if state == null or item_id.is_empty() or not state.has_method("get_item_count"):
		return 0
	var current: int = maxi(int(state.call("get_item_count", item_id)), 0)
	return maxi(current - _reserved_quantity(item_id), 0)


func reserve(
	state: Node,
	item_id: String,
	quantity: int = 1,
	reason_id: String = "",
	context: Dictionary = {}
) -> Dictionary:
	var safe_quantity: int = maxi(quantity, 1)
	if not can_reserve(state, item_id, safe_quantity):
		return {
			"success": false,
			"transaction_id": "",
			"item_id": item_id,
			"quantity": safe_quantity,
			"available": get_available_count(state, item_id),
			"status": "rejected"
		}
	_sequence += 1
	var transaction_id: String = "%s:%d:%d" % [
		item_id,
		Time.get_ticks_usec(),
		_sequence
	]
	var transaction: Dictionary = {
		"transaction_id": transaction_id,
		"item_id": item_id,
		"quantity": safe_quantity,
		"reason_id": reason_id,
		"context": context.duplicate(true),
		"status": STATUS_RESERVED
	}
	_transactions[transaction_id] = transaction
	var result: Dictionary = transaction.duplicate(true)
	result["success"] = true
	result["available"] = get_available_count(state, item_id)
	return result


func commit(state: Node, transaction_id: String, save_after: bool = false) -> Dictionary:
	var transaction: Dictionary = get_transaction(transaction_id)
	if transaction.is_empty() or str(transaction.get("status", "")) != STATUS_RESERVED:
		return {"success": false, "transaction_id": transaction_id, "status": "missing"}
	if state == null or not state.has_method("remove_item"):
		_transactions.erase(transaction_id)
		return {"success": false, "transaction_id": transaction_id, "status": "invalid_state"}
	var item_id: String = str(transaction.get("item_id", ""))
	var quantity: int = maxi(int(transaction.get("quantity", 1)), 1)
	var removed: bool = bool(state.call("remove_item", item_id, quantity, save_after))
	_transactions.erase(transaction_id)
	transaction["status"] = STATUS_COMMITTED if removed else STATUS_ROLLED_BACK
	var result: Dictionary = transaction.duplicate(true)
	result["success"] = removed
	return result


func rollback(transaction_id: String) -> Dictionary:
	var transaction: Dictionary = get_transaction(transaction_id)
	if transaction.is_empty() or str(transaction.get("status", "")) != STATUS_RESERVED:
		return {"success": false, "transaction_id": transaction_id, "status": "missing"}
	_transactions.erase(transaction_id)
	transaction["status"] = STATUS_ROLLED_BACK
	var result: Dictionary = transaction.duplicate(true)
	result["success"] = true
	return result


func clear() -> void:
	_transactions.clear()


func has_active_transactions() -> bool:
	return not _transactions.is_empty()


func get_transaction(transaction_id: String) -> Dictionary:
	var value: Variant = _transactions.get(transaction_id, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else {}


func get_active_transactions() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for value: Variant in _transactions.values():
		if value is Dictionary:
			result.append((value as Dictionary).duplicate(true))
	return result


func _reserved_quantity(item_id: String) -> int:
	var total: int = 0
	for value: Variant in _transactions.values():
		if not value is Dictionary:
			continue
		var transaction: Dictionary = value as Dictionary
		if str(transaction.get("status", "")) != STATUS_RESERVED:
			continue
		if str(transaction.get("item_id", "")) == item_id:
			total += maxi(int(transaction.get("quantity", 0)), 0)
	return total
