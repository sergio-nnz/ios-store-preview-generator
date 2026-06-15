---
name: appstore-specs
description: Authoritative, current Apple App Store screenshot and app preview specifications, including exact pixel dimensions, format constraints, and the rules that cause App Store Connect rejection. Use this whenever planning, rendering, or validating any App Store screenshot or preview asset, deciding output dimensions or formats, or checking whether an asset will pass App Store Connect review. Always defer to this file over training-data recollection of Apple specs, which goes stale with each new device generation.
---

# App Store asset specs

This is the single authoritative source for App Store screenshot and preview specs in this project. `specs.json` holds the machine-readable subset; this file holds the full reference and the rejection rules. If any value here disagrees with `specs.json`, treat that as a bug to reconcile, not a judgment call.

Spec snapshot verified: June 2026. Re-verify against App Store Connect when a new iPhone or iPad flagship ships, then update this file and `specs.json` together.

## Screenshots

Apple scales down from the largest size you upload per device family, so producing the lead size for each family your app supports is the minimum viable set.

| Slot | Portrait (px) | Status |
| :-- | :-- | :-- |
| iPhone 6.9" (17/16 Pro Max) | 1320 x 2868 | Lead — covers all smaller iPhones via scaling |
| iPhone 6.7" (Plus models) | 1290 x 2796 | Accepted alternative |
| iPhone 6.5" (XS Max, 11 Pro Max) | 1242 x 2688 | Legacy |
| iPad 13" (Pro M4) | 2064 x 2752 | Lead iPad size |
| iPad 12.9" (older Pro) | 2048 x 2732 | Legacy |
| iPad 11" | 1668 x 2388 | Optional |

Landscape is the dimensions transposed (e.g. 2868 x 1320). Landscape is typical only for games.

Rules:
- Format PNG or JPEG. No HEIC, no GIF.
- RGB color space, no alpha channel. Transparency is rejected.
- Exact pixel dimensions. There is no off-by-one tolerance; 1320 x 2867 fails.
- 72 DPI minimum. Max 500 MB per file (optimized exports are a few MB in practice).
- 1 to 10 per device class per locale. Most apps do best with 4 to 8.
- Each screenshot must contain real app UI inside the frame. App Store Connect AI-scans for marketing-only / text-only frames and rejects them.
- iPad screenshots are required separately if the app supports iPad; iPhone screenshots cannot satisfy the iPad slots.

## App previews (video)

Preview resolutions are NOT the same as screenshot sizes — Apple uses standardized lower resolutions for video.

| Slot | Portrait (px) | Landscape (px) |
| :-- | :-- | :-- |
| iPhone 6.9" / 6.5" | 886 x 1920 (1080 x 1920 also accepted) | 1920 x 886 |
| iPad 13" / 12.9" | 1200 x 1600 | 1600 x 1200 |

Rules:
- Duration 15 to 30 seconds. Outside that range is a hard rejection. Aim for 20 to 29 seconds.
- Video codec H.264 High profile (up to Level 4.0). Apple ProRes 422 HQ is also accepted but huge. Avoid HEVC — acceptance is inconsistent and it is the most common silent rejection.
- Constant 30 fps. Variable frame rate is rejected. Pixel format yuv420p.
- An audio track must be present even if the video is silent. Use AAC stereo, 256 kbps or higher, 44.1 or 48 kHz. Mono, surround, or a missing audio stream are all rejected.
- Container MOV, MP4, or M4V. Set the faststart flag (moov atom moved to the front).
- Max 500 MB per preview. Up to 3 previews per localization.
- Must be real in-app footage. Apple rejects staged/promotional clips and any content shown from outside the app (Settings, the home screen, etc.).

## Validation checklist

These map one-to-one to what spec-validator checks. Every check is exact; any mismatch is a FAIL that blocks the batch.

Screenshots (PIL):
- `img.size == (slot.w, slot.h)` exactly.
- `img.mode == "RGB"` (not RGBA / LA / P).
- No alpha: `"transparency" not in img.info`.
- `img.format in ("PNG", "JPEG")`.
- File size <= 500 MB.

Previews (ffprobe):
- Video stream: `codec_name == "h264"`, `profile == "High"`.
- `width == slot.w` and `height == slot.h` exactly.
- Constant 30 fps: both `r_frame_rate` and `avg_frame_rate` == `"30/1"`.
- `pix_fmt == "yuv420p"`.
- `15.0 <= duration <= 30.0`.
- An audio stream exists with `codec_name == "aac"`, `channels == 2`, `sample_rate in ("44100", "48000")`.
- `format.size <= 500 MB`.
