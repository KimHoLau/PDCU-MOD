#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a macOS .icns from one square PNG.

    python tools/make_icns.py tools/assets/pdcu_mod_logo_96.png tools/season.icns

Stdlib + Pillow only, no macOS tooling (`iconutil` / `sips`) needed, so the
icon can be regenerated from Windows before the app is built on a Mac.

The container is the modern PNG-chunk form (macOS 10.7+): the 16/32/64 px
slots plus the 128/256/512 slots and their @2x twins, exactly the set
`iconutil` emits for an .iconset.  1024 px is only written when the source
is at least 512 px wide: upscaling a small logo would ship a blurred file
that Finder prefers over the sharper smaller slot.
"""
from __future__ import annotations

import argparse
import io
import struct
import sys
from pathlib import Path

from PIL import Image

MAGIC = b"icns"

# (chunk type, pixel size) in the order iconutil writes them.
SLOTS = [
    ("icp4", 16),
    ("icp5", 32),
    ("icp6", 64),
    ("ic07", 128),
    ("ic08", 256),
    ("ic09", 512),
    ("ic10", 1024),
    ("ic11", 32),     # 16@2x
    ("ic12", 64),     # 32@2x
    ("ic13", 256),    # 128@2x
    ("ic14", 512),    # 256@2x
]

BIG_SLOT_MIN_SOURCE = 512      # only upscale to 1024 from a real 512+ source


def _chunk(kind: str, payload: bytes) -> bytes:
    return kind.encode("ascii") + struct.pack(">I", len(payload) + 8) + payload


def _square_png(image: Image.Image, size: int) -> bytes:
    buffer = io.BytesIO()
    image.resize((size, size), Image.LANCZOS).save(buffer, "PNG")
    return buffer.getvalue()


def build_icns(source: Path, out: Path) -> list[tuple[str, int, int]]:
    """Write the .icns and return the (type, size, bytes) actually written."""
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    side = image.size[0]
    if image.size[0] != image.size[1]:
        raise SystemExit("%s: icon source must be square, got %dx%d"
                         % (source, image.size[0], image.size[1]))

    chunks = []
    written = []
    for kind, size in SLOTS:
        if size == 1024 and side < BIG_SLOT_MIN_SOURCE:
            continue
        payload = _square_png(image, size)
        chunks.append(_chunk(kind, payload))
        written.append((kind, size, len(payload) + 8))

    body = b"".join(chunks)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(MAGIC + struct.pack(">I", len(body) + 8) + body)
    return written


def verify_icns(path: Path) -> list[tuple[str, int]]:
    """Parse the container back and check every length; return (type, size)."""
    data = path.read_bytes()
    if data[:4] != MAGIC:
        raise SystemExit("%s: missing icns magic" % path)
    total = struct.unpack(">I", data[4:8])[0]
    if total != len(data):
        raise SystemExit("%s: header says %d bytes, file is %d"
                         % (path, total, len(data)))
    found = []
    offset = 8
    while offset < len(data):
        kind = data[offset:offset + 4].decode("ascii", "replace")
        length = struct.unpack(">I", data[offset + 4:offset + 8])[0]
        if length < 8 or offset + length > len(data):
            raise SystemExit("%s: bad chunk %r at %d (len %d)"
                             % (path, kind, offset, length))
        payload = data[offset + 8:offset + length]
        try:
            with Image.open(io.BytesIO(payload)) as probe:
                found.append((kind, probe.size[0]))
        except Exception as exc:                       # pragma: no cover
            raise SystemExit("%s: chunk %r is not a valid PNG: %s"
                             % (path, kind, exc))
        offset += length
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?",
                        default=Path("tools/assets/pdcu_mod_logo_96.png"))
    parser.add_argument("output", type=Path, nargs="?",
                        default=Path("tools/season.icns"))
    args = parser.parse_args(argv)

    written = build_icns(args.source, args.output)
    found = verify_icns(args.output)
    if [size for _kind, size, _n in written] != [size for _kind, size in found]:
        raise SystemExit("round-trip mismatch: %r vs %r" % (written, found))

    print("%s -> %s (%d bytes)" % (args.source, args.output,
                                   args.output.stat().st_size))
    for (kind, size, n), (back_kind, back_size) in zip(written, found):
        print("  %s  %4dpx  %6d B  read back %s %dpx"
              % (kind, size, n, back_kind, back_size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
