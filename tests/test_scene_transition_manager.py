from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    project = text("project.godot")
    manager = text("scripts/systems/scene_transition_manager.gd")
    main_menu = text("scripts/menus/main_menu.gd")
    creator_base = text("scripts/character_creation/character_creator.gd")
    creator_custom = text("scripts/character_creation/character_creator_customized.gd")
    visual_scene = text("scenes/menus/loading_screen_visual_v02.tscn")
    visual_script = text("scripts/menus/loading_screen_visual_v02.gd")

    assert 'SceneTransitionManager="*res://scripts/systems/scene_transition_manager.gd"' in project
    for required in (
        "ResourceLoader.load_threaded_request",
        "ResourceLoader.load_threaded_get_status",
        "ResourceLoader.load_threaded_get",
        "THREAD_LOAD_IN_PROGRESS",
        "THREAD_LOAD_LOADED",
        "THREAD_LOAD_FAILED",
        "CACHE_MODE_REUSE",
        "func is_busy() -> bool",
    ):
        assert required in manager, required

    assert "use_sub_threads" not in manager
    assert "false,\n\t\tResourceLoader.CACHE_MODE_REUSE" in manager
    assert "DEFAULT_MINIMUM_VISIBLE_SECONDS: float = 0.35" in manager
    assert "if is_busy():" in manager
    assert "change_scene_to_packed" in manager

    assert "_request_scene_transition(CHARACTER_CREATOR_SCENE)" in main_menu
    assert "_request_scene_transition(GAME_SCENE)" in main_menu
    assert "change_scene_to_file(CHARACTER_CREATOR_SCENE)" not in main_menu
    assert "change_scene_to_file(GAME_SCENE)" not in main_menu

    assert "func _request_scene_transition(scene_path: String) -> void:" in creator_base
    assert "_request_scene_transition(GAME_SCENE)" in creator_base
    assert "_request_scene_transition(GAME_SCENE)" in creator_custom
    assert "get_tree().change_scene_to_file(GAME_SCENE)" not in creator_custom

    assert 'text = "Башня, уходящая вниз"' in visual_scene
    assert "loading_progress_bar_v03.tscn" in visual_scene
    assert "func set_progress(value: float) -> void:" in visual_script
    assert "PROGRESS_CYCLE_SECONDS" not in visual_script

    obsolete_paths = [
        ROOT / ".github/workflows/materialize-loading-screen-visual-v02.yml",
        ROOT / "assets/branding/loading_screen/embedded/loading_screen_visual_v02",
        ROOT / "tools/loading_screen_visual_v02_transport",
    ]
    for path in obsolete_paths:
        assert not path.exists(), f"obsolete loading transport remains: {path}"

    bar_assets = ROOT / "assets/branding/loading_screen/approved/loading_bar_v03"
    assert bar_assets.is_dir()
    assert len(list(bar_assets.glob("*.png"))) == 5
    assert (ROOT / "scenes/ui/loading_progress_bar_v03.tscn").is_file()
    assert (ROOT / "scripts/ui/loading_progress_bar_v03.gd").is_file()

    print("Scene transition manager static contracts passed.")


if __name__ == "__main__":
    main()
