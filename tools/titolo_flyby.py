"""The title level as a flight over the places of the adventure: the rooms of the four levels put side by side in one
project (no enemies, no pickups, no scripts) and one looping flyby (sequence 0) that cuts from place to place.

  titolo_flyby.py <dir with Oliveri/Marinello/Tindari/Sommersa/Title .prj2> <wad dir> <out Title.prj2>

Every level keeps its own textures (the texture list is the union, faces are re-indexed) and its own statics and
furniture. The wads are the union in an order that gives every kept object the same model it has in its level;
objects that would get another model are left out and counted. The cameras are in SHOTS (world units of the level
they belong to). Title.lua (titolo_lua below) changes sky and fog when the flight cuts to another place."""
import json
import os
import re
import struct
import sys

import prj2
import prj2_patch as P
import wadtool
from prj2_check import Reader

# level, prefix of its rooms in the title, offset in sectors (x, z)
LEVELS = [("Tindari", "T_", (0, 0)), ("Marinello", "M_", (0, 130)), ("Oliveri", "O_", (130, 130)), ("Sommersa", "S_", (130, 200))]
# wads whose objects only make sense in play (enemies, traps, emitters)
DROP = ("CdV_Mafiosi", "CdV_Turi", "TR4_Baddy", "TR2_Doberman", "TR1_Rat", "TR4_Bat", "TEN_Wraith", "TR5_Lagoon_Witch",
        "TR2_Shark", "TR4_Skeleton", "TR4_Rolling_Ball", "TR1_Teeth_Spikes", "TEN_Fish_Emitter", "TEN_Firefly",
        "TEN_Pole", "TR4_rope")
BASE_WAD = "TombEngine.wad2"
LARA = ("Marinello", "lara_start")          # the hidden Lara of the title stands where Marinello starts

HIDE, LOOP, CUT_PAN, CUT_TO, FADE_IN, FADE_OUT = 16, 4, 1, 128, 4096, 8192


def rleb(r):
    return r.leb()


def wad_ids(path):
    mv, st = [], []
    for cid, p in wadtool.load(path):
        if cid in (b"W2Moveables", b"W2Statics"):
            for _, p2 in wadtool._chunks(p, 0, len(p)):
                (mv if cid == b"W2Moveables" else st).append(wadtool._leb_u(p2, 0)[0])
    return set(mv), set(st)


def wad_names(settings):
    return [m.decode().split("\\")[-1] for m in re.findall(rb"[\w\\/.$() -]+\.wad2", dict(P.chunks(settings)[0])[b"TeWads"])]


def resolve(names, ids):
    mo, so = {}, {}
    for n in names:
        if n in ids:
            for k in ids[n][0]:
                mo.setdefault(k, n)
            for k in ids[n][1]:
                so.setdefault(k, n)
    return mo, so


def tex_key(chunk_payload):
    return dict(P.chunks(chunk_payload)[0])[b"TePath"].decode("utf-8", "replace").split("\\")[-1].lower()


def blank_name(oc, op):
    """The object chunk with its Lua name emptied (names must be unique in a level)."""
    r = Reader(op)
    r.leb()
    if oc in (b"TeMovTn3", b"TeMovTen2"):
        r.raw(24); r.leb(); r.raw(4 + 2 + 3 + 12)
    else:
        r.raw(28); r.leb(); r.raw(4 + 12 + 2)
    q = r.s.tell()
    n = struct.unpack_from("<i", op, q)[0]
    return op[:q] + struct.pack("<i", 0) + op[q + 4 + n:]


def obj_type(oc, op):
    r = Reader(op)
    r.leb()
    r.raw(24 if oc in (b"TeMovTn3", b"TeMovTen2") else 28)
    r.leb()
    return struct.unpack("<I", r.raw(4))[0]


def reid(op, off):
    r = Reader(op)
    i = r.leb()
    return prj2.leb(i + off) + op[r.s.tell():], i


def merge(src_dir, wad_dir, cams, log=print):
    ids = {}
    levels = []
    for name, prefix, off in LEVELS:
        head, top = P.load(os.path.join(src_dir, name + ".prj2"))
        d = dict(top)
        names = wad_names(d[b"TeSettings"])
        for n in names:
            f = os.path.join(wad_dir, n)
            if n not in ids and os.path.exists(f):
                ids[n] = wad_ids(f)
        levels.append((name, prefix, off, d, names))
    union = [BASE_WAD]
    for name, prefix, off, d, names in levels:
        for n in names:
            if n not in union and not n.startswith(DROP):
                union.append(n)
    umo, uso = resolve(union, ids)

    # textures: union by file name
    tex_chunks, tex_index = [], {}
    remaps = []
    for name, prefix, off, d, names in levels:
        st = dict(P.chunks(d[b"TeSettings"])[0])
        remap = {}
        for c, p in P.chunks(st[b"TeTextures"])[0]:
            sub = P.chunks(p)[0]
            old = Reader(dict(sub)[b"TeI"]).leb()
            k = tex_key(p)
            if k not in tex_index:
                tex_index[k] = len(tex_chunks)
                tex_chunks.append((c, [(a, b) for a, b in sub]))
            remap[old] = tex_index[k]
        remaps.append(remap)
    textures = P.pack([(c, P.pack([(a, prj2.leb(i) if a == b"TeI" else b) for a, b in sub])) for i, (c, sub) in enumerate(tex_chunks)])

    out_rooms, room_base, obj_base, lara = [], 0, 0, None
    stats = {}
    for li, (name, prefix, off, d, names) in enumerate(levels):
        lmo, lso = resolve(names, ids)
        rooms = P.chunks(d[b"TeRooms"])[0]
        idx = {}
        for c, p in rooms:
            r = Reader(p); r.leb(); r.leb()
            idx[Reader(dict(P.chunks(p[r.s.tell():])[0])[b"TeI"]).leb()] = room_base + len(idx)
        max_id = 0
        kept = dropped = 0
        for c, p in rooms:
            r = Reader(p)
            nx, nz = r.leb(), r.leb()
            hd = p[:r.s.tell()]
            items = P.chunks(p[r.s.tell():])[0]
            new = []
            rname = dict(items)[b"TeName"].decode("utf-8", "replace")
            for a, b in items:
                if a == b"TeI":
                    b = prj2.leb(idx[Reader(b).leb()])
                elif a == b"TeName":
                    b = (prefix + rname).encode()
                elif a == b"TePos2":
                    x, y, z = struct.unpack("<3f", b)
                    b = struct.pack("<3f", x + off[0], y, z + off[1])
                elif a == b"TeAlternate":
                    sub = P.chunks(b)[0]
                    b = P.pack([(k, prj2.leb(Reader(v).leb() + 16 * li) if k == b"TeGroup" else prj2.leb(idx[Reader(v).leb()])) for k, v in sub])
                elif a == b"TeSecs":
                    secs = []
                    for sc, sp in P.chunks(b)[0]:
                        sub = []
                        for k, v in P.chunks(sp[4:])[0]:
                            if k == prj2.cid(prj2.TEX_LEVEL2):
                                rr = Reader(v)
                                rr.leb()
                                n = 4 if len(v) - rr.s.tell() >= 50 else 3
                                rr.raw(8 * n + 16)
                                q = rr.s.tell()
                                mode, tex = rr.leb(), rr.leb()
                                v = v[:q] + prj2.leb(mode) + prj2.leb(remaps[li][tex]) + v[rr.s.tell():]
                            sub.append((k, v))
                        secs.append((sc, sp[:4] + P.pack(sub)))
                    b = P.pack(secs)
                elif a == b"TeObjects":
                    obs = []
                    for oc, op in P.chunks(b)[0]:
                        op, old_id = reid(op, obj_base)
                        max_id = max(max_id, old_id)
                        if oc == b"TePor2":
                            rr = Reader(op)
                            v = [rr.leb() for _ in range(6)]
                            v[5] = idx[v[5]]
                            op = b"".join(prj2.leb(x) for x in v) + op[rr.s.tell():]
                        elif oc.startswith(b"TeLig"):
                            pass
                        elif oc in (b"TeMovTn3", b"TeMovTen2"):
                            t = obj_type(oc, op)
                            if (name, None) == (LARA[0], None) and t == 0 and LARA[1].encode() in op:
                                lara = True
                                op = blank_name(oc, op)
                            elif t not in lmo or lmo[t] == BASE_WAD or lmo[t].startswith(DROP) or umo.get(t) != lmo[t]:
                                dropped += 1
                                continue
                            else:
                                op = blank_name(oc, op)
                        elif oc in (b"TeStaTn3", b"TeStaTen2"):
                            t = obj_type(oc, op)
                            if t not in lso or uso.get(t) != lso[t]:
                                dropped += 1
                                continue
                            op = blank_name(oc, op)
                        else:                      # flyby cameras of the level and anything else
                            continue
                        kept += 1
                        obs.append((oc, op))
                    b = obs
                new.append((a, b))
            out_rooms.append([name, rname, hd, new])
        stats[name] = (len(rooms), kept, dropped)
        room_base += len(rooms)
        obj_base += max_id + 1
    assert lara, "no Lara"
    next_id = [obj_base]
    for room in out_rooms:
        name, rname, hd, items = room
        extra = []
        for body in cams.get((name, rname), []):
            extra.append((b"TeFly3", prj2.leb(next_id[0]) + body))
            next_id[0] += 1
        room[3] = [(a, P.pack(b + extra) if a == b"TeObjects" else b) for a, b in items]
    rooms_payload = P.pack([(b"TeRoom", hd + P.pack(items)) for _, _, hd, items in out_rooms])
    log("rooms/kept/dropped objects:", stats, "textures", len(tex_chunks), "wads", len(union))
    return union, textures, rooms_payload


def settings(title_settings, union, textures, like_settings):
    items = P.chunks(title_settings)[0]
    like = dict(P.chunks(like_settings)[0])
    wc = P.chunks(like[b"TeWads"])[0]
    proto = [(c, p) for c, p in wc if b"CdV_Oggetti.wad2" in p][0]
    wads = []
    for n in union:
        if n == BASE_WAD:
            wads.append([(c, p) for c, p in wc if b"\\" + BASE_WAD.encode() in p][0])
        else:
            wads.append((proto[0], P.pack([(k, v.replace(b"CdV_Oggetti.wad2", n.encode())) for k, v in P.chunks(proto[1])[0]])))
    out = []
    for c, p in items:
        if c == b"TeWads":
            p = P.pack(wads)
        elif c == b"TeTextures":
            p = textures
        elif c in (b"TeSelectedSounds", b"TeSoundsCatalogs", b"TeDefaultAmbientLight"):
            p = like[c]
        elif c == b"TeLastRoom":
            p = prj2.leb(0)
        out.append((c, p))
    return P.pack(out)


def fly(pos, yaw, pitch, number, speed=1.0, fov=80.0, flags=0, timer=0, seq=0):
    """Body of a TeFly3 chunk without the object id. pos room-local (Y up), yaw 0 = +Z (north), pitch > 0 looks up."""
    b = struct.pack("<3f", *pos) + struct.pack("<3f", yaw % 360.0, max(-89.0, min(89.0, pitch)), 0.0)
    b += prj2.leb(-1) + struct.pack("<2f", speed, fov) + prj2.leb(flags) + prj2.leb(number) + prj2.leb(seq) + prj2.leb(timer)
    return b + bytes(16)


# ---------------------------------------------------------------------------------------------- the flight
# (level, seconds per leg, [(x, z in sectors, y in clicks above zero), ...], look-at (x, z, y) or None = existing cameras)
SHOTS = [
    ("Oliveri", 6.0, [(84, 21, 15), (68, 21, 13), (52, 21, 12), (39, 22, 11)], (28, 27, 12)),
    ("Marinello", 6.0, [(100, 80, 17), (90, 71, 14), (82, 63, 12), (77, 59, 11)], (66, 50, 6)),
    ("Marinello", 6.0, [(92, 32, 8), (86, 35, 8), (81, 38, 8), (77, 40, 8)], (60, 56, 6)),
    ("Tindari", 6.0, [(111, 60, 104), (115, 59, 105), (119, 58, 106), (122, 57, 107)], (150, 50, 135)),
    ("Tindari", 6.0, [(62, 100, 113), (55, 96, 111), (49, 92, 110), (45, 89, 109)], (40, 76, 104)),
    ("Tindari", 6.5, [(174, 64, 132), (181, 70, 126), (188, 77, 118), (194, 83, 110)], (150, 50, 140)),
    ("Sommersa", 5.0, "D_DECUMANO", None),
]
SOMMERSA_CAMS = [(3072, 900, 6144), (9216, 1500, 10752), (15360, 1300, 8704), (18432, 1100, 8704)]


def find_room(rooms, x, y, z):
    """(room name, local position) of the world point: an open-air room whose sector there has air at that height."""
    best = None
    for rn, (nx, nz, pos, g) in rooms.items():
        if not rn.startswith("T_") or rn.endswith(("_PIENO", "_ASCIUTTO")):
            continue
        lx, lz = x / 1024.0 - pos[0], z / 1024.0 - pos[2]
        if not (1 <= lx < nx - 1 and 1 <= lz < nz - 1):
            continue
        props, fl, ce, _ = g[(int(lx), int(lz))]
        if fl is None or ce is None or props & 1:
            continue
        ce = [c + 65536 if c < 0 else c for c in ce]
        if pos[1] + max(fl) + 384 <= y <= pos[1] + min(ce) - 384:
            best = (rn, (x - pos[0] * 1024, y - pos[1], z - pos[2] * 1024))
    return best


def cameras(src_dir, log=print):
    import math
    import appoggio
    cams, number = {}, 0
    plan = []
    for level, secs, pts, look in SHOTS:
        rooms = appoggio.rooms_of(os.path.join(src_dir, level + ".prj2"))
        if look is None:
            w = [(pts, p, 90.0, 0.0) for p in SOMMERSA_CAMS]
        else:
            w = []
            world = [(x * 1024.0, y * 256.0, z * 1024.0) for x, z, y in pts]
            for p in world:
                tx, ty, tz = look[0] * 1024.0, look[2] * 256.0, look[1] * 1024.0
                dx, dy, dz = tx - p[0], ty - p[1], tz - p[2]
                yaw = math.degrees(math.atan2(dx, dz))
                pitch = math.degrees(math.atan2(dy, math.hypot(dx, dz)))
                w.append((None, p, yaw, pitch))
        # two guards past the last camera: the cut happens on reaching the first, the second only shapes the curve
        (r1, a, yw, pt), (r0, b, _, _) = w[-1], w[-2]
        step = [(a[i] - b[i]) * 0.12 for i in range(3)]
        for k in (1, 2):
            w.append((r1, tuple(a[i] + step[i] * k for i in range(3)), yw, pt))
        if look is not None:                                     # the whole path must stay in the air of the rooms
            for (_, a, _, _), (_, b, _, _) in zip(w, w[1:]):
                for i in range(41):
                    q = tuple(a[j] + (b[j] - a[j]) * i / 40.0 for j in range(3))
                    assert find_room(rooms, *q), ("path leaves the rooms", level, [round(v / 1024, 1) for v in q])
        plan.append((level, rooms, secs, w))
    first = []
    n = 0
    for level, rooms, secs, w in plan:
        first.append(n)
        n += len(w)
    for si, (level, rooms, secs, w) in enumerate(plan):
        speed = 100.0 / (secs * 30.0)
        for k, (room, p, yaw, pitch) in enumerate(w):
            if room is None:
                found = find_room(rooms, *p)
                assert found, ("camera outside the rooms", level, [v / 1024 for v in p])
                room, local = found
            else:
                local = p
            flags, timer, sp = HIDE, 0, speed
            if number == 0:
                flags |= CUT_PAN | LOOP
            if k == 1:
                flags |= FADE_IN
            if k == len(w) - 2:                                  # first guard: fade to black, then cut to the next place
                flags |= FADE_OUT | CUT_TO
                timer = first[(si + 1) % len(plan)]
                sp = 4.0
            if k == len(w) - 1:
                sp = 4.0
            cams.setdefault((level, room), []).append(fly(local, yaw, pitch, number, speed=sp, flags=flags, timer=timer))
            log("cam %2d %-9s %-12s %s yaw %4.0f pitch %4.0f flags %5d timer %d" % (number, level, room, [round(v) for v in local], yaw, pitch, flags, timer))
            number += 1
    return cams


def main():
    src_dir, wad_dir, out = sys.argv[1:4]
    cams = cameras(src_dir)
    union, textures, rooms_payload = merge(src_dir, wad_dir, cams)
    head, top = P.load(os.path.join(src_dir, "Title.prj2"))
    _, like = P.load(os.path.join(src_dir, "Tindari.prj2"))
    st = settings(dict(top)[b"TeSettings"], union, textures, dict(like)[b"TeSettings"])
    P.save(out, head, [(b"TeSettings", st), (b"TeRooms", rooms_payload)])
    print("wads:", ", ".join(union))
    print(out, os.path.getsize(out))


if __name__ == "__main__":
    main()
