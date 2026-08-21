# Blender 4.x/5.x integration stage for the action-potential educational video.
# Reuses refined_models_v03.py, remaps the model states onto a 90 s timeline,
# adds phase-aware ion motion, membrane-potential graph, refractoriness bands,
# and saves a render-ready .blend.
#
# Run from repository root:
#   blender --background --python tools/biomedical_visualization/action_potential/action_potential_video_v04.py

import math
import os
import runpy
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 30
DURATION = 90
FRAME_END = FPS * DURATION
PREVIEW = os.getenv("AP_PREVIEW", "0") == "1"

T = {
    "intro0": 0, "intro1": 8,
    "rest0": 8, "rest1": 23,
    "local0": 23, "local1": 31,
    "threshold0": 31, "threshold1": 36,
    "depol0": 36, "depol1": 52,
    "repol0": 52, "repol1": 64,
    "hyper0": 64, "hyper1": 74,
    "recover0": 74, "recover1": 83,
    "summary0": 83, "summary1": 90,
    "abs_ref0": 36, "abs_ref1": 64,
    "rel_ref0": 64, "rel_ref1": 77,
}


def fr(sec):
    return max(1, min(FRAME_END, int(round(sec * FPS))))


# -----------------------------------------------------------------------------
# Build the refined reusable model pack first.
# -----------------------------------------------------------------------------
MODEL_SCRIPT = Path(__file__).with_name("refined_models_v03.py")
ns = runpy.run_path(str(MODEL_SCRIPT))
M = ns["M"]
COL = {
    "bg": (0.004, 0.010, 0.028),
    "white": (0.92, 0.96, 1.00),
    "muted": (0.42, 0.52, 0.66),
    "red": (0.86, 0.10, 0.12),
    "yellow": (1.00, 0.64, 0.04),
    "cyan": (0.00, 0.82, 1.00),
    "panel": (0.010, 0.022, 0.050),
}

sphere = ns["sphere"]
cube = ns["cube"]
tube = ns["tube"]
text = ns["text"]


def make_mat(name, color, rough=.3, emission=0.0, transmission=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1.0)
    bs.inputs["Roughness"].default_value = rough
    if "Transmission Weight" in bs.inputs:
        bs.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bs.inputs:
        bs.inputs["Transmission"].default_value = transmission
    if emission:
        if "Emission Color" in bs.inputs:
            bs.inputs["Emission Color"].default_value = (*color, 1.0)
            bs.inputs["Emission Strength"].default_value = emission
        elif "Emission" in bs.inputs:
            bs.inputs["Emission"].default_value = (*color, 1.0)
            bs.inputs["Emission Strength"].default_value = emission
    return m


UI = {
    "white": make_mat("M_UIWhite", COL["white"], .30),
    "muted": make_mat("M_UIMuted", COL["muted"], .36),
    "red": make_mat("M_UIRed", COL["red"], .20, .35),
    "yellow": make_mat("M_UIYellow", COL["yellow"], .18, .70),
    "cyan": make_mat("M_UICyan", COL["cyan"], .16, 1.0),
    "panel": make_mat("M_UIPanel", COL["panel"], .58),
}


def set_linear(obj):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def clear_anim(name):
    o = bpy.data.objects.get(name)
    if o:
        o.animation_data_clear()
    return o


def key_scale(o, frame, value):
    o.scale = value
    o.keyframe_insert("scale", frame=frame)


def key_loc(o, frame, value):
    o.location = value
    o.keyframe_insert("location", frame=frame)


def show_between(o, s0, s1, fade_frames=2):
    base = o.scale.copy()
    key_scale(o, max(1, fr(s0)-fade_frames), base * 0.001)
    key_scale(o, fr(s0), base)
    key_scale(o, fr(s1), base)
    key_scale(o, min(FRAME_END, fr(s1)+fade_frames), base * 0.001)
    set_linear(o)


def hide_object(o):
    if o:
        o.hide_render = True
        o.hide_viewport = True


# -----------------------------------------------------------------------------
# Replace demo 1-180 state keys with the 90-second physiological timeline.
# -----------------------------------------------------------------------------
for name in (
    "Na_ActivationGate_L", "Na_ActivationGate_R", "Na_InactivationBall",
    "Na_InactivationTether", "K_Gate_L", "K_Gate_R"
):
    clear_anim(name)

na_l = bpy.data.objects["Na_ActivationGate_L"]
na_r = bpy.data.objects["Na_ActivationGate_R"]
na_ball = bpy.data.objects["Na_InactivationBall"]
na_tether = bpy.data.objects["Na_InactivationTether"]
k_l = bpy.data.objects["K_Gate_L"]
k_r = bpy.data.objects["K_Gate_R"]

na_x = 0.35
k_x = 2.75

# Na+ activation gate: closed -> opens rapidly at threshold -> closes while inactivated -> recovers.
for sec, off in [
    (8, .12), (31, .12), (36.2, .32), (51.4, .32), (52.2, .12),
    (73.5, .12), (77.0, .12), (90, .12),
]:
    key_loc(na_l, fr(sec), (na_x-off, -.18, -.49))
    key_loc(na_r, fr(sec), (na_x+off, -.18, -.49))
set_linear(na_l); set_linear(na_r)

# Distinct fast Na+ channel inactivation particle.
ball_base = Vector((.14, .11, .14))
tether_base = Vector((1, 1, 1))
for obj, base in [(na_ball, ball_base), (na_tether, tether_base)]:
    key_scale(obj, fr(8), base * .001)
    key_scale(obj, fr(49.8), base * .001)
    key_scale(obj, fr(52.0), base)
    key_scale(obj, fr(67.0), base)
    key_scale(obj, fr(74.5), base * .001)
    key_scale(obj, fr(90), base * .001)
    set_linear(obj)

# Delayed rectifier K+ channel: closed during Na+ upstroke, opens for repolarization/hyperpolarization.
for sec, off in [
    (8, .13), (47.0, .13), (52.0, .34), (69.5, .34), (74.0, .28),
    (77.0, .13), (90, .13),
]:
    key_loc(k_l, fr(sec), (k_x-off, -.18, -.45))
    key_loc(k_r, fr(sec), (k_x+off, -.18, -.45))
set_linear(k_l); set_linear(k_r)

# Existing model-pack labels only name the proteins; keep them. Add clean non-overlapping state labels.
state_texts = []
def state_label(name, body, x, z, material, s0, s1):
    o = text(name, body, (x, -.70, z), .24, material)
    show_between(o, s0, s1)
    state_texts.append(o)
    return o

state_label("NaStateClosedA", "закрыт", na_x, 1.18, UI["white"], 8, 36)
state_label("NaStateOpen", "открыт", na_x, 1.18, M["na_hi"], 36, 52)
state_label("NaStateInactivated", "инактивирован", na_x, 1.18, M["red"], 52, 74.5)
state_label("NaStateClosedB", "закрыт", na_x, 1.18, UI["white"], 74.5, 90)
state_label("KStateClosedA", "закрыт", k_x, 1.18, UI["white"], 8, 51.5)
state_label("KStateOpen", "открыт", k_x, 1.18, M["k_hi"], 51.5, 76.5)
state_label("KStateClosedB", "закрыт", k_x, 1.18, UI["white"], 76.5, 90)


# -----------------------------------------------------------------------------
# Ion motion: explicit Na+/K+ fluxes + slower pump + secondary chloride drift.
# -----------------------------------------------------------------------------
def make_ion(name, kind, loc, r=.10):
    mat = {"Na": M["na"], "K": M["k"], "Cl": M["cl"]}[kind]
    lab = {"Na": "Na⁺", "K": "K⁺", "Cl": "Cl⁻"}[kind]
    o = sphere(name, loc, (r, r, r), mat, 32, 18)
    t = text(name+"_Label", lab, (0, -.14, 0), r*1.12, UI["white"])
    t.parent = o
    return o


def moving_ion(name, kind, x, s0, s1, z0, z1, r=.10, lane=0):
    y = -.04 - lane*.018
    o = make_ion(name, kind, (x, y, z0), r)
    key_loc(o, fr(s0), (x, y, z0))
    key_loc(o, fr(s1), (x, y, z1))
    show_between(o, s0, s1, 1)
    set_linear(o)
    return o


def stream(kind, x, s0, s1, direction, count, r=.10):
    span = max(.6, (s1-s0)/3.2)
    for i in range(count):
        start = s0 + (s1-s0) * (i/max(1,count)) * .88
        end = min(s1, start+span)
        z0, z1 = ((1.05, -1.05) if direction < 0 else (-1.05, 1.05))
        xo = x + ((i % 3)-1)*.14
        moving_ion(f"{kind}Flux_{int(s0)}_{i}", kind, xo, start, end, z0, z1, r, i%3)

# Local depolarization and fast Na+ upstroke.
stream("Na", na_x, 23, 31, -1, 7, .095)
stream("Na", na_x, 31, 52, -1, 30, .104)
# Delayed K+ efflux for repolarization and after-hyperpolarization.
stream("K", k_x, 51.5, 64, +1, 28, .108)
stream("K", k_x, 64, 74, +1, 15, .104)
# Chloride: only slow background drift; no chloride-driven AP mechanism implied.
for i, (x, z0, z1, s0, s1) in enumerate([
    (-5.8, 1.05, 1.22, 10, 86), (4.8, 1.40, 1.20, 14, 82),
    (-1.8, -1.62, -1.42, 18, 88), (5.7, -1.72, -1.55, 12, 84),
]):
    o = make_ion(f"ClBackground_{i}", "Cl", (x, .30, z0), .095)
    key_loc(o, fr(s0), (x, .30, z0)); key_loc(o, fr(s1), (x+(.15 if i%2==0 else -.15), .30, z1))
    set_linear(o)

# Continuous Na+/K+-ATPase transport remains active during every AP phase.
for cyc in range(11):
    s = 8 + cyc*7.3
    for i in range(3):
        dx = (i-1)*.14
        moving_ion(f"PumpNa_{cyc}_{i}", "Na", -3.2+dx, s, s+1.8, -.90, .90, .080, i)
    for i in range(2):
        dx = (i-.5)*.18
        moving_ion(f"PumpK_{cyc}_{i}", "K", -3.0+dx, s+2.0, s+3.7, .90, -.90, .084, i)


# -----------------------------------------------------------------------------
# Membrane potential graph with real axes, threshold and phase highlights.
# -----------------------------------------------------------------------------
def vm(p):
    def ss(x):
        x = max(0.0, min(1.0, x)); return x*x*(3-2*x)
    if p < .17: return -70 + 9*(p/.17)
    if p < .23: return -61 + 6*((p-.17)/.06)
    if p < .48: return -55 + 90*ss((p-.23)/.25)
    if p < .73: return 35 - 108*ss((p-.48)/.25)
    if p < .89: return -73 - 14*math.sin(math.pi*((p-.73)/.16))
    return -73 + 3*ss((p-.89)/.11)


def progress(sec):
    anchors = [(8,0),(23,.08),(31,.17),(36,.23),(52,.48),(64,.73),(74,.89),(83,1.0)]
    if sec <= 8: return 0
    for (s0,p0),(s1,p1) in zip(anchors, anchors[1:]):
        if s0 <= sec <= s1:
            u=(sec-s0)/(s1-s0); u=u*u*(3-2*u); return p0+(p1-p0)*u
    return 1.0


def graph_curve(name, x0, x1, zfn, p0, p1, material, width=.025, samples=80, y=.40):
    c = bpy.data.curves.new(name+"_Curve", "CURVE")
    c.dimensions="3D"; c.bevel_depth=width; c.bevel_resolution=4
    s=c.splines.new("POLY"); s.points.add(samples-1)
    for i in range(samples):
        p=p0+(p1-p0)*(i/(samples-1))
        s.points[i].co=(x0+p*(x1-x0), y, zfn(vm(p)), 1)
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    return o

x0,x1=5.05,8.45
z0,z1=-1.58,1.60
minv,maxv=-100,45
zmap=lambda v: z0+(v-minv)/(maxv-minv)*(z1-z0)

cube("GraphPanel", ((x0+x1)/2,.72,.02), ((x1-x0)/2+.28,.035,1.98), UI["panel"], .16)
text("GraphTitle", "Мембранный потенциал", ((x0+x1)/2,-.64,2.04), .29, UI["white"])
cube("GraphYAxis", (x0,.50,.01), (.012,.012,(z1-z0)/2), UI["white"])
cube("GraphXAxis", ((x0+x1)/2,.50,z0), ((x1-x0)/2,.012,.012), UI["white"])
text("GraphYUnit", "мВ", (x0-.20,-.62,z1+.16), .17, UI["white"])
text("GraphXUnit", "Время (мс)", ((x0+x1)/2,-.62,z0-.30), .17, UI["white"])
for val in (40,20,0,-20,-40,-55,-70,-90):
    zz=zmap(val)
    cube(f"YTick{val}",(x0+.055,.48,zz),(.055,.012,.008),UI["muted"])
    text(f"YText{val}",f"{val:+d}" if val>0 else str(val),(x0-.27,-.62,zz),.14,UI["muted"])
for i in range(6):
    xx=x0+(x1-x0)*(i/5)
    cube(f"XTick{i}",(xx,.48,z0+.05),(.008,.012,.05),UI["muted"])
    text(f"XText{i}",str(i),(xx,-.62,z0-.14),.14,UI["muted"])
cube("Threshold",((x0+x1)/2,.50,zmap(-55)),((x1-x0)/2,.01,.008),UI["muted"])
text("ThresholdLabel","Порог",(x0+.30,-.62,zmap(-55)+.13),.16,UI["white"])

graph_curve("VmBase",x0,x1,zmap,0,1,UI["white"],.018,180,.43)
dep=graph_curve("VmDepol",x0,x1,zmap,.17,.48,UI["cyan"],.045,80,.40)
rep=graph_curve("VmRepol",x0,x1,zmap,.48,.73,M["k_hi"],.045,72,.40)
hyp=graph_curve("VmHyper",x0,x1,zmap,.73,.89,UI["yellow"],.040,52,.40)
show_between(dep,23,52); show_between(rep,52,64); show_between(hyp,64,74)
for n,body,loc,mat,s0,s1 in [
    ("GraphDepolLabel","Деполяризация",(6.35,-.66,.58),UI["cyan"],23,52),
    ("GraphRepolLabel","Реполяризация",(7.80,-.66,.32),M["k_hi"],52,64),
    ("GraphHyperLabel","Гиперполяризация",(7.55,-.66,-1.14),UI["yellow"],64,74),
]:
    o=text(n,body,loc,.17,mat); show_between(o,s0,s1)
marker=sphere("VmMarker",(x0,-.02,zmap(-70)),(.095,.095,.095),UI["yellow"],32,18)
for sec in range(8,84):
    p=progress(sec); key_loc(marker,fr(sec),(x0+p*(x1-x0),-.02,zmap(vm(p))))
set_linear(marker)


# -----------------------------------------------------------------------------
# Phase/refractoriness overlays and subtle camera emphasis.
# -----------------------------------------------------------------------------
phase_specs=[
    ("Потенциал покоя",8,23,UI["white"]),
    ("Локальная деполяризация",23,31,UI["yellow"]),
    ("Порог возбуждения",31,36,UI["yellow"]),
    ("Быстрая деполяризация",36,52,M["na_hi"]),
    ("Пик и реполяризация",52,64,M["k_hi"]),
    ("Следовая гиперполяризация",64,74,UI["yellow"]),
    ("Возвращение к потенциалу покоя",74,83,UI["white"]),
    ("Na⁺/K⁺-АТФаза поддерживает градиенты; быстрые фазы ПД создают потенциалзависимые каналы",83,90,M["pump_hi"]),
]
for i,(body,s0,s1,mat) in enumerate(phase_specs):
    o=text(f"PhaseTitle{i}",body,(-.05,-.80,2.55),.30 if i<7 else .22,mat)
    show_between(o,s0,s1)

abs_band=cube("AbsoluteRefBand",(.20,-.22,-2.42),(2.15,.05,.15),UI["red"],.07)
abs_txt=text("AbsoluteRefText","АБСОЛЮТНАЯ РЕФРАКТЕРНОСТЬ",(.20,-.60,-2.42),.22,UI["white"])
rel_band=cube("RelativeRefBand",(.20,-.22,-2.42),(2.15,.05,.15),UI["yellow"],.07)
rel_txt=text("RelativeRefText","ОТНОСИТЕЛЬНАЯ РЕФРАКТЕРНОСТЬ",(.20,-.60,-2.42),.22,UI["white"])
show_between(abs_band,36,64); show_between(abs_txt,36,64)
show_between(rel_band,64,77); show_between(rel_txt,64,77)

# Environment labels, positioned away from ion clouds.
text("OutsideLabelV04","ВНЕКЛЕТОЧНАЯ СРЕДА",(-6.15,-.70,2.12),.28,UI["muted"])
text("InsideLabelV04","ЦИТОПЛАЗМА",(-6.15,-.70,-2.02),.28,UI["muted"])
intro=text("IntroTitle","ПОТЕНЦИАЛ ДЕЙСТВИЯ",(0,-.74,.35),.65,UI["white"])
intro2=text("IntroSub","Na⁺/K⁺-АТФаза • потенциалзависимые каналы • рефрактерность",(0,-.74,-.35),.29,UI["cyan"])
show_between(intro,0,8); show_between(intro2,0,8)

# Camera: preserve full-scene readability, with only subtle emphasis on active channels.
cam=bpy.context.scene.camera
if cam:
    cam.animation_data_clear()
    poses=[
        (0,(0,-22.5,2.8)), (8,(0,-22.5,2.8)),
        (23,(-.2,-21.8,2.65)), (36,(.15,-21.0,2.55)),
        (52,(.45,-21.0,2.55)), (64,(.55,-21.4,2.60)),
        (74,(.25,-21.8,2.68)), (83,(0,-22.5,2.8)), (90,(0,-22.5,2.8)),
    ]
    for sec,loc in poses:
        cam.location=loc
        direction=Vector((.15,0,.02))-cam.location
        cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
        cam.keyframe_insert('location',frame=fr(sec)); cam.keyframe_insert('rotation_euler',frame=fr(sec))


# -----------------------------------------------------------------------------
# Render configuration + save.
# -----------------------------------------------------------------------------
scene=bpy.context.scene
scene.frame_start=1; scene.frame_end=FRAME_END; scene.render.fps=FPS
scene.render.resolution_x=960 if PREVIEW else 1920
scene.render.resolution_y=540 if PREVIEW else 1080
scene.render.resolution_percentage=100
try:
    scene.render.engine='BLENDER_EEVEE_NEXT'
except Exception:
    pass
scene.world.color=COL["bg"]
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4'
scene.render.ffmpeg.codec='H264'
scene.render.ffmpeg.constant_rate_factor='MEDIUM' if PREVIEW else 'HIGH'
scene.render.filepath='//action_potential_pokrovsky_v04_preview.mp4' if PREVIEW else '//action_potential_pokrovsky_v04.mp4'

out=Path(__file__).with_name("action_potential_pokrovsky_v04.blend")
bpy.ops.wm.save_as_mainfile(filepath=str(out))

required=["NaK_ATPase_Root","NaChannel_Root","KChannel_Root","Membrane_Root","VmMarker"]
missing=[name for name in required if bpy.data.objects.get(name) is None]
if missing:
    raise RuntimeError("Missing required integration objects: "+", ".join(missing))

print("ACTION_POTENTIAL_V04_OK", "frames=", FRAME_END, "preview=", PREVIEW, "blend=", out)
