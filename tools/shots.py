"""Trailer shots: flyby sequences placed in every level for recording (riprese mode).

Coordinates are world sectors (x, z); heights are metres above the local ground (roofs included).
Each shot becomes flyby sequence 1, 2, 3... of its level; the title level gets sequence 0 (looping).
Cameras hide Lara and cut straight in (no pan from Lara's camera). Speed is computed per camera so the
camera moves at about `v` metres per second (TEN: per-segment progress = speed * 655 / 65535 per frame).
"""
import json
import math
import os

import numpy as np

import prj2

SECTOR = 1024
M = 512                      # units per metre
CLEAR = 1.2 * M              # minimum clearance over the ground along the path
CEIL_MARGIN = 160            # stay below room ceilings

# Flyby flags (TombEngine spotcam.h)
CUT_PAN, LOOP, HIDE_LARA = 1, 4, 16

SHOTS = {
    "Oliveri": [
        dict(name="Sui tetti di Oliveri", v=2.0, fov=70,
             path=[(186, 140, 4), (196, 150, 4), (204, 157, 5), (208, 160, 8)],
             look=[(205, 158, 6), (209, 161, 6), (212, 164, 7), (214, 166, 8)],
             note="Si scivola tra le case verso Via Gaspare Amodeo 1: apertura del gioco."),
        dict(name="Il castello", v=3.0, fov=70,
             path=[(78, 52, 14), (72, 72, 15), (56, 84, 15), (34, 82, 14)],
             look=[(45, 44, 10)],
             note="Giro attorno al castello e alle mura."),
        dict(name="Gli uliveti", v=1.6, fov=75,
             path=[(40, 190, 2.2), (45, 215, 2.4), (50, 240, 2.6), (55, 265, 2.8)],
             look=[(42, 205, 2.0), (47, 230, 2.2), (52, 255, 2.4), (57, 280, 2.6)],
             note="Passaggio basso tra i filari di ulivi."),
    ],
    "Lungomare": [
        dict(name="Il lungomare all'alba", v=4.0, fov=70,
             path=[(325, 120, 3), (305, 150, 3), (285, 180, 3), (265, 205, 3)],
             look=[(300, 160, 3), (280, 190, 3), (260, 215, 3), (245, 235, 3)],
             note="Lungo la passeggiata con i lampioni a due bracci."),
        dict(name="Le barche", v=2.5, fov=65,
             path=[(236, 290, 2.5), (233, 315, 2.5), (229, 340, 2.5)],
             look=[(190, 320, 5)],
             note="Radente sull'acqua tra le barche ormeggiate, il paese sullo sfondo."),
    ],
    "Marinello": [
        dict(name="La rupe e i laghetti", v=4.0, fov=65,
             path=[(330, 120, 4), (330, 170, 4), (325, 220, 5), (318, 260, 6)],
             look=[(215, 190, 20)],
             note="Dal mare: la rupe di Tindari che incombe sui laghetti."),
        dict(name="Il Casello", v=1.8, fov=70,
             path=[(240, 55, 2), (230, 63, 2), (220, 70, 2.5)],
             look=[(203, 72, 4)],
             note="Avvicinamento al Casello FS."),
        dict(name="La grotta di Donna Villa", v=1.5, fov=70,
             path=[(250, 140, 2), (240, 149, 2), (231, 155, 2.5)],
             look=[(222, 158, 3)],
             note="Verso l'ingresso della grotta, ai piedi della rupe."),
    ],
    "Laghetti": [
        dict(name="Dal mare verso la rupe", v=4.0, fov=65,
             path=[(120, 362, 4), (170, 356, 4), (220, 346, 4)],
             look=[(60, 150, 30)],
             note="Dal largo: i laghetti e la rupe di Tindari."),
        dict(name="La lingua di sabbia", v=2.5, fov=70,
             path=[(335, 120, 2.5), (340, 160, 2.5), (338, 200, 3)],
             look=[(150, 120, 20)],
             note="Sulla lingua di sabbia dove aspetta la banda, la rupe sullo sfondo."),
    ],
    "Tindari": [
        dict(name="Il teatro greco", v=1.5, fov=75,
             path=[(42, 350, 4), (52, 354, 5), (64, 350, 4)],
             look=[(58, 338, 1)],
             note="Dalla cavea verso l'orchestra (la botola dell'enigma)."),
        dict(name="Rocca Femmina", v=1.5, fov=70,
             path=[(245, 215, 2), (255, 222, 2.5), (262, 230, 3)],
             look=[(300, 320, 0)],
             note="Dal ciglio della rupe: la lingua di sabbia e i laghetti (luna, stella, sole)."),
        dict(name="Il parco archeologico", v=2.0, fov=70,
             path=[(110, 310, 4), (125, 312, 4), (136, 302, 4)],
             look=[(122, 296, 3)],
             note="Tra le rovine: Basilica e Torre."),
    ],
}

# Title level (built from the Tindari terrain): slow endless loop on the edge of the cape, over the Laghetti.
TITLE = dict(name="Titolo", v=1.0, fov=65, loop=True,
             path=[(245, 215, 3), (253, 221, 3.5), (260, 229, 4), (254, 236, 4), (246, 229, 3.5)],
             look=[(300, 320, 0), (318, 338, 0), (300, 352, 0), (282, 330, 0), (290, 312, 0)])


def _ground(world, x, z):
    """Highest floor around (x, z), roofs included (units)."""
    x0, x1 = max(0, int(x) - 1), min(world.nx, int(x) + 2)
    z0, z1 = max(0, int(z) - 1), min(world.nz, int(z) + 2)
    return float(world.floor[x0:x1, z0:z1].max())


def _ceil(room, x, z):
    s = room.sectors[int(x) - room.x][int(z) - room.z]
    return room.y + max(s.ceil)


def cameras(ctx, shot):
    """Absolute camera list [(x_units, y_units, z_units, look_xyz)] with clearance and ceiling checks."""
    world, kit = ctx.world, ctx.kit
    pts = []
    for i, (x, z, h) in enumerate(shot["path"]):
        y = _ground(world, x, z) + h * M
        pts.append([x * SECTOR + 512.0, y, z * SECTOR + 512.0])
    # clearance between consecutive cameras: raise both ends until the straight line clears the ground
    for _ in range(4):
        for a, b in zip(pts, pts[1:] + (pts[:1] if shot.get("loop") else [])):
            for t in np.linspace(0, 1, 24):
                px, py, pz = (a[k] + (b[k] - a[k]) * t for k in range(3))
                g = _ground(world, px / SECTOR, pz / SECTOR) + CLEAR
                if py < g:
                    a[1] += g - py
                    b[1] += g - py
    looks = shot["look"]
    out = []
    for i, p in enumerate(pts):
        lx, lz, lh = looks[min(i, len(looks) - 1)]
        ly = _ground(world, lx, lz) + lh * M
        room = kit.room_at(p[0] / SECTOR, p[2] / SECTOR)
        c = _ceil(room, p[0] / SECTOR, p[2] / SECTOR) - CEIL_MARGIN
        if p[1] > c:
            p[1] = c
        g = _ground(world, p[0] / SECTOR, p[2] / SECTOR)
        assert p[1] > g + 256, "%s: camera %d below ground/ceiling (%s)" % (shot["name"], i, p)
        out.append((p, (lx * SECTOR + 512.0, ly, lz * SECTOR + 512.0), room))
    return out


def place(ctx, seq, shot, extra_flags=0):
    level = ctx.level
    cams = cameras(ctx, shot)
    flags = CUT_PAN | HIDE_LARA | extra_flags
    rec = []
    for i, (p, l, room) in enumerate(cams):
        dx, dy, dz = l[0] - p[0], l[1] - p[1], l[2] - p[2]
        rot_y = math.degrees(math.atan2(dx, dz))
        rot_x = math.degrees(math.atan2(dy, math.hypot(dx, dz)))
        nxt = cams[(i + 1) % len(cams)][0] if (shot.get("loop") or i + 1 < len(cams)) else cams[i - 1][0]
        seg_m = max(1.0, math.dist(p, nxt) / M)
        speed = max(0.05, min(4.0, 3.333 * shot["v"] / seg_m))
        rel = (p[0] - room.x * SECTOR, p[1] - room.y, p[2] - room.z * SECTOR)
        level.add_flyby(room, rel, seq, i, rot_y=rot_y, rot_x=rot_x, speed=speed, fov=shot["fov"], flags=flags)
        rec.append({"pos": [p[0], p[1], p[2]], "look": list(l), "room": room.name, "speed": round(speed, 3)})
    return {"seq": seq, "name": shot["name"], "note": shot.get("note", ""), "cams": rec}


def keep_clear(ctx, shot, r=2):
    """Keep decorations out of the camera corridor (cameras ignore static meshes)."""
    block = list(getattr(ctx, "decor_block", []))
    pts = shot["path"]
    for (x0, z0, _), (x1, z1, _) in zip(pts, pts[1:] + ([pts[0]] if shot.get("loop") else [])):
        n = int(max(abs(x1 - x0), abs(z1 - z0))) + 1
        for t in np.linspace(0, 1, n + 1):
            x, z = int(x0 + (x1 - x0) * t), int(z0 + (z1 - z0) * t)
            block.append((x - r, z - r, x + r, z + r))
    ctx.decor_block = block


def place_level(ctx, key):
    if key == "Titolo":
        keep_clear(ctx, TITLE)
        ctx.shots = [place(ctx, 0, TITLE, extra_flags=LOOP)]
        return ctx.shots
    shots = SHOTS.get(key, [])
    for s in shots:
        keep_clear(ctx, s)
    recs = [place(ctx, i + 1, s) for i, s in enumerate(shots)]
    ctx.lua.shots = len(recs)
    ctx.shots = recs
    return recs


def save(ctx, out_dir):
    recs = getattr(ctx, "shots", None)
    if recs:
        with open(os.path.join(out_dir, ctx.key + ".shots.json"), "w") as f:
            json.dump(recs, f, indent=1)
