#!/usr/bin/env python3
"""V4.9.8: time the seven real 3D swallow reveals to the dissolving ink.

High-resolution V4.9.7 QC shows the unwanted dark intermediate stars are
suppressed, but the real swallow rigs still appear too late, leaving a vacant
gap at frame 165. Correct *only* the per-rig visibility-by-scale animation:
advance the bird reveal six frames, and remove the late V4.6 scale reset
anchors that would otherwise make some birds abruptly vanish again.

The 650-vertex source/ink meshes, world-space bird positions and wing joints,
21 other dissolving petals, camera, materials, and 288-frame/24fps edit
remain untouched. True 7-frame renders and contiguous 24fps video are
required before considering this a visually acceptable change.
"""
import bpy
from v46_birds import SCALE_FACTORS

N=7
ADVANCE=6

def build():
    scene=bpy.context.scene
    details=[]
    for ordinal in range(N):
        rig=bpy.data.objects.get("BIRD_%02d_RIG"%ordinal)
        if rig is None:
            raise RuntimeError("V498 missing articulated swallow "+str(ordinal))
        # Original retime_flock keys (v49_silhouette.py):
        # 148+3*i=latent anchor, 159+i=start, 168+i=flock rise,
        # 178+i//2=near-complete bird scale. Those 4 keys are removed.
        # Critically the original 148+3*i anchor for i=5/6 occurs AFTER
        # the new reveal starts; if retained it would create a one-frame
        # "pop-to-zero" artifact in the heart of the morph.
        old=(148+3*ordinal,159+ordinal,
             168+ordinal,178+ordinal//2)
        for frame in old:
            if not rig.keyframe_delete(data_path="scale",frame=frame):
                raise RuntimeError("Missing previous bird scale key %s f%d" %
                                   (rig.name,frame))
        factor=SCALE_FACTORS[ordinal]
        # Defer the emergence no earlier than original f153; the feathered
        # ink lamina is still visually apparent at f153 and largely gone by
        # f165, so scale now overlaps with the late watercolor wash.
        keys=((148+ordinal,.001),
              (153+ordinal,.001),
              (162+ordinal,.24),
              (172+ordinal//2,.47))
        for frame,value in keys:
            s=max(.0001,float(value)*factor)
            rig.scale=(s,s,s)
            rig.keyframe_insert(data_path="scale",frame=frame)
        details.append({"bird":ordinal,"factor":factor,
                        "small_reveal_begin":153+ordinal,
                        "flight_reaches_reference_size":162+ordinal})
    timeline=[]
    for frame in (132,133,153,155,159,162,165,170,175,185):
        scene.frame_set(frame)
        sizes=[float(max(bpy.data.objects["BIRD_%02d_RIG"%i].scale))
               for i in range(N)]
        count=sum(size>.04 for size in sizes)
        timeline.append({"frame":frame,"active_birds":count,
                         "scales":[round(x,5) for x in sizes]})
        if frame==155 and max(sizes)>.025:
            raise RuntimeError("Premature swallow before folded petal dispersal")
        if frame==165 and count<6:
            raise RuntimeError("V498 still leaves an empty flock at frame 165")
        if frame==175 and count!=7:
            raise RuntimeError("All seven small articulated birds must be visible")
        if frame==185 and min(sizes)<.1:
            raise RuntimeError("Legacy bird arrival regression")
    scene.frame_set(132)
    for ordinal in range(N):
        ob=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%ordinal)
        if ob is None or len(ob.data.vertices)!=650:
            raise RuntimeError("Petal carrier topology modified")
        if abs(ob.data.shape_keys.key_blocks["Ink_Wing"].value)>1e-6:
            raise RuntimeError("Premature mesh deformation at handoff")
    scene.frame_set(1)
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("Master 12-second 24fps timing changed")
    result={"bird_rigs_retimed":7,"advance_frames":ADVANCE,
            "world_flight_paths_unchanged":True,
            "original_carrier_mesh_topology":650,
            "scene_frames":288,"fps":24,
            "timeline_sample":timeline,"bird_details":details}
    print("V498_SYNCED_REAL_SWALLOW_REVEAL_QA_PASS",result,flush=True)
    return result
