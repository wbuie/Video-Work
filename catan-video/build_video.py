#!/usr/bin/env python3
"""
High Hamptons Catan Tradition — Dramatic 40s cinematic video
No narration. Ken Burns + fly-through animation. Bold text overlays.

Usage:
  python3 build_video.py

Drop your images into ./images/ before running.
Output: ./out/catan_tradition.mp4
"""

import os, sys, math, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
W, H = 1920, 1080
FPS  = 30
OUT  = "out/catan_tradition.mp4"

FONT_TITLE  = "fonts/Cinzel.ttf"
FONT_FALLBK = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"

IMAGES_DIR = "images"

# ── Scene plan ────────────────────────────────────────────────────────────────
# Each scene: (image_index_or_slug, duration_s, zoom_start, zoom_end, pan, overlay)
# pan = (dx_frac, dy_frac) total pan as fraction of image size (Ken Burns)
# overlay = None | {"lines": [...], "pos": "top"|"bottom"|"center", "delay": s}

SCENES = [
    # 0-4s: Fade in on full board — establishing
    {
        "slug": "full_board",
        "dur": 4.0,
        "zoom": (1.0, 1.15),
        "pan":  (0.0, -0.04),
        "overlay": None,
    },
    # 4-8s: Title card — HIGH HAMPTONS CATAN
    {
        "slug": "full_board",
        "dur": 4.0,
        "zoom": (1.15, 1.25),
        "pan":  (0.02, 0.0),
        "overlay": {
            "lines": ["HIGH HAMPTONS", "CATAN TRADITION"],
            "sizes": [110, 52],
            "pos": "center",
            "delay": 0.4,
        },
    },
    # 8-13s: Ocean/port sweep — blue water intro
    {
        "slug": "ocean",
        "dur": 5.0,
        "zoom": (1.2, 1.05),
        "pan":  (-0.06, 0.0),
        "overlay": {
            "lines": ["THE ISLAND AWAITS"],
            "sizes": [60],
            "pos": "bottom",
            "delay": 1.0,
        },
    },
    # 13-18s: Forest tile close-up
    {
        "slug": "forest",
        "dur": 5.0,
        "zoom": (1.1, 1.3),
        "pan":  (0.0, -0.06),
        "overlay": {
            "lines": ["ANCIENT FORESTS", "LUMBER FOR THE BRAVE"],
            "sizes": [68, 36],
            "pos": "top",
            "delay": 0.8,
        },
    },
    # 18-23s: Mountain/ore tile
    {
        "slug": "mountain",
        "dur": 5.0,
        "zoom": (1.2, 1.05),
        "pan":  (0.04, 0.02),
        "overlay": {
            "lines": ["ORE FROM THE DEEP", "MOUNTAINS NEVER YIELD"],
            "sizes": [68, 36],
            "pos": "bottom",
            "delay": 0.8,
        },
    },
    # 23-27s: Grain/wheat tile
    {
        "slug": "grain",
        "dur": 4.0,
        "zoom": (1.05, 1.2),
        "pan":  (-0.03, 0.0),
        "overlay": {
            "lines": ["GOLDEN WHEAT FIELDS"],
            "sizes": [68],
            "pos": "top",
            "delay": 0.6,
        },
    },
    # 27-32s: Pasture tile with sheep
    {
        "slug": "pasture",
        "dur": 5.0,
        "zoom": (1.15, 1.0),
        "pan":  (0.0, 0.05),
        "overlay": {
            "lines": ["ROLLING PASTURES", "WHERE WOOL IS SPUN TO GOLD"],
            "sizes": [68, 36],
            "pos": "bottom",
            "delay": 0.8,
        },
    },
    # 32-37s: Wide board overhead — pull back
    {
        "slug": "wide",
        "dur": 5.0,
        "zoom": (1.3, 1.0),
        "pan":  (0.0, 0.0),
        "overlay": None,
    },
    # 37-42s: Final card
    {
        "slug": "wide",
        "dur": 5.0,
        "zoom": (1.0, 1.05),
        "pan":  (0.0, 0.0),
        "overlay": {
            "lines": ["EVERY PIECE, HAND PRINTED", "EVERY GAME, A LEGEND", "", "HIGH HAMPTONS · SINCE 2023"],
            "sizes": [58, 58, 10, 32],
            "pos": "center",
            "delay": 0.5,
        },
    },
]

# Image slot assignments — filenames to look for (partial match, case-insensitive)
SLUG_HINTS = {
    "full_board": ["board", "full", "overhead", "wide", "overview"],
    "ocean":      ["ocean", "sea", "blue", "water", "port"],
    "forest":     ["forest", "tree", "wood", "lumber"],
    "mountain":   ["mountain", "ore", "rock", "stone", "gray", "grey", "black"],
    "grain":      ["grain", "wheat", "yellow", "gold", "field"],
    "pasture":    ["pasture", "sheep", "wool", "green"],
    "wide":       ["wide", "full", "board", "overhead"],
}


def load_images():
    """Load all images from images/ dir, return dict slug->PIL.Image."""
    files = sorted(glob.glob(os.path.join(IMAGES_DIR, "*")))
    files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if not files:
        print(f"ERROR: No images found in {IMAGES_DIR}/")
        print("Please drop your photos into the images/ folder and re-run.")
        sys.exit(1)

    print(f"Found {len(files)} images: {[os.path.basename(f) for f in files]}")

    # Try slug matching first
    slug_map = {}
    for slug, hints in SLUG_HINTS.items():
        for f in files:
            name = os.path.basename(f).lower()
            if any(h in name for h in hints):
                slug_map[slug] = f
                break

    # Fallback: assign sequentially to unmatched slugs
    used = set(slug_map.values())
    remaining = [f for f in files if f not in used]
    unmatched_slugs = [s for s in SLUG_HINTS if s not in slug_map]
    for slug, f in zip(unmatched_slugs, remaining):
        slug_map[slug] = f

    # Any still missing: use the first available image
    for slug in SLUG_HINTS:
        if slug not in slug_map:
            slug_map[slug] = files[0]

    print("\nSlug assignments:")
    for slug, f in slug_map.items():
        print(f"  {slug:12s} → {os.path.basename(f)}")

    loaded = {}
    for slug, f in slug_map.items():
        img = Image.open(f).convert("RGB")
        loaded[slug] = img
    return loaded


def cover_crop(img, target_w, target_h, zoom=1.0, pan=(0.0, 0.0)):
    """Zoom+pan then cover-crop to target dimensions."""
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih) * zoom
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    # Pan offset (pan values are fractions of resized dimensions)
    cx = nw // 2 + int(pan[0] * nw)
    cy = nh // 2 + int(pan[1] * nh)

    left  = max(0, cx - target_w // 2)
    top   = max(0, cy - target_h // 2)
    left  = min(left, nw - target_w)
    top   = min(top, nh - target_h)

    return resized.crop((left, top, left + target_w, top + target_h))


def add_vignette(img):
    """Cinematic darkened edges."""
    w, h = img.size
    vign = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(vign)
    steps = 60
    for i in range(steps):
        t = i / steps
        alpha = int(180 * (1 - t) ** 2.2)
        pad = int(t * min(w, h) * 0.5)
        draw.ellipse([pad, pad, w - pad, h - pad], fill=alpha)
    vign_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vign_rgba.putalpha(ImageEnhance.Brightness(vign).enhance(0.8))
    base = img.convert("RGBA")
    # Dark overlay at edges
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    mdraw = ImageDraw.Draw(mask)
    for i in range(40):
        alpha = int(160 * (1 - i / 40) ** 1.8)
        p = i * 4
        mdraw.rectangle([p, p, w - p, h - p], outline=0, fill=0)
    # Simple vignette via radial gradient numpy
    arr = np.array(img).astype(float)
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    xg, yg = np.meshgrid(x, y)
    vg = 1 - np.clip(xg**2 + yg**2, 0, 1) ** 0.6
    vg = np.stack([vg] * 3, axis=-1)
    arr = np.clip(arr * vg, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def add_letterbox(img, bar_h=60):
    """Add cinematic black bars top and bottom."""
    arr = np.array(img)
    arr[:bar_h, :] = 0
    arr[-bar_h:, :] = 0
    return Image.fromarray(arr)


def color_grade(img):
    """Warm dramatic grade: slight desaturation + warm highlights + contrast."""
    from PIL import ImageOps
    arr = np.array(img).astype(float)
    # Slight contrast S-curve
    arr = np.clip((arr / 255.0) ** 0.9 * 255, 0, 255)
    # Warm tint: boost R slightly, reduce B slightly
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.05, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.93, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def get_font(size):
    try:
        return ImageFont.truetype(FONT_TITLE, size)
    except Exception:
        return ImageFont.truetype(FONT_FALLBK, size)


def draw_text_overlay(img, lines, sizes, pos, alpha_t):
    """Draw dramatic text with drop shadow + letter-spacing feel."""
    overlay = img.copy().convert("RGBA")
    txt_layer = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    bar_h = 60  # letterbox height
    usable_h = H - bar_h * 2
    total_text_h = sum(s + 12 for s in sizes)

    if pos == "center":
        base_y = bar_h + (usable_h - total_text_h) // 2
    elif pos == "top":
        base_y = bar_h + 50
    else:  # bottom
        base_y = H - bar_h - total_text_h - 50

    y = base_y
    for line, size in zip(lines, sizes):
        if not line:
            y += size + 12
            continue
        font = get_font(size)
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2

        a = int(255 * min(1.0, alpha_t * 2))

        # Shadow
        shadow_off = max(2, size // 20)
        draw.text((x + shadow_off, y + shadow_off), line, font=font,
                  fill=(0, 0, 0, int(a * 0.7)))
        # Main text — cream/gold color
        draw.text((x, y), line, font=font, fill=(255, 245, 210, a))

        y += size + 12

    # Blend
    result = Image.alpha_composite(overlay, txt_layer).convert("RGB")
    return result


def generate_frames(scenes, images):
    """Yield PIL frames for the full video."""
    total_frames = sum(int(s["dur"] * FPS) for s in scenes)
    print(f"\nGenerating {total_frames} frames at {FPS}fps…")

    global_frame = 0
    prev_last_frame = None

    for si, scene in enumerate(scenes):
        slug     = scene["slug"]
        dur      = scene["dur"]
        z_start  = scene["zoom"][0]
        z_end    = scene["zoom"][1]
        pan      = scene["pan"]
        overlay  = scene["overlay"]
        n_frames = int(dur * FPS)
        img      = images[slug]

        for fi in range(n_frames):
            t = fi / max(n_frames - 1, 1)
            te = ease_in_out(t)

            zoom = lerp(z_start, z_end, te)
            pan_x = lerp(0, pan[0], te)
            pan_y = lerp(0, pan[1], te)

            frame = cover_crop(img, W, H, zoom, (pan_x, pan_y))
            frame = color_grade(frame)
            frame = add_vignette(frame)
            frame = add_letterbox(frame)

            # Cross-dissolve: first 12 frames from prev scene
            if si > 0 and fi < 12 and prev_last_frame is not None:
                blend = fi / 12.0
                frame_arr = np.array(frame).astype(float)
                prev_arr  = np.array(prev_last_frame).astype(float)
                blended   = (prev_arr * (1 - blend) + frame_arr * blend).astype(np.uint8)
                frame     = Image.fromarray(blended)

            # Fade in from black at very start
            if global_frame < 20:
                fade = global_frame / 20.0
                arr = (np.array(frame) * fade).astype(np.uint8)
                frame = Image.fromarray(arr)

            # Fade to black at very end
            total_so_far = sum(int(scenes[i]["dur"] * FPS) for i in range(si))
            remaining_total = total_frames - (total_so_far + fi)
            if remaining_total < 25:
                fade = remaining_total / 25.0
                arr = (np.array(frame) * fade).astype(np.uint8)
                frame = Image.fromarray(arr)

            # Text overlay
            if overlay:
                delay_frames = int(overlay.get("delay", 0) * FPS)
                if fi >= delay_frames:
                    text_t = (fi - delay_frames) / max(FPS * 0.8, 1)
                    # fade out near end of scene
                    end_fade = max(0, (n_frames - fi) / (FPS * 0.5))
                    alpha_t = min(text_t, end_fade, 1.0)
                    frame = draw_text_overlay(
                        frame,
                        overlay["lines"],
                        overlay["sizes"],
                        overlay["pos"],
                        alpha_t,
                    )

            yield frame
            prev_last_frame = frame
            global_frame += 1

            if fi % (FPS * 2) == 0:
                pct = global_frame / total_frames * 100
                print(f"\r  {pct:.0f}%  scene {si+1}/{len(scenes)}", end="", flush=True)

    print("\nDone generating frames.")


def render_video(frames_gen, total_frames, out_path):
    """Write frames to MP4 using imageio-ffmpeg."""
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    import subprocess

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-vcodec", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for frame in frames_gen:
        proc.stdin.write(np.array(frame).tobytes())

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        print(proc.stderr.read().decode())
        raise RuntimeError("ffmpeg failed")

    print(f"\n✓ Rendered: {out_path}")
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"  Size: {size_mb:.1f} MB")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    images = load_images()
    total_frames = sum(int(s["dur"] * FPS) for s in SCENES)
    total_dur = sum(s["dur"] for s in SCENES)
    print(f"\nVideo plan: {total_dur:.0f}s, {total_frames} frames")

    frames = generate_frames(SCENES, images)
    render_video(frames, total_frames, OUT)


if __name__ == "__main__":
    main()
