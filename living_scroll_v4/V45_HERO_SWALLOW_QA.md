# V4.5 — Hero Swallow Pass / Hybrid Realism

## Reference and modeling stance
Reference species: Barn Swallow (*Hirundo rustica*). Shape cues from Cornell Lab / Macaulay Library: https://www.allaboutbirds.org/guide/Barn_Swallow/id . The swallows are **original procedural models**, not replicas of photographs or licensed 3D meshes. Intent is an anatomically *informed* stylization with smooth 3D forms and ink-friendly rendering, not exact field-guide anatomy or a realistic wing aeroelastic solver.

## Contents
- `v45_birds.py`: seven birds built on the existing V4 joint/flight animation; layered 3D torso, ventral plumage, head, eyes, small beak, rust throat, deep forked tail and long streamers.
- 12 modeled primary feathers **per wing**, 8 modeled secondaries **per wing**: 7 × 2 × (12+8) = **280 individual flight-feather meshes**.
- A two-segment wing control: existing animated shoulder pivot plus new asynchronous carpometacarpal control. Feathers have finite curvature and tapered outlines.
- Dark cobalt-tinted dorsal material, warm pale belly, chestnut throat; deliberately low sheen and earthy palette to integrate with watercolor background.
- Legacy polygon body/wing/tail meshes hidden (not destroyed); existing 7 bird rigs retained with original path/scale animation and a subtle independent bank.
- `v45.py` calls proven V4.4 scene builder in probe mode, adds the bird asset kit, then renders four timeline frames and two dedicated closeups. It saves `living_scroll_v45.blend`.

## QA / acceptance criteria
1. Python compiles, pinned Blender 5.2 builds and validates **7 rigs / 280 feather meshes**, and 288-frame × 24fps contract.
2. End-to-end smoke renders 155,175,205,235 and detail views 175 and 205.
3. Bird closeups should show curved elongated wings, individual flight feathers, large forked tail, dark dorsal plumage and paler belly. The look must not regress to paper-thin triangular wings.
4. Flock remains distinguishable at 360×640 without visual obstruction by hero lotus; natural variations in phase.
5. Real run inspected in comparison with V4.4.1 before running 288-frame full MP4.
6. Video pipeline isolated in branch `art/living-scroll-v4-5-hero-swallows`; RPG runtime unaffected.

## Limitations and next tasks
- Feathers are distinct rigid geometry. This is **not** a physically faithful simulated wing skeleton, detailed individual barb microstructure, or proven photorealism. Distal wing rotation is an approximation.
- Performance can be an issue on CPU EEVEE; use LOD/instancing if the full 288-frame render is costly.
- Post-QA: improve scroll's paper surface and lacquer roller material, refine architecture, then scene-integrated volumetric haze and synchronized geometric GP morph.

No paid Blender addons, AI video credits or external ZIP uploads required.
