#!/usr/bin/env python3
"""V4.10.0 real temporal smoke, 24 consecutive Blender frames at 24 FPS.

The in-between-to-bird swap is evaluated in a true 1.0-second continuous
sequence (frames 150..173), not synthesized by optical flow or interpolation.
This test is isolated from the approved source of PR #113.
"""
import json
import math
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v49

BEGIN,END,FPS=150,173,24
OUT=HERE/"temporal_v410"
OUT.mkdir(parents=True,exist_ok=True)

def main():
    v49.build("probe")
    scene=bpy.context.scene
    if scene.frame_end!=288 or scene.render.fps!=FPS:
        raise RuntimeError("Original film timing regression")
    scene.render.resolution_percentage=100
    scene.render.resolution_x=144
    scene.render.resolution_y=256
    scene.render.image_settings.file_format="PNG"
    timeline=[]
    for frame in range(BEGIN,END+1):
        scene.frame_set(frame)
        carriers=[bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i] for i in range(7)]
        birds=[bpy.data.objects["BIRD_%02d_RIG"%i] for i in range(7)]
        scales=[o.scale.x for o in carriers]
        if any((not math.isfinite(s)) or s<0 for s in scales):
            raise RuntimeError("Invalid morph scale at "+str(frame))
        active=sum(not o.hide_render and o.scale.x>.02 for o in carriers)
        bird_count=sum(max(o.scale)>.04 for o in birds)
        timeline.append({"frame":frame,"active_ink_carriers":active,
                         "visible_small_bird_rigs":bird_count,
                         "mean_carrier_scale":round(sum(scales)/7,6)})
        scene.render.filepath=str(OUT/("clip_%04d.png"%frame))
        bpy.ops.render.render(write_still=True)
        print("V410_TRUE_FRAME_OK",frame,flush=True)
    report={
        "version":"V4.10.0","first_frame":BEGIN,"last_frame":END,
        "genuine_blender_frames":END-BEGIN+1,"fps":FPS,
        "seconds":(END-BEGIN+1)/FPS,"resolution":[144,256],
        "synthetic_inbetweens":False,"film_full_length_frames":scene.frame_end,
        "timeline":timeline,
    }
    (OUT/"temporal_scene_report.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("V410_24_FRAME_TEMPORAL_RENDER_PASS",flush=True)

if __name__=="__main__":
    main()
