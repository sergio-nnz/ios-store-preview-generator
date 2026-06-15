"""CLI: validate rendered assets against specs.json (PIL checks).

    python -m appshot.validate [assets/out]

The spec-validator agent can shell out to this. Every image must match its
slot's exact dimensions, be RGB with no alpha, use an allowed format, and stay
under the size limit. The slot is inferred from the parent directory name
(assets/out/<slot>/...). Exits non-zero if any file FAILs.
"""
import sys
from pathlib import Path

from PIL import Image

from . import specs

ROOT = Path(__file__).resolve().parent.parent
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
ALPHA_MODES = {"RGBA", "LA", "PA", "RGBa", "P"}  # P/PA can carry palette transparency


def _check(path, rules, slots):
    slot_name = path.parent.name
    if slot_name not in slots:
        return [f"unknown slot directory {slot_name!r} (cannot determine target size)"]

    failures = []
    expected = (slots[slot_name]["w"], slots[slot_name]["h"])
    with Image.open(path) as img:
        if img.size != expected:
            failures.append(f"size {img.size} != {expected}")
        if img.mode != rules["color_mode"]:
            failures.append(f"mode {img.mode!r} != {rules['color_mode']!r}")
        if not rules["alpha_allowed"] and (
                "transparency" in img.info or img.mode in ALPHA_MODES):
            failures.append(f"alpha/transparency present (mode {img.mode!r})")
        if img.format not in rules["formats"]:
            failures.append(f"format {img.format!r} not in {rules['formats']}")
    if path.stat().st_size > rules["max_file_bytes"]:
        failures.append(f"file size {path.stat().st_size} > {rules['max_file_bytes']}")
    return failures


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]) if argv else ROOT / "assets" / "out"
    rules = specs.screenshot_rules()
    slots = specs.screenshot_slots()

    images = sorted(p for p in root.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        print(f"No images found under {root}", file=sys.stderr)
        return 1

    any_fail = False
    for path in images:
        failures = _check(path, rules, slots)
        rel = path.relative_to(root) if root in path.parents else path
        if failures:
            any_fail = True
            print(f"FAIL {rel}: {'; '.join(failures)}")
        else:
            print(f"PASS {rel}")

    print(f"\n{'FAIL' if any_fail else 'PASS'} — {len(images)} file(s) checked.")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
