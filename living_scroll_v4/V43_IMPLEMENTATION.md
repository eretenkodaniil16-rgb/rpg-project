# The Living Scroll V4.3 — Grease Pencil and Shape Morphing

## Target
Smoother morph from 3D lotus to ink swallow silhouettes, without relying on more particles or a text-to-video model. Preserve working V4.2.1 scene and source branch.

## New systems

- `v43.py`: imports existing `v42` / `scene` to build the same art, camera and 3D pavilion models.
- 20 **mesh shape keys** (`V43_Into_Ink_Feather`) deform actual lotus petal geometry between frames 137 and 170. The V4 root scale still contracts, so this is geometric deformation as one part of the metamorphosis, not a fully continuous one-object morph.
- Blender 5.2 **Grease Pencil v3** data-block with 14 tapered strokes × 18 points, driven by explicit per-frame drawings at two-frame intervals from 118 to 210. The calligraphic contours interpolate from lotus petal paths into the positions of seven swallows, then dissolve.
- Two materials now use procedural noise → ColorRamp to create nonuniform pigment on 3D lotus surfaces, reducing flat CG look.
- 14 individual wing meshes receive slight geometry bends to preserve a hand-drawn outline.
- The 96 existing particle dabs of V4.2.1 are retained, but no extra particle load is introduced.

## Acceptance criteria
1. Headless Blender 5.2.0 builds the scene with actual type `GREASEPENCIL`, 20 petal shape keys, 14 wing meshes, and ≥40 GP drawings.
2. No frame has missing or all-black calligraphic marks due to GP material incompatibility.
3. Test frames: 88 (lotus), 139 (first deformation), 155 (mid morph), 175 (wings), 216 (landscape), 275 (scroll).
4. Keep bird flock readable and avoid dark pigment clumping at frame 155/175.
5. Full MP4 deferred until selected control frames are visually inspected.

## Deployment
- Branch: `art/living-scroll-v4-3-grease-pencil`.
- Workflow: `.github/workflows/living-scroll-v43-ci.yml`.
- Reuses V3 generation + V4.2 art generation before Blender.
- Full renderer optional; baseline = six 360×640 control frames and packed editable .blend.

## Scientific/engineering honesty
The GP geometry has frame-quantized motion at 2-frame increments and is an auxiliary artistic contour system. The petals' mesh shape keys remain parented to a shrinking flower root. This is **not** a fluid simulation, a physically accurate ink-on-paper diffusion model, or a topology-preserving mesh-to-bird conversion.

## Extensibility
After visual QA, pursue graded opacity masks on original petal geometry and Bézier-spline tracking to align wing shapes at exact frame 175 rather than just approximate their centers. 
