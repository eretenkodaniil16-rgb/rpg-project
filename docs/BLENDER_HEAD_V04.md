# Head v04 / proxy v07 — detailed face and hair pass

This revision continues the accepted `silhouette v03` body and the `head v03`
candidate. It does not alter the body rig, camera, baseline, orthographic
scale, equipment sides, `idle`, or `walk_down`.

The active entry point is:

```text
tools/blender_sprite_factory/blender_sprite_factory_head_v04.py
```

It reuses the existing Blender Sprite Factory and replaces only the head
builder for this revision. The previous `head v01`, `head v02`, and `head v03`
profiles remain reproducible in `head_profile.py`.

## Geometry changes

`head v04 / proxy v07` keeps the cranium location and scale from `head v03`.
The production mesh density is increased only for head geometry:

- cranium: 20 segments / 12 rings;
- jaw: 18 segments / 10 rings;
- ears: 12 segments / 8 rings;
- hair cap: 20 segments / 12 rings;
- main hair masses: 16 segments / 10 rings;
- secondary locks: 12 segments / 7 rings;
- nose: 8 vertices.

Separate facial masses are added for both brow ridges, the nose bridge, both
cheeks, the chin, and the lower-lip plane. Eyes and mouth receive separate
upper-lid, mouth-corner, and lower-lip-shadow pieces.

Hair is split into crown, characteristic forelock, temples, side locks, back
waves, nape, top waves, curls, ripples, and nape tips. No negative scale or
mirrored direction is introduced.

## Review boundary

More polygons do not automatically improve a 96x96 result. The geometry is
intentionally limited and must still survive the 192x192 render,
nearest-neighbor normalization, binary alpha, and palette quantization.

The revision remains a candidate until a new three-row `contact_sheet.png` is
visually approved. Do not copy its `.blend`, textures, frames, or atlas into
approved or gameplay directories before that approval.
