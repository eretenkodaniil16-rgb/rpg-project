from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    file_path = REPO_ROOT / path
    content = file_path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}, found {count}")
    file_path.write_text(content.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    srd_old = '''\tif DistanceSystem.is_ranged_weapon(weapon):
\t\tawait _play_weapon_projectile(weapon, target_position, result.hit)
\telse:
\t\tplayer.play_attack_animation(target_position)
\tif _target_is_valid(target):
\t\ttarget.call("receive_player_attack", result, true)
\t\tif int(target.call("get_current_health")) <= 0:
\t\t\t_release_grapples_for(target)
'''
    srd_new = '''\tvar contact_applied: bool = false
\tif DistanceSystem.is_ranged_weapon(weapon):
\t\tawait _play_weapon_projectile(weapon, target_position, result.hit)
\t\tcontact_applied = _apply_player_attack_contact(target, result)
\telse:
\t\tcontact_applied = await _play_player_melee_attack_to_completion(target, weapon, result)
\tif (
\t\tcontact_applied
\t\tand is_instance_valid(target)
\t\tand target.has_method("get_current_health")
\t\tand int(target.call("get_current_health")) <= 0
\t):
\t\t_release_grapples_for(target)
'''
    replace_once("scripts/game/game_srd_combat.gd", srd_old, srd_new)

    helper_anchor = '''\n\nfunc _build_srd_attack_context(target: Node, distance: int) -> Dictionary:
'''
    helper_block = '''\n\nfunc _play_player_melee_attack_to_completion(
\ttarget: Node,
\tweapon: Dictionary,
\tresult: AttackResult
) -> bool:
\tif not is_instance_valid(target):
\t\treturn false
\tif not player.has_method("start_melee_attack_animation") or not player.has_signal("melee_attack_finished"):
\t\tplayer.play_attack_animation((target as Node2D).global_position)
\t\tawait get_tree().create_timer(0.07).timeout
\t\treturn _apply_player_attack_contact(target, result)

\tvar applied_state: Dictionary = {"applied": false}
\tvar contact_callback: Callable = Callable(
\t\tself,
\t\t"_apply_player_attack_contact_and_mark"
\t).bind(target, result, applied_state)
\tvar finished_signal := Signal(player, &"melee_attack_finished")
\tvar sequence_id: int = int(player.call(
\t\t"start_melee_attack_animation",
\t\t(target as Node2D).global_position,
\t\tweapon,
\t\tcontact_callback
\t))
\tif sequence_id < 0:
\t\treturn false
\tawait finished_signal
\treturn bool(applied_state.get("applied", false))


func _apply_player_attack_contact_and_mark(
\ttarget: Node,
\tresult: AttackResult,
\tapplied_state: Dictionary
) -> void:
\tapplied_state["applied"] = _apply_player_attack_contact(target, result)


func _apply_player_attack_contact(target: Node, result: AttackResult) -> bool:
\tif not is_instance_valid(target) or not target.has_method("receive_player_attack"):
\t\treturn false
\ttarget.call("receive_player_attack", result, true)
\treturn true
'''
    replace_once(
        "scripts/game/game_srd_combat.gd",
        helper_anchor,
        helper_block + helper_anchor,
    )

    transactional_old = '''\tvar ranged_attack: bool = DistanceSystem.is_ranged_attack(weapon, distance)
\tif ranged_attack:
\t\tawait _play_weapon_projectile(weapon, target_position, result.hit)
\telse:
\t\tplayer.play_attack_animation(target_position)
\tif _is_recoverable_thrown_attack(weapon, distance):
\t\t_ensure_dropped_inventory_manager()
\t\tif _dropped_inventory_manager != null:
\t\t\t_dropped_inventory_manager.spawn_dropped_item(
\t\t\t\tstr(weapon.get("id", "")),
\t\t\t\t1,
\t\t\t\t_thrown_landing_position(target_position, result.hit)
\t\t\t)
\tif _target_is_valid(target):
\t\ttarget.call("receive_player_attack", result, true)
\t\tif int(target.call("get_current_health")) <= 0:
\t\t\t_release_grapples_for(target)
'''
    transactional_new = '''\tvar ranged_attack: bool = DistanceSystem.is_ranged_attack(weapon, distance)
\tvar contact_applied: bool = false
\tif ranged_attack:
\t\tawait _play_weapon_projectile(weapon, target_position, result.hit)
\t\tcontact_applied = _apply_player_attack_contact(target, result)
\telse:
\t\tcontact_applied = await _play_player_melee_attack_to_completion(target, weapon, result)
\tif _is_recoverable_thrown_attack(weapon, distance):
\t\t_ensure_dropped_inventory_manager()
\t\tif _dropped_inventory_manager != null:
\t\t\t_dropped_inventory_manager.spawn_dropped_item(
\t\t\t\tstr(weapon.get("id", "")),
\t\t\t\t1,
\t\t\t\t_thrown_landing_position(target_position, result.hit)
\t\t\t)
\tif (
\t\tcontact_applied
\t\tand is_instance_valid(target)
\t\tand target.has_method("get_current_health")
\t\tand int(target.call("get_current_health")) <= 0
\t):
\t\t_release_grapples_for(target)
'''
    replace_once(
        "scripts/game/game_consumable_inventory_base_runtime.gd",
        transactional_old,
        transactional_new,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
