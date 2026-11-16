"""The title level: one small dark room with Ed's picture (Lara on the beach of Oliveri, Tindari behind) on the far
wall, and a flyby (sequence 0) that breathes slowly in front of it. TombEngine cannot show a background image in the
title by script (Flow.SetTitleScreenImagePath is not implemented in 2.0), so the picture is a wall.

  titolo_foto.py <picture> <installed level .prj2 (for its sound list)> <out dir>
  -> <out>/Title.prj2, cdv_title.png (Levels\\CdV_Textures), Logo.png (Engine\\Textures), main.png (Engine\\Screens)"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import prj2
import prj2_patch as P

W, H = 1536, 1024            # the picture on the wall: three sectors by two (512 px per sector)
ROOM_H = 2048
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def texture(src, out):
    pic = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
    im = Image.new("RGB", (W, H + 64), (0, 0, 0))
    im.paste(pic, (0, 0))
    im.save(out)
    return pic


def logo(out):
    """The name of the adventure for the top of the title screen (Engine\\Textures\\Logo.png, 1920 x 450)."""
    S = 2
    im = Image.new("RGBA", (1920 * S, 450 * S), (0, 0, 0, 0))
    big = ImageFont.truetype(SERIF, 150 * S)
    small = ImageFont.truetype(SERIF, 44 * S)

    def centred(d, y, text, font, fill, spacing=0, stroke=0, stroke_fill=None):
        w = sum(d.textlength(ch, font=font) for ch in text) + spacing * (len(text) - 1)
        x = (im.width - w) / 2
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            x += d.textlength(ch, font=font) + spacing
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    centred(ds, 70 * S, "A TOMB RAIDER ADVENTURE", small, (0, 0, 0, 200), spacing=14 * S)
    centred(ds, 150 * S, "CODA DI VOLPE", big, (0, 0, 0, 220), spacing=10 * S, stroke=6 * S, stroke_fill=(0, 0, 0, 220))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7 * S))
    im.alpha_composite(shadow, (4 * S, 6 * S))
    # letters: a warm gold, lighter at the top
    mask = Image.new("L", im.size, 0)
    dm = ImageDraw.Draw(mask)
    centred(dm, 150 * S, "CODA DI VOLPE", big, 255, spacing=10 * S)
    grad = Image.new("RGBA", im.size)
    px = grad.load()
    y0, y1 = 170 * S, 330 * S
    for y in range(im.height):
        t = min(1.0, max(0.0, (y - y0) / (y1 - y0)))
        c = (int(255 - 40 * t), int(226 - 96 * t), int(150 - 110 * t), 255)
        for x in range(0, im.width):
            px[x, y] = c
    edge = Image.new("RGBA", im.size, (0, 0, 0, 0))
    de = ImageDraw.Draw(edge)
    centred(de, 150 * S, "CODA DI VOLPE", big, (60, 26, 8, 255), spacing=10 * S, stroke=3 * S, stroke_fill=(60, 26, 8, 255))
    im.alpha_composite(edge)
    im.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(im)
    centred(d, 70 * S, "A TOMB RAIDER ADVENTURE", small, (255, 240, 205, 255), spacing=14 * S, stroke=S, stroke_fill=(60, 26, 8, 255))
    im.resize((1920, 450), Image.LANCZOS).save(out)


def loading(pic, out):
    """The same picture as loading screen of the title (Engine\\Screens\\main.png, 1920 x 1080: cropped to 16:9)."""
    h = int(W * 9 / 16)
    top = (H - h) // 2 + 40
    pic.crop((0, top, W, top + h)).resize((1920, 1080), Image.LANCZOS).save(out)


def level(out, sounds_from):
    lv = prj2.Level()
    lv.use_tombide_ten("title.ten")
    lv.textures.append({"path": "$(LevelDirectory)\\..\\CdV_Textures\\cdv_title.png"})
    r = prj2.Room("TITLE", 5, 6)
    r.ambient = (0.5, 0.5, 0.5)                      # 128: the picture at its own brightness, no lamp
    r.light_effect = 0
    black = [(8, H + 56), (8, H + 8), (56, H + 8), (56, H + 56)]
    for x in range(5):
        for z in range(6):
            s = r.sector(x, z)
            s.ceil = [ROOM_H] * 4
            if not s.wall:
                s.set_tex(prj2.F_FLOOR, black)
                s.set_tex(prj2.F_CEILING, black)
    for x in range(1, 4):                            # the far wall (north): the picture, left to right = west to east
        u0, u1 = (x - 1) * 512, x * 512
        r.sector(x, 5).set_tex(prj2.F_WALL_MIDDLE["-z"], [(u0, H), (u0, 0), (u1, 0), (u1, H)])
        r.sector(x, 0).set_tex(prj2.F_WALL_MIDDLE["+z"], black)
    for z in range(1, 5):
        r.sector(0, z).set_tex(prj2.F_WALL_MIDDLE["+x"], black)
        r.sector(4, z).set_tex(prj2.F_WALL_MIDDLE["-x"], black)
    lv.add_room(r)
    lv.add_moveable(r, 0, (2560.0, 0.0, 1536.0), rot_y=0.0, lua_name="lara_titolo")      # hidden (EnableLaraInTitle(false))
    # the wall is at z = 5120; a screen 16:9 sees the whole width of the picture from 1300 units
    cx, cy, wall = 2560.0, 1024.0, 5120.0
    loop, hide = 4, 16
    for n, d in enumerate((1380.0, 1240.0, 1380.0)):
        lv.add_flyby(r, (cx, cy, wall - d), 0, n, rot_y=0.0, rot_x=0.0, speed=0.07, fov=80.0, flags=hide | loop)          # the loop flag on every camera, as in the trailer shots
    tmp = os.path.join(out, "Title_senza_suoni.prj2")
    lv.save(tmp)
    # the sound list of an installed level: the menu sounds are in it
    _, mt = P.load(sounds_from)
    ms = dict(P.chunks(dict(mt)[b"TeSettings"])[0])
    h, t = P.load(tmp)
    items, _ = P.chunks(dict(t)[b"TeSettings"])
    items = [(c, ms[c] if c in (b"TeSelectedSounds", b"TeSoundsCatalogs") else p) for c, p in items]
    P.save(os.path.join(out, "Title.prj2"), h, [(c, P.pack(items) if c == b"TeSettings" else p) for c, p in t])
    os.remove(tmp)


def main():
    src, sounds_from, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    pic = texture(src, os.path.join(out, "cdv_title.png"))
    logo(os.path.join(out, "Logo.png"))
    loading(pic, os.path.join(out, "main.png"))
    level(out, sounds_from)
    print("title level, texture, logo and loading screen in", out)


if __name__ == "__main__":
    main()
