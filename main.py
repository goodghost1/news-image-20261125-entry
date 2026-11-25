"""Entrypoint for the news-image-20261125 entry.

The World Today -- Wednesday 25 November 2026. The image is rendered
in advance by gen.py and shipped in this repository as entry.png.
This program only checks that file and copies it to the output
directory. It never draws, downloads, or regenerates anything, so a
run on the grader's read-only copy produces exactly the shipped bytes.
"""

import hashlib
import os
import shutil
import struct
import sys


SOURCE_NAME = "entry.png"
MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def fail(message):
    print("error: " + message, file=sys.stderr)
    raise SystemExit(1)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)
    if not os.path.isfile(source):
        fail("missing " + SOURCE_NAME + " next to main.py")
    with open(source, "rb") as handle:
        data = handle.read()
    if len(data) > MAX_BYTES:
        fail("entry.png is %d bytes, over the 1048576 limit" % len(data))
    if not (data.startswith(PNG_MAGIC) or data.startswith(JPEG_MAGIC)):
        fail("entry.png is neither a PNG nor a JPEG by its first bytes")
    if data.startswith(PNG_MAGIC):
        if len(data) < 33 or data[12:16] != b"IHDR":
            fail("entry.png has no IHDR chunk where a PNG must")
        width, height = struct.unpack(">II", data[16:24])
        if (width, height) != (1024, 1024):
            fail("entry.png is %dx%d, expected 1024x1024" % (width, height))
        if not data.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"):
            fail("entry.png is missing its IEND chunk, file is truncated")
    digest = hashlib.sha256(data).hexdigest()
    print("entry.png: %d bytes sha256 %s" % (len(data), digest))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, SOURCE_NAME)
    with open(target, "wb") as handle:
        handle.write(data)
    with open(target, "rb") as handle:
        again = handle.read()
    if hashlib.sha256(again).hexdigest() != digest:
        fail("copy mismatch after writing " + target)
    print("wrote " + target)


if __name__ == "__main__":
    main()
