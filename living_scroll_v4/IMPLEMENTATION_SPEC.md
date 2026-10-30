# The Living Scroll V4 — Blender implementation specification

## Contract and goals
- **Blender 5.2.0 LTS**, headless EEVEE, 24 FPS, 288 frames (12 seconds).
- Vertical 9:16: QA frames 360×640, full output 720×1280, PNG sequence and H.264 MP4.
- Keep V3 project in `living_scroll_v3/` unmodified; V4 imports its generated 2.5D background layers, **not** the old flat lotus, flat bird sprites or frame rods.
- Source of truth: `living_scroll_v4/scene.py`; the `.blend` output is reproducible.

## Scene collection contracts

| Collection | Objects / main contracts | QA |
|---|---|---|
| V4_00_MASTER | Softbox light, fill light, V3 camera | Lighting is soft, no plastic highlights |
| V4_03_LOTUS | `LOTUS_HERO_CTRL`; 12 outer and 8 inner animated petals, pollen core, veins and ink edges | Flower has relief, readable tips, nonuniform organic geometry |
| V4_04_ATMOSPHERE | Three moving, procedural alpha-noise mist cards | Background remains readable under fog |
| V4_05_ARCHITECTURE | Three linked-concept pavilion constructions: foreground, mid, far | Roof eaves and columns visible at chosen scales |
| V4_06_BIRDS | Seven `BIRD_NN_RIG` roots, each with two articulated wings and forked tail | Wings are individually phased, motion is not synchronized |
| V4_07_SCROLL | `SCROLL_REVEAL_CTRL`, paired 3D wooden cylinders, brass caps/inlays, side piping, tassels | Scroll reveal occupies end without hiding the painting |

## Modeling detail
### Lotus
- Ring 0: 12 petals, length 1.64 Blender units, width factor 0.55.
- Ring 1: 8 petals, length 1.19, width factor 0.47, opens 12 frames later.
- Each petal: parametric **17×9 grid mesh** with material-shaded surfaces, separate red tip, two dark edge curves, and center vein.
- Root controls overall flower transform, petal empties have independent rotation keyframes.
- Key ranges: bloom begins ~frame 22; open by frame 110; transitions out by frames 157–194.

### Pavilion kit
- Three pagodas assembled from a terrace, column extrusions, two elevated roof levels and 3D eaves.
- Scene positions and global scales: foreground (-1.66, -2.05, -2.65) ×0.82; middle (1.51,-1.63,-1.60) ×0.53; distant (-1.25,-1.18,-0.25) ×0.31.
- Reusable Python modeling primitive; geometric variation can be added after successful smoke render.

### Birds
- Seven individual rigs, two wing roots each, thin shaped wing meshes and forked tails.
- 6-frame intervals for wing rotation; index-dependent phase. Flight positions keyframed from ~116 to 288.
- Red feather accents tie the birds to the cinnabar ink palette.

### Scroll
- Two horizontal dark wooden rollers and brass caps/inlays, framed paper piping, lightweight tassel strips.
- Global scale animated 223–273. End composition must be readable without cropping.

### Atmosphere
- Three low-opacity EEVEE transparent-mix noise materials.
- Slow drift on X, never obscure main features or darken the whole composition excessively.

## Expected temporal checkpoints (24 FPS)

| Frame | Target |
|---|---|
| 1 | Paper and a single ink drop; no visible 3D flower |
| 48 | Partial lotus reveal; tips and dark outline visible |
| 88 | Fully readable blooming petals |
| 115 | Flower center and veins hero close-up |
| 146 | Flower→birds transition begins |
| 175 | Depth separation and moving birds, first architecture |
| 216 | Mountain flight and pavilion detail |
| 275 | Framed scroll with visible finishing elements |

Smoke output intentionally samples **eight** frames to catch transitions missed by V3's six-frame test.

## Render gates
1. **Static QA**: Python compilation; make V3 asset layers; verify generated image files exist.
2. **Blender QA**: run `scene.py --smoke` with exact verified Blender 5.2.0. Validate object names, timeline, at least 20 petal meshes, seven bird rigs.
3. **Visual QA**: inspect 8 PNGs, especially missing petals/overdraw, ink contour aliasing, fog opacity, roof clipping and frame reveal.
4. **Full movie gate**: only after acceptable preview. Run `scene.py --full`; encode 288-frame PNG sequence using FFmpeg H.264 yuv420p; inspect final 12-second file.
5. **Regression QA**: do not touch RPG runtime or merge into main; preserve the V3 workflow and files.

## Risks and limits
- V4 is a geometry-first **model pass**, not yet a genuine fluid dynamics solver. Source textures inherited from V3 remain a visual limitation.
- Camera-facing 3D geometry must be QAed: a visually plausible mesh in code may still render poorly at 9:16.
- External Blender addons are not required for the baseline; Grease Pencil, Geometry Nodes and compositor are built in. Add plugins only after identifying a demonstrable need.
- Do not call the version visually approved until real Blender frames have been checked.
