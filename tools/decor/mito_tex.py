"""Textures of the mythic props (cave of Donna Villa, Tindari, the temple): photographic CC0 plus flat metals."""
from decor.marinello_tex import photo
from decor.tex import solid


def build(pk):
    pk.put("m_cabinet", cabinet())
    pk.put("m_socket_c", socket((150, 110, 62)))
    pk.put("m_socket_p", socket((226, 184, 70)))
    pk.put("m_lockplate", lockplate())
    pk.put("m_marble", photo("concrete005", (256, 256), tint=(1.0, 0.95, 0.84), gain=1.05))
    pk.put("m_limestone", photo("rock003", (256, 256), tint=(1.0, 0.93, 0.78), gain=0.95))
    pk.put("m_cave", photo("rock022", (256, 256), tint=(0.84, 0.82, 0.8), gain=0.62))
    pk.put("m_bronze", solid(64, 64, (96, 128, 104), 71, 0.3, 8))
    pk.put("m_gold", solid(64, 64, (214, 170, 62), 72, 0.25, 8))
    pk.put("m_shell", solid(64, 64, (226, 200, 176), 73, 0.2, 6))
    pk.put("m_orange", solid(64, 64, (226, 110, 30), 74, 0.12, 4))
    pk.put("m_yellow", solid(32, 32, (220, 190, 40), 75, 0.1, 4))


def cabinet(n=128):
    """Painted iron of the sluice cabinet: dark green plates, rivets along the edges, rust at the bottom."""
    import numpy as np
    from PIL import Image, ImageDraw
    rng = np.random.default_rng(81)
    a = np.empty((n, n, 3))
    g = rng.random((n, n)) * 0.12 + 0.94
    for k, c in enumerate((58, 78, 66)):
        a[..., k] = c * g
    rust = np.clip((np.arange(n)[:, None] - n * 0.62) / (n * 0.38), 0, 1) * (rng.random((n, n)) > 0.45)
    a = a * (1 - rust[..., None] * 0.6) + np.array((126, 72, 38)) * rust[..., None] * 0.6
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, n - 1, n - 1], outline=(34, 46, 40), width=3)
    for k in range(6):
        t = int(n * (k + 0.5) / 6)
        for x, y in ((t, 7), (t, n - 8), (7, t), (n - 8, t)):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(96, 112, 100), outline=(30, 40, 34))
    return np.dstack([np.asarray(im), np.full((n, n), 255, np.uint8)])


def lockplate(w=64, h=128):
    """The lock of the sluice house: an iron door plate with a brass escutcheon and its keyhole, a ring handle."""
    import numpy as np
    from PIL import Image, ImageDraw
    S = 4
    im = Image.new("RGB", (w * S, h * S), (46, 50, 52))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w * S - 7, h * S - 7], outline=(24, 26, 28), width=8)
    for y in (0.08, 0.92):
        for x in (0.16, 0.84):
            d.ellipse([w * S * x - 9, h * S * y - 9, w * S * x + 9, h * S * y + 9], fill=(92, 96, 98), outline=(20, 20, 22), width=3)
    cx, cy = w * S / 2, h * S * 0.40
    d.rounded_rectangle([cx - 52, cy - 96, cx + 52, cy + 96], radius=40, fill=(196, 156, 70), outline=(110, 80, 30), width=6)
    d.ellipse([cx - 18, cy - 44, cx + 18, cy - 8], fill=(16, 14, 12))
    d.polygon([(cx - 9, cy - 16), (cx + 9, cy - 16), (cx + 14, cy + 44), (cx - 14, cy + 44)], fill=(16, 14, 12))
    d.ellipse([cx - 40, h * S * 0.68 - 40, cx + 40, h * S * 0.68 + 40], outline=(150, 152, 150), width=12)
    a = np.asarray(im.resize((w, h), Image.LANCZOS)).astype(float)
    a *= (np.random.default_rng(82).random((h, w)) * 0.1 + 0.95)[..., None]
    return np.dstack([np.clip(a, 0, 255).astype(np.uint8), np.full((h, w), 255, np.uint8)])


def socket(metal, n=128):
    """A socket of the altar of the Stars, seen from above: a ring of metal let into the marble, a disc of dark
    stone, and in it the hollow of an eight-pointed star, lit on one rim and in shadow on the other. Outside the
    ring the texture is empty (alpha 0): only the inlay is drawn on the altar."""
    import math
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    S = 4
    N = n * S
    c = N / 2
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([4, 4, N - 5, N - 5], fill=metal + (255,))
    d.ellipse([10, 10, N - 11, N - 11], outline=tuple(int(v * 0.55) for v in metal) + (255,), width=6)
    r0 = N * 0.43
    d.ellipse([c - r0, c - r0, c + r0, c + r0], fill=(92, 88, 84, 255), outline=tuple(int(v * 0.6) for v in metal) + (255,), width=5)

    def star(ro, ri, dx=0.0, dy=0.0):
        return [(c + dx + (ro if k % 2 == 0 else ri) * math.sin(math.pi * k / 8), c + dy - (ro if k % 2 == 0 else ri) * math.cos(math.pi * k / 8)) for k in range(16)]
    d.polygon(star(N * 0.39, N * 0.17), fill=tuple(min(255, int(v * 1.25)) for v in metal) + (255,))        # the lit rim
    d.polygon(star(N * 0.365, N * 0.155, 5, 5), fill=(8, 7, 7, 255))                                        # the shadow side
    d.polygon(star(N * 0.345, N * 0.145, 2, 2), fill=(34, 30, 28, 255))                                     # the bottom of the hollow
    d.polygon(star(N * 0.17, N * 0.07, 2, 2), fill=(58, 52, 46, 255))
    a = np.asarray(im.resize((n, n), Image.LANCZOS)).copy()
    a[..., 3] = np.where(a[..., 3] > 128, 255, 0)
    return a
