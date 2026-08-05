from __future__ import annotations

from pathlib import Path


ADAPTER = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)
TEST = Path(
    "tools/blender_sprite_factory/tests/test_death_down_keyposes_v01.py"
)


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return content.replace(old, new, 1)


def main() -> int:
    adapter = ADAPTER.read_text(encoding="utf-8")
    adapter = replace_once(
        adapter,
        "def _assert_frame_contract(\n"
        "    frames: tuple[factory.FrameArtifact, ...],\n"
        "    *,\n"
        "    death_variant_id: str,\n"
        ") -> None:\n",
        "def _opaque_component_sizes(path: Path) -> tuple[int, ...]:\n"
        "    image = factory.bpy.data.images.load(str(path), check_existing=False)\n"
        "    try:\n"
        "        width, height = (int(value) for value in image.size)\n"
        "        pixels = tuple(image.pixels[:])\n"
        "        opaque = {\n"
        "            (x, y)\n"
        "            for y in range(height)\n"
        "            for x in range(width)\n"
        "            if pixels[(y * width + x) * 4 + 3] >= 0.5\n"
        "        }\n"
        "        sizes: list[int] = []\n"
        "        while opaque:\n"
        "            seed = opaque.pop()\n"
        "            stack = [seed]\n"
        "            size = 0\n"
        "            while stack:\n"
        "                x, y = stack.pop()\n"
        "                size += 1\n"
        "                for neighbor in (\n"
        "                    (x + 1, y),\n"
        "                    (x - 1, y),\n"
        "                    (x, y + 1),\n"
        "                    (x, y - 1),\n"
        "                ):\n"
        "                    if neighbor in opaque:\n"
        "                        opaque.remove(neighbor)\n"
        "                        stack.append(neighbor)\n"
        "            sizes.append(size)\n"
        "        return tuple(sorted(sizes, reverse=True))\n"
        "    finally:\n"
        "        factory.bpy.data.images.remove(image)\n\n\n"
        "def _assert_frame_contract(\n"
        "    frames: tuple[factory.FrameArtifact, ...],\n"
        "    *,\n"
        "    death_variant_id: str,\n"
        ") -> None:\n",
        "component helper",
    )
    adapter = replace_once(
        adapter,
        "    if frame_number == profile.detachment_frame:\n"
        "        offset = (0.34, -0.15, -0.12)\n"
        "        rotation = (12.0, -8.0, 24.0)\n"
        "    else:\n"
        "        offset = (0.50, -0.22, -0.19)\n"
        "        rotation = (20.0, -12.0, 38.0)\n",
        "    if frame_number == profile.detachment_frame:\n"
        "        offset = (0.82, -0.05, -0.10)\n"
        "        rotation = (12.0, -8.0, 24.0)\n"
        "    else:\n"
        "        offset = (0.95, -0.10, -0.14)\n"
        "        rotation = (20.0, -12.0, 38.0)\n",
        "detached offsets",
    )
    adapter = replace_once(
        adapter,
        "            frames = _find_frames(artifacts, animation_id=profile.animation_id)\n"
        "            _assert_frame_contract(frames, death_variant_id=profile.death_variant_id)\n",
        "            frames = _find_frames(artifacts, animation_id=profile.animation_id)\n"
        "            _assert_frame_contract(frames, death_variant_id=profile.death_variant_id)\n"
        "            if profile.gore_mode == \"left_forearm_detachment\":\n"
        "                for item in frames:\n"
        "                    if item.frame_number < int(profile.detachment_frame):\n"
        "                        continue\n"
        "                    component_sizes = _opaque_component_sizes(item.output_path)\n"
        "                    visible_components = [\n"
        "                        size for size in component_sizes if size >= 8\n"
        "                    ]\n"
        "                    if len(visible_components) < 2:\n"
        "                        raise RuntimeError(\n"
        "                            \"death_03 detached limb is not visually separated: \"\n"
        "                            f\"f{item.frame_number:02d}={component_sizes}\"\n"
        "                        )\n",
        "separation assertion",
    )
    ADAPTER.write_text(adapter, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test = replace_once(
        test,
        "        self.assertIn(\"_apply_gore_state\", source)\n"
        "        self.assertIn(\"left_forearm_detachment\", source)\n",
        "        self.assertIn(\"_apply_gore_state\", source)\n"
        "        self.assertIn(\"_opaque_component_sizes\", source)\n"
        "        self.assertIn(\"detached limb is not visually separated\", source)\n"
        "        self.assertIn(\"left_forearm_detachment\", source)\n",
        "focused test assertions",
    )
    TEST.write_text(test, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
