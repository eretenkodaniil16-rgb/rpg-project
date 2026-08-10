extends Node

signal transition_started(target_path: String)
signal transition_progress(target_path: String, progress: float)
signal transition_completed(target_path: String)
signal transition_failed(target_path: String, reason: String)

const LOADING_SCREEN_SCENE: PackedScene = preload("res://scenes/menus/loading_screen_visual_v02.tscn")
const DEFAULT_MINIMUM_VISIBLE_SECONDS: float = 0.35
const TARGET_TYPE_HINT: String = "PackedScene"

enum TransitionState {
	IDLE,
	LOADING,
	READY_TO_SWITCH,
}

var _state: TransitionState = TransitionState.IDLE
var _target_path: String = ""
var _minimum_visible_seconds: float = DEFAULT_MINIMUM_VISIBLE_SECONDS
var _started_at_msec: int = 0
var _loading_screen: CanvasLayer = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(false)


func _process(_delta: float) -> void:
	if _state == TransitionState.IDLE or _target_path.is_empty():
		set_process(false)
		return

	if _state == TransitionState.READY_TO_SWITCH:
		if _minimum_visibility_elapsed():
			_commit_loaded_scene()
		return

	var progress: Array = []
	var status: ResourceLoader.ThreadLoadStatus = ResourceLoader.load_threaded_get_status(_target_path, progress)
	var ratio: float = _progress_ratio(progress)
	_set_loading_progress(ratio)
	transition_progress.emit(_target_path, ratio)

	match status:
		ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			return
		ResourceLoader.THREAD_LOAD_LOADED:
			_set_loading_progress(1.0)
			transition_progress.emit(_target_path, 1.0)
			_state = TransitionState.READY_TO_SWITCH
			if _minimum_visibility_elapsed():
				_commit_loaded_scene()
		ResourceLoader.THREAD_LOAD_FAILED:
			_fail_transition("Не удалось загрузить сцену в фоновом потоке.")
		ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			_fail_transition("Ресурс сцены недействителен или загрузка не была запущена.")


func request_scene(target_path: String, minimum_visible_seconds: float = DEFAULT_MINIMUM_VISIBLE_SECONDS) -> bool:
	if is_busy():
		return false
	if target_path.is_empty() or not ResourceLoader.exists(target_path, TARGET_TYPE_HINT):
		transition_failed.emit(target_path, "Сцена не найдена: %s" % target_path)
		return false

	_target_path = target_path
	_minimum_visible_seconds = maxf(minimum_visible_seconds, 0.0)
	_started_at_msec = Time.get_ticks_msec()
	_show_loading_screen()

	var error: Error = ResourceLoader.load_threaded_request(
		target_path,
		TARGET_TYPE_HINT,
		false,
		ResourceLoader.CACHE_MODE_REUSE
	)
	if error != OK:
		_fail_transition("Не удалось запустить фоновую загрузку: %s" % error_string(error))
		return false

	_state = TransitionState.LOADING
	set_process(true)
	transition_started.emit(target_path)
	return true


func is_busy() -> bool:
	return _state != TransitionState.IDLE


func current_target_path() -> String:
	return _target_path


func cancel_overlay_for_test() -> void:
	_cleanup_transition()


func _show_loading_screen() -> void:
	if is_instance_valid(_loading_screen):
		_loading_screen.queue_free()
	_loading_screen = LOADING_SCREEN_SCENE.instantiate() as CanvasLayer
	if _loading_screen == null:
		return
	_loading_screen.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_loading_screen)
	if _loading_screen.has_method("set_progress"):
		_loading_screen.call("set_progress", 0.0)
	if _loading_screen.has_method("set_status_text"):
		_loading_screen.call("set_status_text", "Загрузка...")


func _commit_loaded_scene() -> void:
	if _state != TransitionState.READY_TO_SWITCH or _target_path.is_empty():
		return
	var completed_path: String = _target_path
	var resource: Resource = ResourceLoader.load_threaded_get(completed_path)
	if not resource is PackedScene:
		_fail_transition("Загруженный ресурс не является PackedScene.")
		return
	var packed_scene: PackedScene = resource as PackedScene
	var error: Error = get_tree().change_scene_to_packed(packed_scene)
	if error != OK:
		_fail_transition("Не удалось переключить сцену: %s" % error_string(error))
		return
	_cleanup_transition()
	transition_completed.emit(completed_path)


func _fail_transition(reason: String) -> void:
	var failed_path: String = _target_path
	push_error("SceneTransitionManager: %s Target: %s" % [reason, failed_path])
	if is_instance_valid(_loading_screen) and _loading_screen.has_method("set_status_text"):
		_loading_screen.call("set_status_text", "Ошибка загрузки")
	_cleanup_transition()
	transition_failed.emit(failed_path, reason)


func _cleanup_transition() -> void:
	set_process(false)
	_state = TransitionState.IDLE
	_target_path = ""
	_minimum_visible_seconds = DEFAULT_MINIMUM_VISIBLE_SECONDS
	_started_at_msec = 0
	if is_instance_valid(_loading_screen):
		_loading_screen.queue_free()
	_loading_screen = null


func _minimum_visibility_elapsed() -> bool:
	if _started_at_msec <= 0:
		return true
	return float(Time.get_ticks_msec() - _started_at_msec) / 1000.0 >= _minimum_visible_seconds


func _progress_ratio(progress: Array) -> float:
	if progress.is_empty():
		return 0.0
	return clampf(float(progress[0]), 0.0, 1.0)


func _set_loading_progress(ratio: float) -> void:
	if is_instance_valid(_loading_screen) and _loading_screen.has_method("set_progress"):
		_loading_screen.call("set_progress", clampf(ratio, 0.0, 1.0) * 100.0)
