from __future__ import annotations

from pathlib import Path

MAIN_MENU_SCENE = Path("scenes/menus/main_menu.tscn")
SETTINGS_SCENE = Path("scenes/ui/main_menu_settings_panel.tscn")
MAIN_MENU_SCRIPT = Path("scripts/menus/main_menu.gd")
SETTINGS_SCRIPT = Path("scripts/ui/main_menu_settings_panel.gd")
SETTINGS_STORE = Path("scripts/settings/interface_settings_store.gd")
ATMOSPHERE_SCRIPT = Path("scripts/menus/main_menu_atmosphere.gd")
TITLE_GLOW_SCRIPT = Path("scripts/menus/main_menu_title_glow.gd")


def test_required_files_exist() -> None:
    for path in (
        MAIN_MENU_SCENE,
        SETTINGS_SCENE,
        MAIN_MENU_SCRIPT,
        SETTINGS_SCRIPT,
        SETTINGS_STORE,
        ATMOSPHERE_SCRIPT,
        TITLE_GLOW_SCRIPT,
    ):
        assert path.exists(), f"Missing required file: {path}"


def test_main_menu_exposes_settings_without_changing_continue_flow() -> None:
    scene = MAIN_MENU_SCENE.read_text(encoding="utf-8")
    script = MAIN_MENU_SCRIPT.read_text(encoding="utf-8")

    assert 'name="SettingsButton"' in scene
    assert 'text = "НАСТРОЙКИ"' in scene
    assert "res://scenes/ui/main_menu_settings_panel.tscn" in scene
    assert 'method="_on_settings_pressed"' in scene
    assert "_save_slots_panel.open_for_load()" in script
    assert "settings_panel.open()" in script
    assert "buttons.append(settings_button)" in script


def test_settings_panel_has_mobile_sized_controls_and_exact_labels() -> None:
    scene = SETTINGS_SCENE.read_text(encoding="utf-8")

    for label in (
        "НАСТРОЙКИ",
        "Общая громкость",
        "Музыка",
        "Уменьшение движения",
        "ПО УМОЛЧАНИЮ",
        "НАЗАД",
    ):
        assert label in scene

    assert scene.count("custom_minimum_size = Vector2(0, 62)") == 2
    assert "custom_minimum_size = Vector2(170, 54)" in scene
    assert scene.count("custom_minimum_size = Vector2(245, 56)") == 2
    assert 'max_value = 100.0' in scene
    assert scene.count("step = 1.0") == 2


def test_audio_settings_reuse_music_manager_contract() -> None:
    script = SETTINGS_SCRIPT.read_text(encoding="utf-8")

    assert 'get_node_or_null("/root/MusicManager")' in script
    assert '"get_bus_volume_linear"' in script
    assert '"set_bus_volume_linear"' in script
    assert 'const MASTER_BUS: StringName = &"Master"' in script
    assert 'const MUSIC_BUS: StringName = &"Music"' in script
    assert "AudioServer" not in script


def test_reduced_motion_is_persistent_and_applied_live() -> None:
    store = SETTINGS_STORE.read_text(encoding="utf-8")
    menu = MAIN_MENU_SCRIPT.read_text(encoding="utf-8")
    atmosphere = ATMOSPHERE_SCRIPT.read_text(encoding="utf-8")
    title_glow = TITLE_GLOW_SCRIPT.read_text(encoding="utf-8")

    assert 'SETTINGS_PATH: String = "user://interface_settings.cfg"' in store
    assert 'REDUCED_MOTION_KEY: String = "reduced_motion"' in store
    assert 'REDUCED_MOTION_PROJECT_SETTING: String = "accessibility/reduced_motion"' in store
    assert "settings.save(SETTINGS_PATH)" in store
    assert "InterfaceSettingsStore.load_and_apply()" in menu
    assert "atmosphere.set_reduced_motion(enabled)" in menu
    assert "title_glow.set_reduced_motion(enabled)" in menu
    assert "func set_reduced_motion(enabled: bool) -> void:" in atmosphere
    assert "func set_reduced_motion(enabled: bool) -> void:" in title_glow
