"""Writes a solid-color PNG using only the stdlib (zlib/struct) - no PIL needed.
Usage: python scripts/make_solid_png.py <out.png> <width> <height> <hexcolor>
"""
import struct
import sys
import zlib


def write_solid_png(path, width, height, hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))

    row = b"\x00" + bytes([r, g, b]) * width
    raw = row * height
    idat = chunk(b"IDAT", zlib.compress(raw, 9))
    iend = chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(sig + ihdr + idat + iend)


if __name__ == "__main__":
    out, w, h, color = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    write_solid_png(out, w, h, color)
    print(f"wrote {out} ({w}x{h}, {color})")
