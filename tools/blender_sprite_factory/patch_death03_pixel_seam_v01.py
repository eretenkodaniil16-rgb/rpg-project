from __future__ import annotations

from pathlib import Path


ADAPTER = Path(
    "tools/blender_sprite_factory/blender_sprite_factory_death_down_keyposes_v01.py"
)
TEST = Path("tools/blender_sprite_factory/tests/test_death_down_keyposes_v01.py")
DOC = Path("docs/HUMAN_WARRIOR_DEATH_DOWN_KEYPOSES_V01.md")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


PNG_HELPERS = r'''
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _waist_pixel_seam_top_down(
    frame_number: int,
) -> tuple[tuple[int, int], ...]:
    if frame_number == 4:
        return (
            ((19, 63),)
            + tuple((x, 64) for x in range(20, 36))
            + (
                (36, 65),
                (36, 66),
                (36, 67),
                (37, 68),
                (38, 69),
                (39, 70),
                (40, 71),
            )
        )
    if frame_number == 5:
        return tuple((x, x + 28) for x in range(21, 42))
    return ()


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", checksum)
    )


def _paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def _decode_rgba8_png(
    path: Path,
) -> tuple[int, int, list[bytearray], tuple[tuple[bytes, bytes], ...]]:
    data = path.read_bytes()
    if not data.startswith(_PNG_SIGNATURE):
        raise RuntimeError(f"death_03 seam requires PNG: {path}")

    chunks: list[tuple[bytes, bytes]] = []
    idat_parts: list[bytes] = []
    width = 0
    height = 0
    bit_depth = -1
    color_type = -1
    interlace = -1
    offset = len(_PNG_SIGNATURE)
    while offset < len(data):
        if offset + 12 > len(data):
            raise RuntimeError(f"truncated PNG chunk: {path}")
        payload_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + payload_length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise RuntimeError(f"truncated PNG payload: {path}")
        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise RuntimeError(f"PNG CRC mismatch: {path} {chunk_type!r}")
        chunks.append((chunk_type, payload))
        if chunk_type == b"IHDR":
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", payload)
            if compression != 0 or filter_method != 0:
                raise RuntimeError(f"unsupported PNG method: {path}")
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)
        elif chunk_type == b"IEND":
            break
        offset = crc_end

    if (width, height, bit_depth, color_type, interlace) != (96, 96, 8, 6, 0):
        raise RuntimeError(
            "death_03 seam requires 96x96 RGBA8 non-interlaced PNG: "
            f"{path}={(width, height, bit_depth, color_type, interlace)}"
        )
    if not idat_parts:
        raise RuntimeError(f"PNG has no IDAT: {path}")

    packed = zlib.decompress(b"".join(idat_parts))
    row_size = width * 4
    expected_size = height * (row_size + 1)
    if len(packed) != expected_size:
        raise RuntimeError(
            f"unexpected PNG scanline size: {path}={len(packed)}/{expected_size}"
        )

    rows: list[bytearray] = []
    previous = bytearray(row_size)
    cursor = 0
    for _ in range(height):
        filter_type = packed[cursor]
        encoded = packed[cursor + 1 : cursor + 1 + row_size]
        cursor += row_size + 1
        decoded = bytearray(row_size)
        for index, value in enumerate(encoded):
            left = decoded[index - 4] if index >= 4 else 0
            up = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                predictor = _paeth_predictor(left, up, upper_left)
            else:
                raise RuntimeError(f"unsupported PNG filter {filter_type}: {path}")
            decoded[index] = (value + predictor) & 0xFF
        rows.append(decoded)
        previous = decoded
    return width, height, rows, tuple(chunks)


def _write_rgba8_png(
    path: Path,
    width: int,
    height: int,
    rows: list[bytearray],
    chunks: tuple[tuple[bytes, bytes], ...],
) -> None:
    if len(rows) != height or any(len(row) != width * 4 for row in rows):
        raise RuntimeError(f"death_03 seam row contract drifted: {path}")
    packed = b"".join(b"\x00" + bytes(row) for row in rows)
    replacement_idat = zlib.compress(packed, level=9)
    output = bytearray(_PNG_SIGNATURE)
    wrote_idat = False
    for chunk_type, payload in chunks:
        if chunk_type == b"IDAT":
            if not wrote_idat:
                output.extend(_png_chunk(b"IDAT", replacement_idat))
                wrote_idat = True
            continue
        output.extend(_png_chunk(chunk_type, payload))
    if not wrote_idat:
        raise RuntimeError(f"death_03 seam could not replace IDAT: {path}")
    path.write_bytes(bytes(output))


def _apply_waist_pixel_seam(path: Path, frame_number: int) -> int:
    seam = _waist_pixel_seam_top_down(frame_number)
    if not seam:
        return 0
    width, height, rows, chunks = _decode_rgba8_png(path)
    removed_opaque = 0
    for x, top_down_y in seam:
        if not (0 <= x < width and 0 <= top_down_y < height):
            raise RuntimeError(
                f"death_03 seam coordinate outside canvas: f{frame_number:02d} "
                f"{(x, top_down_y)}"
            )
        pixel_offset = x * 4
        if rows[top_down_y][pixel_offset + 3] >= 128:
            removed_opaque += 1
        rows[top_down_y][pixel_offset : pixel_offset + 4] = b"\x00\x00\x00\x00"
    if removed_opaque < len(seam) - 2:
        raise RuntimeError(
            "death_03 seam no longer follows the rendered waist: "
            f"f{frame_number:02d}={removed_opaque}/{len(seam)}"
        )
    _write_rgba8_png(path, width, height, rows, chunks)
    return removed_opaque

'''


def main() -> int:
    adapter = ADAPTER.read_text(encoding="utf-8")
    adapter = replace_once(
        adapter,
        "import hashlib\nimport json\nimport math\nimport sys\n",
        "import binascii\nimport hashlib\nimport json\nimport math\nimport struct\nimport sys\nimport zlib\n",
        "PNG helper imports",
    )
    adapter = replace_once(
        adapter,
        "\ndef _reset_gore_state() -> None:\n",
        "\n" + PNG_HELPERS + "\ndef _reset_gore_state() -> None:\n",
        "PNG seam helpers",
    )
    adapter = replace_once(
        adapter,
        '''                    )
                    artifacts.append(artifact)
                finally:
''',
        '''                    )
                    if split_states:
                        _apply_waist_pixel_seam(
                            artifact.output_path,
                            frame_number,
                        )
                    artifacts.append(artifact)
                finally:
''',
        "seam application after render",
    )
    adapter = replace_once(
        adapter,
        '''        "detachment_frame": profile.detachment_frame,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),''',
        '''        "detachment_frame": profile.detachment_frame,
        "pixel_seam_frames": (
            [4, 5]
            if profile.gore_mode == "waist_torso_legs_separation"
            else []
        ),
        "pixel_seam_preserves_existing_rgb": True,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),''',
        "manifest seam metadata",
    )
    ADAPTER.write_text(adapter, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test = replace_once(
        test,
        '''        self.assertIn("_opaque_component_sizes", source)
        self.assertIn("torso and legs are not visually separated", source)''',
        '''        self.assertIn("_opaque_component_sizes", source)
        self.assertIn("_apply_waist_pixel_seam", source)
        self.assertIn("_decode_rgba8_png", source)
        self.assertIn("_write_rgba8_png", source)
        self.assertIn("pixel_seam_preserves_existing_rgb", source)
        self.assertIn("torso and legs are not visually separated", source)''',
        "pixel seam static assertions",
    )
    TEST.write_text(test, encoding="utf-8")

    doc = DOC.read_text(encoding="utf-8")
    doc = replace_once(
        doc,
        '''Для `f04/f05` CI требует минимум две крупные раздельные alpha-компоненты. Вторая
масса должна составлять не менее 20% первой и содержать минимум 120 непрозрачных
пикселей. Маленький gore-prop не может формально пройти эту проверку.
''',
        '''Для `f04/f05` CI требует минимум две крупные раздельные alpha-компоненты. Вторая
масса должна составлять не менее 20% первой и содержать минимум 120 непрозрачных
пикселей. Маленький gore-prop не может формально пройти эту проверку.

После Blender-рендера два кадра проходят локальную pixel-art сборку: внутри
силуэта вырезается узкий прозрачный шов по линии талии. Post-process работает
на байтах RGBA8 PNG, сохраняет все существующие RGB-значения побайтно и меняет
только alpha у заранее зафиксированных внутренних пикселей. Это не затрагивает
внешний контур, лицо, экипировку, baseline или остальные варианты смерти.
''',
        "pixel seam documentation",
    )
    DOC.write_text(doc, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
