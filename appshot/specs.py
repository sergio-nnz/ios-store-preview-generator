"""Single source of truth for App Store asset specs.

Every dimension and format rule comes from ``specs.json`` through this module.
No other script may hardcode a pixel value or fps literal (see code-reviewer).
"""
import json
import functools
from pathlib import Path

SPECS_PATH = Path(__file__).resolve().parent.parent / "specs.json"


@functools.lru_cache(maxsize=1)
def load_specs():
    """Parse and cache specs.json."""
    with open(SPECS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def screenshot_slots():
    """All screenshot slots: {name: {w, h, family, lead?}}."""
    return load_specs()["screenshots"]["slots"]


def lead_slots():
    """Only the lead slots (one per device family) we actually render."""
    return {name: s for name, s in screenshot_slots().items() if s.get("lead")}


def lead_slot_for(family):
    """The lead slot name for a device family, e.g. 'iphone' -> 'iphone-6.9'."""
    for name, s in lead_slots().items():
        if s["family"] == family:
            return name
    raise KeyError(f"no lead slot for family {family!r}")


def slot_size(name):
    """Exact (width, height) in pixels for a slot."""
    s = screenshot_slots()[name]
    return (s["w"], s["h"])


def screenshot_rules():
    """Format / color / alpha / size-limit rules for screenshots."""
    rules = load_specs()["screenshots"]
    return {
        "formats": rules["formats"],
        "color_mode": rules["color_mode"],
        "alpha_allowed": rules["alpha_allowed"],
        "max_file_bytes": rules["max_file_bytes"],
    }
