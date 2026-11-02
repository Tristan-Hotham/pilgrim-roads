"""Geography for the page and figures: a light world outline file (Natural Earth 1:50m, simplified), country names and
label points, city names, and the simplified route lines.

Route lines (data/routes.json). Each unique segment from 01_clean.py belongs to one owning relation. The segments of
each owner are merged into lines (shapely linemerge), simplified with a tolerance of 0.0008 degrees (under 90 m) and
written with coordinates rounded to 4 decimal places as a compact JSON: per relation, a list of lines, each a flat
list of integer coordinates in 1e-4 degrees, delta encoded. The page decodes it into GeoJSON. Every number in the text
is computed from the full unique segments, never from these simplified lines."""
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from shapely.ops import linemerge
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND", "SOL": "SOM"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


# ---------- world outlines (page fallback map, MapLibre base, figures) ----------
W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIX.get(iso_of(p), iso_of(p))
    g = shape(f["geometry"])
    # finer outlines over Europe, where the routes are
    tol = 0.02 if (p.get("CONTINENT") == "Europe" or iso in ("TUR", "ISR", "JPN")) else 0.06
    gs = g.simplify(tol, preserve_topology=True)
    if gs.is_empty:
        continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"], 3 if tol < .05 else 2)}})
    if iso not in meta:
        nm = (p.get("NAME_EN") or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
        meta[iso] = {"name": nm, "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2), "pop": float(p.get("POP_EST") or 0),
                     "cont": p.get("CONTINENT", "")}
for k, nm in (("CYP", "Cyprus"), ("CZE", "Czechia"), ("BIH", "Bosnia and Herzegovina"), ("GBR", "United Kingdom")):
    if k in meta: meta[k]["name"] = nm
# Natural Earth 1:10m names for places the 1:50m file lacks (Aland, small states)
for iso, m in jload(f"{WORK}/cmeta.json").items():
    if iso not in meta:
        meta[iso] = {"name": m["name"], "lx": None, "ly": None, "pop": m["pop"], "cont": m["cont"]}
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave(meta, f"{DATA}/countries.json")

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 150000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")

# ---------- route lines ----------
S = pd.read_pickle(f"{WORK}/segs.pkl")
K = pd.read_pickle(f"{WORK}/rels.pkl")
RL = pd.read_pickle(f"{WORK}/rid_list.pkl").tolist()
coords = np.stack([np.column_stack([S.x1, S.y1]), np.column_stack([S.x2, S.y2])], axis=1) / 1e4
lines = shapely.linestrings(coords)
order = S.groupby("owner").indices
out = {}
npts = 0
for oi, idx in order.items():
    m = linemerge(shapely.multilinestrings(lines[idx]))
    m = m.simplify(0.0008, preserve_topology=False)
    parts = [m] if m.geom_type == "LineString" else list(m.geoms)
    enc = []
    for ln in parts:
        c = np.rint(np.asarray(ln.coords) * 1e4).astype(np.int64)
        if len(c) < 2: continue
        d = np.vstack([c[:1], np.diff(c, axis=0)])
        keep = np.r_[True, (d[1:] != 0).any(axis=1)]
        d = d[keep]
        if len(d) < 2: continue
        enc.append(d.ravel().tolist()); npts += len(d)
    if enc:
        out[RL[oi]] = enc
jsave({"scale": 1e4, "note": "per OSM relation id: lines, each a flat delta-encoded list [x0, y0, dx1, dy1, ...] in 1e-4 degrees. "
                             "Derived from OpenStreetMap, (c) OpenStreetMap contributors, ODbL 1.0.", "lines": out}, f"{DATA}/routes.json")
print("countries", len(meta), "cities", len(cities), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB;",
      "route owners", len(out), "points", npts, "routes.json", os.path.getsize(f"{DATA}/routes.json") // 1024, "KB")
