"""Render a top-down preview of a generated zone (terrain, buildings, room grid, Lara).

Usage: python3 preview_zone.py A
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LightSource  # noqa: E402
from pyproj import Transformer  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from gen_zone import POI, ROOM_N, ROOT  # noqa: E402

LABELS = {"Castello": (38.12196, 15.05620), "Piazza 24 Maggio": (38.12476, 15.05947),
          "Via Saia Interna": (38.12311, 15.05974), "Municipio": (38.12426, 15.05936)}


def main(zone):
    b = os.path.join(ROOT, "build")
    d = json.load(open(os.path.join(b, "zona_%s_report.json" % zone)))
    r, buildings = d["report"], d["buildings"]
    floor = np.load(os.path.join(b, "zona_%s_floor.npy" % zone))
    bid = np.load(os.path.join(b, "zona_%s_buildings.npy" % zone))
    h = floor.mean(axis=2) / 512.0
    ox, oz = r["origin_3004"]
    t = Transformer.from_crs(4326, 3004, always_xy=True)

    def sec(la, lo):
        x, z = t.transform(lo, la)
        return (x - ox) / 2.0, (z - oz) / 2.0

    fig, ax = plt.subplots(figsize=(13, 12))
    rgb = LightSource(azdeg=315, altdeg=45).shade(h.T, cmap=plt.cm.gist_earth, vert_exag=2,
                                                  blend_mode="soft", vmin=-5, vmax=60)
    ax.imshow(rgb, origin="lower")
    ax.imshow(np.ma.masked_where(bid.T < 0, h.T), origin="lower", cmap="Oranges", alpha=0.6, vmin=0, vmax=40)
    for i in range(0, floor.shape[0], ROOM_N):
        ax.axvline(i + 0.5, color="w", lw=0.4, alpha=0.6)
    for j in range(0, floor.shape[1], ROOM_N):
        ax.axhline(j + 0.5, color="w", lw=0.4, alpha=0.6)
    hx, hz = sec(*POI["casa_amodeo_1"])
    ys, xs = np.nonzero(bid.T >= 0)
    k = ((xs - hx) ** 2 + (ys - hz) ** 2).argmin()
    ax.contour((bid == bid[xs[k], ys[k]]).T, levels=[0.5], colors="red", linewidths=2)
    ax.annotate("Casa Via Amodeo 1", (hx, hz), xytext=(12, -22), textcoords="offset points", color="red",
                fontweight="bold", bbox=dict(fc="w", alpha=0.85))
    lx, lz = sec(*POI["lara_start"])
    ax.plot(lx, lz, "c^", ms=12)
    ax.annotate("Lara", (lx, lz), xytext=(8, 8), textcoords="offset points", color="c", fontweight="bold")
    for name, (la, lo) in LABELS.items():
        x, z = sec(la, lo)
        if 0 <= x < floor.shape[0] and 0 <= z < floor.shape[1]:
            ax.annotate(name, (x, z), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold",
                        bbox=dict(fc="w", alpha=0.7))
    ax.set_title("Zona %s - %s: %dx%d settori (%dx%d m), %d stanze da %dx%d\nterreno DTM 2 m + %d edifici OSM estrusi "
                 "(arancio); griglia = stanze" % (zone, r["name"], r["sectors"][0], r["sectors"][1], r["size_m"][0],
                                                  r["size_m"][1], r["rooms"], ROOM_N + 2, ROOM_N + 2, len(buildings)))
    ax.set_xlabel("settori (est)")
    ax.set_ylabel("settori (nord)")
    plt.tight_layout()
    out = os.path.join(b, "zona_%s_preview.png" % zone)
    plt.savefig(out, dpi=75)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "A")
