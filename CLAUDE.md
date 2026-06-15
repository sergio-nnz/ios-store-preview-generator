# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This project (`appshot`) generates App Store assets that pass App Store Connect (ASC) review without manual intervention. It currently builds **framed marketing screenshots**: each raw phone capture is composited inside a programmatically drawn device bezel, on a colored/gradient background, with a caption headline above — at exact ASC pixel dimensions, RGB, no alpha. App preview **video** is not implemented yet (its specs live in `specs.json` for a later pass).

## Commands

```bash
# one-time setup
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# render: reads config/screenshots.json + raw captures, writes assets/out/<slot>/
.venv/bin/python -m appshot.render                      # default config
.venv/bin/python -m appshot.render path/to/config.json  # alternate config

# validate every rendered asset against specs.json (exits non-zero on any FAIL)
.venv/bin/python -m appshot.validate assets/out
```

Raw captures go in `assets/raw/<family>/` (e.g. `assets/raw/iphone/`) and must be native-resolution screenshots for that device family — iPhone captures cannot fill iPad slots. Currently only **lead slots** are rendered: iPhone 6.9" (1320×2868) and iPad 13" (2064×2752); Apple scales these down to cover smaller devices.

There is **no automated test suite**. Both CLIs are the way to exercise the code: each exposes a `main(argv)` that returns a process exit code (`0`/`1`), so they double as testable entry points and drop into CI. `render` is fault-tolerant — a missing/unreadable capture prints `FAIL …` to stderr and is skipped, but the batch continues and the process still exits non-zero if any shot failed. `validate` exits non-zero on the first `FAIL` across all files.

## Code layout

- `specs.json` — the spec data (see below).
- `appshot/specs.py` — the **only** module that reads dimensions/rules from `specs.json`; everything else imports from here.
- `appshot/frame.py` — `draw_device()` draws the rounded-rect bezel (+ iPhone Dynamic Island) and insets the capture (cover-scaled, center-cropped, with an aspect-mismatch warning).
- `appshot/compose.py` — `render_shot()` builds the full canvas (background → caption → framed device), flattens to RGB, and asserts exact slot size.
- `appshot/render.py` — CLI; maps config families to lead slots and writes numbered PNGs.
- `appshot/validate.py` — CLI; PIL checks per file. Infers the target slot from the parent directory name (`assets/out/<slot>/…`).

## Specs are the single source of truth

`specs.json` is the machine-readable source of truth for all dimensions and frame rates. **Never hardcode a pixel dimension, resolution, or fps value in a render script.** Always read from `specs.json`. If a value in `specs.json` disagrees with `.claude/skills/appstore-specs/SKILL.md`, that is a bug to reconcile.

## Asset output

Rendered assets go to `assets/out/`. The `spec-validator` agent checks every file in that directory before any upload.

## Critical correctness constraints

These silently fail ASC review and are the most important things to get right:

- **Exact pixel dimensions** — no off-by-one tolerance; assert `size == target` after every render.
- **No alpha channel** — all PNGs must be flattened to RGB. RGBA canvases and transparent PNGs are rejected. Check `img.mode == "RGB"` and `"transparency" not in img.info`.
- **Video**: H.264 High profile, constant 30 fps (`r_frame_rate` and `avg_frame_rate` both `"30/1"`, not VFR), AAC stereo audio track present even when silent, `faststart` flag set, duration 15–30 s.

## Agents

- **`code-reviewer`** — reviews render and pipeline code for ASC compliance bugs. Run proactively after editing render scripts or agent definitions. Reports Critical / Warning / Suggestion with file and line; does not edit files.
- **`spec-validator`** — validates every file in `assets/out/` against `specs.json`. Uses PIL for images and `ffprobe` for video. A single FAIL blocks the batch. Run after every render, before upload.

## Toolchain

PIL/Pillow handles image rendering and validation. `ffprobe` (part of ffmpeg) handles video stream inspection — present but unused until the video-preview pass. Caption fonts: `config/screenshots.json` may point `font` at a TTF in `assets/fonts/`; `compose.py` falls back to a system font (`FALLBACK_FONTS`) so the pipeline renders sized captions out of the box.
