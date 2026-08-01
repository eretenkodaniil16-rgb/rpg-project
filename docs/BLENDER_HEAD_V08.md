# human_warrior_m01 — head v08 / proxy v11

## Scope

This revision changes only the hair structure of the existing modular Blender
proxy. The approved idle references are the visual authority for the hair
silhouette. `silhouette v03`, the cranium, face, body rig, camera, baseline,
equipment sides and animation keys remain locked.

## Reason for the revision

`proxy_v10` used too many independent hair accents. After nearest-neighbour
normalization to 96×96, the accents became isolated bumps and long side locks
instead of the compact medium-length wavy hairstyle visible in the approved
idle references.

## Hair structure

`head v08 / proxy v11` replaces the fragmented hair arrangement with five
connected zones:

1. a broad coherent top cap;
2. a compact front crown and hairline;
3. two short side masses at the temples;
4. a broad rear shell and crown bridge;
5. a compact three-part nape.

The characteristic asymmetric forelock remains separate, but it is connected
to the front crown through a root piece. Only two temple curls and two rear
texture accents remain as secondary details. The `proxy_v10` top-wave bumps,
sideburns and three isolated rear crests are intentionally not reused.

The selective mesh-density contract is unchanged from `head v07`: cranium
24×14, jaw 20×12, hair cap 24×14, primary hair 20×12, secondary hair 16×10,
tertiary hair 12×8 and a ten-sided nose. The change is arrangement and
consolidation, not another polygon-density increase.

## Locked parameters

The following are copied exactly from `head v07 / proxy v10`:

- head-base size and location;
- jaw, ears and nose;
- brows, eyes and mouth;
- all separate skin masses and dark face details;
- all mesh-density tiers;
- `silhouette v03`, body modules and the 21-bone rig;
- camera elevation 47°, orthographic scale and baseline `y=91`;
- physical equipment sides and `idle` / `walk_down` keys.

## Approval boundary

A successful Blender run is not visual approval. The generated `.blend`, PNGs
and texture slots remain run artifacts until the new three-row contact sheet is
reviewed. Nothing from this revision may be copied to `source/`,
`textures/approved/`, gameplay assets or a Godot atlas before explicit owner
approval.
