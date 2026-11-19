#!/usr/bin/env python3
"""Shir Levi - Instagram Reels deal generator.

Builds vertical 1080x1920 Reels (MP4, H.264) from the brand logo + photos,
with correctly shaped right-to-left Hebrew text, using Pillow + ffmpeg.

    python3 make_reels.py              # render every reel in deals.json
    python3 make_reels.py 02_brow      # render reels whose id contains "02_brow"

All copy, prices and scene timing live in deals.json.
"""
import json
import math
import random
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "output"

W, H, FPS = 1080, 1920, 30
XFADE = 0.25  # seconds of cross-fade between scenes

# Brand palette (taken from the existing stories: cream logo plate, cocoa box, mauve button)
CREAM = (246, 240, 233)
COCOA = (92, 66, 54)
MAUVE = (128, 82, 90)
INK = (24, 19, 17)
GOLD = (214, 186, 146)
WHITE = (255, 255, 255)


# ---------------------------------------------------------------- helpers
def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = min(max(x, 0.0), 1.0)
    return 3 * x * x - 2 * x * x * x


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def fade(img, opacity):
    if opacity >= 0.999:
        return img
    img = img.copy()
    a = img.getchannel("A").point(lambda v: int(v * max(opacity, 0)))
    img.putalpha(a)
    return img


@lru_cache(maxsize=None)
def font(name, size, weight="Bold"):
    f = ImageFont.truetype(str(ASSETS / "fonts" / f"{name}.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


_LTR_RUN = re.compile(r"[A-Za-z0-9@][A-Za-z0-9@._:%–\-]*[A-Za-z0-9:%]|[A-Za-z0-9]")


def ltr_isolate(text):
    """Keep Latin words and number ranges (POV:, 6–8, @handle) in left-to-right order inside Hebrew lines."""
    return _LTR_RUN.sub(lambda m: "\u2066" + m.group(0) + "\u2069", text)


def text_layer(text, size, color=WHITE, family="heebo", weight="ExtraBold", shadow=True, stroke=0):
    """Render one line of (RTL) text to a tight RGBA image with a soft shadow."""
    f = font(family, size, weight)
    text = ltr_isolate(text)
    kw = dict(direction="rtl", language="he", features=["kern", "liga"])
    bbox = f.getbbox(text, **kw, stroke_width=stroke)
    pad = int(size * 0.35)
    w, h = bbox[2] - bbox[0] + pad * 2, bbox[3] - bbox[1] + pad * 2
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pos = (pad - bbox[0], pad - bbox[1])
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pos[0], pos[1] + size * 0.04), text, font=f, fill=(0, 0, 0, 150), **kw)
        sh = sh.filter(ImageFilter.GaussianBlur(size * 0.12))
        layer.alpha_composite(sh)
    ImageDraw.Draw(layer).text(pos, text, font=f, fill=color, stroke_width=stroke,
                               stroke_fill=color, **kw)
    return layer


def rounded_box(size, color, alpha=255, radius=40):
    box = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=color + (alpha,))
    return box


def paste_center(canvas, layer, cx, cy):
    canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


# ---------------------------------------------------------------- assets
@lru_cache(maxsize=None)
def photo(name):
    return Image.open(ASSETS / "photos" / name).convert("RGB")


@lru_cache(maxsize=None)
def logo(color=INK, width=560):
    """Turn the black-on-white logo into a transparent, recolourable sprite (keeps the glitter)."""
    src = Image.open(ASSETS / "logo.png").convert("RGBA")
    bg = Image.new("RGBA", src.size, WHITE + (255,))
    bg.alpha_composite(src)
    gray = ImageOps.grayscale(bg)
    alpha = ImageOps.autocontrast(ImageOps.invert(gray), cutoff=1).point(lambda v: 0 if v < 18 else min(255, int(v * 1.25)))
    bbox = alpha.getbbox()
    alpha = alpha.crop(bbox)
    out = Image.new("RGBA", alpha.size, color + (255,))
    out.putalpha(alpha)
    h = int(out.height * width / out.width)
    return out.resize((width, h), Image.LANCZOS)


@lru_cache(maxsize=None)
def logo_plate(width=520):
    lg = logo(INK, width - 90)
    plate = rounded_box((width, lg.height + 70), CREAM, 240, radius=34)
    paste_center(plate, lg, plate.width / 2, plate.height / 2)
    return plate


@lru_cache(maxsize=None)
def sparkle_sprite(r=18):
    s = Image.new("RGBA", (r * 4, r * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    c = r * 2
    d.polygon([(c, c - 2 * r), (c + 3, c), (c, c + 2 * r), (c - 3, c)], fill=(255, 255, 255, 230))
    d.polygon([(c - 2 * r, c), (c, c - 3), (c + 2 * r, c), (c, c + 3)], fill=(255, 255, 255, 230))
    d.ellipse([c - 5, c - 5, c + 5, c + 5], fill=(255, 255, 255, 255))
    return s.filter(ImageFilter.GaussianBlur(1.2))


class Sparkles:
    """Twinkling glitter that echoes the glitter in the logo."""

    def __init__(self, n=18, seed=7, region=(60, 200, W - 60, H - 380)):
        rnd = random.Random(seed)
        self.p = [(rnd.uniform(region[0], region[2]), rnd.uniform(region[1], region[3]),
                   rnd.uniform(0.4, 1.0), rnd.uniform(0.5, 1.3), rnd.random()) for _ in range(n)]

    def draw(self, canvas, t, strength=1.0):
        sp = sparkle_sprite()
        for x, y, scale, freq, ph in self.p:
            a = max(0.0, math.sin(2 * math.pi * (t * freq + ph))) ** 4 * strength
            if a < 0.05:
                continue
            size = max(4, int(sp.width * scale * (0.6 + 0.4 * a)))
            paste_center(canvas, fade(sp.resize((size, size), Image.BILINEAR), a), x, y)


# ---------------------------------------------------------------- backgrounds
@lru_cache(maxsize=None)
def cover_base(name, fit=False):
    """Pre-scale an image to slightly bigger than the frame (cover). fit=True: letterbox on a blurred copy."""
    img = photo(name)
    if not fit:
        s = max(W / img.width, H / img.height) * 1.0
        return img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    s = max(W / img.width, H / img.height)
    bg = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.BILINEAR)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), COCOA), 0.25)
    fw = W
    fg = img.resize((fw, int(img.height * fw / img.width)), Image.LANCZOS)
    bg.paste(fg, (0, (H - fg.height) // 2))
    return bg


def ken_burns(name, p, zoom=(1.0, 1.15), focus=(0.5, 0.5), fit=False):
    base = cover_base(name, fit)
    z = zoom[0] + (zoom[1] - zoom[0]) * ease_in_out(p)
    cw, ch = W / z, H / z
    cx = focus[0] * base.width if not fit else base.width / 2
    cy = focus[1] * base.height if not fit else base.height / 2
    x0 = min(max(cx - cw / 2, 0), base.width - cw)
    y0 = min(max(cy - ch / 2, 0), base.height - ch)
    frame = base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    return frame.convert("RGBA")


def vignette():
    if not hasattr(vignette, "img"):
        g = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(g)
        for i in range(0, 520, 4):  # top and bottom gradients for text legibility
            a = int(150 * (1 - i / 520) ** 2)
            d.line([(0, i), (W, i)], fill=a)
            d.line([(0, H - 1 - i), (W, H - 1 - i)], fill=a)
        v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        v.putalpha(g)
        vignette.img = v
    return vignette.img


# ---------------------------------------------------------------- text animation
def animated_lines(canvas, lines, t, pos="top", box=False, start=0.15, stagger=0.22, size0=104, size1=70):
    """Lines slide up + fade in one after another. First line is the big hook."""
    layers = []
    for i, txt in enumerate(lines):
        big = i == 0
        size = size0 if big else size1
        lay = _line(txt, size, "ExtraBold" if big else "Medium")
        while lay.width > W - 90 and size > 40:  # auto-shrink long lines to stay inside safe margins
            size -= 6
            lay = _line(txt, size, "ExtraBold" if big else "Medium")
        layers.append(lay)
    gap = 14
    total_h = sum(l.height for l in layers) - gap * (len(layers) - 1) * 0  # tight layers already padded
    y = {"top": 330, "center": H / 2 - total_h / 2, "lower": 1130}[pos]
    if box:
        bw = min(W - 120, max(l.width for l in layers) + 60)
        a = ease_out((t - start + 0.1) / 0.35)
        bx = rounded_box((int(bw), int(total_h + 40)), COCOA, int(205 * a), radius=36)
        canvas.alpha_composite(bx, (int((W - bw) / 2), int(y - 20 + (1 - a) * 30)))
    for i, l in enumerate(layers):
        p = ease_out((t - start - i * stagger) / 0.45)
        if p > 0:
            paste_center(canvas, fade(l, p), W / 2, y + l.height / 2 + (1 - p) * 60)
        y += l.height


def native_lines(canvas, lines, t, y=300, start=0.1, stagger=0.35, size=68):
    """Instagram/TikTok 'native' captions: black text on white rounded boxes, popping in.
    Native-looking text reads as a real post rather than an ad."""
    for i, txt in enumerate(lines):
        p = ease_back((t - start - i * stagger) / 0.3)
        lay = _native(txt, size)
        while lay.width > W - 90:
            size -= 4
            lay = _native(txt, size)
        if p > 0:
            sc = max(0.01, p)
            lay2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
            paste_center(canvas, lay2, W / 2, y + lay.height / 2)
        y += lay.height + 6


def subtitle_lines(canvas, lines, t, duration, y=1180, size=78):
    """Her own style: white subtitle text with a dark shadow, lower-middle,
    one phrase at a time (like her voice-over captions). Phrase 1 shows from frame 0 = instant hook."""
    if not lines:
        return
    slot = duration / len(lines)
    i = min(int(t / slot), len(lines) - 1)
    lt = t - i * slot
    lay = _subtitle(lines[i], size)
    p = 1.0 if (i == 0 and lt < 0.05) else ease_out(lt / 0.18)
    sc = 0.92 + 0.08 * p
    lay2 = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
    paste_center(canvas, fade(lay2, max(p, 0.35 if i == 0 else 0)), W / 2, y)


@lru_cache(maxsize=None)
def _subtitle(txt, size):
    lay = text_layer(txt, size, WHITE, "heebo", "Bold", shadow=True)
    while lay.width > W - 90 and size > 40:
        size -= 4
        lay = text_layer(txt, size, WHITE, "heebo", "Bold", shadow=True)
    out = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    out.alpha_composite(lay)
    out.alpha_composite(lay)  # double shadow pass = darker, like her captions
    return out


@lru_cache(maxsize=None)
def _native(txt, size):
    t = text_layer(txt, size, INK, "heebo", "Bold", shadow=False)
    box = rounded_box((t.width - int(size * 0.2), t.height - int(size * 0.35)), WHITE, 245, radius=int(size * 0.3))
    paste_center(box, t, box.width / 2, box.height / 2)
    return box


@lru_cache(maxsize=None)
def _number(n):
    d = 170
    b = Image.new("RGBA", (d + 20, d + 20), (0, 0, 0, 0))
    ImageDraw.Draw(b).ellipse([10, 10, d + 10, d + 10], fill=MAUVE + (255,), outline=GOLD + (255,), width=6)
    paste_center(b, text_layer(str(n), 110, WHITE, "heebo", "Black", shadow=False), b.width / 2, b.height / 2)
    return b


def sharp_crop(name, z, focus):
    """Crop straight from the original photo (sharper than the pre-scaled base at high zoom)."""
    img = photo(name)
    s0 = max(W / img.width, H / img.height) * z
    cw, ch = W / s0, H / s0
    cx, cy = focus[0] * img.width, focus[1] * img.height
    x0 = min(max(cx - cw / 2, 0), img.width - cw)
    y0 = min(max(cy - ch / 2, 0), img.height - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")


@lru_cache(maxsize=None)
def _line(txt, size, weight):
    return text_layer(txt, size, WHITE, "heebo", weight)


# ---------------------------------------------------------------- scenes
class Scene:
    def __init__(self, spec, studio):
        self.s, self.studio = spec, studio
        if spec["type"] == "montage":
            self.duration = len(spec["images"]) * spec.get("cut", 0.55)
        else:
            self.duration = spec["duration"]
        self.spark = Sparkles(seed=hash(json.dumps(spec, ensure_ascii=False)) & 0xFFFF)

    def frame(self, t):
        return getattr(self, "_" + self.s["type"])(t)

    # full-bleed photo with ken-burns + kinetic text
    def _photo(self, t):
        s = self.s
        c = ken_burns(s["image"], t / self.duration, tuple(s.get("zoom", (1, 1.15))), tuple(s.get("focus", (0.5, 0.5))), s.get("fit", False))
        c.alpha_composite(vignette())
        self.spark.draw(c, t, 0.7)
        if "number" in s:
            p = ease_back((t - 0.05) / 0.35)
            if p > 0:
                nb = _number(s["number"])
                paste_center(c, nb.resize((max(1, int(nb.width * p)), max(1, int(nb.height * p))), Image.BILINEAR), W / 2, 330)
        if s.get("style") == "subtitle":
            subtitle_lines(c, s.get("lines", []), t, self.duration)
        elif s.get("style") == "native":
            native_lines(c, s.get("lines", []), t, y=s.get("y", 300 if "number" not in s else 470))
        else:
            animated_lines(c, s.get("lines", []), t, s.get("pos", "top"), s.get("box", False))
        if s.get("footer"):
            native_lines(c, [s["footer"]], t, y=1340, start=0.6, size=50)
        return c

    def _reveal(self, t):
        """'Wait for it' - starts on an extreme close-up and pulls back to the full result."""
        s = self.s
        a, b = s["from"], s["to"]
        ra = s.get("reveal_at", 0.65)
        p = ease_in_out(min(1.0, (t / self.duration) / ra))
        z = math.exp(math.log(a["zoom"]) + (math.log(b["zoom"]) - math.log(a["zoom"])) * p)
        foc = (a["focus"][0] + (b["focus"][0] - a["focus"][0]) * p, a["focus"][1] + (b["focus"][1] - a["focus"][1]) * p)
        c = sharp_crop(s["image"], z, foc)
        c.alpha_composite(vignette())
        done = t / self.duration >= ra
        if not done:
            native_lines(c, s.get("lines_before", []), t, y=300)
            # progress bar - makes people wait for the reveal
            bw = int((W - 160) * min(1, (t / self.duration) / ra))
            c.alpha_composite(rounded_box((W - 160, 14), WHITE, 90, 7), (80, 250))
            if bw > 14:
                c.alpha_composite(rounded_box((bw, 14), WHITE, 255, 7), (80, 250))
        else:
            if t - ra * self.duration < 0.12:
                c = Image.blend(c, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.6)
            self.spark.draw(c, t, 1.0)
            native_lines(c, s.get("lines_after", []), t - ra * self.duration, y=300)
        return c

    def _choice(self, t):
        """Comment bait: two options, 'comment 1 or 2' + 'send to a friend'."""
        s = self.s
        c = Image.new("RGBA", (W, H), INK + (255,))
        hh = (H - 8) // 2
        for i, name in enumerate(s["images"]):
            foc = tuple(s.get("focus", [[0.5, 0.5]] * 2)[i])
            fr = ken_burns(name, t / self.duration, (1.0, 1.12), foc)
            fr = fr.resize((W, int(H * W / W)), Image.BILINEAR).crop((0, (H - hh) // 2, W, (H - hh) // 2 + hh))
            slide = (1 - ease_out(t / 0.45)) * (W if i == 0 else -W)
            c.alpha_composite(fr, (int(slide), 0 if i == 0 else hh + 8))
            q = ease_back((t - 0.5 - i * 0.25) / 0.35)
            if q > 0:
                nb = _number(i + 1)
                nb = nb.resize((max(1, int(nb.width * q * 0.8)), max(1, int(nb.height * q * 0.8))), Image.BILINEAR)
                paste_center(c, nb, W - 150, (hh / 2 if i == 0 else hh + 8 + hh / 2))
        native_lines(c, s.get("lines", []), t, y=hh - 40, start=0.3, size=64)
        if s.get("footer"):
            native_lines(c, [s["footer"]], t, y=H - 520, start=1.2, size=54)
        return c

    def _split(self, t):
        s = self.s
        c = Image.new("RGBA", (W, H), INK + (255,))
        half = W // 2 - 4
        for i, name in enumerate(s["images"]):
            foc = tuple(s.get("focus", [[0.5, 0.5]] * 2)[i])
            fr = ken_burns(name, t / self.duration, (1.25, 1.4), foc, fit=False)
            fr = fr.crop(((W - half) // 2, 0, (W - half) // 2 + half, H))
            slide = (1 - ease_out(t / 0.5)) * (half if i == 0 else -half)
            c.alpha_composite(fr, (int((W - half if i == 0 else 0) + slide), 0))  # RTL: first item on the right
        c.alpha_composite(vignette())
        for i, lab in enumerate(s.get("labels", [])):
            p = ease_out((t - 0.5 - i * 0.2) / 0.4)
            lay = fade(_label(lab), p)
            x = (W * 3 / 4) if i == 0 else (W / 4)
            paste_center(c, lay, x, 1250 + (1 - p) * 40)
        animated_lines(c, s.get("lines", []), t, "top", start=0.9)
        return c

    def _deal(self, t):
        s = self.s
        bg = ken_burns(s["image"], 0.4 + 0.3 * t / self.duration, (1.1, 1.2), (0.5, 0.45))
        bg = _blur_dark(bg)
        c = bg.copy()
        self.spark.draw(c, t, 1.0)
        paste_center(c, logo_plate(460), W / 2, 330)
        # badge pops with overshoot
        p = ease_back((t - 0.2) / 0.5)
        if p > 0:
            b = _badge(tuple(s["badge"]))
            sc = max(0.01, p) * (1 + 0.025 * math.sin(t * 5))  # gentle pulse
            bb = b.resize((max(1, int(b.width * sc)), max(1, int(b.height * sc))), Image.BILINEAR)
            paste_center(c, bb, W / 2, 800)
        for i, (txt, size, wt, col) in enumerate([(s["title"], 74, "ExtraBold", WHITE), (s["subtitle"], 54, "Medium", GOLD)]):
            q = ease_out((t - 0.75 - i * 0.2) / 0.4)
            if q > 0:
                lay = fade(_text(txt, size, wt, col), q)
                paste_center(c, lay, W / 2, 1140 + i * 100 + (1 - q) * 40)
        return c

    def _end(self, t):
        s, st = self.s, self.studio
        c = Image.new("RGBA", (W, H), CREAM + (255,))
        p = ease_out(t / 0.6)
        lg = logo(INK, 860)
        sc = 0.9 + 0.1 * p
        lg2 = fade(lg.resize((int(lg.width * sc), int(lg.height * sc)), Image.LANCZOS), p)
        paste_center(c, lg2, W / 2, 640)
        q = ease_out((t - 0.35) / 0.4)
        paste_center(c, fade(_text(s.get("headline", ""), 84, "ExtraBold", COCOA, shadow=False), q), W / 2, 960 + (1 - q) * 30)
        # CTA button (like the mauve pill in the existing story)
        r = ease_back((t - 0.6) / 0.45)
        if r > 0:
            btn = _cta(st["cta"])
            btn = btn.resize((max(1, int(btn.width * r)), max(1, int(btn.height * r))), Image.BILINEAR)
            paste_center(c, btn, W / 2, 1150)
        u = ease_out((t - 0.9) / 0.4)
        paste_center(c, fade(_text(f"{st['city']}  ·  \u2066{st['handle']}\u2069", 50, "Medium", COCOA, shadow=False), u), W / 2, 1300)
        return c

    def _montage(self, t):
        s = self.s
        cut = s.get("cut", 0.55)
        i = min(int(t / cut), len(s["images"]) - 1)
        lt = (t - i * cut) / cut
        name = s["images"][i]
        fit = name == "brow_closeup.jpg"
        c = ken_burns(name, lt, (1.18, 1.0), (0.5, 0.45), fit)  # punch-in on every cut
        if lt < 0.12:  # white flash on the cut
            c = Image.blend(c, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.5 * (1 - lt / 0.12))
        c.alpha_composite(vignette())
        self.spark.draw(c, t, 0.8)
        paste_center(c, logo_plate(400), W / 2, 260)
        lines = s.get("lines", [])
        y = 820
        for k, txt in enumerate(lines):
            q = ease_back((t - 0.4 - k * 0.6) / 0.35)
            if q > 0:
                lay = _text(txt, 150, "Black", WHITE)
                lay = lay.resize((max(1, int(lay.width * q)), max(1, int(lay.height * q))), Image.BILINEAR)
                paste_center(c, lay, W / 2, y)
            y += 190
        return c


@lru_cache(maxsize=None)
def _text(txt, size, weight, color, shadow=True):
    return text_layer(txt, size, color, "heebo", weight, shadow)


@lru_cache(maxsize=None)
def _label(txt):
    t = text_layer(txt, 62, INK, "heebo", "Bold", shadow=False)
    pill = rounded_box((t.width + 40, t.height - 10), CREAM, 235, radius=(t.height - 10) // 2)
    paste_center(pill, t, pill.width / 2, pill.height / 2)
    return pill


@lru_cache(maxsize=None)
def _cta(txt):
    t = text_layer(txt, 52, WHITE, "heebo", "Bold", shadow=False)
    pill = rounded_box((t.width + 80, t.height + 10), MAUVE, 255, radius=(t.height + 10) // 2)
    paste_center(pill, t, pill.width / 2, pill.height / 2)
    return pill


@lru_cache(maxsize=None)
def _badge(lines):
    d = 420
    b = Image.new("RGBA", (d + 40, d + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(b)
    dr.ellipse([20, 20, d + 20, d + 20], fill=MAUVE + (255,), outline=GOLD + (255,), width=8)
    dr.ellipse([42, 42, d - 2, d - 2], outline=(255, 255, 255, 90), width=3)
    big = text_layer(lines[0], 150 if len(lines[0]) <= 4 else 124, WHITE, "heebo", "Black", shadow=False)
    small = text_layer(lines[1], 56, CREAM, "heebo", "Medium", shadow=False)
    paste_center(b, big, b.width / 2, b.height / 2 - 30)
    paste_center(b, small, b.width / 2, b.height / 2 + 95)
    return b


def _blur_dark(img):
    img = img.filter(ImageFilter.GaussianBlur(14))
    return Image.blend(img, Image.new("RGBA", (W, H), COCOA + (255,)), 0.45)


# ---------------------------------------------------------------- render
def render(reel, studio):
    scenes = [Scene(s, studio) for s in reel["scenes"]]
    total = sum(s.duration for s in scenes)
    nframes = int(round(total * FPS))
    out = OUT / f"{reel['id']}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    starts = [sum(s.duration for s in scenes[:i]) for i in range(len(scenes))]
    cover = None
    for f in range(nframes):
        t = f / FPS
        i = max(k for k in range(len(scenes)) if starts[k] <= t + 1e-9)
        lt = t - starts[i]
        frame = scenes[i].frame(lt)
        # cross-fade into the next scene
        if i + 1 < len(scenes) and scenes[i].duration - lt < XFADE and scenes[i].s["type"] != "montage":
            a = 1 - (scenes[i].duration - lt) / XFADE
            frame = Image.blend(frame, scenes[i + 1].frame(0.0), ease_in_out(a))
        elif i + 1 == len(scenes) and reel.get("loop") and total - t < 0.4:
            # seamless loop: fade the last frame into the first so rewatches feel continuous
            a = 1 - (total - t) / 0.4
            frame = Image.blend(frame, scenes[0].frame(0.0), ease_in_out(a))
        rgb = frame.convert("RGB")
        if f == int(1.6 * FPS):
            cover = rgb
        proc.stdin.write(rgb.tobytes())
    proc.stdin.close()
    proc.wait()
    if cover is not None:
        cover.save(OUT / f"{reel['id']}_cover.jpg", quality=92)
    add_sound(reel, scenes, starts, total, out)
    print(f"✔ {out.name}  ({total:.1f}s, {nframes} frames)")


def add_sound(reel, scenes, starts, total, video):
    """Write output/with_sound/<id>.mp4: same video + original music and synced sound effects."""
    import soundtrack
    dst = OUT / "with_sound"
    dst.mkdir(exist_ok=True)
    wav = dst / f"{reel['id']}.wav"
    soundtrack.build(reel, scenes, starts, total, wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "lowpass=f=14000,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(dst / video.name)], check=True)
    wav.unlink()


def main():
    cfg = json.loads((ROOT / "deals.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    flt = sys.argv[1] if len(sys.argv) > 1 else ""
    for reel in cfg["reels"]:
        if flt in reel["id"]:
            render(reel, cfg["studio"])


if __name__ == "__main__":
    main()
