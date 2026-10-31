# The Living Scroll V4.6 — verified small-bird composition QA

## Status / evidence

- **Blender 5.2 GitHub Actions run:** [41246028126](https://github.com/eretenkodaniil16-rgb/rpg-project/actions/runs/41246028126) — **success**.
- Output artifact: `living-scroll-v46-41246028126-1` (four real 360×640 PNGs and packed `living_scroll_v46.blend`).
- Existing V4.5.2 scene remains on `art/living-scroll-v4-5-hero-swallows`.
- New branch: `art/living-scroll-v4-6-bird-composition` (no RPG runtime changes).

## Source-verified changes
- Seven bird root animation scale multipliers: `[.42,.35,.47,.38,.44,.32,.40]`, with subtle independent position offsets.
- The V4.5.2 detailed library with 280 primaries/secondaries is **preserved but hidden for filming**.
- New on-camera bird LOD has 35 low-detail meshes (7 × torso/head/tail/left/right wing).
- All birds use a matte charcoal rather than high-contrast white torso and separately obvious feather meshes.
- Existing camera and mountain/parallax layers are unchanged, allowing a meaningful same-frame comparison.
- GP caligraphy scales down as smaller birds enter.

## Assessment of matched smoke frames
- **Frame 155:** small dark birds stay subordinate to the 3D lotus; previous swallows competed with the bloom.
- **Frame 175:** individual silhouettes become recognizable, but central giant curling ink strokes and clumped pigment from the original morph transition remain a clear visual flaw. Do not treat this as solved by bird LOD.
- **Frame 205:** the flock is now legible as several small distant birds over the mountains, with the landscape as primary visual subject.
- **Frame 235:** smaller silhouettes allow the red sun and architecture to lead the visual composition.

**Decision:** Accept V4.6 bird size/LOD as the new film default. Do not revert to V4.5 280-feather detailed rendering for whole-scene shots. Retain those assets only for possible intentional closeups. Full 288-frame final video still gated on morph/pagoda refinement and production render optimization.

## Next practical work
1. Mask or retime the V4.2 black calligraphic arcs and residual pigment between frames 150–185. Keep the graceful central ink-to-flight movement but remove the criss-crossing clutter.
2. Align swallows' flight paths with the clean ink endpoint, not with large residual brush tangles.
3. Improve pagoda and scroll physical credibility without competing with the soft ink painting.
4. Confirm visual QA with new frame samples 145, 155, 165, 175, 185, 205, then render chunked full film.
