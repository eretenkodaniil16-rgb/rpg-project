#!/usr/bin/env python3
"""Living Scroll V4.9: watercolor-pigment flower and clean frame-133 handoff.

Smoke renders 8 stills and 48 consecutive genuine Blender frames (132..179).
Full renders the original 12s/288f film without changing the edit.
"""
import argparse
from pathlib import Path
import sys
import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v48
import v49_ink
import v49_handoff
import v49_silhouette
import v49_painterly
import v493_slender_morph
import v494_dissolve
import v495_staggered_swallows
import v496_folded_ribbon
import v497_ink_release
import v498_swallow_reveal
import v499_petal_separation

OUT = HERE / 'renders_v49'
STILLS = OUT / 'stills'
CLIP = OUT / 'clip'
STILLS.mkdir(parents=True, exist_ok=True)
CLIP.mkdir(parents=True, exist_ok=True)

def render_frame(scene, frame, path):
    scene.frame_set(frame)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

def build(mode):
    v48.build('probe')
    metrics = v49_ink.build()
    metrics.update(v49_painterly.build())
    metrics.update(v49_silhouette.build())
    metrics.update(v493_slender_morph.build())
    metrics.update(v49_handoff.build())
    metrics.update(v494_dissolve.build())
    metrics.update(v495_staggered_swallows.build())
    metrics.update(v496_folded_ribbon.build())
    metrics.update(v497_ink_release.build())
    metrics.update(v498_swallow_reveal.build())
    metrics.update(v499_petal_separation.build())
    scene = bpy.context.scene
    if (scene.frame_end, scene.render.fps) != (288, 24):
        raise RuntimeError('Original 12-second, 24fps timeline changed')
    scene.frame_set(1)
    scene.render.resolution_x = 360 if mode == 'smoke' else 720
    scene.render.resolution_y = 640 if mode == 'smoke' else 1280
    scene.render.resolution_percentage = 100
    bpy.ops.file.pack_all()
    packed = HERE / 'living_scroll_v49.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(packed))
    print('V49_BUILD_QA_PASS', metrics, packed, flush=True)
    if mode == 'probe':
        return
    if mode == 'smoke':
        for f in (120, 132, 133, 141, 153, 165, 175, 185):
            render_frame(scene, f, STILLS / ('smoke_%03d' % f))
            print('V49_STILL_OK', f, flush=True)
        scene.render.resolution_x = 144
        scene.render.resolution_y = 256
        for f in range(132, 180):
            render_frame(scene, f, CLIP / ('clip_%04d' % f))
            if (f - 132) % 8 == 0:
                print('V49_CONTIGUOUS_PROGRESS', f, flush=True)
        print('V49_48_CONSECUTIVE_FRAMES_OK', flush=True)
    else:
        for f in range(1, 289):
            render_frame(scene, f, OUT / ('frame_%04d' % f))
            if f % 24 == 0:
                print('V49_FULL_PROGRESS', f, flush=True)
    scene.render.filepath = '//'
    print('V49_RENDER_COMPLETE', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--full', action='store_true')
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    args = parser.parse_args(a)
    if sum((args.probe, args.smoke, args.full)) != 1:
        parser.error('Choose exactly one mode')
    build('probe' if args.probe else 'smoke' if args.smoke else 'full')
