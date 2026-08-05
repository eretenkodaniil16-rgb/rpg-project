from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]

ONEHAND_FRAME_HASHES = {
    "down/f01": "2eadac7d8b13991a4cfab06c330446201edceb41add92f32c45f44e404a24aa4",
    "down/f02": "e85b6504f23bcb2d4a5f5ca70032f00f97033feab6e4be598850ed95aad357c7",
    "down/f03": "00900577d427bc89d9d122828fa2ba1e1a56816f14e398b81f52363c0babf9b2",
    "down/f04": "5a4a0f8a429cbb2e4f73ba6dad4da44b0ada6a63799739b69f48efdd06a1dba5",
    "down/f05": "2d83d75c5d10733a014ec0e87daf01c3aebebb3c01247de330921a9d3ea2d8da",
    "down/f06": "13ba06d5940bad9f0a8abb85c3aca0fb61de54be9bc99a1b2e8c55cc153215b7",
    "left/f01": "dd3585c2df7c67a94afcd4d28b83d53eb32375c510c1275fd927b4abea82ddaa",
    "left/f02": "9208cbb6e059aa9bc71d60cf99658a76c12a730b21d1e53b176d2f3f7d015ce3",
    "left/f03": "d1a8426b0c7b54c704f140ae64376418ce0dec77a5aad61fe9e1211cb91217e9",
    "left/f04": "e6a3562a7a8e75cc54887d1b249d3caf90f40e964f0aa449c4faea4b76125933",
    "left/f05": "f12786185bc35df6d0b28d32d784a0a71a984b7036e1024ca82b0b3050130d90",
    "left/f06": "74a7aa1c5ded334de8005f629f0d3eaded0c91700313837580ba3368fed25c24",
    "right/f01": "da11dcd75d019a0ebecdba1cac81190b3d1a0031d6d7ab5b9fd3b0857d15a611",
    "right/f02": "ed60bab36abc82d8b6975f87133b670f131bf7866d92eabaeea473781724b6a6",
    "right/f03": "fd488f5dee286639d8c2420a952d1cc23f40cf96e868c918dcd8d61e03633c6c",
    "right/f04": "e5b54a5b853f6099c9db1fa0332225c5b8fc1dfedc7b4c86f1b6a4869e26ff5d",
    "right/f05": "0785824be82208d0ecf8c26fb2fc3ca1c2072e129cdf867b64ee287ce0d60cbd",
    "right/f06": "af75b9650c1b3b707a8500bc55549ca02f8e14e9a8bf90345257c23a1c938f0b",
    "up/f01": "bc867f7d521e8d97eff9101ceff83a689a7e121ddf907691fabad1486caa61a9",
    "up/f02": "92bb42cde299b9579133173f9193f4edd943e1af03fdf02f707558a45672653b",
    "up/f03": "3ac4099a2fb7548dac9b6afbac5360916e89096f0e4a3c6d72b288e53fa94b72",
    "up/f04": "fd766fa8ca6db6029cdc2eab27459b0679b975dc0ef2f5452516bd5aa280cf77",
    "up/f05": "98654a0012fe3f62e63d75978ae091f5f996233fbabb4767abc2441a9d009e88",
    "up/f06": "e2777fd8f4f53cf6ebbf0bb0f930a4b947c38e420447d57464ea5a0b2a03be2e",
}

TWOHAND_FRAME_HASHES = {
    "down/f01": "26ec090944b27b1e1e42e57cfa457641be7b9c05372fb745fc5a617a23b6efd0",
    "down/f02": "94c218a43a827a08af93dfd39cbae0032e2e79b1d3eb3b8224c8c036ea9465ae",
    "down/f03": "a3eb76faa733aa827c8f58403d57d9dd4b22cd0649d5cb91158353015cc2741f",
    "down/f04": "35148c040235c7b72e6926783a4c63e0f82bde149423e120c0432fc31f7c9aaa",
    "down/f05": "98c1b756ba01ef16826540cfae4f69980d93fb4a69944bcd255df4015ff356d2",
    "down/f06": "a16c3acd22d1bc0508ef5b94332c54c61a373bf06ead27a9a5691966350f93f6",
    "left/f01": "a04b4ddc65d84b637e24b46fb5774b966254e8e7baaf9fd451fa5dc4e36946a4",
    "left/f02": "53875bbe473ce4b1b73568556956a051900dde7a6f863b197aa47e53ab457174",
    "left/f03": "e5b7f219edcdd287ba915e1fc597465ed6b75d4508411118d757341979780008",
    "left/f04": "3e813c869c1b12b29aecffa5a7379b2c342decf091ce6cca404bbf69fbe897d4",
    "left/f05": "60c345465f8e2c18cf40185237ae11e74ccbf2f24857d542e06c7a7c7e7ee40a",
    "left/f06": "8dfc0898b155a939b212ab3a2b96b8fda2c4468f0b9123d160028d0a6024883c",
    "right/f01": "7471e24a2ebcd5c94796a55638470d1d7f4ed1b36764c4c02d65b5153f2de1bf",
    "right/f02": "7c971441bf97705e37c29d08f082a30bec69aa28d98d81db23b942f4564c9cb2",
    "right/f03": "34cc5365854f326c126a1d0c6f457eb456df3bc43a9365d839925af07e09f9f8",
    "right/f04": "316d376ee79759fc6c696c6856943dc7b0708665e894bdf112ba341821381ae5",
    "right/f05": "88c3234797c0cee258703d157cc434fd7c1bbb0886f0d03faa6a9a85704324e4",
    "right/f06": "03e11961e8de2250ec2bc8d34409d92f25ab7beb0ed2b4d2aaa6fc767a6ae26c",
    "up/f01": "d9fbd2cfa5200bb7c75cbba321f28f13d8ee508cfca0ed8123a8c23e32fbdccb",
    "up/f02": "78377e15c6c0729b48be241c72478bbbf620720a2730982c4a73700a0b085093",
    "up/f03": "43eab60b818f252dca5f71e8d9b85d9e552e5bf85b1ff1b52ec3850934d1f55b",
    "up/f04": "83ad943dbcbb427de7fb754a2c88834bd50467b9f28f500ac2b2e29fc68ef78b",
    "up/f05": "5173bf0f9e12c1b9b8f317127068406a9ba5646ae710776153c299116dc5f392",
    "up/f06": "fa0ec881eed04c4c31fd5570af85de798874eea1d2cc2020e19318cfe261d82a",
}


def replace_once(path: str, old: str, new: str) -> None:
    file_path = ROOT / path
    content = file_path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected one match in {path}, found {count}")
    file_path.write_text(content.replace(old, new, 1), encoding="utf-8")


def edge_contract(path: Path) -> dict[str, dict[str, int]]:
    image = Image.open(path).convert("RGBA")
    result: dict[str, dict[str, int]] = {}
    directions = ("down", "left", "right", "up")
    for row, direction in enumerate(directions):
        for column in range(6):
            cell = image.crop((column * 96, row * 96, (column + 1) * 96, (row + 1) * 96))
            alpha = cell.getchannel("A")
            pixels = alpha.load()
            result[f"{direction}/f{column + 1:02d}"] = {
                "left": sum(pixels[0, y] > 0 for y in range(96)),
                "right": sum(pixels[95, y] > 0 for y in range(96)),
                "top": sum(pixels[x, 0] > 0 for x in range(96)),
                "bottom": sum(pixels[x, 95] > 0 for x in range(96)),
            }
    return result


def patch_library() -> None:
    replace_once(
        "scripts/game/human_warrior_animation_library.gd",
        '''\t"attack_sword_01_onehand",\n\t"attack_sword_01_twohand"\n]''',
        '''\t"attack_sword_01_onehand",\n\t"attack_sword_01_twohand",\n\t"hit_01_onehand",\n\t"hit_01_twohand"\n]''',
    )


def patch_player() -> None:
    replace_once(
        "scripts/game/player.gd",
        '''signal melee_attack_contact(sequence_id: int)\nsignal melee_attack_finished(sequence_id: int)''',
        '''signal melee_attack_contact(sequence_id: int)\nsignal melee_attack_finished(sequence_id: int)\nsignal hit_reaction_started(sequence_id: int, damage_amount: int)\nsignal hit_reaction_finished(sequence_id: int)''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''var _attack_tween: Tween = null''',
        '''var _attack_tween: Tween = null\nvar _hit_tween: Tween = null''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''var _pending_attack_contact: Callable = Callable()''',
        '''var _pending_attack_contact: Callable = Callable()\n\nvar _hit_sequence_counter: int = 0\nvar _active_hit_sequence_id: int = 0\nvar _active_hit_animation: StringName = &""\nvar _queued_hit_damage: int = 0\nvar _queued_hit_source_global_position: Vector2 = Vector2.INF''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''func is_action_animation_locked() -> bool:\n\treturn _action_animation_locked\n\n\nfunc apply_character_appearance() -> void:''',
        '''func is_action_animation_locked() -> bool:\n\treturn _action_animation_locked\n\n\nfunc is_hit_reaction_active() -> bool:\n\treturn _active_hit_sequence_id > 0\n\n\nfunc play_hit_reaction(\n\tdamage_amount: int,\n\tsource_global_position: Vector2 = Vector2.INF\n) -> int:\n\tif damage_amount <= 0 or GameState.player_character.current_health <= 0:\n\t\treturn -1\n\tif _action_animation_locked:\n\t\t_queue_hit_reaction(damage_amount, source_global_position)\n\t\treturn _active_hit_sequence_id if _active_hit_sequence_id > 0 else 0\n\treturn _start_hit_reaction(damage_amount, source_global_position)\n\n\nfunc cancel_hit_reaction_for_death() -> void:\n\t_queued_hit_damage = 0\n\t_queued_hit_source_global_position = Vector2.INF\n\tif _active_hit_sequence_id <= 0:\n\t\treturn\n\tif _hit_tween != null:\n\t\t_hit_tween.kill()\n\t\t_hit_tween = null\n\tif is_instance_valid(_character_sprite) and _character_sprite.animation == _active_hit_animation:\n\t\t_character_sprite.stop()\n\tget_active_visual().position = _active_visual_base_position\n\t_active_hit_animation = &""\n\t_active_hit_sequence_id = 0\n\t_action_animation_locked = false\n\n\nfunc _start_hit_reaction(damage_amount: int, source_global_position: Vector2) -> int:\n\t_hit_sequence_counter += 1\n\t_active_hit_sequence_id = _hit_sequence_counter\n\t_action_animation_locked = true\n\t_visual_motion_state = VISUAL_STATE_IDLE\n\t_visual_stop_grace_remaining = 0.0\n\tvelocity = Vector2.ZERO\n\tif _attack_tween != null:\n\t\t_attack_tween.kill()\n\t\t_attack_tween = null\n\tget_active_visual().position = _active_visual_base_position\n\n\tvar grip_mode: StringName = _effective_grip_mode()\n\tvar hit_set_id: StringName = &""\n\tif grip_mode == VISUAL_MODE_ONEHAND:\n\t\thit_set_id = &"hit_01_onehand"\n\telif grip_mode == VISUAL_MODE_TWOHAND:\n\t\thit_set_id = &"hit_01_twohand"\n\tvar direction_id: StringName = _direction_id(_visual_facing_direction)\n\tvar animation_name := StringName("%s_%s" % [str(hit_set_id), str(direction_id)])\n\tif (\n\t\tnot str(hit_set_id).is_empty()\n\t\tand is_instance_valid(_character_sprite)\n\t\tand _character_sprite.visible\n\t\tand _character_sprite.sprite_frames.has_animation(animation_name)\n\t):\n\t\t_active_hit_animation = animation_name\n\t\t_character_sprite.stop()\n\t\t_character_sprite.play(animation_name)\n\t\thit_reaction_started.emit(_active_hit_sequence_id, damage_amount)\n\t\treturn _active_hit_sequence_id\n\n\t_active_hit_animation = &""\n\thit_reaction_started.emit(_active_hit_sequence_id, damage_amount)\n\t_start_fallback_hit_reaction(_active_hit_sequence_id, source_global_position)\n\treturn _active_hit_sequence_id\n\n\nfunc _queue_hit_reaction(damage_amount: int, source_global_position: Vector2) -> void:\n\t_queued_hit_damage = maxi(_queued_hit_damage, damage_amount)\n\tif source_global_position != Vector2.INF:\n\t\t_queued_hit_source_global_position = source_global_position\n\n\nfunc _start_queued_hit_reaction() -> void:\n\tif _queued_hit_damage <= 0 or _action_animation_locked:\n\t\treturn\n\tif GameState.player_character.current_health <= 0:\n\t\t_queued_hit_damage = 0\n\t\t_queued_hit_source_global_position = Vector2.INF\n\t\treturn\n\tvar damage_amount: int = _queued_hit_damage\n\tvar source_position: Vector2 = _queued_hit_source_global_position\n\t_queued_hit_damage = 0\n\t_queued_hit_source_global_position = Vector2.INF\n\t_start_hit_reaction(damage_amount, source_position)\n\n\nfunc apply_character_appearance() -> void:''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''\t\t"action_locked": _action_animation_locked,\n\t\t"library_error": _animation_library_error''',
        '''\t\t"action_locked": _action_animation_locked,\n\t\t"hit_active": _active_hit_sequence_id > 0,\n\t\t"queued_hit_damage": _queued_hit_damage,\n\t\t"library_error": _animation_library_error''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''func _on_character_sprite_animation_finished() -> void:\n\tif not _action_animation_locked or not is_instance_valid(_character_sprite):\n\t\treturn\n\tif _character_sprite.animation != _active_attack_animation:\n\t\treturn\n\t# AnimatedSprite2D completes its internal non-loop transition after emitting\n\t# animation_finished. Finalizing synchronously can restore the finished attack\n\t# over the combat idle selected by _refresh_visual_animation(). Keep the local\n\t# action lock until the deferred call establishes the post-attack state.\n\tcall_deferred("_finish_melee_attack", _active_attack_sequence_id)''',
        '''func _on_character_sprite_animation_finished() -> void:\n\tif not _action_animation_locked or not is_instance_valid(_character_sprite):\n\t\treturn\n\tif not str(_active_hit_animation).is_empty() and _character_sprite.animation == _active_hit_animation:\n\t\tcall_deferred("_finish_hit_reaction", _active_hit_sequence_id)\n\t\treturn\n\tif _character_sprite.animation != _active_attack_animation:\n\t\treturn\n\t# AnimatedSprite2D completes its internal non-loop transition after emitting\n\t# animation_finished. Finalizing synchronously can restore the finished action\n\t# over the combat idle selected by _refresh_visual_animation().\n\tcall_deferred("_finish_melee_attack", _active_attack_sequence_id)''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''func _start_fallback_melee_attack(sequence_id: int, direction: Vector2) -> void:\n\tvar visual: Node2D = get_active_visual()\n\tvisual.position = _active_visual_base_position\n\t_attack_tween = create_tween()\n\t_attack_tween.tween_property(\n\t\tvisual,\n\t\t"position",\n\t\t_active_visual_base_position + direction.normalized() * 15.0,\n\t\t0.07\n\t)\n\t_attack_tween.tween_callback(Callable(self, "_fire_attack_contact").bind(sequence_id))\n\t_attack_tween.tween_property(visual, "position", _active_visual_base_position, 0.11)\n\t_attack_tween.tween_callback(Callable(self, "_finish_melee_attack").bind(sequence_id))''',
        '''func _start_fallback_melee_attack(sequence_id: int, direction: Vector2) -> void:\n\tvar visual: Node2D = get_active_visual()\n\tvisual.position = _active_visual_base_position\n\t_attack_tween = create_tween()\n\t_attack_tween.tween_property(\n\t\tvisual,\n\t\t"position",\n\t\t_active_visual_base_position + direction.normalized() * 15.0,\n\t\t0.07\n\t)\n\t_attack_tween.tween_callback(Callable(self, "_fire_attack_contact").bind(sequence_id))\n\t_attack_tween.tween_property(visual, "position", _active_visual_base_position, 0.11)\n\t_attack_tween.tween_callback(Callable(self, "_finish_melee_attack").bind(sequence_id))\n\n\nfunc _start_fallback_hit_reaction(sequence_id: int, source_global_position: Vector2) -> void:\n\tvar recoil_direction: Vector2 = -_visual_facing_direction\n\tif source_global_position != Vector2.INF:\n\t\tvar away_from_source: Vector2 = global_position - source_global_position\n\t\tif away_from_source.length_squared() > 0.0001:\n\t\t\trecoil_direction = away_from_source.normalized()\n\tif recoil_direction.length_squared() <= 0.0001:\n\t\trecoil_direction = Vector2.DOWN\n\tvar visual: Node2D = get_active_visual()\n\tvisual.position = _active_visual_base_position\n\t_hit_tween = create_tween()\n\t_hit_tween.tween_property(\n\t\tvisual,\n\t\t"position",\n\t\t_active_visual_base_position + recoil_direction.normalized() * 7.0,\n\t\t0.08\n\t)\n\t_hit_tween.tween_property(visual, "position", _active_visual_base_position, 0.18)\n\t_hit_tween.tween_callback(Callable(self, "_finish_hit_reaction").bind(sequence_id))''',
    )
    replace_once(
        "scripts/game/player.gd",
        '''\t_refresh_visual_animation()\n\tmelee_attack_finished.emit(sequence_id)\n\n\nfunc _supports_authored_human_warrior(character: PlayerCharacter) -> bool:''',
        '''\t_refresh_visual_animation()\n\tmelee_attack_finished.emit(sequence_id)\n\tcall_deferred("_start_queued_hit_reaction")\n\n\nfunc _finish_hit_reaction(sequence_id: int) -> void:\n\tif sequence_id != _active_hit_sequence_id:\n\t\treturn\n\tget_active_visual().position = _active_visual_base_position\n\t_hit_tween = null\n\t_active_hit_animation = &""\n\t_active_hit_sequence_id = 0\n\t_action_animation_locked = false\n\t_visual_motion_state = VISUAL_STATE_IDLE\n\t_visual_stop_grace_remaining = 0.0\n\t_last_visual_sample_position = global_position\n\tif GameState.player_character.current_health > 0:\n\t\t_refresh_visual_animation()\n\thit_reaction_finished.emit(sequence_id)\n\tcall_deferred("_start_queued_hit_reaction")\n\n\nfunc _supports_authored_human_warrior(character: PlayerCharacter) -> bool:''',
    )


def patch_damage_runtime() -> None:
    replace_once(
        "scripts/game/game_damage_fall_reactions_runtime.gd",
        '''var _hellish_rebuke_save_overrides: Array[int] = []\nvar _hellish_rebuke_damage_overrides: Array[int] = []''',
        '''var _hellish_rebuke_save_overrides: Array[int] = []\nvar _hellish_rebuke_damage_overrides: Array[int] = []\n\n\nfunc apply_damage_to_player(\n\tamount: int,\n\tdamage_type: String,\n\tcritical_hit: bool = false,\n\tsource: Node = null\n) -> Dictionary:\n\tvar result: Dictionary = super.apply_damage_to_player(amount, damage_type, critical_hit, source)\n\tvar applied: int = int(result.get("applied", 0))\n\tif applied <= 0:\n\t\treturn result\n\tif GameState.player_character.current_health <= 0 or bool(result.get("dead", false)):\n\t\tif player.has_method("cancel_hit_reaction_for_death"):\n\t\t\tplayer.call("cancel_hit_reaction_for_death")\n\t\treturn result\n\tif player.has_method("play_hit_reaction"):\n\t\tvar source_position: Vector2 = Vector2.INF\n\t\tif is_instance_valid(source) and source is Node2D:\n\t\t\tsource_position = (source as Node2D).global_position\n\t\tplayer.call("play_hit_reaction", applied, source_position)\n\treturn result''',
    )


def patch_tests() -> None:
    replace_once(
        "tests/test_human_warrior_animation_assets_v01.py",
        'self.assertEqual(len(self.manifest["sets"]), 8)',
        'self.assertEqual(len(self.manifest["sets"]), 10)',
    )
    replace_once(
        "tests/test_human_warrior_animation_assets_v01.py",
        '''        self.assertTrue(runtime["repeat_attack_locked"])''',
        '''        self.assertTrue(runtime["repeat_attack_locked"])\n        self.assertEqual(runtime["hit_reaction_damage_threshold"], 1)\n        self.assertTrue(runtime["hit_reaction_movement_locked"])\n        self.assertTrue(runtime["hit_reaction_facing_locked"])\n        self.assertTrue(runtime["death_priority_over_hit"])''',
    )
    replace_once(
        "tests/test_human_warrior_animation_assets_v01.py",
        '''        for attack in self.lock["attack_atlases"].values():\n            hashes[Path(str(attack["path"])).name] = str(attack["sha256"])\n        self.assertEqual(len(hashes), 8)''',
        '''        for attack in self.lock["attack_atlases"].values():\n            hashes[Path(str(attack["path"])).name] = str(attack["sha256"])\n        for hit in self.lock["hit_atlases"].values():\n            hashes[Path(str(hit["path"])).name] = str(hit["sha256"])\n        self.assertEqual(len(hashes), 10)''',
    )
    replace_once(
        "tests/test_human_warrior_runtime_animation_v02.gd",
        '''\t"attack_sword_01_onehand": 8,\n\t"attack_sword_01_twohand": 8''',
        '''\t"attack_sword_01_onehand": 8,\n\t"attack_sword_01_twohand": 8,\n\t"hit_01_onehand": 6,\n\t"hit_01_twohand": 6''',
    )
    replace_once(
        "tests/test_human_warrior_runtime_animation_v02.gd",
        '''if frames == null or frames.get_animation_names().size() != 32:\n\t\t_fail("Runtime animation library must expose 32 directional animations.")''',
        '''if frames == null or frames.get_animation_names().size() != 40:\n\t\t_fail("Runtime animation library must expose 40 directional animations.")''',
    )


def patch_lock() -> None:
    lock_path = ROOT / "data/visuals/human_warrior_m01_animation_assets_v01.lock.json"
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    atlas_root = ROOT / "assets/characters/human/warrior_m01/gameplay/approved/atlases"
    data["hit_atlases"] = {
        "onehand": {
            "path": "assets/characters/human/warrior_m01/gameplay/approved/atlases/human_warrior_m01_hit_01_onehand_v01.png",
            "sha256": "77ebc7a5148891f5e9feff6a293eab681eb12744254a7d3e65f6bb1e1fced5ea",
            "size": [576, 384],
            "source_frame_sha256": ONEHAND_FRAME_HASHES,
            "edge_alpha_contract": edge_contract(atlas_root / "human_warrior_m01_hit_01_onehand_v01.png"),
            "first_last_identical": {"down": False, "left": False, "right": False, "up": False},
        },
        "twohand": {
            "path": "assets/characters/human/warrior_m01/gameplay/approved/atlases/human_warrior_m01_hit_01_twohand_v01.png",
            "sha256": "f863064b643e396779a1a99f181e0b83285b0a858f75123b3eeb1a8cf03d5238",
            "size": [576, 384],
            "source_frame_sha256": TWOHAND_FRAME_HASHES,
            "edge_alpha_contract": edge_contract(atlas_root / "human_warrior_m01_hit_01_twohand_v01.png"),
            "first_last_identical": {"down": False, "left": False, "right": False, "up": False},
        },
    }
    lock_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    patch_library()
    patch_player()
    patch_damage_runtime()
    patch_tests()
    patch_lock()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
