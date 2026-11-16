"""The secrets become a thing to find: a Star of the Dioscuri (PUZZLE_ITEM16, a silver copy of the star of Castor in
a wad of its own) lies at every secret place, and the secret is found when Lara picks it up.

  segreto.py wad <CdV_Oggetti.wad2> <out CdV_Segreto.wad2>
  segreto.py level <name> <in.prj2> <in.lua> <out.prj2> <out.lua>
  segreto.py gameflow <in.lua> <out.lua>

level: one star per CDV.Secret of the script, on the floor of the room at that place; when a static or another pickup
is on the very spot the star goes beside it, and the secret's coordinates in the script follow it."""
import math
import re
import struct
import sys
import zlib

import numpy as np

import wadtool as W

SRC, SLOT = 506, 515
WAD = "CdV_Segreto.wad2"


def wad(src, dst):
    import turi as T
    top = W.load(src)
    tex = T.textures(top)
    mov = [p for mid, p in W.moveables(top) if mid == SRC][0]
    _, q = W._leb_u(mov, 0)
    subs = W._chunks(mov, q, len(mov))
    used = set()
    for c, p in subs:
        if c == b"W2Mesh":
            for c2, p2 in W._chunks(p, 0, len(p)):
                if c2 == b"W2Polys":
                    for pc, pp in W._chunks(p2, 0, len(p2)):
                        k = 4 if pc == b"W2Uq2" else 3
                        qq = 0
                        for _ in range(k + 1):
                            _, qq = W._leb_u(pp, qq)
                        used.add(W._leb_u(pp, qq)[0])
    order = sorted(used)
    pages = {old: new for new, old in enumerate(order)}
    tchunks = []
    for old in order:
        w, h, ts = tex[old]
        a = np.frombuffer(dict(ts)[b"W2TxtData"], np.uint8).reshape(h, w, 4).astype(np.float32)      # BGRA
        grey = a[..., :3].mean(axis=2, keepdims=True)
        rgb = np.clip(grey * np.array([1.18, 1.08, 1.0], np.float32) + 22, 0, 255)                # silver, a little cold
        data = np.concatenate([rgb, a[..., 3:]], axis=2).astype(np.uint8).tobytes()
        tchunks.append(T.tex_chunk(w, h, [(c, data if c == b"W2TxtData" else p) for c, p in ts]))
    body = [(c, T.remap_mesh(p, pages) if c == b"W2Mesh" else p) for c, p in subs]
    out = []
    for cid, payload in top:
        if cid == b"W2Textures":
            out.append((cid, T.pack(tchunks)))
        elif cid == b"W2Moveables":
            out.append((cid, T.pack([(b"W2Moveable", W._leb_enc(SLOT) + T.pack(body))])))
        elif cid == b"W2Statics":
            out.append((cid, b"\x00"))
        else:
            out.append((cid, payload))
    data = zlib.compress(T.pack(out), 9)
    open(dst, "wb").write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    print(WAD, "%d texture pages, %d bytes" % (len(tchunks), len(data) + 12))


OLD_LOOP = '''    for _, s in ipairs(secrets) do
        if not S.secrets["s" .. s.index] and CDV.Near(s.x, s.y, s.z, s.r, 1024) then
            S.secrets["s" .. s.index] = true
            TEN.Flow.AddSecret(s.index)
            CDV.Cue("segreto")
            CDV.Say(s.text or "", 5)
            if s.give then CDV.Give(s.give, 1) end
        end
    end
'''
NEW_LOOP = '''    -- A secret is a Star of the Dioscuri lying at its place ("stella_<index>", PUZZLE_ITEM16): it is found when she
    -- picks the star up. The star goes out of the inventory at once; until then it glimmers when she is near.
    -- In a level compiled without the stars a secret is still found by walking onto its place.
    local stars = false
    for _, s in ipairs(secrets) do
        if CDV.M("stella_" .. s.index) ~= nil then stars = true end
    end
    local function found(s)
        S.secrets["s" .. s.index] = true
        TEN.Flow.AddSecret(s.index)
        CDV.Cue("segreto")
        CDV.Say(s.text or "", 5)
        if s.give then CDV.Give(s.give, 1) end
    end
    if stars then
        local lp = Lara:GetPosition()
        local ok, got = pcall(TEN.Inventory.GetItemCount, ID.PUZZLE_ITEM16)
        if ok and got ~= nil and got > 0 then
            pcall(TEN.Inventory.TakeItem, ID.PUZZLE_ITEM16, got)
            local best, bd = nil, 1e18
            for _, s in ipairs(secrets) do
                local d = (lp.x - s.x) ^ 2 + (lp.y - s.y) ^ 2 + (lp.z - s.z) ^ 2
                if not S.secrets["s" .. s.index] and d < bd then best, bd = s, d end
            end
            if best ~= nil then found(best) end
        end
        CDV.starTick = (CDV.starTick or 0) + 1
        for _, s in ipairs(secrets) do
            if not S.secrets["s" .. s.index] and math.abs(lp.x - s.x) < 10240 and math.abs(lp.z - s.z) < 10240 then
                local k = 0.6 + 0.4 * math.sin(CDV.starTick / 9)
                pcall(function()
                    TEN.Effects.EmitLight(TEN.Vec3(s.x, s.y - 160, s.z), TEN.Color(math.floor(210 * k), math.floor(225 * k), math.floor(255 * k)), 5, false, "cdv_stella_" .. s.index)
                end)
            end
        end
    else
        for _, s in ipairs(secrets) do
            if not S.secrets["s" .. s.index] and CDV.Near(s.x, s.y, s.z, s.r, 1024) then found(s) end
        end
    end
'''
ALT = ("_ACQUA", "_BUIO", "_PIENO", "_ASCIUTTO")


def level(name, src, lua, dst, dst_lua):
    import nemici_audit as A
    import prj2_patch as P
    import tindari_pm as TP
    w = A.World(src)
    obs = P.objects(src)
    world = [(w.rooms[o[0]][2][0] * 1024 + o[3][0], w.rooms[o[0]][2][1] + o[3][1], w.rooms[o[0]][2][2] * 1024 + o[3][2], o) for o in obs]
    s = open(lua, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    raw = P.raw_objects(src)
    next_id = max(P.Reader(op).leb() if hasattr(P, "Reader") else A.Reader(op).leb() for _, _, op in raw) + 1
    proto = [(oc, op) for _, oc, op in raw if oc in (b"TeMovTn3", b"TeMovTen2")][0]
    add = {}

    def busy(x, y, z):
        return [o for ox, oy, oz, o in world if math.hypot(ox - x, oz - z) < 380 and abs(oy - y) < 900 and "stella_" not in o[5]]

    def floor_at(x, y, z):
        for f, c, rn, walk, slope in w.cols.get((int(x // 1024), int(z // 1024)), []):
            if abs(f - y) <= 96 and not rn.endswith(ALT) and slope <= 256:
                return rn, f
        return None

    def place(m):
        nonlocal next_id
        i, x, ly, z = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        y = -ly
        spots = [(x, z)] + [(x + dx, z + dz) for d in (440, 620) for dx, dz in ((d, 0), (-d, 0), (0, d), (0, -d), (d, d), (-d, d), (d, -d), (-d, -d))]
        for px, pz in spots:
            fl = floor_at(px, y, pz)
            if fl and not busy(px, fl[1], pz):
                rn, f = fl
                rp = w.rooms[rn][2]
                oc, op = proto
                op = TP.rename(op, "stella_%d" % i, (px - rp[0] * 1024, f - rp[1], pz - rp[2] * 1024), next_id)
                r = A.Reader(op); r.leb(); a = r.s.tell()
                o, _ = P.mov_type(op)
                op = op[:a + 12] + bytes(12) + op[a + 24:o] + struct.pack("<Ih", SLOT, 0) + op[o + 6:]
                next_id += 1
                add.setdefault(rn, []).append((oc, op))
                print("  secret %d: star in %s at %.2f, %.2f%s" % (i, rn, px / 1024, pz / 1024, "" if (px, pz) == (x, z) else "  (moved off %s)" % ", ".join(sorted({o[5] or str(o[2]) for o in busy(x, y, z)}))))
                return "CDV.Secret({ index = %d, x = %d, y = %d, z = %d," % (i, px, -int(round(f)), pz)
        raise SystemExit("no place for secret %d" % i)
    t, n = re.subn(r"CDV\.Secret\(\{ index = (\d+), x = (-?\d+), y = (-?\d+), z = (-?\d+),", place, t)
    assert n >= 1 and t.count(OLD_LOOP) == 1
    t = t.replace(OLD_LOOP, NEW_LOOP)
    head, top = P.load(src)
    d = dict(top)
    rooms = d[b"TeRooms"]
    for rn, chunks in add.items():
        rooms = P.add_objects(rooms, rn, chunks)
    settings = P.add_wad(d[b"TeSettings"], WAD)
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])
    open(dst_lua, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print(name, n, "stars")


def gameflow(src, dst):
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    for old, new in (
            ("Flow.SetTotalSecretCount(10)", "Flow.SetTotalSecretCount(12)"),
            ('    cdv_astro_castore = { "Star of Castor" },\n', '    cdv_astro_castore = { "Star of Castor" },\n    cdv_stella = { "Star of the Dioscuri" },\n'),
            ('        TEN.Flow.InventoryItem("cdv_astro_castore", ID.PUZZLE_ITEM7, 0, 1.80, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),\n',
             '        TEN.Flow.InventoryItem("cdv_astro_castore", ID.PUZZLE_ITEM7, 0, 1.80, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),\n'
             '        TEN.Flow.InventoryItem("cdv_stella", ID.PUZZLE_ITEM16, 0, 1.80, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),\n')):
        assert t.count(old) == 1, old
        t = t.replace(old, new)
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print("gameflow ok")


if __name__ == "__main__":
    {"wad": wad, "level": level, "gameflow": gameflow}[sys.argv[1]](*sys.argv[2:])
