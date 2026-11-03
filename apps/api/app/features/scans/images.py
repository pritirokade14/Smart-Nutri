"""Label-photo checks and preparation before the paid extraction call (ruling R12).

- `sniff_image_mime` trusts only the bytes (never a header or file extension).
- `prepare_for_extraction` applies the EXIF orientation, caps the long edge at 1600 px and
  re-encodes as a plain JPEG. Re-encoding drops every metadata block (EXIF, GPS, XMP, ICC
  comments), so a phone's location never reaches the model provider. CPU-bound: call it via
  `anyio.to_thread.run_sync`.
- `prepare_with_quality` does the same and also returns a `QualityReport` (label v2 item 4):
  cheap CPU checks for blur, glare and resolution, so a clearly unreadable photo is sent back
  for a retake before any paid call. A crop check is reported but never rejects.

Quality gate (all on the prepared image, at most 1600 px; 8 x 8 tiles):
- `too_small`: long edge < MIN_LONG_EDGE_PX or short edge < MIN_SHORT_EDGE_PX.
- `blur`: even the SHARPEST tile has a Laplacian variance < BLUR_MAX_VARIANCE. One sharp
  tile anywhere (a small table on a big plain pack) is enough to pass.
- `glare`: the frame is washed out: at least GLARE_BLOWN_ALL of the tiles are blown out
  (nearly all pixels near-white, every channel >= SATURATED_LEVEL, AND no detail). White paper
  with text, a scan or a screenshot has detail, so it passes. A hot-spot over the centre
  (GLARE_SOFT_BLOWN_CENTER of the central tiles) is only `glare_borderline` (soft).
- `cut_off_suspected` (soft only): edges are much denser on the frame border than inside. A
  tight crop on the table looks the same, so it never rejects.
These are data-quality constants, not health thresholds. They are deliberately conservative
(set from synthetic labels and the repo's images in tests/unit/scans/test_quality_gate.py,
with a wide margin to every readable case) and must be re-tuned on the label eval set.
"""

from __future__ import annotations

import io
from dataclasses import asdict, dataclass
from typing import Any, Literal

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

ImageMime = Literal["image/jpeg", "image/png", "image/webp"]
QualityReason = Literal["too_small", "blur", "glare"]

MAX_EDGE_PX = 1600
# Decompression-bomb guard: a real label photo is far below this (a 50 MP phone ~ 50M px).
MAX_PIXELS = 60_000_000
# PNG/WebP decode at full size (no draft()), so they get a much lower cap.
MAX_PIXELS_NON_JPEG = 25_000_000
JPEG_QUALITY = 85
_FORMATS = ("JPEG", "PNG", "WEBP")

# Quality gate (see the module docstring).
MIN_LONG_EDGE_PX = 400
MIN_SHORT_EDGE_PX = 200
# The sharpest tile's Laplacian variance, measured on the JPEG the model gets. Sharp synthetic
# labels measure ~3600-4300. A Gaussian blur of sigma 2 / 3 / 4 / 6 gives ~37 / 8 / 4 / 2 with
# 20 px text, ~78 / 14 / 5.4 / 3 with 30 px text and ~132 / 28 / 9.5 / 3.8 with 44 px text;
# sensor noise plus JPEG keeps every case >= ~10. So only text smeared well past legibility
# on a noise-free image is a hard reject; noisy phone photos are effectively never rejected
# for blur until this is re-tuned on real photos (see the label-v2 report).
BLUR_MAX_VARIANCE = 5.0
BLUR_SOFT_VARIANCE = 100.0  # borderline: reported, not rejected
FLAT_TILE_VARIANCE = 15.0  # a tile with no detail at all (plain colour, blown-out white)
SATURATED_LEVEL = 250
BLOWN_TILE_SATURATED = 0.9  # share of near-white pixels in a blown-out tile
# Hard glare: the whole frame is washed out (>= 90% of all 64 tiles blown). A hot-spot over the
# centre is only soft: a chart or a white pack with a plain centre looks the same to these
# checks (a real chart image in the repo has 75% of its central tiles flat white).
GLARE_BLOWN_ALL = 0.9
GLARE_SOFT_BLOWN_CENTER = 0.25
EDGE_LEVEL = 40
CUT_OFF_SOFT_RATIO = 3.0

_TILES = 8
_LAPLACIAN = ImageFilter.Kernel((3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), scale=1, offset=128)


class InvalidImage(Exception):
    """The bytes are not a decodable JPEG, PNG or WebP image."""


@dataclass(frozen=True, slots=True)
class QualityReport:
    """`reasons` are the clear failures that stop a scan (422 `image_quality_low`); `soft`
    are borderline signals, kept for calibration only (`scans.analysis.quality`)."""

    width: int
    height: int
    sharpness: float  # the sharpest tile's Laplacian variance
    detail_tiles: float  # share of tiles with any detail (variance >= FLAT_TILE_VARIANCE)
    saturated: float  # share of near-white pixels in the whole frame
    blown_center: float  # share of the 16 central tiles that are blown out
    blown_all: float  # share of all tiles that are blown out
    border_edges: float  # edge density on the frame border / inside (cut-off hint)
    reasons: tuple[QualityReason, ...]
    soft: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.reasons

    def as_dict(self) -> dict[str, Any]:
        """JSON-ready (rounded floats, lists) for `scans.analysis.quality`."""
        out = asdict(self)
        out["reasons"], out["soft"] = list(self.reasons), list(self.soft)
        return {k: round(v, 4) if isinstance(v, float) else v for k, v in out.items()}


@dataclass(frozen=True, slots=True)
class PreparedImage:
    jpeg: bytes  # what the model gets and what replaces the stored photo
    quality: QualityReport


def sniff_image_mime(data: bytes) -> ImageMime | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def prepare_with_quality(data: bytes) -> PreparedImage:
    """Decode, orient, downscale to <= MAX_EDGE_PX, re-encode as metadata-free JPEG, and
    check its quality."""
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
            jpeg = out.getvalue()
            # Measured on exactly what the model gets (the re-encoded JPEG).
            with Image.open(io.BytesIO(jpeg)) as sent:
                quality = quality_report(sent)
            return PreparedImage(jpeg=jpeg, quality=quality)
    except InvalidImage:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        raise InvalidImage("cannot decode") from exc


def prepare_for_extraction(data: bytes) -> bytes:
    """Decode, orient, downscale to <= MAX_EDGE_PX and re-encode as metadata-free JPEG."""
    return prepare_with_quality(data).jpeg


def _tile_boxes(width: int, height: int) -> list[tuple[int, int, int, int]]:
    """8 x 8 tiles, row by row (empty tiles of a tiny image are skipped)."""
    xs = [round(i * width / _TILES) for i in range(_TILES + 1)]
    ys = [round(j * height / _TILES) for j in range(_TILES + 1)]
    return [
        (xs[i], ys[j], xs[i + 1], ys[j + 1])
        for j in range(_TILES)
        for i in range(_TILES)
        if xs[i + 1] > xs[i] and ys[j + 1] > ys[j]
    ]


def _central(box: tuple[int, int, int, int], width: int, height: int) -> bool:
    """The tile's centre lies in the middle half of the frame on both axes (16 of 64)."""
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return width / 4 < cx < width * 3 / 4 and height / 4 < cy < height * 3 / 4


def _share(mask: Image.Image) -> float:
    """Share of 255 pixels in a 0/255 mask."""
    return ImageStat.Stat(mask).mean[0] / 255 if mask.width and mask.height else 0.0


def _laplacian(gray: Image.Image) -> Image.Image:
    """The Laplacian, the same size as `gray`. PIL leaves the outer 1 px ring unfiltered,
    so it is set to the flat value (128) instead of the raw pixel."""
    lap = gray.filter(_LAPLACIAN)
    if gray.width > 2 and gray.height > 2:
        flat = Image.new("L", gray.size, 128)
        flat.paste(lap.crop((1, 1, gray.width - 1, gray.height - 1)), (1, 1))
        return flat
    return Image.new("L", gray.size, 128)


def _border_edges(gray: Image.Image) -> float:
    """Edge density in a thin frame strip / inside it (0 when the image is too small)."""
    width, height = gray.size
    strip = max(2, min(width, height) // 50)
    if width <= 4 * strip or height <= 4 * strip:
        return 0.0
    edges = gray.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v >= EDGE_LEVEL else 0)
    inner = _share(edges.crop((strip, strip, width - strip, height - strip)))
    frame = (
        (0, 0, width, strip),
        (0, height - strip, width, height),
        (0, 0, strip, height),
        (width - strip, 0, width, height),
    )
    border = sum(_share(edges.crop(box)) for box in frame) / len(frame)
    return border / inner if inner > 0 else 0.0


def quality_report(img: Image.Image) -> QualityReport:
    """Blur, glare, resolution and crop signals for an oriented photo (CPU only)."""
    rgb = _to_rgb(img)
    width, height = rgb.size
    gray = rgb.convert("L")
    lap = _laplacian(gray)
    r, g, b = rgb.split()
    white = ImageChops.darker(ImageChops.darker(r, g), b).point(
        lambda v: 255 if v >= SATURATED_LEVEL else 0
    )

    boxes = _tile_boxes(width, height)
    variances = [ImageStat.Stat(lap.crop(box)).var[0] for box in boxes]
    blown = [
        var < FLAT_TILE_VARIANCE and _share(white.crop(box)) >= BLOWN_TILE_SATURATED
        for box, var in zip(boxes, variances, strict=True)
    ]
    central = [i for i, box in enumerate(boxes) if _central(box, width, height)]
    sharpness = max(variances, default=0.0)
    detail_tiles = (
        sum(v >= FLAT_TILE_VARIANCE for v in variances) / len(variances) if variances else 0.0
    )
    blown_center = sum(blown[i] for i in central) / len(central) if central else 0.0
    blown_all = sum(blown) / len(blown) if blown else 0.0

    border_edges = _border_edges(gray)

    reasons: list[QualityReason] = []
    soft: list[str] = []
    if max(width, height) < MIN_LONG_EDGE_PX or min(width, height) < MIN_SHORT_EDGE_PX:
        reasons.append("too_small")
    if sharpness < BLUR_MAX_VARIANCE:
        reasons.append("blur")
    elif sharpness < BLUR_SOFT_VARIANCE:
        soft.append("blur_borderline")
    if blown_all >= GLARE_BLOWN_ALL:
        reasons.append("glare")
    elif blown_center >= GLARE_SOFT_BLOWN_CENTER:
        soft.append("glare_borderline")
    if sharpness >= BLUR_SOFT_VARIANCE and border_edges >= CUT_OFF_SOFT_RATIO:
        soft.append("cut_off_suspected")  # meaningless on a blurred photo (no inner edges)
    return QualityReport(
        width=width,
        height=height,
        sharpness=sharpness,
        detail_tiles=detail_tiles,
        saturated=_share(white),
        blown_center=blown_center,
        blown_all=blown_all,
        border_edges=border_edges,
        reasons=tuple(reasons),
        soft=tuple(soft),
    )


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return img.convert("RGB") if img.mode != "RGB" else img
