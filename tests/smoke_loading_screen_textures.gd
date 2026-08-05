extends SceneTree

const BAR_SCENE: String = "res://scenes/ui/loading_progress_bar_v03.tscn"
const PREVIEW_SCENE: String = "res://scenes/menus/loading_screen_texture_preview.tscn"


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var bar_packed: PackedScene = load(BAR_SCENE) as PackedScene
	assert(bar_packed != null, "Loading bar scene must load")
	var bar: LoadingProgressBarV03 = bar_packed.instantiate() as LoadingProgressBarV03
	assert(bar != null, "Loading bar scene must instantiate")
	bar.size = Vector2(960.0, 104.0)
	root.add_child(bar)
	await process_frame
	await process_frame

	assert(bar.has_complete_textures(), "Loading bar texture set is incomplete")
	assert(is_equal_approx(bar.normalized_value(), 0.72), "Unexpected default progress")
	var full_width: float = bar.full_fill_width()
	assert(full_width > 0.0, "Loading bar full fill width must be positive")

	bar.set_progress(0.0)
	await process_frame
	assert(is_zero_approx(bar.fill_width()), "0 percent must have zero fill width")

	bar.set_progress(50.0)
	await process_frame
	var half_width: float = bar.fill_width()
	assert(half_width > 0.0 and half_width < full_width, "50 percent fill width is invalid")

	bar.set_progress(100.0)
	await process_frame
	assert(is_equal_approx(bar.fill_width(), full_width), "100 percent must fill the full track")

	bar.queue_free()
	await process_frame

	var preview_packed: PackedScene = load(PREVIEW_SCENE) as PackedScene
	assert(preview_packed != null, "Loading screen preview scene must load")
	var preview: LoadingScreenTexturePreview = preview_packed.instantiate() as LoadingScreenTexturePreview
	assert(preview != null, "Loading screen preview scene must instantiate")
	root.add_child(preview)
	await process_frame
	await process_frame
	assert(preview.progress_bar() != null, "Preview must expose its loading bar")
	assert(preview.get_node_or_null("FallbackBackground") != null, "Preview fallback is missing")
	assert(preview.get_node_or_null("PreviewBackground") is ColorRect, "Neutral preview background is missing")
	assert(preview.get_node_or_null("CaptionPanel/LoadingLabel") is Label, "Loading caption is missing")

	preview.queue_free()
	await process_frame
	print("Loading screen texture smoke test passed")
	quit(0)
