extends "res://scripts/game/game_target_free_attacks.gd"

const PREPARED_PANEL_SCRIPT: Script = preload("res://scripts/ui/prepared_action_panel.gd")
const CHARACTER_HUB_SCRIPT: Script = preload("res://scripts/ui/character_hub_level_up.gd")
const COMBAT_FEED_SCRIPT: Script = preload("res://scripts/ui/combat_event_feed.gd")
const D20_OVERLAY_SCRIPT: Script = preload("res://scripts/ui/d20_roll_overlay.gd")
const PLAYER_STATUS_HUD_SCRIPT: Script = preload("res://scripts/ui/player_status_hud.gd")
const LEVEL_UP_PANEL_SCRIPT: Script = preload("res://scripts/ui/level_up_panel.gd")

var _combat_feed: CombatEventFeed
var _d20_overlay: D20RollOverlay
var _player_status_hud: PlayerStatusHud
var _level_up_panel: LevelUpPanel
var _level_up_system: LevelUpSystem = LevelUpSystem.new()


func _ready() -> void:
	super._ready()
	_level_up_system.ensure_migrated(GameState.player_character, GameState)
	_remove_duplicate_inventory_menu()
	_separate_mobile_combat_buttons()
	_compact_world_labels()
	_move_top_menu_buttons()
	var old_sheet: CharacterSheet = _character_sheet
	if old_sheet != null:
		old_sheet.queue_free()
	var hub: CharacterHubLevelUp = CHARACTER_HUB_SCRIPT.new() as CharacterHubLevelUp
	hub.name = "CharacterHub"
	hub.rest_completed.connect(_on_rest_completed)
	hub.prepared_action_changed.connect(_on_prepared_action_changed)
	hub.level_up_requested.connect(_open_level_up)
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
	_level_up_panel = LEVEL_UP_PANEL_SCRIPT.new() as LevelUpPanel
	_level_up_panel.name = "LevelUpPanel"
	_level_up_panel.level_up_completed.connect(_on_level_up_completed)
	$Interface.add_child(_level_up_panel)
	_register_exploration_hud()
	_add_exploration_hud_node(_player_status_hud)
	_sync_exploration_hud_visibility()


func _process(delta: float) -> void:
	super._process(delta)
	set_interaction_suppressed(is_turn_based_combat_active())
	if _attack_button != null and not is_turn_based_combat_active():
		_attack_button.text = "АТАКА"
		_attack_button.custom_minimum_size = Vector2(170.0, 60.0)


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
		_target_button.offset_left = -188.0
		_target_button.offset_top = 116.0
		_target_button.offset_right = -18.0
		_target_button.offset_bottom = 168.0
		_target_button.z_index = 120
		_target_button.mouse_filter = Control.MOUSE_FILTER_STOP
		_target_button.modulate = Color(1.0, 1.0, 1.0, 0.88)
	if _attack_button != null:
		_attack_button.text = "АТАКА"
		_attack_button.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
		_attack_button.offset_left = -198.0
		_attack_button.offset_top = -214.0
		_attack_button.offset_right = -28.0
		_attack_button.offset_bottom = -154.0
		_attack_button.custom_minimum_size = Vector2(170.0, 60.0)
		_attack_button.z_index = 125
		_attack_button.mouse_filter = Control.MOUSE_FILTER_STOP
		_attack_button.add_theme_font_size_override("font_size", 17)
		_attack_button.modulate = Color(1.0, 0.88, 0.70, 0.96)
		var attack_style := StyleBoxFlat.new()
		attack_style.bg_color = Color(0.42, 0.08, 0.07, 0.94)
		attack_style.border_color = Color(0.96, 0.72, 0.25, 1.0)
		attack_style.set_border_width_all(3)
		attack_style.corner_radius_top_left = 12
		attack_style.corner_radius_top_right = 12
		attack_style.corner_radius_bottom_left = 12
		attack_style.corner_radius_bottom_right = 12
		_attack_button.add_theme_stylebox_override("normal", attack_style)


func _compact_world_labels() -> void:
	help_label.add_theme_font_size_override("font_size", 14)
	help_label.offset_right = 650.0
	status_label.add_theme_font_size_override("font_size", 15)
	status_label.offset_top = 48.0
	status_label.offset_right = 700.0


func _move_top_menu_buttons() -> void:
	if _quest_button != null:
		_quest_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
		_quest_button.offset_left = -354.0
		_quest_button.offset_top = 20.0
		_quest_button.offset_right = -188.0
		_quest_button.offset_bottom = 78.0
		_quest_button.add_theme_font_size_override("font_size", 15)
	if _character_button != null:
		_character_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
		_character_button.offset_left = -536.0
		_character_button.offset_top = 20.0
		_character_button.offset_right = -364.0
		_character_button.offset_bottom = 78.0
		_character_button.add_theme_font_size_override("font_size", 15)


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


func _open_level_up() -> void:
	if _level_up_panel == null:
		return
	var hub: CharacterHub = _character_sheet as CharacterHub
	if hub != null and hub.visible:
		hub.close_sheet()
	_level_up_panel.open_for(GameState.player_character, GameState)
	_sync_exploration_hud_visibility()


func _on_level_up_completed(_result: Dictionary) -> void:
	if _player_status_hud != null:
		_player_status_hud.bind_character(GameState.player_character)
	if _ability_panel != null:
		_ability_panel.bind_character(GameState.player_character)
	var hub: CharacterHub = _character_sheet as CharacterHub
	if hub != null:
		hub.open_tab(GameState.player_character, 0)
	_sync_exploration_hud_visibility()


func _on_prepared_action_changed(_ability_id: String) -> void:
	if _ability_panel != null:
		_ability_panel.refresh()
