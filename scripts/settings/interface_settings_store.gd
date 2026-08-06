class_name InterfaceSettingsStore
extends RefCounted

const SETTINGS_PATH: String = "user://interface_settings.cfg"
const ACCESSIBILITY_SECTION: String = "accessibility"
const REDUCED_MOTION_KEY: String = "reduced_motion"
const REDUCED_MOTION_PROJECT_SETTING: String = "accessibility/reduced_motion"
const DEFAULT_REDUCED_MOTION: bool = false


static func load_and_apply() -> bool:
	var reduced_motion: bool = bool(
		ProjectSettings.get_setting(
			REDUCED_MOTION_PROJECT_SETTING,
			DEFAULT_REDUCED_MOTION
		)
	)
	var settings: ConfigFile = ConfigFile.new()
	var load_error: Error = settings.load(SETTINGS_PATH)
	if load_error == OK:
		reduced_motion = bool(
			settings.get_value(
				ACCESSIBILITY_SECTION,
				REDUCED_MOTION_KEY,
				reduced_motion
			)
		)
	ProjectSettings.set_setting(REDUCED_MOTION_PROJECT_SETTING, reduced_motion)
	return reduced_motion


static func is_reduced_motion_enabled() -> bool:
	return bool(
		ProjectSettings.get_setting(
			REDUCED_MOTION_PROJECT_SETTING,
			DEFAULT_REDUCED_MOTION
		)
	)


static func set_reduced_motion_enabled(enabled: bool) -> Error:
	ProjectSettings.set_setting(REDUCED_MOTION_PROJECT_SETTING, enabled)
	var settings: ConfigFile = ConfigFile.new()
	var load_error: Error = settings.load(SETTINGS_PATH)
	if load_error != OK and load_error != ERR_FILE_NOT_FOUND:
		push_warning(
			"Не удалось прочитать интерфейсные настройки перед сохранением: %s"
			% error_string(load_error)
		)
	settings.set_value(ACCESSIBILITY_SECTION, REDUCED_MOTION_KEY, enabled)
	return settings.save(SETTINGS_PATH)
