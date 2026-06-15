"""Programmatic device bezel — no external mockup artwork required.

Draws a rounded-rect device frame and insets the scaled capture into the
rounded screen area, so the pipeline is fully self-contained.
"""
from PIL import Image, ImageDraw

# Per-family frame geometry, expressed as fractions of the screen rect so it
# scales with whatever screen size the caller requests.
FRAME = {
    "iphone": {
        "bezel": 0.030,        # frame thickness as fraction of screen width
        "screen_radius": 0.090,  # inner (screen) corner radius / screen width
        "island": True,        # draw a Dynamic-Island pill
    },
    "ipad": {
        "bezel": 0.022,
        "screen_radius": 0.030,
        "island": False,
    },
}

BEZEL_COLOR = (20, 20, 22, 255)
# Capture aspect may differ from the target screen aspect by at most this much
# before we warn (and center-crop) instead of silently distorting.
ASPECT_TOLERANCE = 0.04


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                           radius=radius, fill=255)
    return mask


def _cover(capture, target):
    """Scale capture to cover ``target`` (w, h), center-cropped. Returns
    (cropped_image, aspect_warning_or_None)."""
    tw, th = target
    cw, ch = capture.size
    warning = None
    target_aspect, cap_aspect = tw / th, cw / ch
    if abs(cap_aspect - target_aspect) / target_aspect > ASPECT_TOLERANCE:
        warning = (f"capture aspect {cap_aspect:.3f} differs from screen aspect "
                   f"{target_aspect:.3f}; center-cropping (supply a native "
                   f"capture for this device to avoid cropping)")
    scale = max(tw / cw, th / ch)
    resized = capture.resize((max(1, round(cw * scale)), max(1, round(ch * scale))),
                             Image.LANCZOS)
    rw, rh = resized.size
    left, top = (rw - tw) // 2, (rh - th) // 2
    return resized.crop((left, top, left + tw, top + th)), warning


def draw_device(capture, family, screen_px):
    """Return (RGBA framed-device image, [warnings]).

    ``screen_px`` is the (w, h) of the screen area; the returned image is
    larger by the bezel on every side.
    """
    if family not in FRAME:
        raise KeyError(f"unknown device family {family!r}")
    cfg = FRAME[family]
    sw, sh = screen_px
    bezel = max(1, round(sw * cfg["bezel"]))
    screen_radius = round(sw * cfg["screen_radius"])

    capture = capture.convert("RGB")
    screen_img, warning = _cover(capture, (sw, sh))
    warnings = [warning] if warning else []

    # Round the screen corners.
    screen_rgba = screen_img.convert("RGBA")
    screen_rgba.putalpha(_rounded_mask((sw, sh), screen_radius))

    # Device body: rounded rect slightly larger radius than the screen.
    dev_w, dev_h = sw + 2 * bezel, sh + 2 * bezel
    body = Image.new("RGBA", (dev_w, dev_h), (0, 0, 0, 0))
    body_radius = screen_radius + bezel
    body_mask = _rounded_mask((dev_w, dev_h), body_radius)
    ImageDraw.Draw(body).rounded_rectangle(
        [0, 0, dev_w - 1, dev_h - 1], radius=body_radius, fill=BEZEL_COLOR)
    body.putalpha(body_mask)

    body.paste(screen_rgba, (bezel, bezel), screen_rgba)

    if cfg["island"]:
        island_w, island_h = round(sw * 0.30), round(sw * 0.085)
        ix = bezel + (sw - island_w) // 2
        iy = bezel + round(sh * 0.018)
        ImageDraw.Draw(body).rounded_rectangle(
            [ix, iy, ix + island_w, iy + island_h],
            radius=island_h // 2, fill=(0, 0, 0, 255))

    return body, warnings
