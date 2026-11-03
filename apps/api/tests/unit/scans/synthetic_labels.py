"""Synthetic nutrition-label photos for the image-quality gate tests (no real photos).

`label()` renders a pack with a nutrition table, ingredients and an allergen line at
phone-photo size; the helpers degrade it the way real photos go wrong (blur, glare,
over-exposure) or stay readable (noise, JPEG, dim light, a tight crop, a small table).
"""

from __future__ import annotations

import io
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROWS = [
    ("Energy (kcal)", "452", "136"),
    ("Protein (g)", "6.8", "2.0"),
    ("Carbohydrate (g)", "68.2", "20.5"),
    ("  Total Sugars (g)", "24.1", "7.2"),
    ("  Added Sugars (g)", "20.0", "6.0"),
    ("Total Fat (g)", "17.0", "5.1"),
    ("  Saturated Fat (g)", "8.2", "2.5"),
    ("  Trans Fat (g)", "<0.1", "<0.1"),
    ("Sodium (mg)", "310", "93"),
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def label(
    size: tuple[int, int] = (1600, 1200),
    *,
    background: tuple[int, int, int] = (236, 232, 222),
    pack: tuple[int, int, int] = (190, 40, 40),
    table_scale: float = 1.0,
    text_px: int = 30,
    margin: float = 0.12,
    seed: int = 1,
) -> Image.Image:
    """A pack photo: coloured pack, a white nutrition panel with rows and lines, text."""
    w, h = size
    img = Image.new("RGB", size, background)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, int(h * 0.18)), fill=pack)
    d.text((int(w * 0.05), int(h * 0.04)), "MASALA CRUNCH", fill=(250, 240, 200), font=_font(70))
    px0, py0 = int(w * margin), int(h * 0.24)
    pw, ph = int(w * 0.76 * table_scale), int(h * 0.62 * table_scale)
    d.rectangle((px0, py0, px0 + pw, py0 + ph), fill=(250, 250, 248), outline=(20, 20, 20), width=3)
    font = _font(max(8, int(text_px * table_scale)))
    d.text(
        (px0 + 12, py0 + 8),
        "NUTRITION INFORMATION  per 100 g   per 30 g",
        fill=(10, 10, 10),
        font=font,
    )
    row_h = (ph - 60) / (len(ROWS) + 3)
    for i, (name, a, b) in enumerate(ROWS):
        y = py0 + 50 + i * row_h
        d.line((px0, y, px0 + pw, y), fill=(40, 40, 40), width=2)
        d.text((px0 + 12, y + 6), name, fill=(10, 10, 10), font=font)
        d.text((px0 + int(pw * 0.6), y + 6), a, fill=(10, 10, 10), font=font)
        d.text((px0 + int(pw * 0.8), y + 6), b, fill=(10, 10, 10), font=font)
    y = py0 + 50 + len(ROWS) * row_h + 10
    d.text(
        (px0 + 12, y),
        "Ingredients: wheat flour, sugar, palm oil, salt,",
        fill=(10, 10, 10),
        font=font,
    )
    d.text(
        (px0 + 12, y + row_h),
        "milk solids. Contains wheat, milk. इसमें गेहूं है।",
        fill=(10, 10, 10),
        font=font,
    )
    rng = random.Random(seed)
    for _ in range(40):  # small print and specks elsewhere on the pack
        x, yy = rng.randrange(w), rng.randrange(int(h * 0.88), h)
        d.text((x, yy), "FSSAI 1001", fill=(60, 60, 60), font=_font(14))
    return img


def camera(img: Image.Image, *, blur: float = 0.6, noise: int = 6, seed: int = 2) -> Image.Image:
    """A phone camera: slight optical softness and sensor noise."""
    out = img.filter(ImageFilter.GaussianBlur(blur)) if blur else img.copy()
    if noise:
        rng = random.Random(seed)
        speck = Image.effect_noise(out.size, noise * 4).convert("RGB")
        out = Image.blend(out, speck, 0.04 + rng.random() * 0.01)
    return out


def jpeg(img: Image.Image, quality: int) -> Image.Image:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def dim(img: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(factor)


def low_contrast(img: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Contrast(img).enhance(factor)


def blurred(img: Image.Image, radius: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius))


def glare(img: Image.Image, *, radius: float = 0.35, centre=(0.5, 0.55)) -> Image.Image:
    """A flash hot-spot: a blown-out white disc with a soft edge over the table."""
    w, h = img.size
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    r = int(min(w, h) * radius)
    cx, cy = int(w * centre[0]), int(h * centre[1])
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(r * 0.15))
    return Image.composite(Image.new("RGB", img.size, (255, 255, 255)), img, mask)


def overexposed(img: Image.Image) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(4.0)


def scan_of_white_label(size=(1600, 1200)) -> Image.Image:
    """A flat-bed scan or screenshot: pure white background, black text (often 255 white)."""
    img = label(size, background=(255, 255, 255), pack=(255, 255, 255))
    return img


def tight_crop(img: Image.Image) -> Image.Image:
    """Cropped to the table: text and lines touch the frame on every side."""
    w, h = img.size
    return img.crop((int(w * 0.13), int(h * 0.26), int(w * 0.86), int(h * 0.84)))
