class_name MainMenuSettingsPanel
extends Control

signal closed
signal reduced_motion_changed(enabled: bool)

const MASTER_BUS: StringName = &"Master"
const MUSIC_BUS: StringName = &"Music"
const DEFAULT_MASTER_PERCENT: float = 100.0
const DEFAULT_MUSIC_PERCENT: float = 80.0

@onready var master_volume_slider: HSlider = %MasterVolumeSlider
@onready var master_volume_value: Label = %MasterVolumeValue
@onready var music_volume_slider: HSlider = %MusicVolumeSlider
@onready var music_volume_value: Label = %MusicVolumeValue
@onready var reduced_motion_toggle: CheckButton = %ReducedMotionToggle
@onready var reset_button: Button = %ResetButton
@onready var back_button: Button = %BackButton

var _syncing_controls: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	set_process_unhandled_input(false)


func open() -> void:
	_sync_controls_from_settings()
	visible = true
	set_process_unhandled_input(true)
	call_deferred("_focus_first_control")


func close() -> void:
	if not visible:
		return
	visible = false
	set_process_unhandled_input(false)
	closed.emit()


func is_open() -> bool:
	return visible


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not event.is_action_pressed("ui_cancel"):
		return
	get_viewport().set_input_as_handled()
	close()


func _sync_controls_from_settings() -> void:
	_syncing_controls = true
	var music_manager: Node = _music_manager()
	if music_manager != null:
		master_volume_slider.value = _read_bus_percent(
			music_manager,
			MASTER_BUS,
			DEFAULT_MASTER_PERCENT
		)
		music_volume_slider.value = _read_bus_percent(
			music_manager,
			MUSIC_BUS,
			DEFAULT_MUSIC_PERCENT
		)
	else:
		master_volume_slider.value = DEFAULT_MASTER_PERCENT
		music_volume_slider.value = DEFAULT_MUSIC_PERCENT
	reduced_motion_toggle.button_pressed = InterfaceSettingsStore.is_reduced_motion_enabled()
	_update_volume_label(master_volume_value, master_volume_slider.value)
	_update_volume_label(music_volume_value, music_volume_slider.value)
	_update_reduced_motion_text(reduced_motion_toggle.button_pressed)
	_syncing_controls = false


func _read_bus_percent(
	music_manager: Node,
	bus_name: StringName,
	fallback_percent: float
) -> float:
	if not music_manager.has_method("get_bus_volume_linear"):
		return fallback_percent
	return clampf(
		float(music_manager.call("get_bus_volume_linear", bus_name)) * 100.0,
		0.0,
		100.0
	)


func _write_bus_percent(bus_name: StringName, percent: float) -> void:
	var music_manager: Node = _music_manager()
	if music_manager == null or not music_manager.has_method("set_bus_volume_linear"):
		push_warning("MusicManager недоступен: громкость не сохранена.")
		return
	var success: bool = bool(
		music_manager.call(
			"set_bus_volume_linear",
			bus_name,
			clampf(percent / 100.0, 0.0, 1.0),
			true
		)
	)
	if not success:
		push_warning("Не удалось применить громкость шины %s." % String(bus_name))


func _music_manager() -> Node:
	return get_node_or_null("/root/MusicManager")


func _update_volume_label(label: Label, percent: float) -> void:
	label.text = "%d%%" % roundi(percent)


func _update_reduced_motion_text(enabled: bool) -> void:
	reduced_motion_toggle.text = "ВКЛЮЧЕНО" if enabled else "ВЫКЛЮЧЕНО"


func _focus_first_control() -> void:
	if visible and is_instance_valid(master_volume_slider):
		master_volume_slider.grab_focus()


func _on_master_volume_changed(value: float) -> void:
	_update_volume_label(master_volume_value, value)
	if not _syncing_controls:
		_write_bus_percent(MASTER_BUS, value)


func _on_music_volume_changed(value: float) -> void:
	_update_volume_label(music_volume_value, value)
	if not _syncing_controls:
		_write_bus_percent(MUSIC_BUS, value)


func _on_reduced_motion_toggled(enabled: bool) -> void:
	_update_reduced_motion_text(enabled)
	if _syncing_controls:
		return
	var save_error: Error = InterfaceSettingsStore.set_reduced_motion_enabled(enabled)
	if save_error != OK:
		push_warning(
			"Не удалось сохранить настройку уменьшения движения: %s"
			% error_string(save_error)
		)
	reduced_motion_changed.emit(enabled)


func _on_reset_pressed() -> void:
	master_volume_slider.value = DEFAULT_MASTER_PERCENT
	music_volume_slider.value = DEFAULT_MUSIC_PERCENT
	reduced_motion_toggle.button_pressed = InterfaceSettingsStore.DEFAULT_REDUCED_MOTION
	_write_bus_percent(MASTER_BUS, DEFAULT_MASTER_PERCENT)
	_write_bus_percent(MUSIC_BUS, DEFAULT_MUSIC_PERCENT)
	var save_error: Error = InterfaceSettingsStore.set_reduced_motion_enabled(
		InterfaceSettingsStore.DEFAULT_REDUCED_MOTION
	)
	if save_error != OK:
		push_warning(
			"Не удалось сохранить настройки по умолчанию: %s"
			% error_string(save_error)
		)
	_update_reduced_motion_text(InterfaceSettingsStore.DEFAULT_REDUCED_MOTION)
	reduced_motion_changed.emit(InterfaceSettingsStore.DEFAULT_REDUCED_MOTION)


func _on_back_pressed() -> void:
	close()
