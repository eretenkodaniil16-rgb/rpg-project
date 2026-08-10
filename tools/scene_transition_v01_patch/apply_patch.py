from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content, encoding="utf-8", newline="\n")


def replace_exact(content: str, old: str, new: str, expected: int, label: str) -> str:
    count = content.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return content.replace(old, new)


def patch_project() -> None:
    path = "project.godot"
    content = read(path)
    marker = 'TouchScrollManager="*res://scripts/ui/touch_scroll_manager.gd"\n'
    addition = marker + 'SceneTransitionManager="*res://scripts/systems/scene_transition_manager.gd"\n'
    if "SceneTransitionManager=" not in content:
        content = replace_exact(content, marker, addition, 1, path)
    write(path, content)


def transition_helper(indent: str = "") -> str:
    return (
        f"{indent}func _request_scene_transition(scene_path: String) -> void:\n"
        f"{indent}\tvar manager: Node = get_node_or_null(\"/root/SceneTransitionManager\")\n"
        f"{indent}\tif manager != null and manager.has_method(\"request_scene\"):\n"
        f"{indent}\t\tmanager.call(\"request_scene\", scene_path)\n"
        f"{indent}\t\treturn\n"
        f"{indent}\tget_tree().change_scene_to_file(scene_path)\n\n\n"
    )


def patch_main_menu() -> None:
    path = "scripts/menus/main_menu.gd"
    content = read(path)
    content = replace_exact(
        content,
        "\tget_tree().change_scene_to_file(CHARACTER_CREATOR_SCENE)\n",
        "\t_request_scene_transition(CHARACTER_CREATOR_SCENE)\n",
        1,
        path + ": new game",
    )
    content = replace_exact(
        content,
        "\t\tget_tree().change_scene_to_file(GAME_SCENE)\n",
        "\t\t_request_scene_transition(GAME_SCENE)\n",
        1,
        path + ": continue",
    )
    marker = "func _refresh_save_status() -> void:\n"
    if "func _request_scene_transition(scene_path: String) -> void:" not in content:
        content = replace_exact(content, marker, transition_helper() + marker, 1, path + ": helper")
    write(path, content)


def patch_character_creator_base() -> None:
    path = "scripts/character_creation/character_creator.gd"
    content = read(path)
    content = replace_exact(
        content,
        "\tget_tree().change_scene_to_file(GAME_SCENE)\n",
        "\t_request_scene_transition(GAME_SCENE)\n",
        1,
        path + ": finish",
    )
    marker = "func _return_to_menu() -> void:\n"
    if "func _request_scene_transition(scene_path: String) -> void:" not in content:
        content = replace_exact(content, marker, transition_helper() + marker, 1, path + ": helper")
    write(path, content)


def patch_character_creator_customized() -> None:
    path = "scripts/character_creation/character_creator_customized.gd"
    content = read(path)
    content = replace_exact(
        content,
        "\tget_tree().change_scene_to_file(GAME_SCENE)\n",
        "\t_request_scene_transition(GAME_SCENE)\n",
        1,
        path + ": finish",
    )
    write(path, content)


def main() -> None:
    patch_project()
    patch_main_menu()
    patch_character_creator_base()
    patch_character_creator_customized()
    print("Scene transition v01 patch applied.")


if __name__ == "__main__":
    main()
