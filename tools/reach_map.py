"""Top-down picture of a World: height shading, water, walls, solid statics, named objects, optional reach set/path."""
from PIL import Image, ImageDraw
import reach


def draw(w, out, R=None, paths=(), box=None, cell=14, labels=True, layer='top', marks=()):
    xs = [k[0] for k in w.cols]; zs = [k[1] for k in w.cols]
    x0, x1, z0, z1 = (min(xs), max(xs), min(zs), max(zs)) if box is None else box
    W, H = (x1 - x0 + 1) * cell, (z1 - z0 + 1) * cell
    im = Image.new('RGB', (W, H), (20, 20, 24))
    d = ImageDraw.Draw(im)

    def px(X, Z):
        return (X - x0) * cell, (z1 - Z) * cell          # north (+Z) up
    for (X, Z), nodes in w.bycol.items():
        if not (x0 <= X <= x1 and z0 <= Z <= z1):
            continue
        n = max(nodes, key=lambda q: w.stand(q)) if layer == 'top' else min(nodes, key=lambda q: w.stand(q))
        if R is not None:
            rs = [q for q in nodes if q in R]
            if rs:
                n = max(rs, key=lambda q: w.stand(q))
        sp = w.nodes[n]
        h = w.stand(n)
        v = max(0, min(255, int(90 + h / 40)))
        col = (v, v, int(v * 0.85))
        if sp['water'] and sp['surface'] is not None:
            col = (30, 70 + max(0, min(120, int((h + 3000) / 30))), 170)
        if R is not None and not any(q in R for q in nodes):
            col = tuple(int(c * 0.35) for c in col)
        elif R is not None:
            col = (min(255, col[0] + 10), min(255, col[1] + 45), col[2])
        x, y = px(X, Z)
        d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=col)
        if cell >= 14:
            d.text((x + 1, y + 1), '%d' % round(h / 256), fill=(0, 0, 0))
        if sp['flags'] & (256 | 512 | 1024 | 2048):
            d.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(255, 0, 255))
    for (a1, y1, b1, a2, y2, b2, t) in w.solid:
        xa, ya = (a1 / 1024 - x0) * cell, (z1 + 1 - b2 / 1024) * cell
        xb, yb = (a2 / 1024 - x0) * cell, (z1 + 1 - b1 / 1024) * cell
        d.rectangle([xa, ya, xb, yb], outline=(255, 140, 0))
    for (cx, cz, cy) in w.closed:
        x, y = px(cx, cz)
        d.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(255, 0, 0), width=2)
    for p, colr in paths:
        pts = [((n[0] - x0 + 0.5) * cell, (z1 - n[1] + 0.5) * cell) for n in p]
        d.line(pts, fill=colr, width=2)
    for (X, Z, colr) in marks:
        x, y = px(X, Z)
        d.rectangle([x + 2, y + 2, x + cell - 3, y + cell - 3], outline=colr, width=2)
    if labels:
        for o in w.objs:
            if o['kind'] == 'mov' and o['name'] and not o['name'].startswith(('pip', 'bestia', 'tess')):
                X, Z = o['pos'][0] / 1024, o['pos'][2] / 1024
                if x0 <= X <= x1 + 1 and z0 <= Z <= z1 + 1:
                    x, y = (X - x0) * cell, (z1 + 1 - Z) * cell
                    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 0))
                    d.text((x + 4, y - 5), o['name'], fill=(255, 255, 0))
    im.save(out)
    return out
