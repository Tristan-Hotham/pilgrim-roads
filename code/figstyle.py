"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines, and the route lines decoded from data/routes.json.
Europe maps use the ETRS89 Lambert azimuthal equal area projection (EPSG:3035); world maps use Equal Earth (EPSG:8857).
Reads data/ only."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import LineCollection
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F3EC", "#1D2128", "#636A72", "#E4DFD3", "#DDD8CC", "#EAEFF1"
HOT, COOL, NAVY, GOLD = "#D2541B", "#2F5FA7", "#1F2F4D", "#C9961A"
TCOL = dict(TRADS)

EE = Transformer.from_crs(4326, 8857, always_xy=True)
LA = Transformer.from_crs(4326, 3035, always_xy=True)
W = jload(f"{DATA}/world.json")
SITE = jload(f"{DATA}/site.json")
REL = {r[0]: r for r in SITE["rels"]}


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def shapes(T, clip=None):
    out = []
    for f in W["features"]:
        for ring in rings(f["geometry"]):
            if clip is not None:
                if ring[:, 0].max() < clip[0] or ring[:, 0].min() > clip[1] or ring[:, 1].max() < clip[2] or ring[:, 1].min() > clip[3]:
                    continue
            x, y = T.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
            out.append((f["properties"]["iso"], np.column_stack([x, y])))
    return out


WSH = shapes(EE)
ESH = shapes(LA, clip=(-32, 50, 25, 75))
WORLD_EXT = (-17.0e6, 17.0e6, -8.75e6, 8.7e6)
EUR_EXT = (2.35e6, 6.35e6, 1.35e6, 5.25e6)        # Iberia and Ireland to Ukraine, Sicily to central Norway


def basemap(ax, sh, ext, lw=.35, ec="#FFFFFF", land=LAND, z=1, sea=None):
    if sea:
        ax.set_facecolor(sea)
    for iso, p in sh:
        ax.add_patch(MPoly(p, closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def route_lines():
    """{osm id: [array (n, 2) lon/lat, ...]} decoded from data/routes.json."""
    J = jload(f"{DATA}/routes.json")
    out = {}
    for rid, lines in J["lines"].items():
        arrs = []
        for flat in lines:
            a = np.cumsum(np.asarray(flat, dtype=np.int64).reshape(-1, 2), axis=0) / J["scale"]
            arrs.append(a)
        out[rid] = arrs
    return out


LINES = route_lines()


def draw_routes(ax, T, fams=None, lw=.7, alpha=1, z=3, color=None, order=("other", "marian", "olav", "francigena", "camino")):
    for f in order:
        if fams and f not in fams: continue
        fi = FKEYS.index(f)
        segs = []
        for rid, arrs in LINES.items():
            if REL[rid][2] != fi: continue
            for a in arrs:
                x, y = T.transform(a[:, 0], a[:, 1]); segs.append(np.column_stack([x, y]))
        ax.add_collection(LineCollection(segs, colors=color or FCOL[f], linewidths=lw, alpha=alpha, zorder=z + .1 * fi, capstyle="round", joinstyle="round"))


def circle_ll(lat0, lon0, r_km, n=360):
    d = r_km / 6371.0; p0, l0 = np.radians(lat0), np.radians(lon0); b = np.linspace(0, 2 * np.pi, n)
    p = np.arcsin(np.sin(p0) * np.cos(d) + np.cos(p0) * np.sin(d) * np.cos(b))
    l = l0 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p0), np.cos(d) - np.sin(p0) * np.sin(p))
    return np.degrees(p), (np.degrees(l) + 540) % 360 - 180


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
