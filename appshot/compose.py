"""Compose a full App Store screenshot: background + caption + framed device.

The output is always flattened to RGB at the exact slot dimensions, with an
assertion guarding the exact-pixel requirement before the image is returned.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import specs
from .frame import draw_device

# Layout as fractions of the canvas.
SIDE_MARGIN = 0.08
CAPTION_TOP = 0.055
CAPTION_FONT = 0.052      # font size / canvas width
CAPTION_LINE_GAP = 0.012
DEVICE_GAP = 0.030        # gap below caption before device
BOTTOM_MARGIN = 0.05

# Drop shadow under the framed device, as fractions of canvas width.
SHADOW_BLUR = 0.016       # gaussian blur radius
SHADOW_OFFSET = 0.006     # vertical drop
SHADOW_ALPHA = 90         # 0-255; lower = subtler

# Fallback fonts tried (in order) when the config font is missing/unset, so the
# pipeline produces a properly sized caption out of the box. Pillow ships no
# bundled TrueType in some builds, so we lean on common system fonts first and
# only drop to load_default() (a tiny bitmap font) as a last resort.
FALLBACK_FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",                  # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",    # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Debian/Ubuntu
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "DejaVuSans.ttf",                                        # if Pillow bundles it
]


def _rgb(value):
    """'#RRGGBB' -> (r, g, b)."""
    v = value.lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def _background(size, spec):
    """Solid color (str) or 2-stop vertical gradient (list[str, str])."""
    w, h = size
    if isinstance(spec, str):
        return Image.new("RGB", size, _rgb(spec))
    top, bottom = _rgb(spec[0]), _rgb(spec[1])
    grad = Image.new("RGB", (1, h))
    px = grad.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(round(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
    return grad.resize(size)


def _load_font(path, size):
    candidates = ([path] if path else []) + FALLBACK_FONTS
    for cand in candidates:
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue
    return ImageFont.load_default()  # last resort; caption will be tiny


def _wrap(draw, text, font, max_width):
    lines, words, cur = [], text.split(), ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render_shot(slot_name, capture, caption, background, font_path, caption_color):
    """Build one screenshot. Returns (RGB image, [warnings])."""
    w, h = specs.slot_size(slot_name)
    family = specs.screenshot_slots()[slot_name]["family"]

    canvas = _background((w, h), background)
    draw = ImageDraw.Draw(canvas)

    # Caption.
    font = _load_font(font_path, round(w * CAPTION_FONT))
    side = round(w * SIDE_MARGIN)
    lines = _wrap(draw, caption, font, w - 2 * side) if caption else []
    y = round(h * CAPTION_TOP)
    line_gap = round(h * CAPTION_LINE_GAP)
    fill = _rgb(caption_color)
    for line in lines:
        tw = draw.textlength(line, font=font)
        ascent, descent = font.getmetrics()
        draw.text(((w - tw) / 2, y), line, font=font, fill=fill)
        y += ascent + descent + line_gap

    # Device. Size the screen to (about) fill the layout box at the slot's
    # aspect so the capture is drawn near its final size rather than at full
    # canvas scale and shrunk; thumbnail() is then a cheap clamp that also
    # absorbs the bezel overflow so the framed device fits inside the box.
    box_top = y + round(h * DEVICE_GAP)
    box_w = w - 2 * side
    box_h = h - box_top - round(h * BOTTOM_MARGIN)
    screen_h = box_h
    screen_w = round(screen_h * (w / h))
    device, warnings = draw_device(capture, family, (screen_w, screen_h))
    device.thumbnail((box_w, box_h), Image.LANCZOS)
    dx = (w - device.width) // 2
    dy = box_top + (box_h - device.height) // 2

    # Drop shadow: a blurred black silhouette of the device, dropped slightly.
    blur = round(w * SHADOW_BLUR)
    pad = blur * 3
    shadow = Image.new("RGBA", (device.width + 2 * pad, device.height + 2 * pad),
                       (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", device.size, (0, 0, 0, SHADOW_ALPHA)),
                 (pad, pad), device)  # device alpha as the mask
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(shadow, (dx - pad, dy - pad + round(w * SHADOW_OFFSET)), shadow)

    canvas.paste(device, (dx, dy), device)

    out = canvas.convert("RGB")  # flatten — guarantees no alpha
    assert out.size == (w, h), f"{slot_name}: got {out.size}, expected {(w, h)}"
    return out, warnings
