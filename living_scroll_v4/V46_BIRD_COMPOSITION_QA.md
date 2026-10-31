# V4.6 — Small Swallow Flock / Composition and LOD Pass

## Motivation (confirmed from actual V4.5.2 contact sheet)

Birds at frames 155–205 are too large relative to the landscape, show distracting white chests, and overlap the pagodas and mountains. When a swallow spans only a few dozen pixels, 280 feather meshes are unnecessary and make the scene less like ink painting.

The art direction is **small charcoal silhouettes integrated into the mountain landscape**. This supersedes the idea of using highly detailed bird assets for every shot; the physically richer assets remain available for intentional closeups only.

## Implementation

- Branch `art/living-scroll-v4-6-bird-composition`.
- `v46_birds.py` preserves seven original keyed flight roots, all V4.5.2 hero models and 280 feathers in the Blender scene.
- At runtime, **V4.5 detailed render meshes are hidden**; **35 simple silhouette meshes** render instead: 7 × (small tapered torso + head + forked tail + two smoothly swept wings).
- Original bird scale curves receive a per-bird multiplier in **0.32–0.47** range; world paths remain unchanged. Small offsets distribute the seven birds more naturally.
- The GP calligraphic morph shrinks progressively with the flock so ink arcs do not remain larger than the birds.
- Matte charcoal ink rather than blue glint/bright ventral plumage.

## QA gate

Smoke at frames 155, 175, 205 and 235, 360×640, with an identical framing to V4.5.2. Visual checks:

1. At 155 the birds are secondary to the lotus, not competing for the hero focal position.
2. At 175 and 205 the flock reads as **small separate silhouettes**, at most a few dozen pixels across, with recognizable swept wings and forked tails.
3. At 235 birds recede relative to mountains and scroll.
4. No large GP ink arcs remain after the bird silhouettes have shrunk.
5. Preserve the full detailed bird library, original wing keyframes, landscape, 28-petal lotus, pavilion models, scroll, 24 FPS × 288 timeline.
6. Report substantive visual improvement only if verified in rendered images. Successful CI alone does not qualify as an art signoff.

## Rationale

For an ink-wash medium shot, apparent anatomical correctness is not proportional to polygon count. Silhouette, relative scale, separation from background, motion phase, and tone are more important. Any full-frame 720×1280 render should follow smoke-frame inspection.
