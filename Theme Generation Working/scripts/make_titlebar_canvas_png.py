"""Writes a full-page-sized PNG with a solid-color band at the top (the title
bar area) and white filling the rest of the canvas below it. Stdlib only.

Usage: python scripts/make_titlebar_canvas_png.py <out.png> <width> <height> <band_height> <band_hexcolor>
"""
import struct
import sys
import zlib


def write_banded_png(path, width, height, band_height, band_hex):
    band_hex = band_hex.lstrip("#")
    br, bg, bb = (int(band_hex[i:i + 2], 16) for i in (0, 2, 4))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))

    band_row = b"\x00" + bytes([br, bg, bb]) * width
    white_row = b"\x00" + bytes([255, 255, 255]) * width
    raw = band_row * band_height + white_row * (height - band_height)
    idat = chunk(b"IDAT", zlib.compress(raw, 9))
    iend = chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(sig + ihdr + idat + iend)


if __name__ == "__main__":
    out, w, h, band_h, color = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    write_banded_png(out, w, h, band_h, color)
    print(f"wrote {out} ({w}x{h}, top {band_h}px = {color}, rest white)")
