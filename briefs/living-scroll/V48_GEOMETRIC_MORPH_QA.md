# The Living Scroll V4.8 — Petal-to-Bird Geometric Continuity

## Engineering intent

The user requested continuing the film after the successful V4.7 *clean ink transition*. In V4.7 the flower still visibly shrinks away, while small bird silhouettes move out separately. V4.8 introduces a **bridging geometry**: seven evaluated physical petals of the detailed 28-petal hero flower are carried toward seven existing bird flight paths, deforming from full petal lamina to ink-brush wing mesh with constant topology and changing pigment.

The full flower, original wing/flight rigs, painted landscape, three pavilions, scroll and V4.7 clean Grease Pencil remain editable.

## Precisely what morphs

- Seven hand-selected **outer hero petals** (out of 28) become seven **650-vertex** independent, evaluated 3D meshes.
- The source petal's original shape and world location are sampled at **frame 132**, and its original mesh is progressively scaled out from frames 132–158.
- New carrier objects begin coincident with the original petals and then move through curved 3D waypoints, ending on corresponding real bird trajectories by frame 175.
- `Ink_Wing` Blender shape keys change their coordinates toward tapered, cambered feather-like strips; Object Info Color animates from warm cream toward charcoal; carrier geometry shrinks away by frame 182.
- The other 21 hero petals retain their original bloom and shrink animation. The small V4.6 bird flock remains the final visible flock. This is a physically **modeled geometric transition**, not an equal-topology whole-lotus-to-whole-bird conversion.

## Source

- `living_scroll_v4/v48_morph.py`: deterministic construction, animated color/material, per-petal interpolation, finite-coordinate and endpoint QA.
- `living_scroll_v4/v48.py`: preserves V4.7 scene, saves packed `living_scroll_v48.blend` and controls probe/smoke/full.
- `.github/workflows/living-scroll-v48-ci.yml`: pinned Python/Blender 5.2 builds, six 360×640 PNGs at frames 132/140/153/165/175/185, and **24 genuine consecutive frames** at 144×256 from frames 148–171 encoded into a 24fps MP4.

## Acceptance checks

1. Blender 5.2 creates 7 carriers × 650 vertices; each has `Lotus_Lamina` and `Ink_Wing` shape keys.
2. The source and detached petal coincide at frame 132; carrier remains finite and spatially continuous through frame 175.
3. Neither carrier nor old radial brush trails occlude the seven little swallows after frame 182.
4. The birds remain appropriately small and distinct; no return to visually oversized V4.5 hero birds.
5. No frame shows a hard teleport, flashing object, or conspicuous double-bright geometry.
6. The 1-second contiguous MP4 should represent *actual frame rendering*, not repeated stills/interpolation.
7. Full 12-second production render stays gated on visual inspection, performance profiling and chunking.

## Known risks / limitations

- The source mesh shrinks while a new mesh carrier assumes its world coordinates; temporal aliasing and visual double exposure during frames 130–140 are possible.
- An ink wing strip does not contain a detailed swallow torso/head. The final bird takes over as the carrier disappears.
- Camera-plane overlap may make the transformation read like a sweeping animated ribbon rather than a literal lotus turning into a swallow.
- CPU EEVEE smoke rendering has previously taken tens of minutes; use probe/build tests separately from expensive motion tests when iterating further.

Do not claim the artistic result is approved until the GitHub CI and its downloaded frames have been inspected.
