"""r/dataisbeautiful collage for pilgrim-roads: 2400 x 3200 px, light background. Numbers from data/results.json.
Map labels sit on open sea or on the paper with a halo; each label box is checked against the land and every route
line, and against the other labels. No leader lines."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from shapely.geometry import Polygon as _Poly, LineString as _LS, box as _box
from shapely.ops import unary_union
from shapely.prepared import prep

R = jload(f"{DATA}/results.json")
F, C, T, ST, CP = R["fam"], R["fam"]["camino"], R["total"], R["sites"], R["compostela"]
BGc = "#F7F4EC"; SEAc = "#E6EDF0"; LANDc = "#E3DDCF"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "All roads lead to Santiago, eventually", fontproperties=DISP, fontsize=40, color=FG, va="top")
fig.text(.045, .942, f"Every waymarked pilgrim route in OpenStreetMap, each stretch counted once: {T['km']:,} km. {C['km']:,} km of it is signed for\n"
         f"Santiago de Compostela, but only {C['within500_pct']:.0f}% lies within 500 km of the cathedral. Germany has {C['by_iso']['DEU']:,} km, Spain {C['by_iso']['ESP']:,} km.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.3)

# ---- map
EXT = (2.0e6, 6.95e6, 1.38e6, 4.92e6)
ax = fig.add_axes([0, .37, 1, .52])
basemap(ax, ESH, EXT, sea=SEAc, land=LANDc, lw=.35, ec=BGc)
draw_routes(ax, LA, lw=.85)
RINGS = (500, 1000, 1500, 2000, 2500)
for r in RINGS:
    la, lo = circle_ll(*SANTIAGO, r); x, y = LA.transform(lo, la)
    ax.plot(x, y, color="#8A7F70", lw=.8, ls=(0, (5, 4)), zorder=2.5)
sx, sy = LA.transform(SANTIAGO[1], SANTIAGO[0])
ax.scatter([sx], [sy], marker="*", s=420, c=HOT, ec="#fff", lw=1.4, zorder=9)
for (lat, lon) in (ROME, NIDAROS):
    x, y = LA.transform(lon, lat); ax.scatter([x], [y], marker="*", s=200, c=FG, ec="#fff", lw=1.2, zorder=9)

# obstacles: land (with a margin) and every route line
import shapely
LANDG = [_Poly(p).buffer(0) for _, p in ESH if len(p) > 3]
lines = []
for rid, arrs in LINES.items():
    for a in arrs:
        x, y = LA.transform(a[:, 0], a[:, 1])
        if len(x) > 1: lines.append(_LS(np.column_stack([x, y])))
LT, LNT = shapely.STRtree(LANDG), shapely.STRtree(lines)


class _Obst:
    def intersects(self, b):
        return len(LT.query(b.buffer(15e3), predicate="intersects")) > 0 or len(LNT.query(b.buffer(12e3), predicate="intersects")) > 0


OBST = _Obst()
fig.canvas.draw(); REN = fig.canvas.get_renderer()
PLACED = []


def tbox(t):
    bb = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 4, bb.y0 - 3], [bb.x1 + 4, bb.y1 + 3]])
    return _box(x0, y0, x1, y1)


def place(name, s, cands, ha="center", col=FG, size=11, w="medium", allow_land=False):
    t = ax.text(0, 0, s, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.15, zorder=10, path_effects=HALO, fontweight=w)
    for (x, y) in cands:
        t.set_position((x, y)); b = tbox(t)
        if not _box(EXT[0] + 4e4, EXT[2] + 4e4, EXT[1] - 4e4, EXT[3] - 4e4).contains(b): continue
        if OBST.intersects(b) or any(b.intersects(o) for _, o in PLACED): continue
        PLACED.append((name, b)); return t
    raise RuntimeError("no clean spot for " + name)


def around(lon, lat, rmax=12, step=5e4):
    x0, y0 = LA.transform(lon, lat)
    out = [(x0, y0)]
    for r in range(1, rmax + 1):
        for k in range(16 * r):
            a = 2 * np.pi * k / (16 * r); out.append((x0 + r * step * np.cos(a), y0 + r * step * np.sin(a)))
    return out


place("santiago", "SANTIAGO DE\nCOMPOSTELA\ngoal of the Camino", around(-12.5, 43.3, 10), ha="center", col=HOT, size=12, w="medium")
for r in RINGS:
    la2, lo2 = circle_ll(*SANTIAGO, r, n=720)
    cands = []
    for bear in list(range(316, 262, -2)) + list(range(318, 360, 2)):
        k = int(720 * bear / 360); cands.append(LA.transform(lo2[k], la2[k]))
    place(f"ring{r}", f"{r:,} km", cands, col="#7A7062", size=10, w="normal")
place("rome", "ROME\nVia Francigena", around(12.0, 38.6, 30), col=COOL, size=10, w="medium")
place("trondheim", "TRONDHEIM\nend of the\nSt Olav Ways", around(3.0, 64.8, 12), col="#1E7A6E", size=11, w="medium")
for nm, b in PLACED:
    assert not OBST.intersects(b), nm
    assert not any(b.intersects(o) for n2, o in PLACED if n2 != nm), nm
print("map labels ok:", len(PLACED))

# legend under the map, on paper
h = [Line2D([], [], color=FCOL[f], lw=4, label=f"{FNAME[f]}  {F[f]['km']:,} km") for f in FKEYS] + \
    [Line2D([], [], color="#8A7F70", lw=1.2, ls=(0, (5, 4)), label="500 km rings from Santiago"),
     Line2D([], [], ls="", marker="*", ms=14, mfc=HOT, mec="#fff", label="Santiago de Compostela"),
     Line2D([], [], ls="", marker="*", ms=11, mfc=FG, mec="#fff", label="Rome and Trondheim")]
fig.legend(handles=h, loc="upper center", bbox_to_anchor=(.5, .368), ncol=3, frameon=False, fontsize=10.5, handlelength=2.2, columnspacing=2.0)

# ---- panel 1: Camino by country
a1 = fig.add_axes([.17, .075, .32, .17]); a1.set_facecolor(BGc)
cc = [c for c in C["countries"] if c["iso"] != "SEA"][:9][::-1]
a1.barh([c["name"] for c in cc], [c["km"] for c in cc], color=[HOT if c["iso"] == "DEU" else (COOL if c["iso"] == "ESP" else "#C9A27E") for c in cc], height=.7)
for i, c in enumerate(cc): a1.text(c["km"] + 200, i, f"{c['km']:,}", va="center", fontsize=9.5, color=FG)
a1.set_xlim(0, cc[-1]["km"] * 1.28); a1.set_xticks([]); spines(a1); a1.spines["bottom"].set_visible(False); a1.tick_params(axis="y", length=0, labelsize=10)
fig.text(.045, .275, "Waymarked Camino, km by country", fontsize=12.5, color=FG, fontweight="medium")

# ---- panel 2: distance bands
a2 = fig.add_axes([.56, .095, .41, .15]); a2.set_facecolor(BGc)
B = R["bands"]; mx = max(b["km"] for b in B)
a2.bar(range(len(B)), [b["km"] for b in B], color=[HOT if b["km"] == mx else "#C9A27E" for b in B], width=.74)
for i, b in enumerate(B): a2.text(i, b["km"] + mx * .03, f"{b['pct']:.0f}%", ha="center", fontsize=9.5, color=FG)
a2.set_xticks(range(len(B))); a2.set_xticklabels([f"{b['lo']:,}" for b in B], fontsize=9.5)
a2.tick_params(axis="x", length=0); a2.set_yticks([]); spines(a2); a2.spines["left"].set_visible(False); a2.set_ylim(0, mx * 1.15)
a2.set_xlabel("start of each band, km from Santiago (straight line)", fontsize=9.5, color=MUT)
fig.text(.56, .275, "Share of the Camino by distance from Santiago", fontsize=12.5, color=FG, fontweight="medium")
fig.text(.56, .257, f"Farthest: {C['far_route']}, Ukraine, {C['far_km']:,} km away", fontsize=10, color=MUT)

# ---- footer
fig.text(.045, .028, f"Data: OpenStreetMap pilgrimage route relations via Overpass, (c) OpenStreetMap contributors, ODbL. {R['source']['ids_failed']} of {R['source']['ids_requested']:,} relation ids failed to download\n"
         f"and some famous routes are missing, so totals are lower bounds. Families from route names, Wikidata links and the scallop shell. Outlines: Natural Earth.",
         fontsize=8.6, color=MUT, va="bottom", linespacing=1.4)
fig.text(.955, .012, "maps.tristanhotham.com/pilgrim-roads", fontsize=10, color=FG, ha="right", va="bottom")
out = os.path.join(ROOT, "reddit", "pilgrim_roads.png")
fig.savefig(out, dpi=200, facecolor=BGc)
from PIL import Image
im = Image.open(out); assert im.size == (2400, 3200), im.size
print("collage", out, im.size)
