# The Living Scroll V4.4 — Hybrid Realism, Hero Lotus

Branch: `art/living-scroll-v4-4-hybrid-realism`

## Status

Source of truth: `living_scroll_v4/v44_lotus.py` (anatomically informed mesh builder) and `living_scroll_v4/v44.py` (integration and QA). Based on successful V4.3 Grease Pencil/pavilion landscape stack.

Blender 5.2 smoke run **41235211440** succeeded with six PNG images and a packed `living_scroll_v44.blend`. A follow-up render, **41235939547**, tests the correction to flower scale at frame 155 and a separate unanimated camera for closeup shots. Do not report that second run as successful without inspecting GitHub Actions.

## Construction contract

- 13 outer, 9 middle, 6 inner petals: **28 individually editable double-sided petal meshes**.
- Structured 25 × 13 grid per surface plus seam faces; nonuniform edge and camber.
- Per-petal Shape Keys: `BudFold`, `WindFlex`, `InkDeparture`.
- Distinct surface materials, blended tip/petal pigment, micro-bump, mild subsurface scattering via Principled BSDF.
- **84 stamens** with separate anthers and **23 seed depressions**, stylized convex receptacle.
- Existing ink-particle animation, Grease Pencil contours, pavilion kit, birds, EEVEE atmosphere and scroll remain intact.

## Observations from real run 41235211440

Strengths compared with V4.3: palpable volume, petal layer hierarchy, more descriptive receptacle, believable light gradients. Critical shortcomings:

1. Regular whorl arrangement and overly broad petals still convey synthetic procedural symmetry, not an observed natural bloom.
2. Pink matte material is noticeably CGI-like despite using mild subsurface scattering. More varied translucency, edge imperfections and nonuniform veining are required.
3. Frame 155 model remained large and occluded the flock. Subsequent code introduces earlier taper of V44 hero flower scale.
4. The first two 'detail' renders were byte-identical to standard smoke shots because the same camera datablock retained its animated ortho-scale. Subsequent code uses a temporary independent camera with a fixed 4.15 orthographic scale.

## Acceptance criteria for corrected run

- Six real frames: timeline 48/88/115/155 and independent details at 88/115.
- Detail frames visibly have tighter framing than respective timeline frames.
- Hero lotus at frame 155 visibly smaller, allowing flock silhouettes to separate.
- Blossom visible in early frames, entirely withdrawn by landscape/mountain phase.
- No malformed petal normals, seed pits, abrupt clipping, or SSS noise at 360×640 QA.
- Packed `.blend` generated and Python syntax/Blender API checks successful.

## Next production milestone

**Hero Swallow Pass**, not full MP4: anatomically informed swallow silhouettes with independent primaries, secondaries and forked tail, asynchronous wing cycles, and matching GP strokes. Once V4.4 lotus and birds pass close-up QA, improve pavilion/scroll materials, atmospheric integration and final morph, before investing in 288-frame full render.

The asset is not botanical photogrammetry, not 100% physically accurate, and should not be described as a real scan.
