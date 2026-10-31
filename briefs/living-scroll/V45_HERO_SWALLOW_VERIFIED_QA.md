# The Living Scroll V4.5.2 — Hero Swallow Pass: verified QA

Branch: `art/living-scroll-v4-5-hero-swallows`. Current verified commit `521b952f7d18fa004d445e39d6a2079cf2c31c62`.

## Real runs and assessment
- 41236901886 — V4.5 first hero birds — **successful**. Bodies, 280 feathers, independent wing controls, closeups produced; strong but visibly synthetic and uniform feather scallops.
- 41237598205 — V4.5.1 — **successful**, but artistically rejected. Feather vane taper created excessive separate pointed spikes, unlike continuous real swallow wings.
- 41238443286 — V4.5.2 — **successful and preferred**. Added hand/wing coverts which overlap individual primaries; restored overlap, narrowed the rigid beak-like feather teeth, softened belly contrast and made banking slightly more varied.

## Rendering evidence
- Six real EEVEE frames at 360×640: 155, 175, 205, 235 + dedicated 175/205 closeups.
- Saved `living_scroll_v45.blend` is packed and editable.
- Seven rigged swallows, **280 primary/secondary feather meshes** verified automatically in runtime output.
- V4.4's sculpted 28-petal lotus, layered atmospheric mountains, separate pavilion meshes, 49 Grease Pencil frames and scroll remain intact.

## Qualitative judgment
Improvements are grounded in actual render comparison, not automatic success markers. The latest wing silhouette is less comb-like, and feather roots form a more coherent surface.

Remaining weaknesses:
1. Birds still face the camera too frontally and have somewhat torpedo-shaped bellies/head silhouettes.
2. Wings have an articulated approximation but lack anatomically accurate humerus/radius/ulna or feather deformation under aerodynamic load.
3. The seven-bird flock overlaps near the first lotus→bird transition; crowding and excessive large curved ink strokes remain.
4. Distant pagodas are simple compared with hero bird/lotus geometry. Need a subsequent architecture/scroll art pass.
5. This is **high-detail stylized geometry**, not photo-scanned or truly photorealistic wildlife.

## Timing and full-film warning
V4.5 first six smoke frames took ~5m51s for the render step at 360×640 on GitHub CPU. V4.5.2 smoke frames took ~4m41s. Extrapolating 288 frames at 24fps is **not** a reliable full render ETA, because scene complexity and frame-to-frame startup vary, but suggests that a single 720×1280 CPU workflow may exceed its configured 165-minute timeout. Render optimization / chunking is needed before full MP4. Do not launch the full job blindly.

## Next technical priority
1. Profile source of EEVEE bottlenecks; bake frame-invariant watercolor shaders and use mesh instancing/LODs.
2. Improve bird poses with asymmetric glide/flap trajectories and anatomical silhouettes.
3. More convincing pavilion wood/roof material and physical scroll, then polish GP morph.
4. Only then 288-frame film, using chunked Actions jobs and deterministic FFmpeg stitching.

Reference species and identification: [Cornell Lab Barn Swallow](https://www.allaboutbirds.org/guide/Barn_Swallow/id).
