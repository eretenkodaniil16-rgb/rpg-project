class_name InGamePauseMenu
extends Control

signal resume_requested
signal return_to_menu_requested

@onready var resume_button: Button = $CenterContainer/PausePanel/Margin/Content/ResumeButton
@onready var settings_button: Button = $CenterContainer/PausePanel/Margin/Content/SettingsButton
@onready var return_to_menu_button: Button = $CenterContainer/PausePanel/Margin/Content/ReturnToMenuButton
@onready var settings_panel: MainMenuSettingsPanel = $SettingsPanel


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_STOP
	if not settings_panel.closed.is_connected(_on_settings_closed):
		settings_panel.closed.connect(_on_settings_closed)
	_set_pause_focus_enabled(true)


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not event.is_action_pressed("ui_cancel"):
		return
	if handle_cancel():
		get_viewport().set_input_as_handled()


func open() -> void:
	if settings_panel.is_open():
		settings_panel.close()
	return_to_menu_button.disabled = false
	_set_pause_focus_enabled(true)
	show()
	resume_button.grab_focus()


func close() -> void:
	if settings_panel.is_open():
		settings_panel.close()
	hide()


func is_open() -> bool:
	return visible


func is_settings_open() -> bool:
	return settings_panel.is_open()


func open_settings() -> void:
	if not visible or settings_panel.is_open():
		return
	_set_pause_focus_enabled(false)
	settings_panel.open()


func handle_cancel() -> bool:
	if not visible:
		return false
	if settings_panel.is_open():
		settings_panel.close()
		return true
	resume_requested.emit()
	return true


func get_settings_panel_for_testing() -> MainMenuSettingsPanel:
	return settings_panel


func _on_resume_pressed() -> void:
	resume_requested.emit()


func _on_settings_pressed() -> void:
	open_settings()


func _on_return_to_menu_pressed() -> void:
	return_to_menu_button.disabled = true
	return_to_menu_requested.emit()


func _on_settings_closed() -> void:
	if not visible:
		return
	_set_pause_focus_enabled(true)
	settings_button.grab_focus()


func _set_pause_focus_enabled(enabled: bool) -> void:
	var focus_mode: Control.FocusMode = Control.FOCUS_ALL if enabled else Control.FOCUS_NONE
	for button: Button in _pause_buttons():
		button.focus_mode = focus_mode


func _pause_buttons() -> Array[Button]:
	return [resume_button, settings_button, return_to_menu_button]
