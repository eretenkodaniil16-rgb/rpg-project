extends "res://scripts/game/game_party_navigation_follow_runtime.gd"


func _restore_target_for_active_actor() -> void:
	var actor: Node = _party_control_context.active_actor()
	if not is_instance_valid(actor):
		return
	var remembered_target: Node = _party_control_context.target_for(actor)
	if _target_is_valid(remembered_target):
		_set_selected_target(remembered_target)
	else:
		# Потеря прямой видимости временно запрещает действие по цели, но не должна
		# стирать отдельный выбор персонажа. Цель восстановится, когда снова станет
		# доступна, либо будет заменена игроком через кнопку выбора цели.
		_set_selected_target(null)
	_update_target_label()
