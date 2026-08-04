# Blender Heart Cycle

Procedural Blender foundation for a **frontally cut human heart** with visible chambers, valves and blood-flow guides. The animation timeline follows the nine-phase cardiac-cycle structure used in the Pokrovsky physiology textbook and is expanded to a 15-second educational loop.

## Current model revision

`heart_cutaway_v02`

The second revision keeps the stable phase controls from v01 and adds the first dedicated anatomical refinement pass:

- non-mirrored ventricular proportions, with a longer thick-walled left ventricle and a broader, shorter right ventricle;
- reduced and differentiated mitral, tricuspid, aortic and pulmonary valve assemblies;
- refined papillary-muscle proportions plus a septal papillary muscle for the right ventricle;
- atrial appendage proxies and visible pectinate-muscle ridges;
- left- and right-ventricular trabeculae;
- a right-ventricular moderator band;
- visible LV and RV outflow-tract ridges;
- explicit left and right pulmonary-artery branches;
- revised myocardium, endocardial and valve materials;
- smaller blood-flow guides so anatomy remains visually dominant;
- independent atrial and ventricular deformation controls;
- a 450-frame, 30 FPS timeline with nine named markers;
- a JSON manifest containing Russian phase text, real durations and frame ranges.

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

Use `-RenderAnimation` only when the preview is approved; it renders all 450 PNG frames.

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

## Current review boundary

The v02 CI artifact must be visually reviewed before the geometry is treated as approved. The next pass should focus on leaflet topology, true right-ventricular crescent geometry, endocardial surface integration and a more anatomical relationship between the aortic root, pulmonary root and atrioventricular junctions. After that, the phase rig can be refined beyond uniform controller scaling.
