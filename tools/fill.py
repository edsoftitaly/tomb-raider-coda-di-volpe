"""Last pass before saving: every wall, floor or ceiling face that exists and has no texture takes the texture
of the nearest textured face (same sector first, then the neighbours, then anything of its kind in the room).
A stretched texture is better than a hole. Faces marked invisible (portals, sky) are left alone."""
import prj2
from kit import DIRS

FLOORS = (prj2.F_FLOOR, prj2.F_FLOOR_TRI2)
CEILS = (prj2.F_CEILING, prj2.F_CEILING_TRI2)


def _wanted(room, lx, lz):
    s = room.sectors[lx][lz]
    border = lx in (0, room.nx - 1) or lz in (0, room.nz - 1)
    out = []
    if border:
        return out
    if not s.wall:
        out.append(("f", prj2.F_FLOOR))
        if len(set(s.floor)) > 1:
            out.append(("f", prj2.F_FLOOR_TRI2))
        if not room.outside:
            out.append(("c", prj2.F_CEILING))
            if len(set(s.ceil)) > 1:
                out.append(("c", prj2.F_CEILING_TRI2))
    for d, (oi, pi, (dx, dz)) in DIRS.items():
        o = room.sectors[lx + dx][lz + dz]
        if o.wall:
            continue
        nbf = (o.floor[pi[0]], o.floor[pi[1]])
        nbc = (o.ceil[pi[0]], o.ceil[pi[1]])
        tops = [(s.floor[oi[0]], s.floor[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in (s.fsplits or [])]
        for i, top in enumerate(tops):
            bot = nbf
            if i + 1 < len(tops) and tops[i + 1][0] >= nbf[0] and tops[i + 1][1] >= nbf[1]:
                bot = tops[i + 1]
            if top[0] > bot[0] or top[1] > bot[1]:
                out.append(("w", prj2.f_wall_floor(d, i)))
        if s.wall:
            lo = (max(s.floor[oi[0]], nbf[0]), max(s.floor[oi[1]], nbf[1]))
            hi = (min(s.ceil[oi[0]], nbc[0]), min(s.ceil[oi[1]], nbc[1]))
            if hi[0] > lo[0] or hi[1] > lo[1]:
                out.append(("w", prj2.F_WALL_MIDDLE[d]))
        if room.outside:
            continue
        bots = [(s.ceil[oi[0]], s.ceil[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in (s.csplits or [])]
        for i, bot in enumerate(bots):
            top = nbc
            if i + 1 < len(bots) and bots[i + 1][0] <= nbc[0] and bots[i + 1][1] <= nbc[1]:
                top = bots[i + 1]
            if top[0] > bot[0] or top[1] > bot[1]:
                out.append(("w", prj2.f_wall_ceiling(d, i)))
    return out


def _kind(face):
    return "f" if face in FLOORS else "c" if face in CEILS else "w"


def fill_missing(level):
    total = 0
    for room in level.rooms:
        if not room.sectors:
            continue
        any_of = {}
        for col in room.sectors:
            for s in col:
                for face, t in (s.tex or {}).items():
                    any_of.setdefault(_kind(face), t)
        for lx in range(1, room.nx - 1):
            for lz in range(1, room.nz - 1):
                s = room.sectors[lx][lz]
                for kind, face in _wanted(room, lx, lz):
                    if (s.tex and face in s.tex) or (s.invisible and face in s.invisible):
                        continue
                    src = None
                    for cand in [s] + [room.sectors[lx + a][lz + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))]:
                        for f2, t in (cand.tex or {}).items():
                            if _kind(f2) == kind:
                                src = t
                                break
                        if src:
                            break
                    src = src or any_of.get(kind)
                    if src is None:
                        continue
                    if s.tex is None:
                        s.tex = {}
                    coords = src[0]
                    if kind != "w" and len(coords) == 4 and face in (prj2.F_FLOOR_TRI2, prj2.F_CEILING_TRI2):
                        coords = coords[:3]
                    s.tex[face] = (coords, src[1], src[2])
                    total += 1
    return total
