"""Image sniffing and server-side downscale (Plan 4 Task 4, ruling R12)."""

import io

import pytest
from PIL import Image

from app.features.scans.images import (
    MAX_EDGE_PX,
    InvalidImage,
    prepare_for_extraction,
    sniff_image_mime,
)


def img_bytes(fmt="JPEG", size=(40, 30), mode="RGB", **save) -> bytes:
    buf = io.BytesIO()
    color = (10, 200, 10, 128) if mode == "RGBA" else (10, 200, 10)
    Image.new(mode, size, color).save(buf, format=fmt, **save)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("data", "mime"),
    [
        (img_bytes("JPEG"), "image/jpeg"),
        (img_bytes("PNG"), "image/png"),
        (img_bytes("WEBP"), "image/webp"),
        (b"\xff\xd8\xff\xdb" + b"\0" * 10, "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n" + b"\0" * 10, "image/png"),
        (b"RIFF\x10\0\0\0WEBPVP8 ", "image/webp"),
    ],
)
def test_sniff_known(data, mime):
    assert sniff_image_mime(data) == mime


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\xff\xd8",
        b"%PDF-1.7",
        b"GIF89a....",
        b"RIFF\x10\0\0\0WAVEfmt ",
        b"<svg xmlns=...>",
        img_bytes("GIF"),
        img_bytes("BMP"),
    ],
)
def test_sniff_rejects(data):
    assert sniff_image_mime(data) is None


def test_small_image_reencoded_to_jpeg_same_size():
    out = prepare_for_extraction(img_bytes("PNG", (300, 200)))
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG" and img.size == (300, 200)


@pytest.mark.parametrize(
    ("size", "expected"), [((4000, 1000), (1600, 400)), ((900, 2700), (533, 1600))]
)
def test_long_edge_capped(size, expected):
    img = Image.open(io.BytesIO(prepare_for_extraction(img_bytes("JPEG", size))))
    assert max(img.size) == MAX_EDGE_PX == 1600
    assert img.size == expected


def test_exif_and_gps_stripped():
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"
    exif[0x8825] = {1: "N", 2: (18.0, 31.0, 12.0)}
    out = prepare_for_extraction(img_bytes("JPEG", (50, 50), exif=exif.tobytes()))
    img = Image.open(io.BytesIO(out))
    assert not img.getexif() and "exif" not in img.info


def test_exif_orientation_applied_before_strip():
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 CW on display
    out = prepare_for_extraction(img_bytes("JPEG", (200, 100), exif=exif.tobytes()))
    assert Image.open(io.BytesIO(out)).size == (100, 200)


def test_alpha_flattened():
    out = prepare_for_extraction(img_bytes("PNG", (20, 20), mode="RGBA"))
    assert Image.open(io.BytesIO(out)).mode == "RGB"


@pytest.mark.parametrize(
    "data", [b"\xff\xd8\xff\xe0" + b"junk" * 40, b"\x89PNG\r\n\x1a\n" + b"\0" * 40, b"%PDF"]
)
def test_undecodable_raises(data):
    with pytest.raises(InvalidImage):
        prepare_for_extraction(data)


def test_pixel_bomb_rejected(monkeypatch):
    from app.features.scans import images

    monkeypatch.setattr(images, "MAX_PIXELS", 100)
    monkeypatch.setattr(images, "MAX_PIXELS_NON_JPEG", 100)
    for fmt in ("JPEG", "PNG"):
        with pytest.raises(InvalidImage):
            prepare_for_extraction(img_bytes(fmt, (20, 20)))


def test_big_png_rejected_before_full_decode(monkeypatch):
    # 1-bit 6000x5000 (30 MP) compresses to a few KB but would decode to a huge buffer.
    buf = io.BytesIO()
    Image.new("1", (6000, 5000)).save(buf, format="PNG")
    data = buf.getvalue()

    def boom(self, *a, **k):
        raise AssertionError("decoded an oversized PNG")

    monkeypatch.setattr(Image.Image, "load", boom)
    with pytest.raises(InvalidImage):
        prepare_for_extraction(data)


def test_jpeg_keeps_the_larger_pixel_limit():
    from app.features.scans import images

    assert images.MAX_PIXELS == 60_000_000
    assert images.MAX_PIXELS_NON_JPEG == 25_000_000
