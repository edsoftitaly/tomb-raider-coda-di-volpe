"""Italian street vehicles for Coda di Volpe (v8, 01/11/2026): Fiat Panda (1st and 3rd series), Fiat Grande
Punto, Lancia Ypsilon, Fiat 500, Iveco Daily, Fiat Ducato motorhome, Piaggio Ape 50, Vespa.

Built like the cars of the late PlayStation games: a lofted body that follows the real silhouette (side
profile, plan rounding, tumblehome of the glasshouse) and painted textures projected on it: one side
elevation (both sides, mirrored), front and rear elevations, a plan view. Windows, pillars, door cuts,
handles, lights, grille and plates are painted at their real positions, so the low polygon count still
reads as the real car. No badges or brand logos; plates are invented.

All sizes in metres, from the manufacturers' data sheets. Model axes: +Z forward, +Y up, base centre at the
origin (ground level).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from decor.geom import M

SS = 4          # supersampling of the painted images
MAXR = 256      # largest texture region (px)


# ------------------------------------------------------------------------------------------- helpers
def interp(points, z):
    """Piecewise-linear y(z) through [(z, y), ...] sorted by z."""
    zs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return float(np.interp(z, zs, ys))


def shade(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


class Canvas:
    """PIL drawing in metre coordinates, supersampled. x_m(u) / y_m(v) map metres to image px."""

    def __init__(self, w_m, h_m, pxm, fx, fy, bg):
        self.pxm = pxm
        self.w = max(8, int(round(w_m * pxm)))
        self.h = max(8, int(round(h_m * pxm)))
        self.im = Image.new("RGB", (self.w * SS, self.h * SS), bg)
        self.d = ImageDraw.Draw(self.im)
        self.fx, self.fy = fx, fy      # functions metres -> px (unscaled)

    def P(self, a, b):
        return (self.fx(a) * SS, self.fy(b) * SS)

    def poly(self, pts, fill, outline=None, width=1):
        self.d.polygon([self.P(a, b) for a, b in pts], fill=fill, outline=outline, width=width * SS if outline else 0)

    def rect(self, a0, b0, a1, b1, fill, outline=None, width=1):
        p0, p1 = self.P(a0, b0), self.P(a1, b1)
        box = [min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])]
        self.d.rectangle(box, fill=fill, outline=outline, width=width * SS if outline else 0)

    def rrect(self, a0, b0, a1, b1, r, fill, outline=None, width=1):
        p0, p1 = self.P(a0, b0), self.P(a1, b1)
        box = [min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])]
        self.d.rounded_rectangle(box, radius=r * self.pxm * SS, fill=fill, outline=outline,
                                 width=width * SS if outline else 0)

    def ellipse(self, a, b, ra, rb, fill, outline=None, width=1):
        p = self.P(a, b)
        self.d.ellipse([p[0] - ra * self.pxm * SS, p[1] - rb * self.pxm * SS, p[0] + ra * self.pxm * SS,
                        p[1] + rb * self.pxm * SS], fill=fill, outline=outline, width=width * SS if outline else 0)

    def line(self, pts, fill, width=1):
        self.d.line([self.P(a, b) for a, b in pts], fill=fill, width=max(1, int(width * SS)))

    def text(self, a, b, s, fill, size_m):
        from PIL import ImageFont
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", int(size_m * self.pxm * SS))
        except OSError:
            f = ImageFont.load_default()
        p = self.P(a, b)
        self.d.text(p, s, fill=fill, font=f, anchor="mm")

    def array(self):
        im = self.im.resize((self.w, self.h), Image.LANCZOS)
        a = np.asarray(im).astype(float)
        out = np.zeros((self.h, self.w, 4))
        out[..., :3] = a
        out[..., 3] = 255
        return out


def grain(a, seed, amount=0.035):
    r = np.random.default_rng(seed)
    a[..., :3] *= (1 + r.normal(0, amount, a.shape[:2]))[..., None]
    return a


def vgrad(a, top=1.08, bottom=0.82, y0=0.0, y1=1.0):
    """Vertical light falloff: lighter at the shoulder, darker towards the sill (painted curvature)."""
    h = a.shape[0]
    t = np.clip((np.arange(h) / max(1, h - 1) - y0) / max(1e-6, (y1 - y0)), 0, 1)
    k = top + (bottom - top) * t
    a[..., :3] *= k[:, None, None]
    return a


def glass_fill(cv, pts, seed=0, tint=(34, 42, 52), interior=True, heads=()):
    """Window: dark tinted glass, a soft sky reflection band and interior shapes (headrests)."""
    cv.poly(pts, fill=tint)
    if interior:
        for (a, b, ra, rb) in heads:
            cv.ellipse(a, b, ra, rb, fill=shade(tint, 0.78))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # diagonal reflection streak clipped to the window
    mask = Image.new("L", cv.im.size, 0)
    ImageDraw.Draw(mask).polygon([cv.P(a, b) for a, b in pts], fill=255)
    refl = Image.new("L", cv.im.size, 0)
    rd = ImageDraw.Draw(refl)
    w = (x1 - x0)
    for k, (o, s) in enumerate(((0.15, 0.22), (0.55, 0.08))):
        a0 = x0 + w * o
        rd.polygon([cv.P(a0, y1), cv.P(a0 + w * s, y1), cv.P(a0 + w * s - (y1 - y0) * 0.5, y0),
                    cv.P(a0 - (y1 - y0) * 0.5, y0)], fill=70 if k == 0 else 45)
    refl = Image.composite(refl, Image.new("L", cv.im.size, 0), mask).filter(ImageFilter.GaussianBlur(SS * 2))
    light = Image.new("RGB", cv.im.size, (190, 205, 220))
    cv.im = Image.composite(light, cv.im, refl)
    cv.d = ImageDraw.Draw(cv.im)


# ------------------------------------------------------------------------------------------- body loft
class Body:
    """A car body lofted through stations along Z.

    spec keys: L, W, top [(z, y)], belt [(z, y)], bottom [(z, y)], plan [(z, half-width factor)],
    tumble (m the glasshouse leans in at the roof), green (z0, z1) glasshouse span, pxm (texture px/m),
    paint(name, canvas, kind) callbacks via the vehicle class.
    """

    def __init__(self, key, spec):
        self.key = key
        self.s = spec
        self.L, self.W = spec["L"], spec["W"]
        self.zmin, self.zmax = -self.L / 2, self.L / 2
        self.H = max(p[1] for p in spec["top"])
        self.pxm = spec.get("pxm", 96)
        zs = set(np.round(np.linspace(self.zmin, self.zmax, spec.get("n", 22)), 4))
        for p in spec["top"] + spec["belt"]:
            zs.add(round(p[0], 4))
        for z in spec.get("extra_z", ()):
            zs.add(round(z, 4))
        for p in spec["plan"]:
            zs.add(round(p[0], 4))
        # chunk borders of the side and top images (z where the image x crosses a multiple of 256 px)
        n_side = int(math.ceil(self.L * self.pxm / MAXR))
        self.side_chunks = n_side
        for k in range(1, n_side):
            zs.add(round(self.zmax - k * self.L / n_side, 4))
        self.z = sorted(z for z in zs if self.zmin <= z <= self.zmax)

    # profile functions
    def top(self, z):
        return interp(self.s["top"], z)

    def belt(self, z):
        return min(interp(self.s["belt"], z), self.top(z) - 0.01)

    def bottom(self, z):
        return interp(self.s["bottom"], z)

    def half(self, z):
        return self.W / 2 * interp(self.s["plan"], z)

    def glasshouse(self, z):
        g0, g1 = self.s["green"]
        return g0 <= z <= g1

    def ring(self, z):
        """Right half of the section, bottom -> top: P0 underside edge, P1 lower side, P2 shoulder, P3 top edge."""
        w = self.half(z)
        yb, yt, yl = self.bottom(z), self.top(z), self.belt(z)
        tumble = self.s.get("tumble", 0.08)
        roofw = self.s.get("roofw", 0.9)
        if yt - yl > 0.12:
            t = min(1.0, (yt - yl) / 0.5)
            p3 = (w - tumble * t - 0.02, yt)
        else:
            p3 = (w * roofw + (w - w * roofw) * 0.3, yt)
        tuck = self.s.get("tuck", 0.06)
        # rounded section: tucked sill, widest at the "waist", shoulder pulled in under the belt line
        y1 = yb + min(0.12, (yl - yb) * 0.3)
        ym = yb + (yl - yb) * 0.62
        sh = self.s.get("shoulder", 0.025)
        return [(w - tuck, yb), (w - 0.015, y1), (w, ym), (w - sh, yl), p3]

    # image coordinates (px, unscaled)
    def side_px(self, z, y):
        return ((self.zmax - z) * self.pxm, (self.H + 0.02 - y) * self.pxm)

    # TombEngine is left-handed: seen from the front of the car, +x is on the viewer's left
    def front_px(self, x, y):
        return ((self.W / 2 + 0.02 - x) * self.pxm, (self.H + 0.02 - y) * self.pxm)

    def rear_px(self, x, y):
        return ((x + self.W / 2 + 0.02) * self.pxm, (self.H + 0.02 - y) * self.pxm)

    def top_px(self, x, z):
        return ((x + self.W / 2 + 0.02) * self.pxm, (self.zmax - z) * self.pxm)

    # ----------------------------------------------------------------------------------- textures
    def canvases(self):
        """Blank canvases with the projection maps (the vehicle paints on them)."""
        W2, H2 = self.W + 0.04, self.H + 0.04
        side = Canvas(self.L, H2, self.pxm, lambda z: (self.zmax - z) * self.pxm, lambda y: (self.H + 0.02 - y) * self.pxm, (0, 0, 0))
        front = Canvas(W2, H2, self.pxm, lambda x: (self.W / 2 + 0.02 - x) * self.pxm, lambda y: (self.H + 0.02 - y) * self.pxm, (0, 0, 0))
        rear = Canvas(W2, H2, self.pxm, lambda x: (x + self.W / 2 + 0.02) * self.pxm, lambda y: (self.H + 0.02 - y) * self.pxm, (0, 0, 0))
        top = Canvas(W2, self.L, self.pxm, lambda x: (x + self.W / 2 + 0.02) * self.pxm, lambda z: (self.zmax - z) * self.pxm, (0, 0, 0))
        return side, front, rear, top

    def register(self, pk, images):
        """Split the images into <= 256 px regions and put them in the packer."""
        self.regions = {}
        for name, a in images.items():
            h, w = a.shape[:2]
            if name in ("side", "top"):
                long_ = w if name == "side" else h
                n = int(math.ceil(long_ / MAXR)) if name == "top" else self.side_chunks
                n = max(n, int(math.ceil(long_ / MAXR)))
                edges = [int(round(long_ * k / n)) for k in range(n + 1)]
                chunks = []
                for k in range(n):
                    a0, a1 = edges[k], edges[k + 1]
                    part = a[:, a0:a1] if name == "side" else a[a0:a1, :]
                    rn = "veh_%s_%s_%d" % (self.key, name, k)
                    if part.shape[0] > MAXR or part.shape[1] > MAXR:
                        part = np.asarray(Image.fromarray(part.astype(np.uint8)).resize(
                            (min(MAXR, part.shape[1]), min(MAXR, part.shape[0])), Image.LANCZOS)).astype(float)
                        # keep the mapping: the region is scaled, uv stays relative
                    pk.put(rn, part)
                    chunks.append((a0, a1, rn))
                self.regions[name] = (chunks, w, h)
            else:
                rn = "veh_%s_%s" % (self.key, name)
                if a.shape[0] > MAXR or a.shape[1] > MAXR:
                    a = np.asarray(Image.fromarray(a.astype(np.uint8)).resize(
                        (min(MAXR, a.shape[1]), min(MAXR, a.shape[0])), Image.LANCZOS)).astype(float)
                    self.regions[name] = ([(0, 0, rn)], None, None, True)
                pk.put(rn, a)
                self.regions.setdefault(name, ([(0, 0, rn)], None, None))
        self.img_size = {k: v.shape[:2] for k, v in images.items()}

    # ----------------------------------------------------------------------------------- mesh
    def uv_for(self, view, pts_m):
        """Region and per-corner uv for a face projected on `view` (side/front/rear/top)."""
        h, w = self.img_size[view]
        if view == "side":
            px = [self.side_px(p[2], p[1]) for p in pts_m]
        elif view == "front":
            px = [self.front_px(p[0], p[1]) for p in pts_m]
        elif view == "rear":
            px = [self.rear_px(p[0], p[1]) for p in pts_m]
        else:
            px = [self.top_px(p[0], p[2]) for p in pts_m]
        info = self.regions[view]
        chunks = info[0]
        if view in ("side", "top"):
            along = [q[0] for q in px] if view == "side" else [q[1] for q in px]
            mid = sum(along) / len(along)
            a0, a1, rn = next(((a0, a1, rn) for a0, a1, rn in chunks if a0 - 0.5 <= mid <= a1 + 0.5), chunks[-1])
            if view == "side":
                uv = [((q[0] - a0) / max(1, a1 - a0), q[1] / h) for q in px]
            else:
                uv = [(q[0] / w, (q[1] - a0) / max(1, a1 - a0)) for q in px]
        else:
            rn = chunks[0][2]
            uv = [(q[0] / w, q[1] / h) for q in px]
        uv = [(min(1.0, max(0.0, u)), min(1.0, max(0.0, v))) for u, v in uv]
        return rn, uv

    def mesh(self, extra_under=True):
        from decor.geom import Mesh
        m = Mesh()
        rings = []
        for z in self.z:
            r = self.ring(z)
            rings.append([(x, y, z) for x, y in r])
        n = len(rings)
        for i in range(n - 1):
            A, B = rings[i], rings[i + 1]     # A rear, B front
            z0, z1 = A[0][2], B[0][2]
            for j in range(len(A) - 1):       # side strips, right and left
                for s in (1, -1):
                    q = [(s * B[j + 1][0], B[j + 1][1], z1), (s * A[j + 1][0], A[j + 1][1], z0),
                         (s * A[j][0], A[j][1], z0), (s * B[j][0], B[j][1], z1)]
                    add_face(m, self, q, "side", out=(s, 0, 0))
            # top strip
            t = len(A) - 1
            q = [(-B[t][0], B[t][1], z1), (B[t][0], B[t][1], z1), (A[t][0], A[t][1], z0), (-A[t][0], A[t][1], z0)]
            slope = abs(B[t][1] - A[t][1]) / max(1e-6, z1 - z0)
            view = "top"
            ymid = (A[t][1] + B[t][1]) / 2
            zmid = (z0 + z1) / 2
            # windscreen / rear window: inclined and above the belt line (raked screens of modern cars are
            # only 27-35 degrees steep, so the slope alone is not enough); bumpers and noses: steep
            if slope > 0.75 or (slope > 0.3 and ymid > self.belt(zmid) + 0.04):
                view = "front" if zmid > 0 else "rear"
            add_face(m, self, q, view, out=(0, 1, 0))
            if extra_under:
                q = [(A[0][0], A[0][1], z0), (-A[0][0], A[0][1], z0), (-B[0][0], B[0][1], z1), (B[0][0], B[0][1], z1)]
                add_face(m, self, q, None, out=(0, -1, 0), region=self.s.get("under", "veh_under"))
        # end caps
        for ring, view, sgn in ((rings[-1], "front", 1), (rings[0], "rear", -1)):
            z = ring[0][2]
            for j in range(len(ring) - 1):
                q = [(-ring[j + 1][0], ring[j + 1][1], z), (ring[j + 1][0], ring[j + 1][1], z),
                     (ring[j][0], ring[j][1], z), (-ring[j][0], ring[j][1], z)]
                add_face(m, self, q, view, out=(0, 0, sgn))
        return m


def add_face(m, body, q, view, out, region=None, uv=None):
    """q: 4 points in metres (any winding); turned so the face looks along `out`."""
    P = [np.array(p, float) for p in q]
    if np.linalg.norm(P[0] - P[1]) < 1e-6 and np.linalg.norm(P[3] - P[2]) < 1e-6:
        return
    if region is None:
        region, uv = body.uv_for(view, q)
    elif uv is None:
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    nrm = -np.cross(P[1] - P[0], P[2] - P[0])
    if np.linalg.norm(nrm) < 1e-12:
        nrm = -np.cross(P[2] - P[0], P[3] - P[0])
    o = np.array(out, float)
    if o[0] != 0:   # side faces: outward is +-x but follow the section (tumblehome, tuck)
        o = np.array([o[0], 0.0, 0.0])
    if np.dot(nrm, o) < 0:
        P = P[::-1]
        uv = uv[::-1]
    # drop degenerate corners (triangles)
    pts, uvs = [], []
    for p, t in zip(P, uv):
        if pts and np.linalg.norm(p - pts[-1]) < 1e-6:
            continue
        pts.append(p)
        uvs.append(t)
    if len(pts) > 3 and np.linalg.norm(pts[0] - pts[-1]) < 1e-6:
        pts, uvs = pts[:-1], uvs[:-1]
    if len(pts) < 3:
        return
    m.face([p * M for p in pts], region, uv=uvs)


# ------------------------------------------------------------------------------------------- parts
def wheel(m, r, width, x, z, rim_region, tyre_region="veh_tyre", n=14, side=1):
    """Wheel with its axle along X; the outer face (rim) looks to `side`."""
    cx = x
    xo, xi = cx + side * width / 2, cx - side * width / 2
    ring = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        c0, s0 = ring[k]
        c1, s1 = ring[(k + 1) % n]
        q = [(xo, r + s0 * r, z + c0 * r), (xo, r + s1 * r, z + c1 * r), (xi, r + s1 * r, z + c1 * r), (xi, r + s0 * r, z + c0 * r)]
        mid = np.array([cx, r + (s0 + s1) / 2 * r, z + (c0 + c1) / 2 * r])
        add_face(m, None, q, None, out=tuple(mid - np.array([cx, r, z])), region=tyre_region,
                 uv=[(0, k / n), (0, (k + 1) / n), (1, (k + 1) / n), (1, k / n)])
    # outer rim disc: triangles from the centre with polar uv
    for k in range(n):
        c0, s0 = ring[k]
        c1, s1 = ring[(k + 1) % n]
        tri = [(xo + side * 0.004, r, z), (xo + side * 0.004, r + s0 * r, z + c0 * r), (xo + side * 0.004, r + s1 * r, z + c1 * r)]
        uv = [(0.5, 0.5), (0.5 + 0.5 * c0 * side, 0.5 - 0.5 * s0), (0.5 + 0.5 * c1 * side, 0.5 - 0.5 * s1)]
        tri3(m, tri, uv, rim_region, out=(side, 0, 0))
    for k in range(n):      # inner face, dark
        c0, s0 = ring[k]
        c1, s1 = ring[(k + 1) % n]
        tri = [(xi, r, z), (xi, r + s0 * r, z + c0 * r), (xi, r + s1 * r, z + c1 * r)]
        tri3(m, tri, [(0.5, 0.5), (0.5, 0), (1, 0.5)], "veh_under", out=(-side, 0, 0))


def tri3(m, tri, uv, region, out):
    P = [np.array(p, float) for p in tri]
    nrm = -np.cross(P[1] - P[0], P[2] - P[0])
    if np.dot(nrm, np.array(out, float)) < 0:
        P = P[::-1]
        uv = uv[::-1]
    m.face([p * M for p in P], region, uv=list(uv))


def boxm(m, x0, x1, y0, y1, z0, z1, region, faces="all", uvs=None):
    """Axis box in metres with correct outward winding; region may be a dict per face key."""
    F = {
        "+z": ([(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)], (0, 0, 1)),
        "-z": ([(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)], (0, 0, -1)),
        "+x": ([(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)], (1, 0, 0)),
        "-x": ([(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)], (-1, 0, 0)),
        "+y": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0)),
        "-y": ([(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)], (0, -1, 0)),
    }
    for k, (q, o) in F.items():
        if faces != "all" and k not in faces:
            continue
        reg = region.get(k) if isinstance(region, dict) else region
        if reg is None:
            continue
        add_face(m, None, q, None, out=o, region=reg, uv=(uvs or {}).get(k))


def loft_ellipse(m, sections, region, n=10, uvmode="side", body=None, cap0=True, cap1=True, half=False):
    """Loft of elliptical sections [(z, yc, rx, ry), ...] (metres) along Z. uv: u around, v along."""
    rings = []
    a0 = -math.pi / 2 if half else 0
    a1 = math.pi / 2 if half else 2 * math.pi
    kk = n if not half else n
    for (z, yc, rx, ry) in sections:
        rings.append([(math.cos(a0 + (a1 - a0) * k / kk) * rx, yc + math.sin(a0 + (a1 - a0) * k / kk) * ry, z) for k in range(kk + 1)])
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(kk):
            q = [B[k + 1], B[k], A[k], A[k + 1]]
            zc = (A[0][2] + B[0][2]) / 2
            yc = (sections[i][1] + sections[i + 1][1]) / 2
            mid = np.mean([np.array(p) for p in q], axis=0)
            out = mid - np.array([0, yc, zc])
            out[2] = 0
            uv = [((k + 1) / kk, 1 - (i + 1) / (len(rings) - 1)), (k / kk, 1 - (i + 1) / (len(rings) - 1)),
                  (k / kk, 1 - i / (len(rings) - 1)), ((k + 1) / kk, 1 - i / (len(rings) - 1))]
            add_face(m, None, q, None, out=tuple(out), region=region, uv=uv)
    return rings


# ------------------------------------------------------------------------------------------- shared paint
TYRE = (24, 24, 26)
TRIM = (34, 35, 37)          # black plastic
GREYPL = (78, 80, 82)        # grey bumper plastic (Panda 141)
CHROME = (190, 194, 198)
GLASS = (30, 38, 48)


def plate(cv, xc, yc, text, w=0.52, h=0.11, mirror=False):
    """Italian EU plate: white, blue bands left (EU) and right (year/province)."""
    cv.rect(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2, fill=(236, 236, 230))
    bw = w * 0.085
    left, right = (xc - w / 2, xc - w / 2 + bw), (xc + w / 2 - bw, xc + w / 2)
    cv.rect(left[0], yc - h / 2, left[1], yc + h / 2, fill=(30, 60, 150))
    cv.rect(right[0], yc - h / 2, right[1], yc + h / 2, fill=(30, 60, 150))
    cv.text(xc, yc, text, fill=(20, 20, 24), size_m=h * 0.72)


def headlamp(cv, x0, y0, x1, y1, r=0.02, round_=False):
    if round_:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        cv.ellipse(cx, cy, abs(x1 - x0) / 2, abs(y1 - y0) / 2, fill=(70, 74, 80))
        cv.ellipse(cx, cy, abs(x1 - x0) / 2 * 0.78, abs(y1 - y0) / 2 * 0.78, fill=(214, 218, 220))
        cv.ellipse(cx, cy, abs(x1 - x0) / 2 * 0.35, abs(y1 - y0) / 2 * 0.35, fill=(250, 250, 240))
        return
    cv.rrect(x0, y0, x1, y1, r, fill=(70, 74, 80))
    dx, dy = (x1 - x0) * 0.08, (y1 - y0) * 0.12
    cv.rrect(x0 + dx, y0 + dy, x1 - dx, y1 - dy, r, fill=(205, 210, 214))
    cv.rect(x0 + dx * 2, (y0 + y1) / 2 - dy, x0 + (x1 - x0) * 0.45, (y0 + y1) / 2 + dy, fill=(248, 248, 238))


def tail(cv, x0, y0, x1, y1, r=0.015):
    cv.rrect(x0, y0, x1, y1, r, fill=(150, 20, 22))
    h = (y1 - y0)
    cv.rect(x0 + (x1 - x0) * 0.08, y0 + h * 0.12, x1 - (x1 - x0) * 0.08, y0 + h * 0.4, fill=(210, 40, 36))
    cv.rect(x0 + (x1 - x0) * 0.08, y0 + h * 0.55, x1 - (x1 - x0) * 0.08, y0 + h * 0.72, fill=(220, 120, 30))


def wiper(cv, x0, y0, length, ang):
    cv.line([(x0, y0), (x0 + length * math.cos(ang), y0 + length * math.sin(ang))], fill=(18, 18, 18), width=2)


def finish(cv, seed, top=1.07, bottom=0.86):
    a = cv.array()
    a = vgrad(a, top, bottom)
    return grain(a, seed, 0.012)


def rim_texture(kind, size=128):
    cv = Canvas(1.0, 1.0, size, lambda x: (x + 0.5) * size, lambda y: (0.5 - y) * size, (20, 20, 22))
    cv.ellipse(0, 0, 0.5, 0.5, fill=TYRE)
    cv.ellipse(0, 0, 0.47, 0.47, fill=(36, 36, 38))
    if kind == "steel":          # painted steel wheel with a black/silver hubcap
        cv.ellipse(0, 0, 0.34, 0.34, fill=(150, 152, 155))
        for k in range(6):
            a = 2 * math.pi * k / 6
            cv.ellipse(0.24 * math.cos(a), 0.24 * math.sin(a), 0.035, 0.035, fill=(60, 60, 62))
        cv.ellipse(0, 0, 0.17, 0.17, fill=(40, 40, 42))
        cv.ellipse(0, 0, 0.12, 0.12, fill=(170, 172, 175))
    elif kind == "cover":        # plastic wheel cover (Panda, Ypsilon base)
        cv.ellipse(0, 0, 0.35, 0.35, fill=(170, 174, 178))
        for k in range(12):
            a = 2 * math.pi * k / 12
            cv.line([(0.12 * math.cos(a), 0.12 * math.sin(a)), (0.33 * math.cos(a), 0.33 * math.sin(a))], fill=(90, 92, 96), width=3)
        cv.ellipse(0, 0, 0.1, 0.1, fill=(120, 122, 126))
    elif kind == "alloy":        # five spoke alloy
        cv.ellipse(0, 0, 0.35, 0.35, fill=(60, 62, 66))
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.3
            pts = [(0.07 * math.cos(a - 0.5), 0.07 * math.sin(a - 0.5)), (0.34 * math.cos(a - 0.17), 0.34 * math.sin(a - 0.17)),
                   (0.34 * math.cos(a + 0.17), 0.34 * math.sin(a + 0.17)), (0.07 * math.cos(a + 0.5), 0.07 * math.sin(a + 0.5))]
            cv.poly(pts, fill=(185, 188, 192))
        cv.ellipse(0, 0, 0.35, 0.35, fill=None, outline=(200, 202, 206), width=2)
        cv.ellipse(0, 0, 0.08, 0.08, fill=(150, 152, 156))
    elif kind == "van":          # steel van wheel, black centre
        cv.ellipse(0, 0, 0.34, 0.34, fill=(50, 52, 54))
        for k in range(8):
            a = 2 * math.pi * k / 8
            cv.ellipse(0.22 * math.cos(a), 0.22 * math.sin(a), 0.04, 0.04, fill=(25, 25, 26))
        cv.ellipse(0, 0, 0.12, 0.12, fill=(80, 82, 84))
    elif kind == "scooter":      # small alloy wheel of the Vespa
        cv.ellipse(0, 0, 0.33, 0.33, fill=(175, 178, 182))
        for k in range(5):
            a = 2 * math.pi * k / 5
            cv.ellipse(0.2 * math.cos(a), 0.2 * math.sin(a), 0.06, 0.06, fill=(70, 72, 74))
        cv.ellipse(0, 0, 0.1, 0.1, fill=(120, 122, 126))
    a = cv.array()
    return grain(a, 7, 0.02)


def tread(w=32, h=128):
    a = np.zeros((h, w, 4))
    a[..., 3] = 255
    a[..., :3] = TYRE
    for y in range(0, h, 6):
        a[y:y + 2, 4:w - 4, :3] = (14, 14, 15)
    a[:, :3, :3] = (40, 40, 42)
    a[:, -3:, :3] = (40, 40, 42)
    return grain(a, 3, 0.05)


def stripes_rubber():
    a = np.zeros((32, 32, 4))
    a[..., 3] = 255
    a[..., :3] = (40, 40, 42)
    for x in range(2, 32, 6):
        a[:, x:x + 2, :3] = (20, 20, 21)
    return a


def lamp_round():
    cv = Canvas(1.0, 1.0, 32, lambda x: (x + 0.5) * 32, lambda y: (0.5 - y) * 32, (40, 40, 42))
    cv.ellipse(0, 0, 0.48, 0.48, fill=(210, 214, 218))
    cv.ellipse(0, 0, 0.25, 0.25, fill=(250, 250, 240))
    return cv.array()


def swatch(c, n=16):
    a = np.zeros((n, n, 4))
    a[..., :3] = c
    a[..., 3] = 255
    return grain(a, 5, 0.02)


# ------------------------------------------------------------------------------------------- vehicles
VEHICLES = {}      # key -> dict(body=Body, paint=fn, wheels=[...], rim=str, extras=fn)


def vehicle(key, **kw):
    VEHICLES[key] = kw
    return kw


def body_paint(cv, colour):
    cv.rect(-50, -50, 50, 50, fill=colour)


def side_common(B, cv, colour, wheels, arch_r, lower=None, lower_y=0.0):
    """Body colour, lower protection band, wheel arches."""
    body_paint(cv, colour)
    if lower is not None:
        cv.poly([(B.zmax, -1), (B.zmax, lower_y), (B.zmin, lower_y), (B.zmin, -1)], fill=lower)
    for (z, r) in wheels:
        cv.ellipse(z, r, arch_r, arch_r, fill=(14, 14, 15))


def glass_side(B, cv, pts, heads=()):
    glass_fill(cv, pts, tint=GLASS, heads=heads)


# --- Fiat Panda, first series (141), 1986-2003: 3,41 x 1,49 x 1,45 m, passo 2,16 m ---------------------
def panda141(colour, plate_txt, key):
    L = 3.408
    B = Body(key, dict(
        L=L, W=1.494, pxm=96, tumble=0.07, roofw=0.92, tuck=0.05,
        top=[(-1.704, 0.86), (-1.69, 0.95), (-1.64, 1.40), (-1.58, 1.445), (0.32, 1.445), (0.38, 1.42),
             (0.86, 0.93), (1.60, 0.86), (1.704, 0.83)],
        belt=[(-1.704, 0.93), (0.86, 0.90), (1.704, 0.82)],
        bottom=[(-1.704, 0.26), (-1.58, 0.19), (1.55, 0.19), (1.704, 0.26)],
        plan=[(-1.704, 0.92), (-1.62, 0.98), (-1.4, 1.0), (1.45, 1.0), (1.64, 0.98), (1.704, 0.93)],
        green=(-1.66, 0.86), extra_z=(-1.11, 1.05, -0.36, 0.62)))
    wz = [(1.05, 0.275), (-1.11, 0.275)]

    def paint(B):
        side, front, rear, top = B.canvases()
        # side
        side_common(B, side, colour, wz, 0.33, lower=GREYPL, lower_y=0.40)
        side.rect(B.zmin, 0.40, B.zmax, 0.43, fill=shade(GREYPL, 0.7))
        side.poly([(1.704, 0.40), (1.704, 0.20), (1.40, 0.20), (1.40, 0.40)], fill=GREYPL)   # bumper ends
        win = [(0.80, 0.955), (0.36, 1.39), (-1.55, 1.39), (-1.62, 0.955)]
        side.poly([(0.84, 0.93), (0.37, 1.42), (-1.58, 1.42), (-1.66, 0.93)], fill=TRIM)       # frame
        glass_side(B, side, win, heads=[(0.02, 1.13, 0.09, 0.11), (-0.95, 1.12, 0.09, 0.10)])
        side.rect(-0.40, 0.93, -0.33, 1.42, fill=TRIM)                                          # B pillar
        side.line([(0.64, 0.43), (0.64, 0.93)], fill=shade(colour, 0.55), width=1.5)            # door cut
        side.line([(-0.37, 0.43), (-0.37, 0.93)], fill=shade(colour, 0.55), width=1.5)
        side.rect(-0.30, 0.82, -0.20, 0.85, fill=TRIM)                                          # handle
        side.rect(1.38, 0.66, 1.44, 0.69, fill=(225, 135, 35))                                  # indicator
        side.ellipse(-1.30, 0.80, 0.045, 0.045, fill=shade(colour, 0.8))                        # fuel cap
        side.line([(B.zmin, 0.90), (B.zmax, 0.84)], fill=shade(colour, 1.18), width=1)          # shoulder light
        # front
        body_paint(front, colour)
        front.rrect(-0.75, 0.19, 0.75, 0.43, 0.04, fill=GREYPL)
        front.rect(-0.75, 0.36, 0.75, 0.38, fill=shade(GREYPL, 0.7))
        plate(front, 0.0, 0.29, plate_txt)
        front.rect(-0.70, 0.50, 0.70, 0.77, fill=TRIM)                                          # grille panel
        for k in range(6):
            yy = 0.535 + k * 0.04
            front.line([(-0.36, yy), (0.36, yy)], fill=(58, 60, 62), width=1)
        front.poly([(-0.28, 0.51), (-0.16, 0.51), (-0.26, 0.76), (-0.38, 0.76)], fill=(70, 72, 74))
        headlamp(front, -0.68, 0.56, -0.42, 0.74)
        headlamp(front, 0.42, 0.56, 0.68, 0.74)
        front.rect(-0.70, 0.45, -0.55, 0.49, fill=(225, 135, 35))
        front.rect(0.55, 0.45, 0.70, 0.49, fill=(225, 135, 35))
        front.rect(-0.70, 0.93, 0.70, 1.43, fill=TRIM)                                          # screen frame
        glass_fill(front, [(-0.64, 0.95), (0.64, 0.95), (0.62, 1.40), (-0.62, 1.40)], tint=GLASS,
                   heads=[(-0.33, 1.12, 0.1, 0.12), (0.33, 1.12, 0.1, 0.12)])
        wiper(front, -0.55, 0.96, 0.45, 0.25)
        wiper(front, 0.05, 0.96, 0.45, 0.25)
        # rear
        body_paint(rear, colour)
        rear.rrect(-0.75, 0.19, 0.75, 0.43, 0.04, fill=GREYPL)
        rear.rect(-0.75, 0.36, 0.75, 0.38, fill=shade(GREYPL, 0.7))
        tail(rear, -0.72, 0.47, -0.56, 0.80)
        tail(rear, 0.56, 0.47, 0.72, 0.80)
        plate(rear, 0.0, 0.58, plate_txt)
        rear.rect(-0.52, 0.68, 0.52, 0.70, fill=shade(colour, 0.6))                              # tailgate cut
        rear.rect(-0.66, 0.93, 0.66, 1.42, fill=TRIM)
        glass_fill(rear, [(-0.60, 0.97), (0.60, 0.97), (0.58, 1.38), (-0.58, 1.38)], tint=GLASS,
                   heads=[(-0.35, 1.08, 0.09, 0.1), (0.35, 1.08, 0.09, 0.1)])
        wiper(rear, -0.05, 0.98, 0.4, 0.5)
        # top
        body_paint(top, colour)
        top.rect(-0.75, 1.62, 0.75, 1.704, fill=TRIM)          # grille top edge
        top.line([(-0.55, 1.6), (-0.55, 0.9)], fill=shade(colour, 0.7), width=1)
        top.line([(0.55, 1.6), (0.55, 0.9)], fill=shade(colour, 0.7), width=1)
        for k in range(4):                                      # roof ribs of the 141
            x = -0.45 + k * 0.3
            top.line([(x, 0.2), (x, -1.4)], fill=shade(colour, 0.85), width=1)
        return dict(side=finish(side, 1), front=finish(front, 2, 1.04, 0.9), rear=finish(rear, 3, 1.04, 0.9),
                    top=finish(top, 4, 1.05, 1.0))
    return dict(body=B, paint=paint, wheels=wz, wheel_w=0.15, rim="steel", mirror=(0.80, 0.98, colour))



def mirror_x(pts):
    return [(-x, y) for x, y in pts]


def squircle(z0, y0, z1, y1, r):
    """Points of a rounded rectangle (metres), for windows drawn as polygons."""
    pts = []
    zc0, zc1, yc0, yc1 = min(z0, z1) + r, max(z0, z1) - r, min(y0, y1) + r, max(y0, y1) - r
    for (cz, cy, a0) in ((zc1, yc1, 0), (zc0, yc1, 90), (zc0, yc0, 180), (zc1, yc0, 270)):
        for k in range(5):
            a = math.radians(a0 + k * 22.5)
            pts.append((cz + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def modern(key, colour, plate_txt, spec, wheels, wheel_w, rim, sidep, frontp, rearp, topp=None, mirror=None, extras=None):
    """Modern hatchback: body + painter assembled from part lists (all coordinates in metres).

    sidep: frame (black surround polygon), windows [polygons], pillars [(z0, z1, ytop)], cuts [(z, y0, y1)],
           handles [(z, y)], lower (y, colour) cladding, strip (y0, y1, colour), lamps [(polygon, colour)],
           arch (radius), cap (z, y)
    frontp/rearp: callables painting on the elevation canvas (x mirrored helpers available)
    """
    B = Body(key, spec)

    def paint(B):
        side, front, rear, top = B.canvases()
        side_common(B, side, colour, wheels, sidep.get("arch", wheels[0][1] + 0.05 if wheels else 0.0),
                    lower=sidep.get("lower", (None, None))[1], lower_y=sidep.get("lower", (0, None))[0])
        for (y0, y1, c) in sidep.get("strips", ()):
            side.rect(B.zmin, y0, B.zmax, y1, fill=c)
        if sidep.get("frame"):
            side.poly(sidep["frame"], fill=TRIM)
        for w in sidep.get("windows", ()):
            glass_side(B, side, w, heads=sidep.get("heads", ()))
        for (z0, z1, y0, y1) in sidep.get("pillars", ()):
            side.rect(z0, y0, z1, y1, fill=TRIM)
        for (z, y0, y1) in sidep.get("cuts", ()):
            side.line([(z, y0), (z, y1)], fill=shade(colour, 0.5), width=1.5)
        for (z, y) in sidep.get("handles", ()):
            side.rrect(z - 0.06, y - 0.017, z + 0.06, y + 0.017, 0.01, fill=sidep.get("handle_col", shade(colour, 0.75)))
        for (poly, c) in sidep.get("lamps", ()):
            side.poly(poly, fill=c)
        if sidep.get("cap"):
            z, y = sidep["cap"]
            side.ellipse(z, y, 0.05, 0.045, fill=shade(colour, 0.82))
        for (pts, c, w) in sidep.get("lines", ()):
            side.line(pts, fill=c, width=w)
        if sidep.get("post"):
            sidep["post"](side)
        body_paint(front, colour)
        frontp(front)
        body_paint(rear, colour)
        rearp(rear)
        body_paint(top, colour)
        if topp:
            topp(top)
        return dict(side=finish(side, hash(key) % 97), front=finish(front, 2, 1.04, 0.9), rear=finish(rear, 3, 1.04, 0.9),
                    top=finish(top, 4, 1.05, 1.0))
    return dict(body=B, paint=paint, wheels=wheels, wheel_w=wheel_w, rim=rim, mirror=mirror, extras=extras)


def both(cv, fn):
    """Call fn(sign) for the right and left halves of a symmetric elevation."""
    fn(1)
    fn(-1)


def screen(cv, x_half_bot, y0, x_half_top, y1, heads=(), wipers=2, frame=TRIM):
    cv.poly([(-x_half_bot - 0.04, y0 - 0.03), (x_half_bot + 0.04, y0 - 0.03), (x_half_top + 0.03, y1 + 0.03), (-x_half_top - 0.03, y1 + 0.03)], fill=frame)
    glass_fill(cv, [(-x_half_bot, y0), (x_half_bot, y0), (x_half_top, y1), (-x_half_top, y1)], tint=GLASS, heads=heads)
    if wipers == 2:
        wiper(cv, x_half_bot * 0.85, y0 + 0.02, x_half_bot * 0.9, math.radians(168))
        wiper(cv, -x_half_bot * 0.05, y0 + 0.02, x_half_bot * 0.9, math.radians(168))
    elif wipers == 1:
        wiper(cv, -0.05, y0 + 0.02, x_half_bot * 0.9, math.radians(150))


# --- Fiat Panda, third series (319), 2012-: 3,65 x 1,64 x 1,55 m, passo 2,30 m -------------------------
def panda3(colour, plate_txt, key):
    hz = 1.8265
    spec = dict(L=3.653, W=1.643, pxm=96, tumble=0.15, roofw=0.9, tuck=0.06,
                top=[(-hz, 0.92), (-1.80, 1.06), (-1.72, 1.40), (-1.62, 1.52), (-1.2, 1.545), (0.0, 1.551),
                     (0.27, 1.53), (1.10, 0.99), (1.60, 0.90), (1.77, 0.83), (hz, 0.70)],
                belt=[(-hz, 1.02), (-1.3, 1.03), (1.10, 0.97), (hz, 0.70)],
                bottom=[(-hz, 0.40), (-1.70, 0.21), (1.62, 0.20), (hz, 0.36)],
                plan=[(-hz, 0.88), (-1.79, 0.94), (-1.72, 0.975), (-1.55, 1.0), (1.35, 1.0), (1.60, 0.975), (1.74, 0.94), (hz, 0.86)],
                extra_z=(-1.163, 1.137, -0.16, -1.0))
    wz = [(1.137, 0.29), (-1.163, 0.29)]
    sidep = dict(
        lower=(0.30, TRIM), strips=[(0.56, 0.63, TRIM)],
        frame=[(1.10, 0.97), (0.28, 1.50), (-1.30, 1.50), (-1.64, 1.33), (-1.66, 1.03)],
        windows=[squircle(1.02, 1.0, -0.10, 1.45, 0.07), squircle(-0.20, 1.0, -0.98, 1.45, 0.06),
                 squircle(-1.07, 1.06, -1.56, 1.40, 0.07)],
        pillars=[(-0.19, -0.11, 0.97, 1.50)], heads=[(0.10, 1.16, 0.08, 0.1), (-0.75, 1.15, 0.08, 0.1)],
        cuts=[(1.12, 0.30, 0.97), (-0.15, 0.30, 0.97), (-1.02, 0.30, 1.02)],
        handles=[(-0.02, 0.93), (-0.88, 0.95)], cap=(-1.40, 0.93),
        lamps=[([(1.60, 0.70), (1.82, 0.70), (1.82, 0.86), (1.66, 0.86)], (205, 210, 214)),
               ([(-1.60, 0.92), (-1.82, 0.92), (-1.80, 1.34), (-1.68, 1.34)], (170, 25, 28))])

    def front(cv):
        cv.rrect(-0.80, 0.20, 0.80, 0.40, 0.05, fill=TRIM)
        cv.poly([(-0.48, 0.30), (0.48, 0.30), (0.40, 0.50), (-0.40, 0.50)], fill=(26, 27, 29))
        for k in range(4):
            cv.line([(-0.42, 0.34 + k * 0.04), (0.42, 0.34 + k * 0.04)], fill=(52, 54, 56), width=1)
        plate(cv, 0, 0.56, plate_txt)
        cv.rrect(-0.38, 0.66, 0.38, 0.71, 0.02, fill=(26, 27, 29))            # upper slot
        both(cv, lambda s: headlamp(cv, s * 0.50, 0.62, s * 0.78, 0.84, r=0.05))
        both(cv, lambda s: cv.ellipse(s * 0.66, 0.36, 0.05, 0.05, fill=(200, 204, 208)))
        screen(cv, 0.72, 0.99, 0.62, 1.52, heads=[(-0.34, 1.20, 0.1, 0.12), (0.34, 1.20, 0.1, 0.12)])

    def rear(cv):
        cv.rrect(-0.80, 0.22, 0.80, 0.44, 0.05, fill=TRIM)
        cv.rect(-0.30, 0.30, 0.30, 0.33, fill=(150, 20, 22))
        both(cv, lambda s: tail(cv, min(s * 0.62, s * 0.80), 0.92, max(s * 0.62, s * 0.80), 1.34, r=0.05))
        plate(cv, 0, 0.66, plate_txt)
        cv.rect(-0.30, 0.75, 0.30, 0.77, fill=CHROME)
        cv.rrect(-0.60, 1.06, 0.60, 1.50, 0.06, fill=TRIM)
        glass_fill(cv, squircle(-0.55, 1.09, 0.55, 1.46, 0.07), tint=GLASS)
        cv.rect(-0.25, 1.47, 0.25, 1.50, fill=(150, 20, 22))                 # third stop light

    def topp(cv):
        both(cv, lambda s: cv.rect(s * 0.62, 0.3, s * 0.66, -1.5, fill=TRIM))  # roof rails
    return modern(key, colour, plate_txt, spec, wz, 0.18, "cover", sidep, front, rear, topp, mirror=(1.02, 1.0, colour))


# --- Fiat Grande Punto (199), 2005-2018: 4,03 x 1,69 x 1,49 m, passo 2,51 m ----------------------------
def punto(colour, plate_txt, key):
    hz = 2.015
    spec = dict(L=4.03, W=1.687, pxm=96, tumble=0.17, roofw=0.9, tuck=0.06,
                top=[(-hz, 0.98), (-1.99, 1.06), (-1.80, 1.26), (-1.45, 1.44), (-0.6, 1.49), (0.05, 1.47),
                     (1.05, 0.96), (1.70, 0.82), (1.95, 0.70), (hz, 0.58)],
                belt=[(-hz, 1.04), (-1.4, 1.06), (1.05, 0.93), (hz, 0.60)],
                bottom=[(-hz, 0.42), (-1.85, 0.23), (1.80, 0.21), (hz, 0.32)],
                plan=[(-hz, 0.86), (-1.96, 0.93), (-1.85, 0.97), (-1.6, 1.0), (1.25, 1.0), (1.65, 0.96), (1.88, 0.90), (hz, 0.80)],
                extra_z=(1.145, -1.365, -0.20, -1.08))
    wz = [(1.145, 0.30), (-1.365, 0.30)]
    sidep = dict(
        lower=(0.27, TRIM), strips=[(0.60, 0.64, shade(colour, 0.7))],
        frame=[(1.07, 0.94), (0.10, 1.45), (-1.25, 1.44), (-1.62, 1.18), (-1.63, 1.06)],
        windows=[[(0.98, 0.98), (0.12, 1.41), (-0.13, 1.42), (-0.13, 0.96)],
                 [(-0.24, 0.97), (-0.24, 1.42), (-1.05, 1.41), (-1.12, 1.04)],
                 [(-1.18, 1.05), (-1.20, 1.38), (-1.30, 1.38), (-1.56, 1.10)]],
        pillars=[(-0.24, -0.13, 0.95, 1.46)], heads=[(0.0, 1.16, 0.08, 0.1), (-0.8, 1.17, 0.08, 0.1)],
        cuts=[(1.10, 0.27, 0.94), (-0.19, 0.27, 0.96), (-1.10, 0.27, 1.05)],
        handles=[(-0.05, 0.89), (-0.95, 0.92)], cap=(-1.45, 0.92), handle_col=shade(colour, 0.72),
        lamps=[([(1.40, 0.80), (1.90, 0.68), (2.01, 0.62), (1.95, 0.60), (1.45, 0.72)], (200, 205, 210)),
               ([(-1.72, 1.00), (-1.98, 0.96), (-2.0, 1.12), (-1.85, 1.20)], (170, 25, 28))])

    def front(cv):
        cv.poly([(-0.78, 0.22), (0.78, 0.22), (0.80, 0.42), (-0.80, 0.42)], fill=shade(colour, 0.85))
        cv.poly([(-0.50, 0.24), (0.50, 0.24), (0.42, 0.44), (-0.42, 0.44)], fill=(24, 25, 27))   # lower intake
        both(cv, lambda s: cv.ellipse(s * 0.62, 0.32, 0.055, 0.045, fill=(190, 194, 198)))
        plate(cv, 0, 0.37, plate_txt)
        cv.poly([(-0.26, 0.48), (0.26, 0.48), (0.20, 0.56), (-0.20, 0.56)], fill=(24, 25, 27))   # upper grille
        both(cv, lambda s: cv.poly([(s * 0.30, 0.50), (s * 0.80, 0.56), (s * 0.82, 0.62), (s * 0.34, 0.62)], fill=(70, 74, 80)))
        both(cv, lambda s: cv.poly([(s * 0.36, 0.53), (s * 0.76, 0.57), (s * 0.77, 0.60), (s * 0.38, 0.60)], fill=(214, 218, 222)))
        screen(cv, 0.74, 0.96, 0.60, 1.45, heads=[(-0.34, 1.18, 0.1, 0.12), (0.34, 1.18, 0.1, 0.12)])

    def rear(cv):
        cv.rrect(-0.82, 0.30, 0.82, 0.52, 0.05, fill=shade(colour, 0.9))
        cv.rect(-0.82, 0.28, 0.82, 0.34, fill=TRIM)
        plate(cv, 0, 0.66, plate_txt)
        cv.rect(-0.32, 0.74, 0.32, 0.76, fill=CHROME)
        both(cv, lambda s: tail(cv, min(s * 0.58, s * 0.82), 0.92, max(s * 0.58, s * 0.82), 1.20, r=0.04))
        cv.rrect(-0.55, 1.05, 0.55, 1.43, 0.05, fill=TRIM)
        glass_fill(cv, squircle(-0.50, 1.08, 0.50, 1.40, 0.05), tint=GLASS)
    return modern(key, colour, plate_txt, spec, wz, 0.19, "alloy", sidep, front, rear, mirror=(1.0, 0.98, colour))


# --- Lancia Ypsilon (846), 2011-: 3,84 x 1,68 x 1,52 m, passo 2,39 m -----------------------------------
def ypsilon(colour, plate_txt, key):
    hz = 1.92
    spec = dict(L=3.84, W=1.676, pxm=96, tumble=0.17, roofw=0.9, tuck=0.06,
                top=[(-hz, 0.98), (-1.90, 1.10), (-1.78, 1.32), (-1.50, 1.48), (-0.6, 1.52), (0.1, 1.49),
                     (1.10, 0.97), (1.70, 0.84), (1.88, 0.72), (hz, 0.60)],
                belt=[(-hz, 1.07), (-1.3, 1.09), (1.10, 0.95), (hz, 0.64)],
                bottom=[(-hz, 0.42), (-1.78, 0.22), (1.75, 0.21), (hz, 0.33)],
                plan=[(-hz, 0.86), (-1.86, 0.93), (-1.76, 0.97), (-1.55, 1.0), (1.30, 1.0), (1.62, 0.96), (1.82, 0.90), (hz, 0.80)],
                extra_z=(1.17, -1.22, -0.18, -1.05))
    wz = [(1.17, 0.30), (-1.22, 0.30)]
    chrome_line = ([(1.08, 0.97), (0.12, 1.47), (-1.25, 1.47), (-1.62, 1.10)], CHROME, 1.5)
    sidep = dict(
        lower=(0.27, TRIM),
        frame=[(1.10, 0.95), (0.12, 1.47), (-1.25, 1.47), (-1.62, 1.12), (-1.64, 1.08)],
        windows=[[(1.0, 0.99), (0.14, 1.43), (-0.12, 1.44), (-0.12, 0.98)],
                 [(-0.22, 0.99), (-0.22, 1.44), (-1.10, 1.43), (-1.10, 1.05)],
                 [(-1.16, 1.07), (-1.17, 1.38), (-1.28, 1.40), (-1.55, 1.12)]],
        pillars=[(-0.22, -0.12, 0.97, 1.47)], heads=[(0.0, 1.17, 0.08, 0.1), (-0.8, 1.18, 0.08, 0.1)],
        cuts=[(1.12, 0.27, 0.95), (-0.17, 0.27, 0.98), (-1.12, 0.27, 1.06)],
        handles=[(-0.04, 0.90)], cap=(-1.42, 0.94), lines=[chrome_line],
        lamps=[([(1.42, 0.82), (1.88, 0.72), (1.92, 0.66), (1.50, 0.74)], (200, 205, 210)),
               ([(-1.70, 1.04), (-1.92, 0.98), (-1.92, 1.10), (-1.78, 1.12)], (170, 25, 28))])

    def front(cv):
        cv.poly([(-0.80, 0.22), (0.80, 0.22), (0.82, 0.40), (-0.82, 0.40)], fill=shade(colour, 0.85))
        cv.poly([(-0.55, 0.24), (0.55, 0.24), (0.50, 0.33), (-0.50, 0.33)], fill=(24, 25, 27))
        both(cv, lambda s: cv.poly([(s * 0.52, 0.30), (s * 0.70, 0.30), (s * 0.70, 0.38), (s * 0.54, 0.38)], fill=(30, 31, 33)))
        # the Lancia "calice" grille: chrome frame, black vertical bars
        g = [(-0.20, 0.36), (0.20, 0.36), (0.26, 0.62), (0.20, 0.70), (-0.20, 0.70), (-0.26, 0.62)]
        cv.poly(g, fill=CHROME)
        cv.poly([(-0.17, 0.39), (0.17, 0.39), (0.22, 0.61), (0.17, 0.67), (-0.17, 0.67), (-0.22, 0.61)], fill=(26, 27, 29))
        for k in range(-3, 4):
            cv.line([(k * 0.045, 0.40), (k * 0.05, 0.66)], fill=(150, 154, 158), width=1)
        plate(cv, 0, 0.30, plate_txt, w=0.45, h=0.10)
        both(cv, lambda s: cv.poly([(s * 0.32, 0.56), (s * 0.80, 0.58), (s * 0.82, 0.66), (s * 0.36, 0.66)], fill=(70, 74, 80)))
        both(cv, lambda s: cv.poly([(s * 0.38, 0.59), (s * 0.76, 0.60), (s * 0.77, 0.64), (s * 0.40, 0.64)], fill=(214, 218, 222)))
        screen(cv, 0.74, 0.97, 0.60, 1.48, heads=[(-0.34, 1.18, 0.1, 0.12), (0.34, 1.18, 0.1, 0.12)])

    def rear(cv):
        cv.rrect(-0.82, 0.28, 0.82, 0.50, 0.05, fill=shade(colour, 0.9))
        cv.rect(-0.82, 0.26, 0.82, 0.31, fill=TRIM)
        plate(cv, 0, 0.66, plate_txt)
        both(cv, lambda s: tail(cv, min(s * 0.40, s * 0.82), 0.96, max(s * 0.40, s * 0.82), 1.10, r=0.03))
        cv.rect(-0.40, 1.00, 0.40, 1.04, fill=CHROME)
        cv.rrect(-0.55, 1.12, 0.55, 1.46, 0.05, fill=TRIM)
        glass_fill(cv, squircle(-0.50, 1.15, 0.50, 1.43, 0.05), tint=GLASS)
    return modern(key, colour, plate_txt, spec, wz, 0.19, "alloy", sidep, front, rear, mirror=(1.02, 0.99, colour))


# --- Fiat 500 (312), 2007-: 3,55 x 1,63 x 1,49 m, passo 2,30 m -----------------------------------------
def cinquecento(colour, plate_txt, key):
    hz = 1.773
    spec = dict(L=3.546, W=1.627, pxm=96, tumble=0.18, roofw=0.86, tuck=0.07,
                top=[(-hz, 0.92), (-1.76, 1.02), (-1.68, 1.28), (-1.52, 1.43), (-1.1, 1.475), (0.0, 1.488),
                     (0.25, 1.46), (1.00, 0.98), (1.45, 0.92), (1.70, 0.82), (hz, 0.62)],
                belt=[(-hz, 1.0), (-1.3, 1.01), (1.0, 0.95), (hz, 0.62)],
                bottom=[(-hz, 0.40), (-1.66, 0.22), (1.62, 0.21), (hz, 0.34)],
                plan=[(-hz, 0.82), (-1.73, 0.90), (-1.64, 0.95), (-1.45, 1.0), (1.20, 1.0), (1.48, 0.97), (1.65, 0.90), (hz, 0.76)],
                extra_z=(1.143, -1.157, -0.58))
    wz = [(1.143, 0.29), (-1.157, 0.29)]
    sidep = dict(
        lower=(0.26, TRIM), lines=[([(1.0, 0.96), (0.26, 1.45), (-1.10, 1.45), (-1.45, 1.20)], CHROME, 1.5)],
        frame=[(1.0, 0.95), (0.26, 1.45), (-1.10, 1.45), (-1.46, 1.18), (-1.48, 1.01)],
        windows=[[(0.93, 0.99), (0.27, 1.41), (-0.52, 1.41), (-0.52, 0.98)],
                 [(-0.62, 0.99), (-0.62, 1.41), (-1.08, 1.41), (-1.40, 1.04)]],
        pillars=[(-0.62, -0.52, 0.96, 1.45)], heads=[(-0.05, 1.15, 0.08, 0.1)],
        cuts=[(1.02, 0.26, 0.95), (-0.58, 0.26, 0.98)], handles=[(-0.45, 0.91)], handle_col=CHROME, cap=(-1.35, 0.92),
        lamps=[([(1.66, 0.74), (1.77, 0.72), (1.77, 0.78), (1.68, 0.80)], (225, 140, 40)),
               ([(-1.66, 0.92), (-1.77, 0.92), (-1.77, 1.06), (-1.70, 1.08)], (170, 25, 28))])

    def front(cv):
        cv.poly([(-0.76, 0.22), (0.76, 0.22), (0.80, 0.44), (-0.80, 0.44)], fill=shade(colour, 0.9))
        cv.poly([(-0.40, 0.25), (0.40, 0.25), (0.32, 0.35), (-0.32, 0.35)], fill=(26, 27, 29))      # lower "smile"
        plate(cv, 0, 0.40, plate_txt, w=0.46, h=0.10)
        both(cv, lambda s: headlamp(cv, s * 0.48, 0.44, s * 0.66, 0.60, round_=True))
        both(cv, lambda s: cv.ellipse(s * 0.56, 0.71, 0.10, 0.04, fill=(232, 232, 226)))           # upper DRL
        both(cv, lambda s: cv.line([(s * 0.06, 0.66), (s * 0.30, 0.70)], fill=CHROME, width=3))      # "moustache"
        cv.ellipse(0, 0.66, 0.05, 0.035, fill=CHROME)
        screen(cv, 0.70, 0.98, 0.56, 1.46, heads=[(-0.32, 1.18, 0.1, 0.12), (0.32, 1.18, 0.1, 0.12)])

    def rear(cv):
        cv.poly([(-0.78, 0.24), (0.78, 0.24), (0.80, 0.46), (-0.80, 0.46)], fill=shade(colour, 0.9))
        cv.rect(-0.78, 0.24, 0.78, 0.30, fill=TRIM)
        plate(cv, 0, 0.64, plate_txt)
        cv.rect(-0.28, 0.73, 0.28, 0.76, fill=CHROME)
        for s in (1, -1):
            x0, x1 = sorted((s * 0.56, s * 0.76))
            cv.rrect(x0, 0.86, x1, 1.08, 0.04, fill=(170, 24, 26))
            cv.rrect(x0 + 0.04, 0.91, x1 - 0.04, 1.03, 0.03, fill=colour)                         # body-colour centre
        cv.rrect(-0.55, 1.10, 0.55, 1.44, 0.05, fill=TRIM)
        glass_fill(cv, squircle(-0.50, 1.13, 0.50, 1.41, 0.06), tint=GLASS)
    return modern(key, colour, plate_txt, spec, wz, 0.18, "alloy", sidep, front, rear, mirror=(0.95, 0.98, colour))


# --- Iveco Daily furgone (2014-), passo 3520, tetto H2: 5,48 x 2,01 x 2,55 m ------------------------------
def daily(colour, plate_txt, key):
    hz = 2.74
    spec = dict(L=5.48, W=2.01, pxm=80, tumble=0.07, roofw=0.95, tuck=0.05, shoulder=0.02,
                top=[(-hz, 2.46), (-2.72, 2.53), (-2.62, 2.55), (1.50, 2.55), (1.62, 2.50), (2.28, 1.36),
                     (2.55, 1.20), (2.70, 1.02), (hz, 0.62)],
                belt=[(-hz, 1.32), (1.62, 1.30), (2.28, 1.28), (hz, 0.80)],
                bottom=[(-hz, 0.50), (-2.62, 0.40), (2.55, 0.40), (hz, 0.46)],
                plan=[(-hz, 0.97), (-2.66, 1.0), (1.70, 1.0), (2.30, 0.985), (2.60, 0.95), (hz, 0.90)],
                extra_z=(1.74, -1.78, 1.18, 0.95, -0.35))
    wz = [(1.74, 0.355), (-1.78, 0.355)]
    sidep = dict(
        lower=(0.58, TRIM), arch=0.43,
        frame=[(2.26, 1.30), (1.66, 2.42), (1.18, 2.42), (1.18, 1.30)],
        windows=[[(2.18, 1.34), (1.68, 2.30), (1.24, 2.30), (1.24, 1.34)]], heads=[(1.55, 1.70, 0.12, 0.15)],
        cuts=[(2.30, 0.58, 1.30), (1.16, 0.58, 2.46), (0.95, 0.58, 2.40), (-0.35, 0.58, 2.40), (-2.70, 0.58, 2.46)],
        handles=[(1.30, 1.22), (0.85, 1.25)], handle_col=TRIM,
        lines=[([(0.95, 1.92), (-0.65, 1.92)], shade(colour, 0.55), 2), ([(0.95, 0.70), (-0.35, 0.70)], shade(colour, 0.6), 1)],
        lamps=[([(2.38, 1.05), (2.70, 0.95), (2.74, 1.10), (2.45, 1.22)], (205, 210, 214)),
               ([(-2.62, 0.62), (-2.74, 0.62), (-2.74, 1.30), (-2.62, 1.30)], (160, 22, 24))],
        cap=(1.0, 0.95))

    def front(cv):
        cv.rect(-1.0, 0.40, 1.0, 0.78, fill=TRIM)
        plate(cv, 0, 0.58, plate_txt)
        cv.poly([(-0.62, 0.80), (0.62, 0.80), (0.70, 1.18), (-0.70, 1.18)], fill=(22, 23, 25))      # grille
        for k in range(5):
            cv.line([(-0.62, 0.86 + k * 0.065), (0.62, 0.86 + k * 0.065)], fill=(60, 62, 64), width=2)
        both(cv, lambda s: cv.poly([(s * 0.72, 0.92), (s * 0.98, 0.98), (s * 0.98, 1.20), (s * 0.74, 1.18)], fill=(70, 74, 80)))
        both(cv, lambda s: cv.poly([(s * 0.76, 0.98), (s * 0.94, 1.02), (s * 0.94, 1.15), (s * 0.77, 1.13)], fill=(214, 218, 222)))
        screen(cv, 0.94, 1.36, 0.88, 2.42, heads=[(-0.45, 1.75, 0.13, 0.16), (0.45, 1.75, 0.13, 0.16)])

    def rear(cv):
        cv.rect(-1.0, 0.40, 1.0, 0.62, fill=TRIM)
        plate(cv, 0.25, 0.75, plate_txt)
        cv.line([(0.0, 0.62), (0.0, 2.46)], fill=shade(colour, 0.5), width=2)
        both(cv, lambda s: cv.rect(min(s * 0.88, s * 1.0), 0.62, max(s * 0.88, s * 1.0), 1.30, fill=(160, 22, 24)))
        both(cv, lambda s: cv.rect(min(s * 0.89, s * 0.99), 0.95, max(s * 0.89, s * 0.99), 1.05, fill=(220, 130, 30)))
        both(cv, lambda s: cv.rrect(min(s * 0.12, s * 0.80), 1.60, max(s * 0.12, s * 0.80), 2.25, 0.04, fill=TRIM))
        both(cv, lambda s: glass_fill(cv, [(s * 0.16, 1.64), (s * 0.76, 1.64), (s * 0.76, 2.21), (s * 0.16, 2.21)], tint=GLASS, interior=False))
        both(cv, lambda s: cv.rect(min(s * 0.05, s * 0.2), 1.18, max(s * 0.05, s * 0.2), 1.24, fill=TRIM))

    def topp(cv):
        for k in range(6):
            z = 1.2 - k * 0.7
            cv.line([(-0.9, z), (0.9, z)], fill=shade(colour, 0.85), width=2)
    return modern(key, colour, plate_txt, spec, wz, 0.22, "van", sidep, front, rear, topp, mirror=(2.20, 1.55, TRIM))


# --- Camper profilato su Fiat Ducato (passo 3800): 6,99 x 2,30 x 2,90 m -------------------------------------
def camper(key):
    hz = 3.495
    colour = (238, 238, 234)
    spec = dict(L=6.99, W=2.30, pxm=64, tumble=0.05, roofw=0.96, tuck=0.04, shoulder=0.015,
                top=[(-hz, 2.70), (-3.47, 2.85), (-3.36, 2.90), (1.05, 2.90), (1.55, 2.62), (1.95, 2.12),
                     (2.10, 2.02), (2.78, 1.24), (3.18, 1.06), (3.42, 0.88), (hz, 0.58)],
                belt=[(-hz, 1.30), (1.90, 1.25), (2.78, 1.22), (hz, 0.82)],
                bottom=[(-hz, 0.80), (-3.25, 0.55), (-2.4, 0.45), (3.20, 0.42), (hz, 0.48)],
                plan=[(-hz, 0.96), (-3.40, 1.0), (1.55, 1.0), (2.05, 0.91), (3.10, 0.89), (3.38, 0.85), (hz, 0.80)],
                extra_z=(2.565, -1.235, 1.95, 1.30, 0.20, -0.40, -2.2))
    wz = [(2.565, 0.345), (-1.235, 0.345)]
    sidep = dict(
        lower=(0.62, (188, 190, 192)), arch=0.42,
        strips=[(0.62, 0.66, (120, 122, 126))],
        frame=[(2.76, 1.24), (2.06, 2.02), (1.90, 2.02), (1.90, 1.24)],
        windows=[[(2.70, 1.28), (2.08, 1.96), (1.95, 1.96), (1.95, 1.28)],
                 squircle(1.20, 1.45, 0.35, 2.05, 0.08), squircle(-1.10, 1.45, -1.90, 2.05, 0.08),
                 squircle(-2.40, 1.55, -3.10, 2.05, 0.08)],
        heads=[], cuts=[(2.80, 0.62, 1.22), (1.88, 0.62, 2.02)], handles=[(1.98, 1.15)], handle_col=TRIM,
        lamps=[([(3.05, 1.00), (3.40, 0.86), (3.47, 1.00), (3.12, 1.10)], (205, 210, 214))])

    def post(cv):
        # entrance door with its small window, fridge vents, a storage locker, the side decal sweep
        cv.rrect(-0.05, 0.62, -0.68, 2.10, 0.06, fill=shade(colour, 0.96), outline=(150, 152, 156), width=1)
        glass_fill(cv, squircle(-0.15, 1.55, -0.58, 1.95, 0.05), tint=GLASS, interior=False)
        cv.rect(-0.12, 1.15, -0.22, 1.20, fill=TRIM)
        for y in (1.05, 1.75):
            cv.rrect(-2.05, y, -2.30, y + 0.45, 0.03, fill=(40, 42, 44))
            for k in range(6):
                cv.line([(-2.07, y + 0.05 + k * 0.07), (-2.28, y + 0.05 + k * 0.07)], fill=(90, 92, 94), width=1)
        cv.rrect(-2.50, 0.70, -3.25, 1.30, 0.04, fill=shade(colour, 0.95), outline=(150, 152, 156), width=1)
        cv.line([(-2.65, 1.05), (-2.80, 1.05)], fill=TRIM, width=2)
        sweep = [(1.45, 2.55), (-0.8, 2.62), (-3.49, 2.40), (-3.49, 2.30), (-0.8, 2.50), (1.30, 2.45)]
        cv.poly(sweep, fill=(110, 112, 118))
        cv.poly([(1.0, 0.95), (-3.49, 1.05), (-3.49, 1.12), (1.0, 1.0)], fill=(176, 140, 90))
        cv.poly([(1.0, 0.88), (-3.49, 0.95), (-3.49, 1.0), (1.0, 0.92)], fill=(110, 112, 118))
    sidep["post"] = post

    def front(cv):
        cv.rect(-1.0, 0.42, 1.0, 0.75, fill=(120, 122, 126))
        plate(cv, 0, 0.58, "FC 802 SA")
        cv.poly([(-0.60, 0.76), (0.60, 0.76), (0.66, 1.05), (-0.66, 1.05)], fill=(26, 27, 29))
        for k in range(4):
            cv.line([(-0.58, 0.81 + k * 0.06), (0.58, 0.81 + k * 0.06)], fill=(70, 72, 74), width=2)
        both(cv, lambda s: cv.poly([(s * 0.68, 0.82), (s * 0.92, 0.86), (s * 0.92, 1.06), (s * 0.70, 1.05)], fill=(70, 74, 80)))
        both(cv, lambda s: cv.poly([(s * 0.71, 0.87), (s * 0.89, 0.89), (s * 0.89, 1.02), (s * 0.72, 1.01)], fill=(214, 218, 222)))
        screen(cv, 0.86, 1.25, 0.80, 2.00, heads=[(-0.42, 1.62, 0.13, 0.16), (0.42, 1.62, 0.13, 0.16)])
        cv.rect(-1.05, 2.10, 1.05, 2.90, fill=colour)
        glass_fill(cv, squircle(-0.55, 2.35, 0.55, 2.70, 0.06), tint=(50, 56, 62), interior=False)   # spoiler skylight

    def rear(cv):
        cv.rect(-1.15, 0.45, 1.15, 0.80, fill=(120, 122, 126))
        plate(cv, 0, 0.62, "FC 802 SA")
        both(cv, lambda s: cv.rrect(min(s * 0.78, s * 1.08), 0.85, max(s * 0.78, s * 1.08), 1.45, 0.04, fill=(160, 22, 24)))
        both(cv, lambda s: cv.rect(min(s * 0.82, s * 1.04), 1.12, max(s * 0.82, s * 1.04), 1.22, fill=(220, 130, 30)))
        glass_fill(cv, squircle(-0.55, 1.75, 0.55, 2.35, 0.08), tint=GLASS, interior=False)
        cv.rect(-1.15, 2.55, 1.15, 2.62, fill=(110, 112, 118))
        cv.rect(-0.75, 0.85, 0.75, 0.88, fill=(110, 112, 118))

    def topp(cv):
        cv.rect(-0.55, -0.6, 0.55, -2.0, fill=(30, 40, 70))                    # solar panel
        for k in range(1, 5):
            cv.line([(-0.55, -0.6 - k * 0.28), (0.55, -0.6 - k * 0.28)], fill=(150, 160, 175), width=1)
        for (z, w) in ((0.6, 0.4), (-2.7, 0.4)):
            cv.rrect(-w / 2, z, w / 2, z - w, 0.04, fill=(205, 208, 212))      # skylights
    return modern(key, colour, "FC 802 SA", spec, wz, 0.22, "van", sidep, front, rear, topp, mirror=(2.65, 1.45, TRIM))


# --- Piaggio Ape 50 (2,46 x 1,25 x 1,60 m) -----------------------------------------------------------------
def ape(colour, key):
    hz = 0.48
    spec = dict(L=0.96, W=1.20, pxm=110, tumble=0.06, roofw=0.92, tuck=0.04, shoulder=0.02, n=10,
                top=[(-hz, 1.50), (-0.44, 1.58), (-0.38, 1.60), (0.14, 1.60), (0.22, 1.55), (0.40, 1.02),
                     (0.46, 0.86), (hz, 0.40)],
                belt=[(-hz, 1.00), (0.40, 0.98), (hz, 0.70)],
                bottom=[(-hz, 0.45), (0.20, 0.45), (0.38, 0.55), (hz, 0.55)],
                plan=[(-hz, 0.98), (-0.40, 1.0), (0.18, 1.0), (0.36, 0.92), (0.44, 0.80), (hz, 0.66)])
    sidep = dict(
        arch=0.0, lower=(0.50, TRIM),
        frame=[(0.38, 1.0), (0.20, 1.55), (-0.38, 1.55), (-0.38, 1.0)],
        windows=[[(0.33, 1.04), (0.18, 1.50), (-0.33, 1.50), (-0.33, 1.04)]], heads=[(-0.1, 1.22, 0.1, 0.12)],
        cuts=[(0.36, 0.50, 1.0), (-0.40, 0.50, 1.55)], handles=[(-0.30, 0.92)], handle_col=TRIM)

    def front(cv):
        cv.rect(-0.6, 0.40, 0.6, 0.52, fill=TRIM)
        headlamp(cv, -0.10, 0.62, 0.10, 0.80, round_=True)
        both(cv, lambda s: cv.rrect(min(s * 0.30, s * 0.42), 0.70, max(s * 0.30, s * 0.42), 0.76, 0.02, fill=(225, 140, 40)))
        for k in range(4):
            cv.line([(-0.18, 0.52 + k * 0.025), (0.18, 0.52 + k * 0.025)], fill=shade(colour, 0.6), width=1)
        screen(cv, 0.50, 1.03, 0.47, 1.52, heads=[(-0.2, 1.22, 0.11, 0.13)], wipers=1)

    def rear(cv):
        cv.rect(-0.6, 0.45, 0.6, 1.0, fill=shade(colour, 0.92))
        cv.rrect(-0.45, 1.05, 0.45, 1.48, 0.04, fill=TRIM)
        glass_fill(cv, squircle(-0.40, 1.09, 0.40, 1.44, 0.04), tint=GLASS, interior=False)

    v = modern(key, colour, "", spec, [], 0.12, "steel", sidep, front, rear, mirror=(0.36, 1.05, TRIM))

    def builder():
        from decor.geom import Mesh
        B = v["body"]
        cab = car_mesh_only(key)
        m = Mesh()
        m.merge(cab.transformed(t=(0, 0, 0.75 * M)))
        # cassone (bed), z -1.23 .. 0.25, floor at 0.62, sides 0.30
        bp, bi = "veh_%s_bed" % key, "veh_%s_bedin" % key
        x0, x1, z0, z1 = -0.62, 0.62, -1.23, 0.25
        boxm(m, x0, x1, 0.55, 0.62, z0, z1, {"+y": bi, "-y": "veh_under", "+x": bp, "-x": bp, "+z": bp, "-z": bp})
        for (a0, a1, c0, c1) in ((x0, x0 + 0.03, z0, z1), (x1 - 0.03, x1, z0, z1), (x0, x1, z0, z0 + 0.03), (x0, x1, z1 - 0.03, z1)):
            boxm(m, a0, a1, 0.62, 0.92, c0, c1, {"+y": bp, "+x": bp, "-x": bp, "+z": bp, "-z": bp})
        boxm(m, -0.25, 0.25, 0.30, 0.55, -1.05, 0.25, "veh_under")                     # chassis and engine
        # plate and lights on the tailgate
        boxm(m, -0.21, 0.21, 0.66, 0.77, z0 - 0.012, z0, {"-z": "veh_%s_plate" % key},
             uvs={"-z": [(0, 0), (1, 0), (1, 1), (0, 1)][::-1][2:] + [(0, 0), (1, 0), (1, 1), (0, 1)][::-1][:2]})
        for s in (1, -1):
            boxm(m, s * 0.52 - 0.06, s * 0.52 + 0.06, 0.66, 0.74, z0 - 0.015, z0, {"-z": "veh_taillamp"})
        for s in (1, -1):
            wheel(m, 0.21, 0.055, s * 0.0275, 1.08, "veh_rim_steel", side=s)
        for s in (1, -1):
            wheel(m, 0.22, 0.13, s * 0.50, -0.62, "veh_rim_steel", side=s)
        return m
    v["builder"] = builder
    v["bed"] = colour
    return v


def car_mesh_only(key):
    v = VEHICLES[key]
    m = v["body"].mesh()
    if v.get("mirror"):
        zm, ym, _ = v["mirror"]
        B = v["body"]
        for s in (1, -1):
            x0 = B.half(zm) - 0.02
            xa, xb = (x0, x0 + 0.12) if s > 0 else (-x0 - 0.12, -x0)
            boxm(m, xa, xb, ym, ym + 0.09, zm - 0.05, zm, {"+z": "veh_trim", "-z": "veh_mirror_glass", "+x": "veh_trim",
                 "-x": "veh_trim", "+y": "veh_trim", "-y": "veh_trim"})
    return m


# --- Vespa Primavera 125 (1,86 m) ---------------------------------------------------------------------------
def shield(m, levels, region, n=8):
    """Curved leg shield: horizontal arcs [(y, half width, bulge, z of the edges)] stacked upwards, both faces."""
    rows = []
    for (y, hw, bulge, ze) in levels:
        rows.append([(hw * math.sin(-math.pi / 2 + math.pi * k / n), y, ze + bulge * math.cos(-math.pi / 2 + math.pi * k / n)) for k in range(n + 1)])
    for i in range(len(rows) - 1):
        A, B = rows[i], rows[i + 1]
        for k in range(n):
            q = [B[k], B[k + 1], A[k + 1], A[k]]
            add_face(m, None, q, None, out=(0, 0, 1), region=region)
            add_face(m, None, q, None, out=(0, 0, -1), region=region)


def vespa(colour, key):
    def builder():
        from decor.geom import Mesh
        m = Mesh()
        P, S, C = "veh_%s_paint" % key, "veh_seat", "veh_chrome"
        # rear cowl over engine and luggage bay, sitting on the floorboard
        loft_ellipse(m, [(-0.86, 0.52, 0.05, 0.07), (-0.80, 0.50, 0.19, 0.22), (-0.64, 0.49, 0.28, 0.27),
                         (-0.40, 0.48, 0.30, 0.28), (-0.18, 0.46, 0.25, 0.24), (-0.04, 0.42, 0.16, 0.18),
                         (0.03, 0.37, 0.07, 0.10)], P, n=12)
        loft_ellipse(m, [(-0.70, 0.78, 0.05, 0.03), (-0.64, 0.80, 0.14, 0.05), (-0.12, 0.81, 0.15, 0.05),
                         (0.02, 0.79, 0.12, 0.04), (0.08, 0.77, 0.04, 0.02)], S, n=8)
        boxm(m, -0.16, 0.16, 0.20, 0.29, -0.10, 0.50, {"+y": "veh_floor", "+x": P, "-x": P, "-y": "veh_under"})
        shield(m, [(0.22, 0.21, 0.05, 0.49), (0.45, 0.24, 0.07, 0.50), (0.72, 0.22, 0.07, 0.51), (0.92, 0.15, 0.05, 0.52),
                   (1.00, 0.07, 0.03, 0.53)], P)
        loft_ellipse(m, [(0.44, 1.04, 0.04, 0.04), (0.50, 1.07, 0.13, 0.07), (0.60, 1.07, 0.13, 0.065), (0.67, 1.04, 0.05, 0.04)], P, n=8)
        boxm(m, -0.34, 0.34, 1.08, 1.11, 0.52, 0.55, "veh_trim")                          # handlebar
        for s in (1, -1):
            boxm(m, s * 0.29 - 0.05, s * 0.29 + 0.05, 1.07, 1.12, 0.51, 0.56, "veh_grip")
            boxm(m, s * 0.19 - 0.008, s * 0.19 + 0.008, 1.11, 1.24, 0.52, 0.535, C)      # mirror stalk
            boxm(m, s * 0.20 - 0.045, s * 0.20 + 0.045, 1.22, 1.27, 0.52, 0.54, C)
        boxm(m, -0.065, 0.065, 1.00, 1.10, 0.665, 0.675, {"+z": "veh_headlamp"})
        loft_ellipse(m, [(0.50, 0.40, 0.05, 0.10), (0.58, 0.45, 0.085, 0.11), (0.72, 0.44, 0.085, 0.10), (0.84, 0.37, 0.06, 0.06)], P, n=6)
        boxm(m, -0.02, 0.02, 0.22, 0.48, 0.52, 0.56, "veh_trim")                          # fork
        for (z, r) in ((0.66, 0.205), (-0.60, 0.205)):
            for s in (1, -1):
                wheel(m, r, 0.05, s * 0.025, z, "veh_rim_scooter", side=s)
        boxm(m, -0.24, -0.21, 0.0, 0.22, -0.12, -0.09, "veh_trim")                        # side stand
        boxm(m, -0.09, 0.09, 0.56, 0.62, -0.88, -0.84, {"-z": "veh_taillamp", "+x": P, "-x": P, "+y": P})
        return m.transformed(rz=-0.06)
    return dict(builder=builder, paint_col=colour)

def build_tex(pk):
    """Paint every vehicle and put its regions in the decoration packer (called by decor.tex.build)."""
    pk.put("veh_tyre", tread())
    pk.put("veh_under", swatch((16, 16, 17)))
    pk.put("veh_trim", swatch(TRIM))
    pk.put("veh_mirror_glass", swatch((60, 70, 80)))
    for k in ("steel", "cover", "alloy", "van", "scooter"):
        pk.put("veh_rim_" + k, rim_texture(k))
    pk.put("veh_seat", swatch((30, 26, 24)))
    pk.put("veh_grip", swatch((20, 20, 20)))
    pk.put("veh_chrome", vgrad(swatch(CHROME, 32), 1.2, 0.7))
    pk.put("veh_floor", stripes_rubber())
    pk.put("veh_headlamp", lamp_round())
    pk.put("veh_taillamp", swatch((180, 24, 26)))
    for key, v in VEHICLES.items():
        if v.get("body"):
            imgs = v["paint"](v["body"])
            v["body"].register(pk, imgs)
        if v.get("mirror"):
            pk.put("veh_%s_paint" % key, swatch(v["mirror"][2]))
        if v.get("paint_col"):
            pk.put("veh_%s_paint" % key, vgrad(swatch(v["paint_col"], 32), 1.12, 0.85))
        if v.get("bed"):
            pk.put("veh_%s_bed" % key, swatch(v["bed"]))
            pk.put("veh_%s_bedin" % key, swatch(shade(v["bed"], 0.6)))
            cv = Canvas(0.44, 0.11, 160, lambda x: (x + 0.22) * 160, lambda y: (0.055 - y) * 160, (0, 0, 0))
            plate(cv, 0, 0, "X4 7KD", w=0.44, h=0.11)
            pk.put("veh_%s_plate" % key, cv.array())


def model_mesh(key):
    v = VEHICLES[key]
    if v.get("builder"):
        return v["builder"]()
    return car_mesh(key)


def car_mesh(key):
    from decor.geom import Mesh
    v = VEHICLES[key]
    B = v["body"]
    m = B.mesh()
    for (z, r) in v["wheels"]:
        for s in (1, -1):
            x = s * (B.half(z) + 0.012 - v["wheel_w"] / 2)
            wheel(m, r, v["wheel_w"], x, z, "veh_rim_" + v["rim"], side=s)
    if v.get("mirror"):
        zm, ym, _ = v["mirror"]
        for s in (1, -1):
            x0 = B.half(zm) - 0.02
            xa, xb = (x0, x0 + 0.17) if s > 0 else (-x0 - 0.17, -x0)
            boxm(m, xa, xb, ym, ym + 0.11, zm - 0.06, zm, {"+z": "veh_%s_paint" % key, "-z": "veh_mirror_glass",
                 "+x": "veh_%s_paint" % key, "-x": "veh_%s_paint" % key, "+y": "veh_%s_paint" % key, "-y": "veh_trim"})
    if v.get("extras"):
        v["extras"](m, B)
    return m


def cbox_m(B, h=None):
    W, L = B.W, B.L
    H = h or B.H
    return ((-W / 2 * M, 0, -L / 2 * M), (W / 2 * M, H * M, L / 2 * M))


vehicle("panda141_rossa", **panda141((168, 26, 30), "AL 482 KD", "panda141_rossa"))
vehicle("panda_bianca", **panda3((232, 232, 228), "FG 715 RM", "panda_bianca"))
vehicle("punto_grigia", **punto((150, 154, 158), "EM 203 TP", "punto_grigia"))
vehicle("ypsilon_blu", **ypsilon((26, 40, 78), "GA 368 BN", "ypsilon_blu"))


def carabinieri(key):
    """Fiat Grande Punto of the Carabinieri: dark blue, red stripe along the flanks, white lettering, blue light bar
    painted on the roof (12/11/2026, for the road block of the prologue)."""
    global modern
    blue, red, white = (10, 18, 46), (196, 22, 30), (236, 236, 236)
    plain = modern

    def liveried(k, colour, plate_txt, spec, wheels, wheel_w, rim, sidep, frontp, rearp, topp=None, mirror=None, extras=None):
        def side(cv):
            cv.rect(-1.95, 0.76, 1.55, 0.83, fill=red)
            cv.text(-1.05, 0.50, "CARABINIERI", white, 0.17)

        def front(cv):
            frontp(cv)
            cv.rect(-0.80, 0.63, 0.80, 0.67, fill=red)

        def rear(cv):
            rearp(cv)
            cv.rect(-0.80, 0.80, 0.80, 0.85, fill=red)

        def top(cv):
            cv.rect(-0.55, -0.45, 0.55, -0.20, fill=(30, 70, 235))
            cv.rect(-0.12, -0.45, 0.12, -0.20, fill=white)
        return plain(k, colour, plate_txt, spec, wheels, wheel_w, rim, dict(sidep, post=side), front, rear, topp=top,
                     mirror=mirror, extras=extras)
    modern = liveried
    try:
        return punto(blue, "CC DH 418", key)
    finally:
        modern = plain


vehicle("punto_carabinieri", **carabinieri("punto_carabinieri"))
vehicle("cinquecento_azzurra", **cinquecento((132, 176, 200), "FK 954 ME", "cinquecento_azzurra"))
vehicle("daily_bianco", **daily((236, 236, 232), "GB 541 ZT", "daily_bianco"))
vehicle("camper", **camper("camper"))
vehicle("ape", **ape((138, 158, 170), "ape"))
vehicle("vespa_rossa", **vespa((176, 22, 26), "vespa_rossa"))
vehicle("vespa_crema", **vespa((226, 214, 184), "vespa_crema"))
