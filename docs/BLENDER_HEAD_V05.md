# human_warrior_m01 — head v05 / proxy v08

## Scope

This revision changes only the head, face and hair production geometry. The
accepted `silhouette v03`, body rig, body bones, camera, orthographic scale,
baseline, equipment sides and animation keys remain locked.

## Geometry changes

- cranium: 24 segments / 14 rings;
- jaw: 20 segments / 12 rings;
- ears: 14 segments / 9 rings;
- hair cap: 24 segments / 14 rings;
- primary hair masses: 20 segments / 12 rings;
- secondary hair masses: 16 segments / 10 rings;
- tertiary hair locks: 12 segments / 8 rings;
- nose: 10-sided frustum.

The cranium scale and location are copied verbatim from `head v04`. The jaw is
slightly narrower, shorter and higher. Brows, eyes and mouth have independent
vertical pixel budgets. The face is split into brow ridges, nose bridge,
cheekbones, jaw planes, philtrum, lower-lip plane and chin.

Hair uses connected crown, forelock, temple, side, back-crest, ripple and nape
masses. The rear crown is raised locally to restore the missing `idle_up`
height without changing the body or render scale.

## Versioning

- active head revision: `v05`;
- active proxy revision: `v08`;
- previous `head v04 / proxy v07` remains reproducible in separate source files;
- the active profile, previous profile and adapter SHA-256 values are written to
  `run_manifest.json`.

## Approval boundary

This is a visual candidate only. Do not copy its `.blend`, textures or PNGs to
approved source directories or Godot assets until the new three-row contact
sheet has been reviewed and explicitly accepted.
