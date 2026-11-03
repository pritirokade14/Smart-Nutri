"""Label-photo checks and preparation before the paid extraction call (ruling R12).

- `sniff_image_mime` trusts only the bytes (never a header or file extension).
- `prepare_for_extraction` applies the EXIF orientation, caps the long edge at 1600 px and
  re-encodes as a plain JPEG. Re-encoding drops every metadata block (EXIF, GPS, XMP, ICC
  comments), so a phone's location never reaches the model provider. CPU-bound: call it via
  `anyio.to_thread.run_sync`.
"""

from __future__ import annotations

import io
from typing import Literal

from PIL import Image, ImageOps

ImageMime = Literal["image/jpeg", "image/png", "image/webp"]

MAX_EDGE_PX = 1600
# Decompression-bomb guard: a real label photo is far below this (a 50 MP phone ~ 50M px).
MAX_PIXELS = 60_000_000
# PNG/WebP decode at full size (no draft()), so they get a much lower cap.
MAX_PIXELS_NON_JPEG = 25_000_000
JPEG_QUALITY = 85
_FORMATS = ("JPEG", "PNG", "WEBP")


class InvalidImage(Exception):
    """The bytes are not a decodable JPEG, PNG or WebP image."""


def sniff_image_mime(data: bytes) -> ImageMime | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def prepare_for_extraction(data: bytes) -> bytes:
    """Decode, orient, downscale to <= MAX_EDGE_PX and re-encode as metadata-free JPEG."""
    if sniff_image_mime(data) is None:
        raise InvalidImage("unsupported format")
    try:
        with Image.open(io.BytesIO(data), formats=_FORMATS) as img:
            width, height = img.size
            max_px = MAX_PIXELS if img.format == "JPEG" else MAX_PIXELS_NON_JPEG
            if width * height > max_px:
                raise InvalidImage("too many pixels")
            img.draft("RGB", (MAX_EDGE_PX, MAX_EDGE_PX))  # JPEG: decode at reduced scale
            img.load()
            oriented = ImageOps.exif_transpose(img)
            oriented.thumbnail((MAX_EDGE_PX, MAX_EDGE_PX), Image.Resampling.LANCZOS)
            rgb = _to_rgb(oriented)
            out = io.BytesIO()
            # No exif/icc/comment arguments: the output carries no metadata.
            rgb.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            return out.getvalue()
    except InvalidImage:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        raise InvalidImage("cannot decode") from exc


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return img.convert("RGB") if img.mode != "RGB" else img
