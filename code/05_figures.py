"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; lines from data/routes.json. Reads data/ only."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.2, foreground=SEA)]
HALOB = [pe.withStroke(linewidth=3.2, foreground=BG)]
F = R["fam"]; CAM = F["camino"]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        w = fig.get_size_inches()[0]
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=1800 / w, facecolor=fig.get_facecolor())
    plt.close(fig)


def fam_legend(fig, loc, anchor, ncol=5, fs=10, kms=True):
    h = [Line2D([], [], color=FCOL[f], lw=3, label=f"{FNAME[f]}" + (f" ({F[f]['km']:,} km)" if kms else "")) for f in FKEYS]
    fig.legend(handles=h, loc=loc, bbox_to_anchor=anchor, ncol=ncol, frameon=False, fontsize=fs, handlelength=1.6, columnspacing=1.4)


from shapely.geometry import Polygon as _Poly, Point
from shapely.ops import unary_union
from shapely.prepared import prep
LANDP = prep(unary_union([_Poly(p).buffer(0) for _, p in ESH if len(p) > 3]))


def santiago_rings(ax, T, radii=(500, 1000, 1500, 2000, 2500), lab=True, fs=8.5, col="#8A7F70"):
    for r in radii:
        la, lo = circle_ll(*SANTIAGO, r); x, y = T.transform(lo, la)
        ax.plot(x, y, color=col, lw=.7, ls=(0, (4, 3)), zorder=2.5, alpha=.9)
        if lab:
            # label each ring where it crosses the open Atlantic north west of Santiago (bearing about 330 degrees)
            la2, lo2 = circle_ll(*SANTIAGO, r, n=720)
            x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
            for bear in list(range(330, 260, -2)) + list(range(332, 360, 2)) + list(range(0, 40, 2)):
                k = int(720 * bear / 360); xx, yy = T.transform(lo2[k], la2[k])
                if x0 + 1.2e5 < xx < x1 - 1.2e5 and y0 + 6e4 < yy < y1 - 6e4 and not LANDP.contains(Point(xx, yy).buffer(9e4)): break
            ax.text(xx, yy, f"{r:,} km", fontsize=fs, color=col, ha="center", va="center", zorder=6, path_effects=HALO, rotation=0)
    x, y = T.transform(SANTIAGO[1], SANTIAGO[0])
    ax.scatter([x], [y], marker="*", s=180, c=HOT, ec="#fff", lw=1.0, zorder=9)


# ---------- 1. Europe map of the routes ----------
fig = plt.figure(figsize=(12, 13.4), facecolor=BG)
ax = fig.add_axes([0, .06, 1, .875]); basemap(ax, ESH, EUR_EXT, sea=SEA)
draw_routes(ax, LA, lw=.75)
santiago_rings(ax, LA)
x, y = LA.transform(SANTIAGO[1], SANTIAGO[0])
ax.text(x - 9e4, y + 9e4, "Santiago de\nCompostela", ha="right", va="bottom", fontsize=10, color=FG, fontweight="medium", path_effects=HALO, zorder=10)
for nm, (lat, lon), dx, dy, ha in (("Rome", ROME, 7e4, -9e4, "left"), ("Trondheim", NIDAROS, -7e4, 4e4, "right")):
    x, y = LA.transform(lon, lat); ax.scatter([x], [y], s=26, c=FG, zorder=9, ec="#fff", lw=.8)
    ax.text(x + dx, y + dy, nm, ha=ha, fontsize=10, color=FG, path_effects=HALO, zorder=10)
fig.text(.02, .975, f"{R['total']['km']:,} km of waymarked pilgrim routes in OpenStreetMap, {R['fam']['camino']['km']:,} km of them signed for Santiago", fontsize=12, color=FG, va="top")
fig.text(.02, .952, "Dashed rings: straight line distance from the cathedral of Santiago de Compostela", fontsize=10, color=MUT, va="top")
fam_legend(fig, "lower center", (.5, 0), ncol=3, fs=10)
both(fig, "map")

# ---------- 2. Camino km by country ----------
cc = [c for c in CAM["countries"] if c["iso"] != "SEA"][:14][::-1]
fig = plt.figure(figsize=(11, 6.2), facecolor=BG); ax = fig.add_axes([.2, .1, .74, .78]); ax.set_facecolor(BG)
cols = [HOT if c["iso"] in ("DEU",) else (COOL if c["iso"] == "ESP" else "#C9A27E") for c in cc]
ax.barh([c["name"] for c in cc], [c["km"] for c in cc], color=cols, height=.68)
for i, c in enumerate(cc):
    ax.text(c["km"] + 150, i, f"{c['km']:,} km  ({c['pct']:.0f}%)" if c["pct"] >= 1 else f"{c['km']:,} km", va="center", fontsize=9.5, color=FG)
ax.set_xlim(0, cc[-1]["km"] * 1.25); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10.5)
fig.text(.02, .96, f"Waymarked Camino de Santiago in OpenStreetMap, by country: {CAM['km']:,} km in {CAM['n_countries']} countries", fontsize=12, color=FG, va="top")
fig.text(.02, .92, "Unique kilometres of routes signed for Santiago (Jakobsweg, Droga sw. Jakuba, Camino...). Top 14 countries.", fontsize=9.5, color=MUT, va="top")
both(fig, "camino")

# ---------- 3. distance from Santiago ----------
B = R["bands"]
fig = plt.figure(figsize=(11, 5.6), facecolor=BG); ax = fig.add_axes([.03, .2, .94, .62]); ax.set_facecolor(BG)
xs = np.arange(len(B)); mx = max(b["km"] for b in B)
ax.bar(xs, [b["km"] for b in B], color=[HOT if b["km"] == mx else "#C9A27E" for b in B], width=.72)
for i, b in enumerate(B):
    ax.text(i, b["km"] + mx * .02, f"{b['km']:,} km\n{b['pct']:.0f}%", ha="center", fontsize=9.5, color=FG)
    ax.text(i, -mx * .03, b["band"].replace(" km", ""), ha="center", va="top", fontsize=9.5, color=FG, fontweight="medium")
    if b["top"]:
        ax.text(i, -mx * .11, "\n".join(n for n, k in b["top"][:2]), ha="center", va="top", fontsize=8.5, color=MUT)
ax.set_xlim(-.6, len(B) - .4); ax.set_ylim(-mx * .3, mx * 1.18); ax.axhline(0, color=MUT, lw=.8)
ax.set_xticks([]); ax.set_yticks([]); [sp.set_visible(False) for sp in ax.spines.values()]
fig.text(.02, .965, "How far from Santiago is the Camino? Waymarked km by straight line distance from the cathedral", fontsize=12, color=FG, va="top")
top_b = max(B, key=lambda b: b["km"])
fig.text(.02, .92, f"Distance bands in km. Under each band, the two countries with most Camino in it. The busiest band, {top_b['band']}, is mostly {top_b['top'][0][0]}.", fontsize=9.5, color=MUT, va="top")
both(fig, "bands")

# ---------- 4. the longest route systems ----------
LG = R["longest"][:12][::-1]
fig = plt.figure(figsize=(11, 6.4), facecolor=BG); ax = fig.add_axes([.34, .09, .62, .8]); ax.set_facecolor(BG)
ax.barh([l["name"].replace(" - The Central-European Pilgrimway", "").replace("Wanderroute ", "") for l in LG], [l["km"] for l in LG],
        color=[FCOL[l["fam"]] for l in LG], height=.68)
for i, l in enumerate(LG):
    ax.text(l["km"] + 40, i, f"{l['km']:,} km  " + ", ".join(l["countries"][:3]) + (" ..." if len(l["countries"]) > 3 else ""), va="center", fontsize=8.8, color=FG)
ax.set_xlim(0, LG[-1]["km"] * 1.62); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=9.8)
fig.text(.02, .965, "The longest mapped pilgrim route systems: OpenStreetMap relations with all their stages and branches", fontsize=12, color=FG, va="top")
fig.text(.02, .925, "Unique kilometres, each stretch counted once. A system's branches and alternatives count too.", fontsize=9.5, color=MUT, va="top")
fam_legend(fig, "lower center", (.6, -.005), ncol=5, fs=8.5, kms=False)
both(fig, "longest")

# ---------- 5. pilgrimage sites, world ----------
SI = SITE["sites"]
fig = plt.figure(figsize=(12, 6.6), facecolor=BG); ax = fig.add_axes([0, .07, 1, .86])
outline(ax, fc=SEA, ec="#C9CDD0"); basemap(ax, WSH, WORLD_EXT, ec=BG)
ax.set_facecolor(BG)
order = ["Not recorded", "Christian", "Buddhist", "Muslim", "Hindu", "Jain", "Jewish"]
TN = [t for t, _ in TRADS]
for t in order:
    pts = np.array([[s[0], s[1]] for s in SI if TN[s[4]] == t])
    if not len(pts): continue
    x, y = EE.transform(pts[:, 0], pts[:, 1])
    ax.scatter(x, y, s=9 if t != "Not recorded" else 7, c=TCOL[t], alpha=.85, lw=.25, ec="#fff", zorder=5 if t != "Not recorded" else 4)
st = R["sites"]
fig.text(.02, .965, f"{st['n']:,} pilgrimage sites in Wikidata, in {st['n_countries']} countries; {st['europe_pct']:.0f}% of them in Europe", fontsize=12, color=FG, va="top")
h = [Line2D([], [], ls="", marker="o", ms=7, mfc=TCOL[t], mec="#fff", label=f"{t} ({st['trad'].get(t, 0):,})") for t in order if st["trad"].get(t)]
fig.legend(handles=h, loc="lower center", bbox_to_anchor=(.5, 0), ncol=7, frameon=False, fontsize=9, handletextpad=.3, columnspacing=1.1)
fig.text(.98, .93, "Tradition: Wikidata's religion where recorded,\notherwise from the site's name", fontsize=8.5, color=MUT, ha="right", va="top")
both(fig, "sites")

# ---------- 6. sites by country (paper) ----------
top = st["top"][:15][::-1]; dens = st["dens"][:12][::-1]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.6), facecolor=BG); fig.subplots_adjust(left=.15, right=.97, wspace=.62, top=.86, bottom=.06)
for a, rows, key, col, t in ((a1, top, "n", COOL, "Pilgrimage sites"), (a2, dens, "per_m", HOT, "Sites per million people (10 or more sites)")):
    a.set_facecolor(BG); a.barh([r["name"] for r in rows], [r[key] for r in rows], color=col, height=.68)
    for i, r in enumerate(rows): a.text(r[key] * 1.02 + (2 if key == "n" else .05), i, f"{r[key]:,}" if key == "n" else f"{r[key]:.1f}", va="center", fontsize=9)
    a.set_title(t, loc="left", fontsize=11, color=FG); a.set_xticks([]); spines(a); a.spines["bottom"].set_visible(False); a.tick_params(axis="y", length=0, labelsize=9.5)
    a.set_xlim(0, max(r[key] for r in rows) * 1.2)
both(fig, "sites_country", blog=False)

# ---------- 7. Compostela certificates ----------
C = R["compostela"]; yy = np.array([y for y, v in C["years"]]); vv = np.array([v for y, v in C["years"]])
import datetime as _dt
holy = {y for y in range(1985, 2026) if _dt.date(y, 7, 25).weekday() == 6}   # Holy Years: 25 July on a Sunday
assert holy == {1993, 1999, 2004, 2010, 2021}
fig = plt.figure(figsize=(11, 5), facecolor=BG); ax = fig.add_axes([.09, .12, .88, .72]); ax.set_facecolor(BG)
ax.bar(yy, vv / 1000, color=[GOLD if y in holy else "#C9A27E" for y in yy], width=.8)
for y in (1985, 1993, 2010, 2020, 2025):
    v = dict(C["years"])[y]; ax.text(y, v / 1000 + 9, f"{v:,}", ha="center", fontsize=9, color=FG)
ax.set_xlim(1984, 2026); spines(ax); ax.set_ylabel("certificates, thousands"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
fig.text(.02, .965, "Compostela certificates issued by the Pilgrim's Office in Santiago, 1985 to 2025", fontsize=12, color=FG, va="top")
fig.text(.02, .92, "Gold: Holy Years, when 25 July, St James's day, falls on a Sunday (1993, 1999, 2004, 2010, 2021). 2020 and 2021: the pandemic. Source: Wikipedia.", fontsize=9.5, color=MUT, va="top")
both(fig, "compostela")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.43, 0, .57, 1]); ext = (2.4e6, 6.31e6, 1.45e6, 5.05e6)
basemap(ax, ESH, ext, sea=SEA, lw=.2)
draw_routes(ax, LA, lw=.55)
santiago_rings(ax, LA, lab=False)
fig.text(.04, .86, "Pilgrim", fontproperties=DISP, fontsize=64, color=HOT, va="top")
fig.text(.04, .66, "roads", fontproperties=DISP, fontsize=64, color=FG, va="top")
fig.text(.04, .43, f"{R['total']['km']:,} km of waymarked pilgrim\nroutes, {CAM['km']:,} km of them\nsigned for Santiago, and\n{st['n']:,} pilgrimage sites.", fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.3)
fig.text(.04, .05, "maps.tristanhotham.com/pilgrim-roads", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
