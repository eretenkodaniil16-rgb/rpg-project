# The Living Scroll V4.2 — Art & Morphing Pass

**Scope:** Iteration on the validated V4.1 model pass. Existing branch `art/living-scroll-v4-model-pass` is preserved; changes are isolated in `art/living-scroll-v4-2-art-morph`.

## Specific engineering changes

1. **V4.2 art generator — `v42_art.py`**
   - Replaces hard polygon mountain ridgelines with a mixture of broad Gaussian massing, seeded low/high-frequency ink variation, pigment stains, fractured ridge ink marks, and pine silhouettes.
   - Splits far/middle/near plans into three separate RGBA layers so parallax remains programmable; paper and cinnabar sun stay on the background plane.
   - All layers remain deterministic, reproducible in GitHub Actions with fixed Python/Pillow/NumPy versions.
   - Important limitation: these are procedurally stylized landscapes, **not a simulation of a master artist's brushwork**. Do not claim equivalence to the original TikTok without inspection.

2. **V4.2 morph controller — `v42.py`**
   - Preserves the full editable V4 3D lotus, birds, architecture, camera and scroll.
   - Adds **96 moving ink dabs**, initially distributed around the blooming lotus; their paths redistribute toward the seven bird trajectories, then fade.
   - Adds **8 controlled sweeping ink-curve strokes** with Blender's bevel-factor animation and **24 atmospheric brush fibers**.
   - The particle system is keyframed, reproducible and not a generic crossfade. It is, however, a stylized redistribution of pigment **rather than a mathematically continuous topology-preserving petal-to-bird mesh morph**.

## Time checkpoints / QA

| Frame | Target and failure modes |
|---:|---|
| 1 | clean paper, falling ink drop, no accidental geometry |
| 48 | emerging 3D lotus |
| 88 | mature lotus with individual organic petals |
| 115 | complete blossom; no pigment sparks yet |
| 139 | visible start of ink splitting; inspect contours |
| 155 | particles actively connect flower to bird trajectories; avoid opaque black blob |
| 175 | bird flock and mountain depth appear; no hard layer cuts |
| 216 | pavilions and birds remain readable; foreground isn't excessively dark |
| 275 | final scroll frame fully visible and spatially balanced |

## Quality gates

- GitHub CI passes `python -m py_compile`, deterministic artwork generation, Blender 5.2 SHA verification, object-contract validation and nine actual EEVEE smoke renders (verified in run 41212702314, CI packaging path then corrected).
- Inspect the downloaded PNG contact sheet; high contrast alone is **not** acceptance. Specific attention to pigment density, organic ridges, contrast, feathered mist, birds and frame crop.
- Do not trigger a full 288-frame render until smoke frames pass. Next iteration should pursue illustrated master assets and improved continuous shape morph if still visibly schematic.

## Run

```bash
python living_scroll_v3/generate_assets.py
python living_scroll_v4/v42_art.py
blender -b --python-exit-code 1 --python living_scroll_v4/v42.py -- --smoke
```

To render a full sequence, use `--full`. The workflow `.github/workflows/living-scroll-v42-ci.yml` handles Blender/FFmpeg and uploads the final video as a GitHub artifact in full mode.

**No extra Blender addons, API keys or model credits are required.**
