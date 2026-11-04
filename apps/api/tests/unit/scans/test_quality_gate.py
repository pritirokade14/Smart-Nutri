"""Label accuracy v2, item 4: the image-quality gate before the paid extraction call.

The gate must NEVER reject a readable photo, so every "good" case below (dim, low contrast,
JPEG 40, slight blur, a small table, small text, a white scan, a tight crop, a small hot-spot,
640 px) must pass, and only clear failures are rejected. Synthetic labels only (no real label
photos in the repo). Calibration notes: images.py docstring and the label-v2 report.
"""

import io
import json

import pytest
from PIL import Image

from app.features.scans.images import (
    BLUR_MAX_VARIANCE,
    MAX_EDGE_PX,
    PreparedImage,
    prepare_for_extraction,
    prepare_with_quality,
    quality_report,
)
from tests.unit.scans import synthetic_labels as s


def _bytes(img: Image.Image, fmt: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **({"quality": 92} if fmt == "JPEG" else {}))
    return buf.getvalue()


def _report(img: Image.Image):
    return prepare_with_quality(_bytes(img.convert("RGB"))).quality


BASE = s.camera(s.label())

GOOD = {
    "clean": lambda: BASE,
    "large_photo": lambda: s.camera(s.label((2400, 1800), text_px=44)),
    "jpeg_q40": lambda: s.jpeg(BASE, 40),
    "slight_blur": lambda: s.blurred(BASE, 1.5),
    "soft_blur": lambda: s.blurred(BASE, 2),
    "blur_sigma3": lambda: s.blurred(BASE, 3),
    "blur_sigma3_noisy": lambda: s.camera(s.blurred(s.label(), 3), blur=0),
    "blur_sigma3_small_text": lambda: s.blurred(s.label(text_px=20), 3),
    "blur_sigma4_large_text": lambda: s.blurred(s.label(text_px=44), 4),
    "dim_light": lambda: s.dim(BASE, 0.25),
    "low_contrast": lambda: s.low_contrast(BASE, 0.25),
    "small_table": lambda: s.camera(s.label(table_scale=0.4)),
    "small_text": lambda: s.camera(s.label(text_px=16)),
    "white_scan": lambda: s.scan_of_white_label(),
    "white_scan_jpeg": lambda: s.jpeg(s.scan_of_white_label(), 70),
    "tight_crop": lambda: s.tight_crop(BASE),
    "bright_background": lambda: s.camera(s.label(background=(248, 248, 246))),
    "rotated": lambda: BASE.rotate(8, expand=True, fillcolor=(90, 80, 70)),
    "small_hot_spot": lambda: s.glare(BASE, radius=0.12, centre=(0.8, 0.12)),
    "centre_hot_spot": lambda: s.glare(BASE, radius=0.3),  # soft only: may still be readable
    "over_exposed_text_visible": lambda: s.overexposed(BASE),
    "640x480": lambda: BASE.resize((640, 480)),
    "480x360": lambda: BASE.resize((480, 360)),
    "portrait": lambda: s.camera(s.label((900, 1600))),
}

BAD = {
    "blur_sigma6": (lambda: s.blurred(BASE, 6), {"blur"}),
    "blur_sigma6_png": (lambda: s.blurred(s.label(), 6), {"blur"}),
    "blur_sigma10": (lambda: s.blurred(BASE, 10), {"blur"}),
    "blank": (lambda: Image.new("RGB", (1600, 1200), (240, 240, 240)), {"blur"}),
    "washed_out": (lambda: s.glare(BASE, radius=1.5), {"blur", "glare"}),
    "white_frame": (lambda: Image.new("RGB", (1600, 1200), (255, 255, 255)), {"blur", "glare"}),
    "tiny": (lambda: BASE.resize((300, 225)), {"too_small"}),
    "small_square": (lambda: BASE.resize((320, 320)), {"too_small"}),  # 102k px < 120k
    "sliver": (lambda: s.strip((1600, 100), lines=1), {"too_small"}),  # short edge 100 < 120
}


# P9 safety S6: readable strip labels and gallery crops must pass the size check.
STRIPS = {
    # A 10:1 phone photo of a wrapper strip: the 1600 px cap makes it 1600 x 168.
    "phone_strip_4000x420": lambda: s.camera(s.strip((4000, 420))),
    "strip_1600x160": lambda: s.strip((1600, 160), lines=2),
    "strip_1200x150": lambda: s.strip((1200, 150), lines=2),
    "strip_900x140": lambda: s.strip((900, 140), lines=2, text_px=22),
    "gallery_crop_380x340": lambda: s.gallery_crop(BASE),
    "gallery_crop_360x360": lambda: s.gallery_crop(BASE, (360, 360)),
    "gallery_crop_640x220": lambda: s.gallery_crop(BASE, (640, 220)),
}


@pytest.mark.parametrize("name", sorted(STRIPS))
def test_readable_strips_and_gallery_crops_pass(name):
    report = _report(STRIPS[name]())
    assert "too_small" not in report.reasons, (name, report)
    assert report.ok, (name, report)


def test_size_limits_are_area_and_short_edge():
    from app.features.scans.images import MIN_AREA_PX, MIN_SHORT_EDGE_PX

    assert (MIN_AREA_PX, MIN_SHORT_EDGE_PX) == (120_000, 120)
    blank = (250, 250, 248)
    for size, small in [
        ((347, 346), False),  # 120,062 px
        ((346, 346), True),  # 119,716 px
        ((1600, 120), False),
        ((1600, 119), True),
    ]:
        report = quality_report(Image.new("RGB", size, blank))
        assert ("too_small" in report.reasons) is small, size


@pytest.mark.parametrize("name", sorted(GOOD))
def test_readable_photos_are_never_rejected(name):
    report = _report(GOOD[name]())
    assert report.ok, (name, report)


@pytest.mark.parametrize("name", sorted(BAD))
def test_clearly_bad_photos_are_rejected(name):
    make, reasons = BAD[name]
    report = _report(make())
    assert not report.ok and set(report.reasons) == reasons, (name, report)


def test_borderline_signals_are_soft_only():
    assert "glare_borderline" in _report(s.glare(BASE, radius=0.4)).soft
    assert "blur_borderline" in _report(s.blurred(BASE, 2)).soft
    assert _report(s.blurred(BASE, 2)).ok


def test_blur_threshold_has_margin_below_readable_blur():
    """Lossless input (the worst case: no JPEG noise): sigma 3 on 30 px text and sigma 4 on
    44 px text, both still readable, sit well above the hard threshold."""
    for img in (s.blurred(s.label(), 3), s.blurred(s.label(text_px=44), 4)):
        report = prepare_with_quality(_bytes(img, "PNG")).quality
        assert report.sharpness > 1.8 * BLUR_MAX_VARIANCE


def test_report_is_json_ready():
    data = _report(BASE).as_dict()
    assert json.loads(json.dumps(data)) == data
    assert data["reasons"] == [] and isinstance(data["sharpness"], float)


def test_prepare_with_quality_returns_the_same_jpeg():
    raw = _bytes(BASE, "PNG")
    prepared = prepare_with_quality(raw)
    assert isinstance(prepared, PreparedImage)
    assert prepared.jpeg == prepare_for_extraction(raw)
    img = Image.open(io.BytesIO(prepared.jpeg))
    assert (
        max(img.size) <= MAX_EDGE_PX
        and (prepared.quality.width, prepared.quality.height) == img.size
    )


@pytest.mark.parametrize("locale", ["en", "hi", "mr"])
def test_every_reason_has_a_retake_hint(locale):
    from pathlib import Path
    from typing import get_args

    from app.features.scans.images import QualityReason

    messages = Path(__file__).resolve().parents[5] / "packages" / "i18n" / "messages"
    data = json.loads((messages / f"{locale}.json").read_text(encoding="utf-8"))
    assert data["error"]["image_quality_low"]
    assert all(data["image_quality"].get(r) for r in get_args(QualityReason))


def test_tiny_images_do_not_crash():
    for size in ((1, 1), (2, 3), (7, 5)):
        report = quality_report(Image.new("RGB", size, (10, 20, 30)))
        assert "too_small" in report.reasons
