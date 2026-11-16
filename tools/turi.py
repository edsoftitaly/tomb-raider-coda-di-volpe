"""Turi 'a Vulpi as a mafia boss, and faster than his men (Ed, 16 Nov).

He was the bare-chested masked man with two revolvers (WORKER_DUAL_REVOLVER), like the other gang leaders. Now he is
the man in the pinstripe suit of the Venice gang (the model of GOON_SILENCER1 in CdV_Mafiosi.wad2) without the carnival
mask: his own face, dark glasses, a moustache, a red tie. He goes in a wad of his own, CdV_Turi.wad2, as
GOON_SILENCER3, a slot no one else uses in La meta' sommersa; the level loads that wad first.

Faster: the animations of the model are key frames played one every 3, 4 or 6 game frames. They are played one every
2, 3 or 4 instead, and the speed written in each animation grows by the same factor, so the feet still match the
ground: he runs at 58 units a frame (Lara: 47; his men: 39), walks, turns, aims and shoots half as fast again.

  turi.py <CdV_Mafiosi.wad2> <out CdV_Turi.wad2> [Sommersa.prj2 out.prj2]"""
import math
import struct
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import wadtool as W

SRC_SLOT, SLOT, OLD_SLOT = 152, 154, 158
NEW_RATE = {3: 2, 4: 3, 5: 3, 6: 4, 2: 2, 1: 1}


def leb_s(d, p):
    r = s = 0
    while True:
        b = d[p]
        p += 1
        r |= (b & 0x7F) << s
        s += 7
        if not b & 0x80:
            if b & 0x40:
                r -= 1 << s
            return r, p


def pack(chunks):
    return b"".join(W._chunk(c, p) for c, p in chunks) + b"\x00"


# ------------------------------------------------------------------------------------------ the face and the tie
def paint(im):
    """Page 11 of the wad (512 x 512): half a face in profile at x 355-420, y 0-130 (used for both sides), the shirt
    front along the right edge."""
    a = np.array(im.convert("RGBA")).astype(float)
    skin = a[100:112, 392:408, :3].reshape(-1, 3).mean(0)             # the jaw, under the mask
    reg = a[14:104, 348:428, :3]
    mx, mn = reg.max(2), reg.min(2)
    white = (mn > 95) & ((mx - mn) < 46)                              # the mask: white to grey, no colour
    lum = reg.mean(2) / 235.0
    for k in range(3):
        ch = reg[..., k]
        ch[white] = np.clip(skin[k] * (0.55 + 0.5 * lum[white]), 0, 255)
    a[14:104, 348:428, :3] = reg
    nose = a[128:166, 294:324, :3]                                    # the nose has a patch of its own
    mx, mn = nose.max(2), nose.min(2)
    w2 = (mn > 95) & ((mx - mn) < 46)
    l2 = nose.mean(2) / 235.0
    for k in range(3):
        ch = nose[..., k]
        ch[w2] = np.clip(skin[k] * (0.55 + 0.5 * l2[w2]), 0, 255)
    a[128:166, 294:324, :3] = nose
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(out)
    dark = tuple(int(c * 0.62) for c in skin) + (255,)
    # the eye socket, where the hole of the mask was (the eyeball is a mesh of its own, in front of it)
    d.ellipse((367, 43, 390, 61), fill=dark)
    # a heavy eyebrow and a moustache
    d.polygon([(357, 37), (378, 33), (397, 37), (396, 41), (378, 38), (358, 41)], fill=(22, 15, 11, 255))
    d.polygon([(353, 85), (372, 83), (388, 90), (386, 94), (370, 91), (353, 93)], fill=(20, 14, 10, 255))
    # the tie on the shirt front: the chest is mapped from x 465 (lapel) to x 500 (the middle of the body)
    d.polygon([(491, 100), (501, 100), (501, 112), (493, 110)], fill=(92, 8, 12, 255))                # the knot
    d.polygon([(494, 110), (501, 112), (501, 182), (492, 176), (490, 140)], fill=(134, 14, 18, 255))
    d.line((495, 112, 493, 174), fill=(90, 8, 12, 255), width=1)
    return out


# ------------------------------------------------------------------------------------------ the wad
def textures(top):
    out = []
    for c, p in W._chunks(dict(top)[b"W2Textures"], 0, len(dict(top)[b"W2Textures"])):
        w, q = W._leb_u(p, 0)
        h, q = W._leb_u(p, q)
        out.append((w, h, W._chunks(p, q, len(p))))
    return out


def tex_chunk(w, h, subs):
    return (b"W2Txt", W._leb_enc(w) + W._leb_enc(h) + pack(subs))


def remap_mesh(payload, pages):
    """A W2Mesh payload with the texture numbers of its polygons replaced through `pages`."""
    out = []
    for c, p in W._chunks(payload, 0, len(payload)):
        if c == b"W2Polys":
            polys = []
            for pc, pp in W._chunks(p, 0, len(p)):
                k = 4 if pc == b"W2Uq2" else 3
                q = 0
                for _ in range(k + 1):                     # the corners, then the shine
                    _, q = W._leb_u(pp, q)
                page, q2 = W._leb_u(pp, q)
                polys.append((pc, pp[:q] + W._leb_enc(pages[page]) + pp[q2:]))
            p = pack(polys)
        out.append((c, p))
    return pack(out)


def faster(anims):
    """[(chunk id, payload)] of the animations with fewer game frames per key frame."""
    parsed = []
    for c, a in anims:
        assert c == b"W2Ani3", c
        pos, v = 0, []
        for _ in range(6):
            x, pos = leb_s(a, pos)
            v.append(x)
        parsed.append((v, W._chunks(a, pos, len(a))))
    f = [NEW_RATE.get(v[2], v[2]) / v[2] for v, _ in parsed]        # frames of each animation shrink by this
    out = []
    for i, (v, subs) in enumerate(parsed):
        state, end, rate, nxt, nxt_frame, blend = v
        new = []
        for c, p in subs:
            if c == b"W2StCh":
                st, q = leb_s(p, 0)
                disp = []
                for c2, p2 in W._chunks(p, q, len(p)):
                    q2, dv = 0, []
                    for _ in range(6):
                        x, q2 = leb_s(p2, q2)
                        dv.append(x)
                    lo = int(dv[0] * f[i])
                    hi = max(lo + (1 if dv[1] > dv[0] else 0), math.ceil(dv[1] * f[i]))
                    t = f[dv[2]] if 0 <= dv[2] < len(f) else 1.0
                    dv = [lo, hi, dv[2], int(dv[3] * t), int(dv[4] * t), dv[5]]
                    disp.append((c2, b"".join(W._leb_enc(x) for x in dv) + p2[q2:]))
                p = W._leb_enc(st) + pack(disp)
            elif c == b"W2Cmd2":
                q, cv = 0, []
                for _ in range(4):
                    x, q = leb_s(p, q)
                    cv.append(x)
                if cv[0] in (5, 6):                         # sound, flip effect: the frame they happen at
                    cv[1] = int(cv[1] * f[i])
                p = b"".join(W._leb_enc(x) for x in cv) + p[q:]
            elif c == b"W2AniV":
                vel = struct.unpack("<4f", p)
                p = struct.pack("<4f", *[x / f[i] for x in vel])
            new.append((c, p))
        t = f[nxt] if 0 <= nxt < len(f) else 1.0
        head = [state, int(end * f[i]), NEW_RATE.get(rate, rate), nxt, int(nxt_frame * t), blend]
        out.append((b"W2Ani3", b"".join(W._leb_enc(x) for x in head) + pack(new)))
    return out


def build(src, dst):
    top = W.load(src)
    tex = textures(top)
    mov = [p for mid, p in W.moveables(top) if mid == SRC_SLOT][0]
    _, q = W._leb_u(mov, 0)
    subs = W._chunks(mov, q, len(mov))
    used = set()

    def pages_of(mesh):
        for c, p in W._chunks(mesh, 0, len(mesh)):
            if c == b"W2Polys":
                for pc, pp in W._chunks(p, 0, len(p)):
                    k = 4 if pc == b"W2Uq2" else 3
                    qq = 0
                    for _ in range(k + 1):
                        _, qq = W._leb_u(pp, qq)
                    used.add(W._leb_u(pp, qq)[0])
    for c, p in subs:
        if c == b"W2Mesh":
            pages_of(p)
        elif c == b"W2MovSkin":
            for c2, p2 in W._chunks(p, 0, len(p)):
                if c2 == b"W2Mesh":
                    pages_of(p2)
    order = sorted(used)
    pages = {old: new for new, old in enumerate(order)}
    tchunks = []
    for old in order:
        w, h, ts = tex[old]
        if old == 11:                                      # the page with the face and the shirt
            d = dict(ts)[b"W2TxtData"]
            im = Image.fromarray(np.frombuffer(d, np.uint8).reshape(h, w, 4)[..., [2, 1, 0, 3]], "RGBA")
            data = np.array(paint(im))[..., [2, 1, 0, 3]].tobytes()
            ts = [(c, data if c == b"W2TxtData" else p) for c, p in ts]
        tchunks.append(tex_chunk(w, h, ts))
    body = []
    anims = [(c, p) for c, p in subs if c.startswith(b"W2Ani")]
    fast = iter(faster(anims))
    for c, p in subs:
        if c == b"W2Mesh":
            p = remap_mesh(p, pages)
        elif c == b"W2MovSkin":
            p = pack([(c2, remap_mesh(p2, pages) if c2 == b"W2Mesh" else p2) for c2, p2 in W._chunks(p, 0, len(p))])
        elif c.startswith(b"W2Ani"):
            c, p = next(fast)
        body.append((c, p))
    moveable = (b"W2Moveable", W._leb_enc(SLOT) + pack(body))
    out = []
    for cid, payload in top:
        if cid == b"W2Textures":
            out.append((cid, pack(tchunks)))
        elif cid == b"W2Moveables":
            out.append((cid, pack([moveable])))
        elif cid == b"W2Statics":
            out.append((cid, b"\x00"))
        else:
            out.append((cid, payload))
    raw = pack(out)
    data = zlib.compress(raw, 9)
    open(dst, "wb").write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)       # as wadtool.remap writes them
    print("CdV_Turi.wad2: %d textures, %d animations, %.1f MB" % (len(tchunks), len(anims), (len(data) + 12) / 1e6))


def level(src, dst):
    import prj2_patch as P
    head, top = P.load(src)
    d = dict(top)
    settings = P.add_wad(d[b"TeSettings"], "CdV_Turi.wad2", like=b"CdV_Mafiosi.wad2", first=True)
    n = [0]

    def fn(room, oc, op):
        if oc in (b"TeMovTn3", b"TeMovTen2") and op.rstrip(b"\0").endswith(b"turi"):
            o, t = P.mov_type(op)
            assert t == OLD_SLOT, t
            n[0] += 1
            return op[:o] + struct.pack("<I", SLOT) + op[o + 4:]
        return op
    rooms = P.map_objects(d[b"TeRooms"], fn)
    assert n[0] == 1, n
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])
    print("turi is now slot", SLOT)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 4:
        level(sys.argv[3], sys.argv[4])
