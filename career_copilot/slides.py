"""Render slide outlines to 1080x1350 PNGs and a multi-page PDF carousel (Pillow only)."""
from __future__ import annotations
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG, FG, ACCENT, MUTED = (15, 23, 42), (241, 245, 249), (56, 189, 248), (148, 163, 184)


def _font(size: int, bold: bool = False):
    names = ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for d in ["/usr/share/fonts/truetype/dejavu", ""]:
        for n in names:
            try:
                return ImageFont.truetype(os.path.join(d, n) if d else n, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render_slide(title: str, body: str, index: int, total: int, footer: str = "") -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 16], fill=ACCENT)
    y = 140
    for line in textwrap.wrap(title, 22):
        d.text((90, y), line, font=_font(72, True), fill=FG)
        y += 90
    y += 40
    for para in body.split("\n"):
        for line in textwrap.wrap(para, 38) or [""]:
            d.text((90, y), line, font=_font(44), fill=FG)
            y += 60
        y += 20
    d.text((90, H - 110), footer, font=_font(32), fill=MUTED)
    d.text((W - 200, H - 110), f"{index}/{total}", font=_font(32, True), fill=ACCENT)
    return img


def render_carousel(outline: list[dict], out_dir: str, footer: str = "") -> tuple[list[str], str]:
    os.makedirs(out_dir, exist_ok=True)
    images, paths = [], []
    for i, s in enumerate(outline, 1):
        img = render_slide(s["title"], s.get("body", ""), i, len(outline), footer)
        p = os.path.join(out_dir, f"slide-{i}.png")
        img.save(p)
        images.append(img)
        paths.append(p)
    pdf = os.path.join(out_dir, "carousel.pdf")
    images[0].save(pdf, save_all=True, append_images=images[1:])
    return paths, pdf
