"""CLI: render configured raw captures into compliant marketing screenshots.

    python -m appshot.render [config/screenshots.json]

Reads device families from the config, maps each to its lead slot (from
specs.json), and writes numbered PNGs to assets/out/<slot>/.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from . import specs
from .compose import render_shot

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "screenshots.json"


def _out_name(index, raw_name):
    stem = re.sub(r"^\d+[-_]", "", Path(raw_name).stem)
    return f"{index:02d}-{stem}.png"


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    config_path = Path(argv[0]) if argv else DEFAULT_CONFIG
    with open(config_path, encoding="utf-8") as fh:
        config = json.load(fh)

    rendered, failures = 0, 0
    for family, fam_cfg in config.items():
        shots = fam_cfg.get("shots", [])
        if not shots:
            continue
        slot_name = specs.lead_slot_for(family)
        raw_dir = ROOT / "assets" / "raw" / family
        out_dir = ROOT / "assets" / "out" / slot_name
        out_dir.mkdir(parents=True, exist_ok=True)
        background = fam_cfg["background"]
        font_path = fam_cfg.get("font")
        if font_path:
            font_path = str(ROOT / font_path)
        caption_color = fam_cfg.get("caption_color", "#FFFFFF")

        for i, shot in enumerate(shots, start=1):
            raw_path = raw_dir / shot["raw"]
            if not raw_path.is_file():
                print(f"FAIL {family}: missing raw capture {raw_path}", file=sys.stderr)
                failures += 1
                continue
            out_path = out_dir / _out_name(i, shot["raw"])
            try:
                with Image.open(raw_path) as capture:
                    capture.load()
                    img, warnings = render_shot(
                        slot_name, capture, shot.get("caption", ""),
                        background, font_path, caption_color)
                img.save(out_path, "PNG")
            except UnidentifiedImageError:
                print(f"FAIL {family}: {raw_path} is not a readable image",
                      file=sys.stderr)
                failures += 1
                continue
            except OSError as exc:
                # truncated/unreadable capture, or a failed write (full disk,
                # read-only path) — report and keep processing remaining shots.
                print(f"FAIL {family}: {raw_path}: {exc}", file=sys.stderr)
                failures += 1
                continue
            for w in warnings:
                print(f"WARN {out_path.name}: {w}", file=sys.stderr)
            print(f"OK   {out_path.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}")
            rendered += 1

    print(f"\nRendered {rendered} screenshot(s); {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
