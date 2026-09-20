# Action potential Blender models v03

Standalone Blender 4.x/5.x model builder for the membrane/action-potential educational animation.

## What changed in v03

- Enlarged and thickened phospholipid bilayer with larger heads and curved hydrocarbon tails.
- Rebuilt Na+/K+-ATPase as an asymmetric multi-lobed protein rather than two simple primitives.
- Added Na+ and K+ binding-pocket cues to the pump.
- The Na+/K+-ATPase remains active throughout the action potential; the demo animation uses a slow repeating conformational cycle rather than an inactivation state.
- Rebuilt the voltage-gated Na+ channel with a clear central pore, activation-gate leaves, selectivity-filter rings and a separate red inactivation particle/tether.
- Rebuilt the voltage-gated K+ channel with a clear pore and delayed gate opening.
- Added example state keyframes: Na channel closed -> open -> inactivated -> recovered; K channel closed -> delayed open -> closed.
- Enlarged Na+, K+ and Cl- ions and reduced their density so labels and particles do not overlap excessively.
- Added Cl- as a background ion without making chloride the dominant mechanism of the neuronal action potential.
- Improved protein/ion materials with controlled transmission, subsurface contribution, emission accents and four-point lighting.

## Output

Run `refined_models_v03.py` from Blender. It saves:

`action_potential_models_v03.blend`

The generated `.blend` is a reusable model pack. The full 90-second animation generator can use the model roots:

- `NaK_ATPase_Root`
- `NaChannel_Root`
- `KChannel_Root`
- `Membrane_Root`

## Demo state frames

The standalone model pack uses frames 1–180 only to demonstrate geometry/state transitions:

- frame 1: resting configuration
- frame 60: Na+ channel open
- frame 120: Na+ channel inactivated, K+ channel open
- frame 180: recovered/closed configuration

These are not intended as the final physiological timing; the 90-second video generator maps these states to the educational timeline.

## 90-second integration v04

`action_potential_video_v04.py` executes the refined model builder and remaps the reusable model states onto the educational 90-second timeline. The integration adds phase-specific Na+ and K+ fluxes, slow background Cl- drift, continuous Na+/K+-ATPase transport, a membrane-potential graph with axes/threshold/current-phase highlight, a moving Vm marker, absolute and relative refractory-period overlays, and subtle camera emphasis.

The validation workflow `validate-action-potential-blender.yml` runs the generator in preview mode, saves `action_potential_pokrovsky_v04.blend`, and renders representative keyframes for rest/local depolarization/depolarization/repolarization/hyperpolarization/recovery before any full-resolution movie render is attempted.
