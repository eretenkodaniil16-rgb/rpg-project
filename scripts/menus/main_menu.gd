extends Control

const GAME_SCENE: String = "res://scenes/game/game.tscn"

@onready var continue_button: Button = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/ContinueButton
@onready var status_label: Label = $CenterContainer/MenuPanel/MarginContainer/VBoxContainer/StatusLabel


func _ready() -> void:
	continue_button.disabled = not GameState.has_save()
	status_label.text = "Найдена сохранённая игра." if GameState.has_save() else "Сохранение пока не создано."


func _on_new_game_pressed() -> void:
	GameState.new_game()
	GameState.save_game()
	get_tree().change_scene_to_file(GAME_SCENE)


func _on_continue_pressed() -> void:
	if GameState.load_game():
		get_tree().change_scene_to_file(GAME_SCENE)
	else:
		status_label.text = "Не удалось загрузить сохранение."
		continue_button.disabled = true


func _on_quit_pressed() -> void:
	get_tree().quit()
