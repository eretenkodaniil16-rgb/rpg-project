from __future__ import annotations

from pathlib import Path

GAME_SCENE = Path("scenes/game/game.tscn")
PAUSE_SCENE = Path("scenes/ui/in_game_pause_menu.tscn")
PAUSE_SCRIPT = Path("scripts/ui/in_game_pause_menu.gd")
CONTROLLER_SCRIPT = Path("scripts/game/in_game_pause_controller.gd")
MOBILE_CONTROLS_SCRIPT = Path("scripts/ui/mobile_controls.gd")
SHARED_SETTINGS_SCENE = Path("scenes/ui/main_menu_settings_panel.tscn")


def test_required_files_exist() -> None:
    for path in (
        GAME_SCENE,
        PAUSE_SCENE,
        PAUSE_SCRIPT,
        CONTROLLER_SCRIPT,
        MOBILE_CONTROLS_SCRIPT,
        SHARED_SETTINGS_SCENE,
    ):
        assert path.exists(), f"Missing required file: {path}"


def test_pause_scene_reuses_shared_settings_and_mobile_sized_buttons() -> None:
    scene = PAUSE_SCENE.read_text(encoding="utf-8")

    assert "res://scenes/ui/main_menu_settings_panel.tscn" in scene
    for label in ("П А У З А", "ПРОДОЛЖИТЬ", "НАСТРОЙКИ", "В ГЛАВНОЕ МЕНЮ"):
        assert label in scene
    assert scene.count("custom_minimum_size = Vector2(0, 64)") == 3
    assert "process_mode = 3" in scene
    assert 'name="SettingsPanel"' in scene


def test_game_keeps_existing_runtime_and_installs_modular_pause_controller() -> None:
    scene = GAME_SCENE.read_text(encoding="utf-8")

    assert "res://scripts/game/game_guard_post_polish_runtime.gd" in scene
    assert "res://scripts/game/in_game_pause_controller.gd" in scene
    assert 'name="InGamePauseController"' in scene
    assert 'groups=["pause_menu_controller"]' in scene
    assert "process_mode = 3" in scene


def test_controller_owns_pause_and_preserves_existing_return_contract() -> None:
    controller = CONTROLLER_SCRIPT.read_text(encoding="utf-8")

    assert "get_tree().paused = true" in controller
    assert "_owns_tree_pause" in controller
    assert "tree.paused = false" in controller
    assert 'has_method("return_to_menu")' in controller
    assert '_game_world.call("return_to_menu")' in controller
    assert "release_all_input" in controller
    assert "GameState.save_game" not in controller


def test_mobile_menu_uses_pause_with_safe_legacy_fallback() -> None:
    controls = MOBILE_CONTROLS_SCRIPT.read_text(encoding="utf-8")

    toggle_position = controls.index('has_method("toggle_pause_menu")')
    fallback_position = controls.index('has_method("return_to_menu")')
    assert toggle_position < fallback_position
    assert 'get_first_node_in_group("pause_menu_controller")' in controls
    assert "func release_all_input() -> void:" in controls


def test_pause_menu_routes_back_through_resume_and_nested_settings() -> None:
    script = PAUSE_SCRIPT.read_text(encoding="utf-8")

    assert "func handle_cancel() -> bool:" in script
    assert "settings_panel.close()" in script
    assert "resume_requested.emit()" in script
    assert "settings_panel.open()" in script
    assert "process_mode = Node.PROCESS_MODE_ALWAYS" in script
