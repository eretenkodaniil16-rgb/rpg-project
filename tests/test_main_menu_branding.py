#!/usr/bin/env python3
"""Static contract checks for animated main menu branding v01."""
from __future__ import annotations
import json, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STRIPS = ROOT / "assets/branding/main_menu/approved/strips"
MANIFEST = ROOT / "assets/branding/main_menu/main_menu_tower_down_v01.json"
SCENE = ROOT / "scenes/menus/main_menu.tscn"
MENU_SCRIPT = ROOT / "scripts/menus/main_menu.gd"
TILED_SCRIPT = ROOT / "scripts/menus/main_menu_tiled_background.gd"
ATMOSPHERE_SCRIPT = ROOT / "scripts/menus/main_menu_atmosphere.gd"
TITLE_GLOW_SCRIPT = ROOT / "scripts/menus/main_menu_title_glow.gd"
EXPECTED = [
    ("main_menu_strip_c00.webp", 120), ("main_menu_strip_c01.webp", 120),
    ("main_menu_strip_c02.webp", 120), ("main_menu_strip_c03.webp", 120),
    ("main_menu_strip_c04a.webp", 60), ("main_menu_strip_c04b.webp", 60),
    ("main_menu_strip_c05a.webp", 60), ("main_menu_strip_c05b.webp", 60),
    ("main_menu_strip_c06a.webp", 60), ("main_menu_strip_c06b.webp", 60),
    ("main_menu_strip_c07.webp", 120), ("main_menu_strip_c08.webp", 120),
    ("main_menu_strip_c09.webp", 120), ("main_menu_strip_c10.webp", 120),
    ("main_menu_strip_c11.webp", 120), ("main_menu_strip_c12.webp", 120),
    ("main_menu_strip_c13.webp", 120), ("main_menu_strip_c14.webp", 120),
    ("main_menu_strip_c15.webp", 120),
]
MIN_TOTAL_STRIP_BYTES = 130_000

def read_webp_size(path: Path) -> tuple[int,int]:
    data=path.read_bytes()
    if len(data)<30 or data[:4]!=b"RIFF" or data[8:12]!=b"WEBP": raise AssertionError(f"Not WebP: {path}")
    if struct.unpack("<I",data[4:8])[0]+8 != len(data): raise AssertionError(f"RIFF mismatch: {path}")
    chunk=data[12:16]
    if chunk==b"VP8X": return 1+int.from_bytes(data[24:27],"little"),1+int.from_bytes(data[27:30],"little")
    if chunk==b"VP8 ":
        marker=data.find(b"\x9d\x01\x2a",20)
        if marker < 0: raise AssertionError(f"VP8 marker missing: {path}")
        return struct.unpack("<H",data[marker+3:marker+5])[0]&0x3FFF, struct.unpack("<H",data[marker+5:marker+7])[0]&0x3FFF
    if chunk==b"VP8L":
        bits=int.from_bytes(data[21:25],"little"); return (bits&0x3FFF)+1,((bits>>14)&0x3FFF)+1
    raise AssertionError(f"Unsupported WebP: {path}")

def require(path:Path, fragment:str)->None:
    if fragment not in path.read_text(encoding="utf-8"): raise AssertionError(f"Missing in {path}: {fragment}")

def main()->None:
    expected_names=[name for name,_ in EXPECTED]
    actual=sorted(p.name for p in STRIPS.glob("*.webp"))
    if actual!=sorted(expected_names): raise AssertionError(f"Segment set mismatch: {actual}")
    paths=[]
    for name,width in EXPECTED:
        path=STRIPS/name; paths.append(path)
        if read_webp_size(path)!=(width,1080): raise AssertionError(f"Unexpected size: {name}")
    total=sum(p.stat().st_size for p in paths)
    if total<MIN_TOTAL_STRIP_BYTES: raise AssertionError(f"HQ background over-compressed: {total}")
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_id")!="main_menu_tower_down_v01" or manifest.get("status")!="runtime_candidate": raise AssertionError("Manifest identity/status")
    if manifest.get("approval",{}).get("logo_variant_approved")!=2: raise AssertionError("Logo variant")
    contract=manifest.get("render_contract",{})
    if contract.get("source_size")!=[1920,1080]: raise AssertionError("Runtime source")
    if contract.get("segment_count")!=19 or sum(contract.get("segment_widths",[]))!=1920: raise AssertionError("Segment contract")
    if contract.get("background_encoding")!="webp_q75" or contract.get("texture_filter")!="linear": raise AssertionError("HQ encoding/filter")
    glow=manifest.get("title_glow",{})
    if glow.get("wait_seconds_min")!=5.0 or glow.get("wait_seconds_max")!=10.0: raise AssertionError("Glow interval")
    for fragment in ['node name="FallbackBackground"','node name="ApprovedBackground" type="Control"','node name="Atmosphere"','node name="TitleGlow" type="ColorRect"','script = ExtResource("4_title_glow")','hint_screen_texture','node name="Title" type="Label"','text = "ХРОНИКИ СТРАННИКА"','node name="Subtitle" type="Label"','text = "Башня, уходящая вниз"']:
        require(SCENE,fragment)
    for name in ("ContinueButton","NewGameButton","QuitButton"): require(SCENE,f'node name="{name}"')
    for fragment in ("MainMenuTiledBackground","has_complete_tiles()","_install_save_slots_panel()","_on_new_game_pressed","_on_continue_pressed"): require(MENU_SCRIPT,fragment)
    for fragment in ('const SOURCE_SIZE: Vector2 = Vector2(1920.0, 1080.0)','const SEGMENT_NAMES: Array[String]','const SEGMENT_WIDTHS: Array[float]','TEXTURE_FILTER_LINEAR','scale_factor: float = maxf','has_complete_tiles'):
        require(TILED_SCRIPT,fragment)
    require(ATMOSPHERE_SCRIPT,'const PARTICLE_COUNT: int = 28'); require(ATMOSPHERE_SCRIPT,'_draw_torch_glow'); require(ATMOSPHERE_SCRIPT,'accessibility/reduced_motion')
    require(TITLE_GLOW_SCRIPT,'class_name MainMenuTitleGlow'); require(TITLE_GLOW_SCRIPT,'const MIN_WAIT_SECONDS: float = 5.0'); require(TITLE_GLOW_SCRIPT,'const MAX_WAIT_SECONDS: float = 10.0'); require(TITLE_GLOW_SCRIPT,'set_shader_parameter("intensity"'); require(TITLE_GLOW_SCRIPT,'accessibility/reduced_motion')
    print("Main menu branding validation passed")
if __name__=="__main__": main()
