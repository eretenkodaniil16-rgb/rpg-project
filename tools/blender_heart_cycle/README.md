# Blender Heart Cycle

Procedural Blender model of a **frontally cut human heart** with visible chambers, valves, internal relief, blood-flow guides and a Russian educational overlay. The scene follows the nine-phase cardiac-cycle structure used in the Pokrovsky physiology textbook and presents it as a 15-second loop.

## Current revision

`heart_cutaway_reference_layout_v05_phase_rig_v03_infographic_v04_presentation_v06_animation_v07`

The current branch keeps the successful first-preview chamber layout, adds the anatomical refinement pass, drives the chambers and valves through nine physiological phases, and exports a resumable PNG frame sequence that is encoded into MP4 and GIF with FFmpeg.

### Anatomy v02

- differentiated left and right ventricular anatomy;
- mitral, tricuspid, aortic and pulmonary valve assemblies;
- papillary muscles and chordae tendineae;
- atrial appendages and pectinate-muscle ridges;
- left- and right-ventricular trabeculae;
- right-ventricular moderator band;
- LVOT and RVOT ridges;
- pulmonary-artery bifurcation;
- revised myocardium, endocardial and valve materials.

### Phase rig v03

- independent left- and right-ventricular deformation profiles;
- approximately isovolumetric shape change during tension and relaxation;
- separate rapid/slow ejection and filling states;
- continuous AV and semilunar valve-opening fractions;
- delayed left/right ventricular tension during asynchronous contraction;
- phase-specific direct and brief reverse blood flow;
- animated chamber pressures and normalized volumes;
- Blender 5.2 layered Actions / Action Slots support;
- seamless physiological boundary between frames 450 and 1.

### Infographic v04

- Russian phase card for each of the nine phases;
- phase index, title, physiological description and real duration;
- AV- and semilunar-valve state labels;
- camera-parented UI and cross-platform Cyrillic font lookup;
- principal composed preview and nine mid-phase previews.

### Corrected layout v05

- chamber coordinates restored from the approved first preview;
- ventricles kept below the atria by a runtime anatomical validator;
- the left ventricle again forms the inferior apex;
- layout metrics written into the JSON manifest;
- dependent cavities, septum and internal structures remain synchronized.

### Presentation polish v06

- canonical flow visibility at every phase boundary;
- validation of expected and visible flow groups in all nine phases;
- title confined to the left header card;
- heart shifted right and slightly down to prevent aortic text occlusion.

### Animation export v07

- full authored timeline: 450 frames at 30 FPS, 15 seconds;
- review profile: every second source frame, 225 frames at 15 FPS, still 15 seconds;
- default review resolution: 640×360;
- final-quality profile retained at all 450 frames and 30 FPS;
- Blender renders a lossless, resumable PNG sequence in `review_frames/`;
- external FFmpeg encoding produces H.264/MPEG-4, palette-based GIF and a poster frame;
- automatic MP4 frame-count, resolution, FPS and duration verification;
- failed encoding preserves the PNG sequence for recovery;
- successful CI delivery removes the bulky intermediate frames;
- export metadata written into `heart_cycle_manifest.json`.

Blender's own direct video output is intentionally not required. The frame-sequence workflow is more recoverable: a stopped render keeps completed PNG files, and encoding can be repeated without rerendering the 3D scene.

This remains an educational procedural model and is not intended for diagnostic visualization.

## Windows launchers

Build the `.blend`, principal preview and nine phase previews:

```text
01_BUILD_HEART_CYCLE.cmd
```

Render the 15-second 360p/15 FPS review sequence and encode MP4 when FFmpeg is installed:

```text
02_RENDER_HEART_CYCLE_REVIEW.cmd
```

Both launchers look for Blender 5.2 first and write to:

```text
artifacts/blender_heart_cycle/
```

When FFmpeg is absent, the second launcher keeps all completed PNG files and prints their location. The GitHub animation workflow includes FFmpeg and performs MP4/GIF encoding automatically.

## PowerShell usage

Control-frame and model build:

```powershell
.\tools\blender_heart_cycle\run_blender_heart_cycle.ps1 `
  -BlenderExe "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  -RenderPreview `
  -Resolution 720
```

Review animation:

```powershell
.\tools\blender_heart_cycle\run_blender_heart_cycle.ps1 `
  -RenderAnimation `
  -AnimationResolution 360 `
  -SampleStep 2
```

Full 30 FPS animation:

```powershell
.\tools\blender_heart_cycle\run_blender_heart_cycle.ps1 `
  -RenderAnimation `
  -AnimationResolution 720 `
  -SampleStep 1 `
  -VideoBitrate 8000
```

The review profile is intended for rapid evaluation of motion, valve timing, flow visibility and phase-card transitions. The full-quality profile is substantially more expensive to render.

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

The v07 review animation must be inspected before the expensive 720p/30 FPS export. Review should focus on the continuity of ventricular deformation, valve timing, arrow direction, flow disappearance at phase boundaries, text transitions and the seam from the final frame back to frame 1.
