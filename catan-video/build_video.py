#!/usr/bin/env python3
"""
High Hamptons Catan Tradition — Dramatic 45s cinematic video
No narration. Ken Burns + procedural hex animation. Bold text overlays.

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

# ── Procedural hex board ──────────────────────────────────────────────────────

# Catan board layout: 19 hexes in rings 0,1,2 from center
CATAN_LAYOUT = [
    # (row_offset, col_offset) in axial coords — hand-tuned for a hex grid
    (0, 0),
    (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1),
    (2, 0), (1, 1), (0, 2), (-1, 2), (-2, 2), (-2, 1),
    (-2, 0), (-1, -1), (0, -2), (1, -2), (2, -2), (2, -1),
]

RESOURCE_DEFS = [
    # (color_rgb, label)
    ((34,  90,  34), "FOREST"),
    ((34,  90,  34), "FOREST"),
    ((34,  90,  34), "FOREST"),
    ((34,  90,  34), "FOREST"),
    ((180, 210,  60), "GRAIN"),
    ((180, 210,  60), "GRAIN"),
    ((180, 210,  60), "GRAIN"),
    ((180, 210,  60), "GRAIN"),
    ((80,  160,  80), "PASTURE"),
    ((80,  160,  80), "PASTURE"),
    ((80,  160,  80), "PASTURE"),
    ((80,  160,  80), "PASTURE"),
    ((140,  70,  30), "BRICK"),
    ((140,  70,  30), "BRICK"),
    ((140,  70,  30), "BRICK"),
    ((90,   90, 110), "ORE"),
    ((90,   90, 110), "ORE"),
    ((90,   90, 110), "ORE"),
    ((210, 190, 120), "DESERT"),
]

def hex_pts(cx, cy, r):
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def draw_single_hex(draw, cx, cy, r, color, label=None, font=None, alpha=1.0):
    pts = hex_pts(cx, cy, r)
    c = tuple(int(v * alpha) for v in color)
    draw.polygon(pts, fill=c)
    border = tuple(int(v * 0.5 * alpha) for v in color)
    draw.polygon(pts, outline=border)
    if label and font and alpha > 0.3:
        txt_a = int(255 * min(1.0, (alpha - 0.3) / 0.7))
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy - th // 2), label, font=font,
                  fill=(255, 245, 210, txt_a))


def axial_to_pixel(q, r, hex_r, cx_off, cy_off):
    x = hex_r * math.sqrt(3) * (q + r / 2)
    y = hex_r * 1.5 * r
    return x + cx_off, y + cy_off


def make_hex_board_frame(fi, n_frames, show_labels=False):
    """Animated procedural hex board: hexes fade in one by one."""
    img = Image.new("RGB", (W, H), (12, 8, 4))
    draw = ImageDraw.Draw(img, "RGBA")

    hex_r = 115
    cx_off, cy_off = W // 2, H // 2 - 20

    try:
        lbl_font = ImageFont.truetype(FONT_TITLE, 18)
    except Exception:
        lbl_font = ImageFont.truetype(FONT_FALLBK, 18)

    t_total = fi / max(n_frames - 1, 1)

    for i, (q, r) in enumerate(CATAN_LAYOUT):
        reveal_start = i / len(CATAN_LAYOUT) * 0.65
        reveal_end   = reveal_start + 0.2
        alpha = max(0.0, min(1.0, (t_total - reveal_start) / max(reveal_end - reveal_start, 0.01)))
        alpha = alpha * alpha * (3 - 2 * alpha)

        px, py = axial_to_pixel(q, r, hex_r, cx_off, cy_off)
        color, label = RESOURCE_DEFS[i]

        lbl = label if show_labels else None
        draw_single_hex(draw, px, py, hex_r - 4, color, lbl, lbl_font, alpha)

    return img


def make_resource_reveal_frame(fi, n_frames):
    """5 resource tiles sweep in with labels — cinematic resource reveal."""
    img = Image.new("RGB", (W, H), (8, 5, 2))
    draw = ImageDraw.Draw(img, "RGBA")

    t = fi / max(n_frames - 1, 1)
    te = t * t * (3 - 2 * t)

    resources = [
        ((34,  90,  34), "FOREST",  "LUMBER"),
        ((140,  70,  30), "BRICK",  "BRICK"),
        ((90,   90, 110), "ORE",    "ORE"),
        ((180, 210,  60), "GRAIN",  "GRAIN"),
        ((80,  160,  80), "PASTURE","WOOL"),
    ]

    n = len(resources)
    card_w = 280
    spacing = 50
    total_w = n * card_w + (n - 1) * spacing
    start_x = (W - total_w) // 2
    cy = H // 2

    try:
        big_font   = ImageFont.truetype(FONT_TITLE, 36)
        small_font = ImageFont.truetype(FONT_TITLE, 20)
    except Exception:
        big_font   = ImageFont.truetype(FONT_FALLBK, 36)
        small_font = ImageFont.truetype(FONT_FALLBK, 20)

    for i, (color, label, resource) in enumerate(resources):
        card_start = i / n * 0.5
        card_t = max(0.0, min(1.0, (t - card_start) / 0.35))
        card_t = card_t * card_t * (3 - 2 * card_t)

        cx = start_x + i * (card_w + spacing) + card_w // 2

        # Slide in from below
        slide_y = cy + int((1 - card_t) * 300)

        # Draw hex
        hex_r = 95
        pts = hex_pts(cx, slide_y, hex_r)
        alpha_i = int(255 * card_t)
        c = color + (alpha_i,)
        draw.polygon(pts, fill=c)
        border = tuple(int(v * 0.5) for v in color) + (alpha_i,)
        draw.polygon(pts, outline=border)

        if card_t > 0.3:
            txt_a = int(255 * min(1.0, (card_t - 0.3) / 0.4))
            # Resource label
            bbox = draw.textbbox((0, 0), resource, font=big_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            sx, sy = cx - tw // 2, slide_y - th // 2 - 8
            draw.text((sx + 2, sy + 2), resource, font=big_font, fill=(0, 0, 0, int(txt_a * 0.6)))
            draw.text((sx, sy), resource, font=big_font, fill=(255, 245, 210, txt_a))

            # Subtitle
            bbox2 = draw.textbbox((0, 0), label, font=small_font)
            tw2 = bbox2[2] - bbox2[0]
            draw.text((cx - tw2 // 2, slide_y + th // 2 + 8), label,
                      font=small_font, fill=(200, 190, 160, int(txt_a * 0.7)))

    # Top banner fades in late
    if t > 0.7:
        banner_a = min(1.0, (t - 0.7) / 0.2)
        try:
            banner_font = ImageFont.truetype(FONT_TITLE, 28)
        except Exception:
            banner_font = ImageFont.truetype(FONT_FALLBK, 28)
        banner = "THE RESOURCES OF CATAN"
        bbox = draw.textbbox((0, 0), banner, font=banner_font)
        bw = bbox[2] - bbox[0]
        ba = int(255 * banner_a)
        draw.text(((W - bw) // 2 + 2, 82), banner, font=banner_font, fill=(0, 0, 0, int(ba * 0.6)))
        draw.text(((W - bw) // 2, 80), banner, font=banner_font, fill=(255, 245, 210, ba))

    return img


def make_outro_hex_frame(fi, n_frames):
    """Procedural hex grid zooming in with gold shimmer for transition."""
    img = Image.new("RGB", (W, H), (10, 6, 2))
    draw = ImageDraw.Draw(img, "RGBA")

    t = fi / max(n_frames - 1, 1)
    te = t * t * (3 - 2 * t)

    # Scale up over time — dramatic zoom in
    base_r = 60 + int(te * 80)
    cx_off = W // 2
    cy_off = H // 2

    # Draw a large tiled hex grid, partially visible
    cols = range(-5, 6)
    rows = range(-5, 6)
    for q in cols:
        for r in rows:
            px, py = axial_to_pixel(q, r, base_r, cx_off, cy_off)
            if px < -base_r or px > W + base_r or py < -base_r or py > H + base_r:
                continue
            dist = math.sqrt((px - cx_off) ** 2 + (py - cy_off) ** 2)
            max_dist = math.sqrt((W / 2) ** 2 + (H / 2) ** 2)
            edge_fade = max(0.0, 1 - (dist / max_dist) ** 0.8)
            shimmer = 0.5 + 0.5 * math.sin(t * math.pi * 4 + (q + r) * 1.2)
            brightness = edge_fade * (0.15 + 0.1 * shimmer)
            gold_color = (
                int(180 * brightness),
                int(140 * brightness),
                int(60 * brightness),
                200
            )
            draw.polygon(hex_pts(px, py, base_r - 3), outline=gold_color)

    return img


# ── Scene plan ────────────────────────────────────────────────────────────────

SCENES = [
    # 0-4s: Fade in — full board overhead establishing shot
    {
        "slug": "full_board",
        "dur": 4.0,
        "zoom": (1.05, 1.2),
        "pan":  (0.0, -0.03),
        "overlay": None,
    },
    # 4-8.5s: Title card over full board
    {
        "slug": "full_board",
        "dur": 4.5,
        "zoom": (1.2, 1.3),
        "pan":  (0.02, 0.0),
        "overlay": {
            "lines": ["HIGH HAMPTONS", "CATAN TRADITION"],
            "sizes": [108, 50],
            "pos": "center",
            "delay": 0.5,
        },
    },
    # 8.5-12.5s: PROCEDURAL — hex board builds itself
    {
        "generator": "hex_board",
        "dur": 4.0,
        "overlay": {
            "lines": ["THE ISLAND OF CATAN"],
            "sizes": [62],
            "pos": "bottom",
            "delay": 1.5,
        },
    },
    # 12.5-17s: Ocean sweep with red ship
    {
        "slug": "ocean",
        "dur": 4.5,
        "zoom": (1.25, 1.05),
        "pan":  (-0.05, 0.0),
        "overlay": {
            "lines": ["THE ISLAND AWAITS"],
            "sizes": [62],
            "pos": "bottom",
            "delay": 1.0,
        },
    },
    # 17-21s: Forest close-up
    {
        "slug": "forest",
        "dur": 4.0,
        "zoom": (1.1, 1.3),
        "pan":  (0.0, -0.05),
        "overlay": {
            "lines": ["ANCIENT FORESTS", "LUMBER FOR THE BRAVE"],
            "sizes": [66, 34],
            "pos": "top",
            "delay": 0.8,
        },
    },
    # 21-25s: Grain field
    {
        "slug": "grain",
        "dur": 4.0,
        "zoom": (1.05, 1.22),
        "pan":  (-0.03, 0.02),
        "overlay": {
            "lines": ["GOLDEN WHEAT FIELDS"],
            "sizes": [66],
            "pos": "top",
            "delay": 0.6,
        },
    },
    # 25-30s: PROCEDURAL — resource reveal cards
    {
        "generator": "resource_reveal",
        "dur": 5.0,
        "overlay": None,
    },
    # 30-34s: Mountain/ore
    {
        "slug": "mountain",
        "dur": 4.0,
        "zoom": (1.2, 1.05),
        "pan":  (0.04, 0.02),
        "overlay": {
            "lines": ["ORE FROM THE DEEP"],
            "sizes": [66],
            "pos": "bottom",
            "delay": 0.8,
        },
    },
    # 34-38s: Stone/brick ruins — "BRICK & ORE"
    {
        "slug": "stone",
        "dur": 4.0,
        "zoom": (1.1, 1.28),
        "pan":  (0.03, -0.03),
        "overlay": {
            "lines": ["BRICK & ORE"],
            "sizes": [80],
            "pos": "center",
            "delay": 0.7,
        },
    },
    # 38-41s: PROCEDURAL — gold hex grid zoom for transition
    {
        "generator": "outro_hex",
        "dur": 3.0,
        "overlay": None,
    },
    # 41-45.5s: Wide overhead — pull back dramatically
    {
        "slug": "wide",
        "dur": 4.5,
        "zoom": (1.35, 1.0),
        "pan":  (0.0, 0.0),
        "overlay": None,
    },
    # 45.5-51.5s: Final outro — low dramatic angle with title
    {
        "slug": "outro",
        "dur": 6.0,
        "zoom": (1.0, 1.1),
        "pan":  (0.0, -0.03),
        "overlay": {
            "lines": ["EVERY PIECE, HAND PRINTED", "EVERY GAME, A LEGEND", "", "HIGH HAMPTONS  ·  EST. 2025"],
            "sizes": [56, 56, 8, 30],
            "pos": "center",
            "delay": 0.8,
        },
    },
]

# Image slot assignments — filenames to look for (partial match, case-insensitive)
# Explicit file assignments (overrides hint-matching)
SLUG_FILES = {
    "full_board": "IMG_3108.jpeg",  # full overhead board
    "ocean":      "IMG_3114.jpeg",  # red ship on ocean
    "forest":     "IMG_3115.jpeg",  # forest tiles close-up
    "grain":      "IMG_3116.jpeg",  # grain hex with wagon
    "mountain":   "IMG_3109.jpeg",  # dark ore/mountain tile
    "pasture":    "IMG_3110.jpeg",  # teal pasture with barn
    "desert":     "IMG_3111.jpeg",  # white desert tile
    "stone":      "IMG_3112.jpeg",  # red stone ruins tile
    "wide":       "IMG_3117.jpeg",  # second overhead wide
    "outro":      "IMG_3118.jpeg",  # low dramatic angle
}

SLUG_HINTS = {
    "full_board": ["board", "full", "overhead", "wide", "overview"],
    "ocean":      ["ocean", "sea", "blue", "water", "port"],
    "forest":     ["forest", "tree", "wood", "lumber"],
    "mountain":   ["mountain", "ore", "rock", "stone", "gray", "grey", "black"],
    "grain":      ["grain", "wheat", "yellow", "gold", "field"],
    "pasture":    ["pasture", "sheep", "wool", "green"],
    "wide":       ["wide", "full", "board", "overhead"],
    "desert":     ["desert", "sand", "white"],
    "stone":      ["stone", "red", "ruins"],
    "outro":      ["outro", "final"],
}


def load_images():
    """Load all images from images/ dir, return dict slug->PIL.Image."""
    files = sorted(glob.glob(os.path.join(IMAGES_DIR, "*")))
    files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if not files:
        print(f"ERROR: No images found in {IMAGES_DIR}/")
        sys.exit(1)

    print(f"Found {len(files)} images")

    # Build name->path lookup
    name_map = {os.path.basename(f): f for f in files}

    slug_map = {}
    # Use explicit assignments first
    for slug, fname in SLUG_FILES.items():
        if fname in name_map:
            slug_map[slug] = name_map[fname]
        else:
            print(f"WARNING: {fname} not found for slug '{slug}'")

    # Hint-based fallback for anything still missing
    for slug, hints in SLUG_HINTS.items():
        if slug not in slug_map:
            for f in files:
                name = os.path.basename(f).lower()
                if any(h in name for h in hints):
                    slug_map[slug] = f
                    break

    # Final fallback
    for slug in list(SLUG_FILES.keys()) + list(SLUG_HINTS.keys()):
        if slug not in slug_map:
            slug_map[slug] = files[0]

    print("\nSlug assignments:")
    for slug, f in slug_map.items():
        print(f"  {slug:12s} → {os.path.basename(f)}")

    # Pre-downscale oversized sources
    MAX_SRC_W = 2800
    loaded = {}
    for slug, f in slug_map.items():
        img = Image.open(f).convert("RGB")
        if img.width > MAX_SRC_W:
            new_h = int(img.height * MAX_SRC_W / img.width)
            img = img.resize((MAX_SRC_W, new_h), Image.LANCZOS)
        loaded[slug] = img
    return loaded


def cover_crop(img, target_w, target_h, zoom=1.0, pan=(0.0, 0.0)):
    """Zoom+pan then cover-crop to target dimensions."""
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih) * zoom
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    cx = nw // 2 + int(pan[0] * nw)
    cy = nh // 2 + int(pan[1] * nh)

    left  = max(0, cx - target_w // 2)
    top   = max(0, cy - target_h // 2)
    left  = min(left, nw - target_w)
    top   = min(top, nh - target_h)

    return resized.crop((left, top, left + target_w, top + target_h))


def add_vignette(img):
    """Cinematic darkened edges."""
    arr = np.array(img).astype(float)
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
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
    """Warm dramatic grade."""
    arr = np.array(img).astype(float)
    arr = np.clip((arr / 255.0) ** 0.9 * 255, 0, 255)
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
    """Draw dramatic text with drop shadow."""
    overlay = img.copy().convert("RGBA")
    txt_layer = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    bar_h = 60
    usable_h = H - bar_h * 2
    total_text_h = sum(s + 12 for s in sizes)

    if pos == "center":
        base_y = bar_h + (usable_h - total_text_h) // 2
    elif pos == "top":
        base_y = bar_h + 50
    else:
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

        shadow_off = max(2, size // 20)
        draw.text((x + shadow_off, y + shadow_off), line, font=font,
                  fill=(0, 0, 0, int(a * 0.7)))
        draw.text((x, y), line, font=font, fill=(255, 245, 210, a))

        y += size + 12

    result = Image.alpha_composite(overlay, txt_layer).convert("RGB")
    return result


def generate_frames(scenes, images):
    """Yield PIL frames for the full video."""
    total_frames = sum(int(s["dur"] * FPS) for s in scenes)
    print(f"\nGenerating {total_frames} frames at {FPS}fps…")

    global_frame = 0
    prev_last_frame = None

    for si, scene in enumerate(scenes):
        dur      = scene["dur"]
        overlay  = scene.get("overlay")
        n_frames = int(dur * FPS)
        generator = scene.get("generator")

        for fi in range(n_frames):
            t = fi / max(n_frames - 1, 1)
            te = ease_in_out(t)

            if generator:
                # Procedural frame
                if generator == "hex_board":
                    frame = make_hex_board_frame(fi, n_frames)
                elif generator == "resource_reveal":
                    frame = make_resource_reveal_frame(fi, n_frames)
                elif generator == "outro_hex":
                    frame = make_outro_hex_frame(fi, n_frames)
                else:
                    frame = Image.new("RGB", (W, H), (0, 0, 0))
                frame = add_vignette(frame)
                frame = add_letterbox(frame)
            else:
                slug    = scene["slug"]
                z_start = scene["zoom"][0]
                z_end   = scene["zoom"][1]
                pan     = scene["pan"]
                img     = images[slug]

                zoom  = lerp(z_start, z_end, te)
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
    import subprocess

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    cmd = [
        ffmpeg, "-y",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-vcodec", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        out_path,
    ]

    # IMPORTANT: redirect ffmpeg's stderr to a LOG FILE, not a pipe.
    # stderr=PIPE deadlocks when the 64KB buffer fills — ffmpeg blocks on
    # stderr write while Python blocks in wait(), moov atom never written.
    log_path = out_path + ".ffmpeg.log"
    with open(log_path, "wb") as logf:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=logf)

        try:
            for frame in frames_gen:
                proc.stdin.write(np.array(frame).tobytes())
        except BrokenPipeError:
            proc.wait()
            with open(log_path) as lf:
                print(lf.read())
            raise RuntimeError("ffmpeg exited early — see log above")

        proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        with open(log_path) as lf:
            print(lf.read())
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode})")

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
