# appshot

Generate **App Store Connect–compliant marketing screenshots** from raw phone captures.

Each raw screenshot is composited inside a programmatically drawn device bezel, on a
colored or gradient background, with a caption headline above it — and saved at the
exact pixel dimensions Apple requires, in RGB with no alpha channel. A validator checks
every output against the spec before you upload.

> App preview **videos** are not generated yet. Their specs already live in `specs.json`
> for a later pass.

---

## Requirements

- Python 3.9+
- [Pillow](https://python-pillow.org/) (installed below)
- ffmpeg/ffprobe — only needed for the future video pass, not for screenshots

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Quick start

The repo ships with placeholder captures and a sample config so you can see it work
immediately:

```bash
.venv/bin/python -m appshot.render            # writes assets/out/iphone-6.9/*.png
.venv/bin/python -m appshot.validate assets/out
```

You should see two `OK` lines from the render and two `PASS` lines from the validator.

## Using it with your own screenshots

1. **Drop your captures** into `assets/raw/<family>/`, where `<family>` is `iphone` or
   `ipad`. Use native-resolution screenshots for that device — iPhone captures cannot
   fill iPad slots, and an aspect mismatch is center-cropped (with a warning).

   ```
   assets/raw/iphone/01-home.png
   assets/raw/iphone/02-detail.png
   assets/raw/ipad/01-home.png
   ```

2. **Edit `config/screenshots.json`** to list the shots and their captions:

   ```json
   {
     "iphone": {
       "background": ["#0A84FF", "#0040A0"],
       "caption_color": "#FFFFFF",
       "font": "assets/fonts/Headline.ttf",
       "shots": [
         {"raw": "01-home.png",   "caption": "Everything in one place"},
         {"raw": "02-detail.png", "caption": "The details that matter"}
       ]
     },
     "ipad": {
       "background": ["#0A84FF", "#0040A0"],
       "caption_color": "#FFFFFF",
       "font": "assets/fonts/Headline.ttf",
       "shots": []
     }
   }
   ```

   | Field | Meaning |
   | :-- | :-- |
   | `background` | A single hex string for a solid color, or `["#top", "#bottom"]` for a vertical gradient. |
   | `caption_color` | Hex color of the caption text. Defaults to `#FFFFFF`. |
   | `font` | Path (relative to the repo root) to a `.ttf`/`.ttc` caption font. Drop one in `assets/fonts/`. If missing, a system font is used automatically. |
   | `shots` | Ordered list; `raw` is the filename inside `assets/raw/<family>/`, `caption` is the headline. Output files are numbered in this order (`01-…`, `02-…`), which is the order they appear on the App Store. |

3. **Render**, then **validate**:

   ```bash
   .venv/bin/python -m appshot.render
   .venv/bin/python -m appshot.validate assets/out
   ```

   Output lands in `assets/out/<slot>/NN-<name>.png` (e.g. `assets/out/iphone-6.9/01-home.png`).
   Upload these to App Store Connect once validation passes.

### Using an alternate config

```bash
.venv/bin/python -m appshot.render path/to/other-config.json
```

## What gets produced

Only the **lead device sizes** are rendered, since Apple scales these down to cover every
smaller device in the same family:

| Family | Slot | Dimensions |
| :-- | :-- | :-- |
| iPhone | `iphone-6.9` | 1320 × 2868 |
| iPad | `ipad-13` | 2064 × 2752 |

## Validation

`appshot.validate` checks every PNG/JPEG under a directory against `specs.json`:

- exact pixel dimensions for its slot (inferred from the parent directory name),
- RGB mode with no alpha / transparency,
- an allowed format (PNG or JPEG),
- file size under Apple's limit.

It prints `PASS`/`FAIL` per file and exits non-zero if anything fails, so it drops into a
CI step. Always run it before uploading.

## Specs are the source of truth

All dimensions and format rules come from [`specs.json`](specs.json); no dimension is
hardcoded in the render code. The full human-readable Apple reference (and the rules that
cause silent App Store Connect rejection) lives in
[`.claude/skills/appstore-specs/SKILL.md`](.claude/skills/appstore-specs/SKILL.md). If a
value in `specs.json` ever disagrees with that file, treat it as a bug to reconcile, not a
judgment call.

## Project layout

```
specs.json                 spec data (dimensions, format rules)
config/screenshots.json    your shots, captions, backgrounds, fonts
assets/raw/<family>/        input captures you provide
assets/fonts/               optional caption fonts
assets/out/<slot>/          generated, validated screenshots
appshot/
  specs.py                 the only reader of specs.json
  frame.py                 draws the device bezel and insets the capture
  compose.py               background + caption + framed device → RGB canvas
  render.py                CLI: config → numbered PNGs
  validate.py              CLI: checks output against specs.json
```
