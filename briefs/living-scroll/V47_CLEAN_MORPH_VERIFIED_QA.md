# Living Scroll V4.7 — Verified Clean Morph and True Motion QA

## Verified release state

- Source branch: `art/living-scroll-v4-7-clean-morph` (V4.6 stable remains unchanged).
- Blender 5.2 EEVEE CI: [GitHub Actions run 41247530304](https://github.com/eretenkodaniil16-rgb/rpg-project/actions/runs/41247530304), **completed successfully**.
- Packed scene: `living_scroll_v47.blend`, downloadable in the run artifact.
- 6 full vertical control stills, rendered at **360 × 640** at frames **145, 155, 165, 175, 185, 205**.
- **Continuous, genuine 48-frame MP4** at **180 × 320, 24fps, exactly 2.000 seconds**, frames **148–195** (not motion interpolated).
- Main animation contract preserved: **288 frames at 24fps**, 12 seconds. Full 12-second final film has **not** been rendered.

## Blender runtime proof

```
V47_MORPH_QA_PASS {'large_brush': 8, 'old_gp': 1, 'fibers': 24, 'particles': 64} GP frames 41 7 swallows
V47_SCENE_QA_PASS {... 'grease_pencil_frames': 41, 'visible_particles': 32, 'active_strokes': 7}
V47_SMOKE_AND_48_FRAME_CLIP_OK
duration=2.000000
```

## Visual findings

Compared against the actual V4.6 frame 175, the V4.7 version **eliminates the large criss-crossing black ink arcs**, which had overlapped the entire flock and mountains. With the new scale-preserving bird LOD, separate small birds and architecture remain readable.

A twelve-sample contact sheet across frames 148,152,...192 was inspected. The sequence shows the flower decreasing in scale, vanishing, and the seven small swallows continuing over the landscape. The direct contamination of the frame by brush strokes is removed.

**Important limitation:** Although morph strokes and ink grains accompany the transition, the flower visually **shrinks away** rather than undergoing a topology-preserving transformation into bird geometry. The transition is cleaner, not yet a physically or visually seamless one-object metamorphosis.

## Engineering/performance cost

A 6-still plus 48-frame smoke run took roughly 37 minutes in GitHub Actions from its start. The continuous frames consumed the majority of that time. Do not schedule a single high-resolution full 288-frame job using these settings. Prefer render profiling, image-layer baking, and 24–48 frame parallel chunks with deterministic stitching.

## Next production tasks

1. V4.8: improve the lotus-to-bird continuity with controlled petal fragmentation and matching short strokes; avoid reverting to large black radial trails.
2. Refine pavilion roof/column proportions and scroll material/rollers without overwhelming the shan-shui painting.
3. Render a 12-second low-resolution full-cut proof using chunked parallel rendering; then final 1080×1920 with monitored performance.

The retained V4.5 hero bird library can still be enabled for deliberate macro shots; V4.6 lightweight small flock remains the default landscape scale.
