"""The prologue as a video (Engine\\FMV\\cdv_intro.mp4, which Oliveri already plays at its start): Ed's own
photographs of Tindari, Marinello and Oliveri, slowly moving, while the story of the episode scrolls up in English.
Music: the main theme of Tomb Raider II, from Ed's soundtrack folder. The player can skip it (Look or Deselect).

  intro_video.py <photo dir> <music.mp3> <out.mp4>"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1280, 720, 30
SLIDE, FADE = 8.4, 1.2                   # seconds each photograph stays, cross-fade
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
PHOTOS = ["38247f1a", "f26936fe", "d810d59a", "93d2e707", "56964529", "9e49007b", "87ac6be4", "5ed2cd1f", "7bc8c89f"]
# (zoom from, zoom to, pan x from, to, pan y from, to) in fractions of the spare margin
MOVES = [(1.00, 1.10, .5, .5, .6, .5), (1.12, 1.02, .2, .7, .5, .5), (1.02, 1.14, .5, .5, .3, .4), (1.10, 1.00, .8, .3, .5, .5),
         (1.00, 1.12, .3, .6, .4, .6), (1.14, 1.02, .5, .5, .2, .5), (1.02, 1.12, .2, .8, .6, .5), (1.10, 1.00, .7, .3, .6, .6),
         (1.00, 1.12, .5, .5, .5, .4)]
STORY = [
    "Castor and Pollux. One of them mortal, the other not.",
    "When Castor died, Pollux shared his immortality with him: one day among the dead, one day among the stars.",
    "On this headland the Greeks built Tyndaris, named after the father of the twins. Its sailors were entrusted "
    "with two stars of metal, the Astri, that kept the sea quiet.",
    "Then, Pliny writes, half of the city fell into the sea. One of the Stars went down with it.",
    "Ever since, the cliff has had a keeper. They call her Donna Villa.",
    "Today a Black Madonna watches from the top, and under her the sand of Marinello changes shape with every storm.",
    "A Byzantine monk once wrote down where to look. His diary has found its way to a house in Via Amodeo, in Oliveri.",
    "Lara Croft has come for the diary.",
    "Tonight the lights go out. Somebody else has come for it too.",
]
TITLE = "CODA DI VOLPE"


def wrap(d, text, font, width):
    lines, line = [], ""
    for word in text.split():
        t = (line + " " + word).strip()
        if d.textlength(t, font=font) > width and line:
            lines.append(line)
            line = word
        else:
            line = t
    lines.append(line)
    return lines


def crawl():
    """The whole text as one tall strip (white letters and their alpha), to be slid up the screen."""
    font = ImageFont.truetype(SERIF, 36)
    big = ImageFont.truetype(SERIF_B, 64)
    probe = ImageDraw.Draw(Image.new("L", (10, 10)))
    rows = []
    for par in STORY:
        for ln in wrap(probe, par, font, 940):
            rows.append((ln, font))
        rows.append(("", font))
    rows += [("", font), (TITLE, big)]
    lh = 52
    h = sum(lh if f is font else 96 for _, f in rows) + 40
    im = Image.new("L", (W, h), 0)
    d = ImageDraw.Draw(im)
    y = 10
    for ln, f in rows:
        if ln:
            w = d.textlength(ln, font=f)
            d.text(((W - w) / 2, y), ln, font=f, fill=255)
        y += lh if f is font else 96
    shadow = im.filter(ImageFilter.GaussianBlur(4)).point(lambda v: min(255, int(v * 2.2)))
    return np.array(im, float) / 255.0, np.array(shadow, float) / 255.0


def frame_of(img, move, t):
    """The photograph at time t (0..1) of its move, cropped to 16:9 and scaled to the frame."""
    z0, z1, x0, x1, y0, y1 = move
    e = t * t * (3 - 2 * t)
    z = z0 + (z1 - z0) * e
    iw, ih = img.size
    cw = iw / z
    ch = cw * H / W
    if ch > ih / 1.0:
        ch = ih / z
        cw = ch * W / H
    cx = (iw - cw) * (x0 + (x1 - x0) * e)
    cy = (ih - ch) * (y0 + (y1 - y0) * e)
    return np.asarray(img.resize((W, H), Image.BILINEAR, box=(cx, cy, cx + cw, cy + ch)), float)


def main():
    src, music, out = sys.argv[1:4]
    imgs = [Image.open(os.path.join(src, p + ".jpg")).convert("RGB") for p in PHOTOS]
    text, shadow = crawl()
    total = len(PHOTOS) * SLIDE + 3.0
    n = int(total * FPS)
    # the strip enters from the bottom at 1.5 s; its title stops in the middle of the screen at the end
    travel = H + text.shape[0] - (H / 2 + 60)
    speed = travel / (n - int(1.5 * FPS) - int(2.5 * FPS))             # pixels a frame
    vig = np.linspace(0, 1, H)[:, None]
    shade = (0.50 + 0.18 * np.abs(vig - 0.5) * 2)[..., None]         # the picture darkened, a little more at the edges
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
                           "-r", str(FPS), "-i", "-", "-i", music, "-t", "%.2f" % total,
                           "-af", "afade=t=in:d=1.5,afade=t=out:st=%.2f:d=3,volume=0.9" % (total - 3.2),
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        k = min(len(imgs) - 1, int(t / SLIDE))
        u = (t - k * SLIDE) / (SLIDE + FADE)
        fr = frame_of(imgs[k], MOVES[k], min(1.0, u))
        into = t - k * SLIDE
        if k > 0 and into < FADE:                                     # still fading from the one before
            a = into / FADE
            prev = frame_of(imgs[k - 1], MOVES[k - 1], min(1.0, (t - (k - 1) * SLIDE) / (SLIDE + FADE)))
            fr = prev * (1 - a) + fr * a
        fr = fr * shade
        off = int(H - (i - 1.5 * FPS) * speed) if i > 1.5 * FPS else H
        off = max(off, int(H / 2 + 60 - text.shape[0] + 0))
        y0, y1 = max(0, off), min(H, off + text.shape[0])
        if y1 > y0:
            a = text[y0 - off:y1 - off][..., None]
            s = shadow[y0 - off:y1 - off][..., None]
            edge = np.clip(np.minimum(np.arange(y0, y1) - 20, H - 30 - np.arange(y0, y1)) / 70.0, 0, 1)[:, None, None]   # fades in and out at the borders
            if i > n - 3 * FPS:
                edge = np.maximum(edge, 0) * 1.0
            fr[y0:y1] = fr[y0:y1] * (1 - 0.75 * s * edge)
            fr[y0:y1] = fr[y0:y1] * (1 - a * edge) + np.array([250, 240, 214.0]) * a * edge
        fade = min(1.0, t / 1.2, (total - t) / 1.5)                   # in from black, out to black
        ff.stdin.write(np.clip(fr * max(0.0, fade), 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close()
    ff.wait()
    print(out, "%.1f s" % total, "crawl %.2f px a frame" % speed)


if __name__ == "__main__":
    main()
