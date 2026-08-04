# Blender Heart Cycle

Procedural Blender foundation for a **frontally cut human heart** with visible chambers, valves and blood-flow guides. The animation timeline follows the nine-phase cardiac-cycle structure used in the Pokrovsky physiology textbook and is expanded to a 15-second educational loop.

## Current model revision

`heart_cutaway_v01`

The first revision deliberately prioritizes a stable, editable anatomical hierarchy over final sculptural realism. It creates:

- left and right atrial and ventricular cutaway shells;
- visible chamber surfaces and interventricular septum;
- mitral, tricuspid, aortic and pulmonary valve assemblies;
- chordae tendineae and papillary muscle proxies;
- aorta, pulmonary trunk, venae cavae and pulmonary veins;
- red/blue flow-arrow groups;
- independent atrial and ventricular deformation controls;
- a 450-frame, 30 FPS timeline with nine named markers;
- a JSON manifest containing Russian phase text, real durations and frame ranges.

This is an educational procedural proxy and is not intended for diagnostic visualization.

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

## Next anatomical pass

The next pass should refine the ventricular asymmetry, right-ventricular crescent geometry, atrial appendages, outflow tract continuity, valve leaflet topology and endocardial trabeculation before final materials and infographic compositing are locked.
