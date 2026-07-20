extends "res://scripts/game/game_target_free_attacks.gd"

const PREPARED_PANEL_SCRIPT: Script = preload("res://scripts/ui/prepared_action_panel.gd")
const CHARACTER_HUB_SCRIPT: Script = preload("res://scripts/ui/character_hub_inventory.gd")
const COMBAT_FEED_SCRIPT: Script = preload("res://scripts/ui/combat_event_feed.gd")
const D20_OVERLAY_SCRIPT: Script = preload("res://scripts/ui/d20_roll_overlay.gd")
const PLAYER_STATUS_HUD_SCRIPT: Script = preload("res://scripts/ui/player_status_hud.gd")

var _combat_feed: CombatEventFeed
var _d20_overlay: D20RollOverlay
var _player_status_hud: PlayerStatusHud


func _ready() -> void:
	super._ready()
	_remove_duplicate_inventory_menu()
	_separate_mobile_combat_buttons()
	var old_sheet: CharacterSheet = _character_sheet
	if old_sheet != null:
		old_sheet.queue_free()
	var hub: CharacterHub = CHARACTER_HUB_SCRIPT.new() as CharacterHub
	hub.name = "CharacterHub"
	hub.rest_completed.connect(_on_rest_completed)
	hub.prepared_action_changed.connect(_on_prepared_action_changed)
	$Interface.add_child(hub)
	_character_sheet = hub
	var old_panel: AbilityPanel = _ability_panel
	if old_panel != null:
		old_panel.free()
	var prepared_panel: PreparedActionPanel = PREPARED_PANEL_SCRIPT.new() as PreparedActionPanel
	prepared_panel.name = "PreparedActionPanel"
	prepared_panel.ability_requested.connect(_on_ability_requested)
	$Interface.add_child(prepared_panel)
	prepared_panel.bind_character(GameState.player_character)
	_ability_panel = prepared_panel
	_player_status_hud = PLAYER_STATUS_HUD_SCRIPT.new() as PlayerStatusHud
	_player_status_hud.name = "PlayerStatusHud"
	$Interface.add_child(_player_status_hud)
	_player_status_hud.bind_character(GameState.player_character)
	_d20_overlay = D20_OVERLAY_SCRIPT.new() as D20RollOverlay
	_d20_overlay.name = "D20RollOverlay"
	$Interface.add_child(_d20_overlay)
	_combat_feed = COMBAT_FEED_SCRIPT.new() as CombatEventFeed
	_combat_feed.name = "CombatEventFeed"
	$Interface.add_child(_combat_feed)
	_register_exploration_hud()
	_add_exploration_hud_node(_player_status_hud)
	_sync_exploration_hud_visibility()


func _remove_duplicate_inventory_menu() -> void:
	var old_button: Button = _inventory_button
	_inventory_button = null
	if old_button != null:
		old_button.queue_free()
	var old_inventory: InventoryPanel = _inventory_panel
	_inventory_panel = null
	if old_inventory != null:
		old_inventory.queue_free()


func _separate_mobile_combat_buttons() -> void:
	if _target_button != null:
		_target_button.offset_top = -398.0
		_target_button.offset_bottom = -338.0
		_target_button.z_index = 90
		_target_button.mouse_filter = Control.MOUSE_FILTER_STOP
	if _attack_button != null:
		_attack_button.offset_top = -328.0
		_attack_button.offset_bottom = -248.0
		_attack_button.z_index = 90
		_attack_button.mouse_filter = Control.MOUSE_FILTER_STOP


func _open_character_sheet() -> void:
	if GameState.input_locked or _character_sheet == null:
		return
	var hub: CharacterHub = _character_sheet as CharacterHub
	if hub != null:
		hub.open_tab(GameState.player_character, 0)
	else:
		_character_sheet.open_sheet(GameState.player_character)
	_sync_exploration_hud_visibility()


func _open_inventory() -> void:
	if GameState.input_locked or _character_sheet == null:
		return
	var hub: CharacterHub = _character_sheet as CharacterHub
	if hub != null:
		hub.open_tab(GameState.player_character, 1)
	else:
		super._open_inventory()
	_sync_exploration_hud_visibility()


func _on_prepared_action_changed(_ability_id: String) -> void:
	if _ability_panel != null:
		_ability_panel.refresh()
