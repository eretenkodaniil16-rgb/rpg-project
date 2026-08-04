# Blender Heart Cycle

Procedural Blender foundation for a **frontally cut human heart** with visible chambers, valves and blood-flow guides. The animation timeline follows the nine-phase cardiac-cycle structure used in the Pokrovsky physiology textbook and is expanded to a 15-second educational loop.

## Current model revision

`heart_cutaway_v02_phase_rig_v03`

The current stage combines the anatomy refinement pass `heart_cutaway_v02` with the first physiological phase rig `heart_cycle_phase_rig_v03`.

### Anatomy v02

- non-mirrored ventricular proportions, with a longer thick-walled left ventricle and a broader, shorter right ventricle;
- reduced and differentiated mitral, tricuspid, aortic and pulmonary valve assemblies;
- refined papillary-muscle proportions plus a septal papillary muscle for the right ventricle;
- atrial appendage proxies and visible pectinate-muscle ridges;
- left- and right-ventricular trabeculae;
- a right-ventricular moderator band;
- visible LV and RV outflow-tract ridges;
- explicit left and right pulmonary-artery branches;
- revised myocardium, endocardial and valve materials;
- smaller blood-flow guides so anatomy remains visually dominant.

### Phase rig v03

- independent left- and right-ventricular deformation profiles;
- volume-preserving shape change during asynchronous and isometric contraction;
- distinct rapid-ejection, slow-ejection and filling deformation states;
- progressive atrial filling during ventricular systole;
- continuous AV and semilunar valve opening fractions instead of binary switching;
- delayed left/right tension during asynchronous contraction;
- phase-specific fast, slow and brief-reverse blood-flow intensity;
- keyframed left/right atrial and ventricular pressures;
- keyframed aortic and pulmonary-artery pressures;
- keyframed normalized atrial and ventricular volume channels;
- a seamless loop boundary between frame 450 and frame 1;
- nine mid-phase preview renders for visual validation;
- an extended JSON manifest describing the rig and preview frames.

This remains an educational procedural model and is not intended for diagnostic visualization.

## Build on Windows

Double-click:

```text
01_BUILD_HEART_CYCLE.cmd
```

The launcher looks for Blender 5.2 first and writes output to:

```text
artifacts/blender_heart_cycle/
```

PowerShell usage:

```powershell
.\tools\blender_heart_cycle\run_blender_heart_cycle.ps1 `
  -BlenderExe "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  -RenderPreview
```

`-RenderPreview` creates the principal preview plus nine phase-specific PNG files in `phase_previews/`.

Use `-RenderAnimation` only after the nine phase previews are approved; it renders all 450 PNG frames.

## Timeline

| Phase | Frames | Real duration |
|---|---:|---:|
| Систола предсердий | 1–56 | 0.10 s |
| Асинхронное сокращение | 57–84 | 0.05 s |
| Изометрическое сокращение | 85–101 | 0.03 s |
| Быстрое изгнание | 102–169 | 0.12 s |
| Медленное изгнание | 170–242 | 0.13 s |
| Протодиастолический период | 243–264 | 0.04 s |
| Изометрическое расслабление | 265–309 | 0.08 s |
| Быстрое наполнение | 310–354 | 0.08 s |
| Медленное наполнение | 355–450 | 0.17 s |

## Review boundary

The v03 CI artifact must be reviewed across all nine phase previews before rendering the complete 450-frame sequence. The next pass should correct any visible chamber intersections, excessive valve travel or flow-guide occlusion, then add the educational compositor with the Russian phase title, explanatory text and duration panel.
