"""Floors of Ed's house in Oliveri: Italian tiles from CC0 photographs (ambientCG, assets/tex_cc0).

cdv_pavimenti.png, 2048 x 1024, six 512 px squares = one sector (2 m) each, all tileable:
  0 cotto esagonale con tozzetti chiari (ingresso, disimpegno)   1 cotto esagonale (cantina, laboratorio, dispensa)
  2 marmette di graniglia 40 cm, impasto caldo (soggiorno, galleria, ripostiglio)
  3 marmette di graniglia 40 cm, impasto chiaro (camere)
  4 maiolica bianca e blu (cucina)                               5 piastrelle bianche con angoli blu (bagni, lavanderia)
"""
import os
import sys

import numpy as np
from PIL import Image

CC0 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "tex_cc0")
SLOTS = {"cotto_tozzetti": 0, "cotto": 1, "graniglia_calda": 2, "graniglia_chiara": 3, "maiolica": 4, "bagno": 5}


def photo(name, gain=1.0, sat=1.0):
    a = np.asarray(Image.open(os.path.join(CC0, name + ".jpg")).convert("RGB").resize((512, 512), Image.LANCZOS)).astype(float)
    g = a.mean(axis=2, keepdims=True)
    return np.clip((g + (a - g) * sat) * gain, 0, 255)


def graniglia(name, seed, n=5, tint=(1, 1, 1)):
    """n x n cement tiles in a sector, each cut from another spot of the terrazzo, with its own tone and a fine joint."""
    rng = np.random.default_rng(seed)
    src = np.asarray(Image.open(os.path.join(CC0, name + ".jpg")).convert("RGB")).astype(float)
    S = 2048
    out = np.zeros((S, S, 3))
    t = S // n + 1
    edges = [round(i * S / n) for i in range(n + 1)]
    for i in range(n):
        for j in range(n):
            x, y = rng.integers(0, 1024 - t, 2)
            cut = np.rot90(src[y:y + t, x:x + t], int(rng.integers(0, 4)))
            h, w = edges[i + 1] - edges[i], edges[j + 1] - edges[j]
            out[edges[i]:edges[i + 1], edges[j]:edges[j + 1]] = cut[:h, :w] * rng.normal(1.0, 0.035) * np.array(tint)
    for e in edges[:-1]:                                    # joints: a dark hairline with a soft worn edge
        for d, f in ((0, 0.45), (1, 0.45), (2, 0.8), (3, 0.92), (-1, 0.8), (-2, 0.92)):
            out[(e + d) % S] *= f
            out[:, (e + d) % S] *= f
    return np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS)).astype(float)


def main(out):
    tiles = [photo("tiles065", 0.92), photo("tiles066", 0.86, 0.9), graniglia("terrazzo012", 5, tint=(1.0, 0.97, 0.9)),
             graniglia("terrazzo002", 6, tint=(1.0, 0.98, 0.93)), photo("tiles101", 0.90, 0.85), photo("tiles104", 0.90, 0.85)]
    img = Image.new("RGB", (2048, 1024), (0, 0, 0))
    for i, t in enumerate(tiles):
        img.paste(Image.fromarray(t.astype(np.uint8)), ((i % 4) * 512, (i // 4) * 512))
    img.save(os.path.join(out, "cdv_pavimenti.png"), optimize=True)


if __name__ == "__main__":
    main(sys.argv[1])
