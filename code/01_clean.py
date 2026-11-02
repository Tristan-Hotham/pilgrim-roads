"""Read the OpenStreetMap pilgrim route relations, classify each into a route family, break every way into unique
segments so that no stretch of path is counted twice, and give each segment a country; read the Wikidata pilgrimage
sites and pilgrim routes.

Which relations count. Every relation in the extract is kept unless (a) its route tag is a road, bus, ski piste or
fitness trail, or (b) it is one of five relations in common.DROP that inspection showed are not pilgrimage routes.
Super-relations (type=superroute or route relations with child relations) are kept as containers.

Families (common.FAMILIES, in priority order): Camino de Santiago, Via Francigena, St Olav Ways, Marian ways, other.
A relation's own family comes from keyword rules on its names, its pilgrimage, symbol and wikipedia tags (a scallop
shell symbol counts for the Camino) and its Wikidata id; a relation the rules do not place inherits the family of its
nearest classified parent, and a container that is still unplaced takes the family of most of its children's length.
Wikidata pilgrim route items that are part of the Way of St James and name an OSM relation also mark that relation.

Unique segments. Coordinates come rounded to 4 decimal places (about 10 m). Each way is split into its consecutive
point pairs; a pair is the same segment whichever direction it is drawn in. A segment shared by several relations (a
stage and the super-route it belongs to, two overlapping routes, a way listed twice) is counted once. Kilometres are
great circle lengths of the unique segments. Each segment is owned by one relation for the map: the leaf relation of
the highest priority family that uses it, the longest first.

Country. The midpoint of each segment is placed in a Natural Earth 1:10m country; the few midpoints that fall just
outside every outline (coasts, rivers) take the nearest country within about 2 km."""
import numpy as np, pandas as pd, csv
import shapely
from shapely.geometry import shape
from common import *

D = jload(f"{RAW}/osm_pilgrim_routes.json")
G = D["geo"]
pg = D["pg"]
m = re.search(r"done (\d+)/(\d+) fails (\d+)", pg[0]); assert m, pg
chk = {"pg": pg, "ids_requested": int(m.group(2)), "failed_batches": int(m.group(3)), "batch_size": 20,
       "relations_fetched": len(G)}
chk["ids_failed"] = chk["failed_batches"] * chk["batch_size"]
assert chk["relations_fetched"] == 1906 and chk["failed_batches"] == 5

# ---------- relation table ----------
NAMEKEYS = lambda t: [v for k, v in t.items() if k in ("name", "int_name", "alt_name", "official_name", "short_name", "loc_name", "old_name")
                      or k.startswith("name:") or k.startswith("alt_name:")]


def text_of(t):
    parts = NAMEKEYS(t) + [t.get("pilgrimage", ""), t.get("wikipedia", ""), t.get("symbol", ""), t.get("wiki:symbol", "")]
    return norm(" | ".join(p for p in parts if p))


def own_family(t):
    tx = text_of(t)
    if t.get("wikidata") in FAM_WD:
        return FAM_WD[t["wikidata"]], "wikidata"
    for k in ("camino", "francigena", "olav", "marian"):
        if FAM_RE[k].search(tx):
            return k, "name"
    if SHELL_RE.search(norm(t.get("osmc:symbol", "") + " " + t.get("symbol", "") + " " + t.get("wiki:symbol", ""))):
        return "camino", "shell symbol"
    return None, None


rows = []
for rid, v in G.items():
    t = v["tags"]
    drop = ""
    if t.get("route") in BAD_ROUTE: drop = "route=" + t.get("route")
    if rid in DROP: drop = DROP[rid]
    if t.get("type") == "network": drop = drop or "type=network"
    fam, how = own_family(t)
    rows.append({"id": rid, "name": t.get("name") or t.get("name:en") or t.get("ref") or "", "name_en": t.get("name:en", ""),
                 "type": t.get("type", ""), "route": t.get("route", ""), "network": t.get("network", ""), "pilgrimage": t.get("pilgrimage", ""),
                 "religion": t.get("religion", ""), "wikidata": t.get("wikidata", ""), "wikipedia": t.get("wikipedia", ""),
                 "distance_tag": t.get("distance", ""), "from": t.get("from", ""), "to": t.get("to", ""), "operator": t.get("operator", ""),
                 "n_ways": len(v["ways"]), "subrels": [str(s) for s in v["subrels"]], "own_fam": fam, "own_how": how, "dropped": drop})
REL = pd.DataFrame(rows).set_index("id")
chk["dropped"] = REL[REL.dropped != ""].dropped.to_dict()
K = REL[REL.dropped == ""].copy()
ids = set(K.index)
K["kids"] = K.subrels.map(lambda s: [c for c in s if c in ids])
K["kids_missing"] = K.subrels.map(lambda s: [c for c in s if c not in G])
par = {}
for rid, kids in K.kids.items():
    for c in kids:
        par.setdefault(c, []).append(rid)
K["parents"] = [par.get(r, []) for r in K.index]
chk["subrels_listed"] = int(K.subrels.map(len).sum()); chk["subrels_missing"] = int(K.kids_missing.map(len).sum())
chk["containers_all_missing"] = int(((K.n_ways == 0) & (K.subrels.map(len) > 0) & (K.kids.map(len) == 0)).sum())
chk["empty_relations"] = int(((K.n_ways == 0) & (K.subrels.map(len) == 0)).sum())

# Wikidata: OSM relations of items that are part of the Way of St James
W0 = pd.read_csv(f"{RAW}/wd_pilgrim_routes.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE)
W0.columns = [c.lstrip("?") for c in W0.columns]
W = pd.DataFrame({"qid": W0.r.map(qid), "label": W0.rLabel.map(lit), "type": W0.type.map(qid), "osm": W0.osm.map(lit),
                  "len": W0.len.map(lit), "start": W0.start.map(qid), "dest": W0.dest.map(qid), "partof": W0.partof.map(qid),
                  "country": W0.co.map(qid), "en": W0.en.str.strip("<>")})
wd_camino = set(W[(W.partof == "Q41150") | (W.type == "Q41150")].osm) - {""}
K["wd_camino"] = K.index.isin(wd_camino)
K.loc[K.own_fam.isna() & K.wd_camino, "own_how"] = "wikidata part of"
K.loc[K.own_fam.isna() & K.wd_camino, "own_fam"] = "camino"

# inherit from the nearest classified ancestor
def anc_fam(r, seen=()):
    for p in K.at[r, "parents"]:
        if p in seen: continue
        if K.at[p, "own_fam"]: return K.at[p, "own_fam"]
        f = anc_fam(p, seen + (r,))
        if f: return f
    return None


K["fam"] = K.own_fam
for r in K.index[K.fam.isna()]:
    f = anc_fam(r)
    if f: K.at[r, "fam"] = f; K.at[r, "own_how"] = "parent"

# ---------- segments ----------
A, B, RI = [], [], []
rid_list = list(K.index); RIDX = {r: i for i, r in enumerate(rid_list)}
nways = 0; npts = 0
for r in rid_list:
    for w in G[r]["ways"]:
        if len(w) < 2: continue
        a = np.rint(np.asarray(w, dtype=float) * 1e4).astype(np.int64)
        nways += 1; npts += len(a)
        p, q = a[:-1], a[1:]
        keep = (p != q).any(axis=1)
        A.append(p[keep]); B.append(q[keep]); RI.append(np.full(keep.sum(), RIDX[r], dtype=np.int32))
A = np.vstack(A); B = np.vstack(B); RI = np.concatenate(RI)
chk["ways_in_kept"] = nways; chk["points_in_kept"] = npts; chk["segments_raw"] = int(len(A))
swap = (A[:, 0] > B[:, 0]) | ((A[:, 0] == B[:, 0]) & (A[:, 1] > B[:, 1]))
P1 = np.where(swap[:, None], B, A); P2 = np.where(swap[:, None], A, B)
KEY = np.hstack([P1, P2])
U, inv = np.unique(KEY, axis=0, return_inverse=True)
inv = inv.ravel()
S = pd.DataFrame(U, columns=["x1", "y1", "x2", "y2"])
S["km"] = hav(S.y1 / 1e4, S.x1 / 1e4, S.y2 / 1e4, S.x2 / 1e4)
chk["segments_unique"] = len(S)
chk["km_raw_sum"] = round(float(hav(A[:, 1] / 1e4, A[:, 0] / 1e4, B[:, 1] / 1e4, B[:, 0] / 1e4).sum()), 1)
chk["km_unique"] = round(float(S.km.sum()), 1)
# a few very long segments are ferry or mapping jumps; keep them but record them
chk["segments_over_5km"] = int((S.km > 5).sum()); chk["km_in_segments_over_5km"] = round(float(S.km[S.km > 5].sum()), 1)

# relation x segment membership (unique pairs)
M = pd.DataFrame({"r": RI, "s": inv}).drop_duplicates()
K["km_own"] = 0.0
own_km = M.assign(km=S.km.values[M.s.values]).groupby("r").km.sum()
K.loc[[rid_list[i] for i in own_km.index], "km_own"] = own_km.values

# containers still unplaced: family of most of their children's length
def desc(r, seen=None):
    seen = seen if seen is not None else set()
    if r in seen: return seen
    seen.add(r)
    for c in K.at[r, "kids"]: desc(c, seen)
    return seen


K["desc"] = [sorted(desc(r)) for r in K.index]
for r in K.index[K.fam.isna()]:
    kids = [c for c in K.at[r, "desc"] if c != r and K.at[c, "fam"]]
    if kids:
        s = K.loc[kids].groupby("fam").km_own.sum()
        if s.sum() > 0: K.at[r, "fam"] = s.idxmax(); K.at[r, "own_how"] = "children"
K["fam"] = K.fam.fillna("other"); K.loc[K.own_how.isna(), "own_how"] = "none (other)"
chk["family_how"] = K.groupby(["fam", "own_how"]).size().rename(lambda x: str(x)).to_dict() if False else {f"{a}|{b}": int(n) for (a, b), n in K.groupby(["fam", "own_how"]).size().items()}

# family mask and owner per segment
FI = {f: i for i, f in enumerate(FKEYS)}
M["fi"] = K.fam.map(FI).values[M.r.values]
M["leaf"] = (K.kids.map(len).values[M.r.values] == 0).astype(int)
M["rkm"] = K.km_own.values[M.r.values]
S["mask"] = 0
mask = M.groupby("s").fi.agg(lambda v: int(sum(1 << int(x) for x in set(v))))
S.loc[mask.index, "mask"] = mask.values
own = M.sort_values(["s", "leaf", "fi", "rkm"], ascending=[True, False, True, False]).drop_duplicates("s")
S["owner"] = -1; S.loc[own.s.values, "owner"] = own.r.values
assert (S.owner >= 0).all()
S["fam"] = K.fam.map(FI).values[S.owner.values]           # family of the owning relation
S["nrel"] = M.groupby("s").size().reindex(S.index).values

# ---------- countries ----------
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND", "SOL": "SOM"}
C10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
cgeo, ciso, cmeta, wdiso = [], [], {}, {}
for f in C10:
    p = f["properties"]; iso = FIX.get(iso_of(p), iso_of(p))
    cgeo.append(shape(f["geometry"])); ciso.append(iso)
    if p.get("WIKIDATAID"): wdiso[p["WIKIDATAID"]] = iso
    if iso not in cmeta or p.get("POP_EST", 0) > cmeta[iso]["pop"]:
        nm = (p.get("NAME_EN") or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
        cmeta[iso] = {"name": nm, "pop": float(p.get("POP_EST") or 0), "cont": p.get("CONTINENT", ""), "region": p.get("REGION_UN", ""),
                      "subregion": p.get("SUBREGION", "")}
cmeta.get("CYP", {}).update(name="Cyprus")
cmeta.get("CZE", {}).update(name="Czechia")
ciso = np.array(ciso)
TREE = shapely.STRtree(cgeo)


def place(lon, lat, tol=0.02):
    pts = shapely.points(lon, lat)
    out = np.full(len(pts), "", dtype=object)
    pi, gi = TREE.query(pts, predicate="intersects")
    out[pi] = ciso[gi]
    miss = np.where(out == "")[0]
    if len(miss):
        near = TREE.query_nearest(pts[miss], max_distance=tol, return_distance=False, all_matches=False)
        out[miss[near[0]]] = ciso[near[1]]
    return out


mx = (S.x1 + S.x2).values / 2e4; my = (S.y1 + S.y2).values / 2e4
S["iso"] = place(mx, my)
chk["segments_no_country"] = int((S.iso == "").sum()); chk["km_no_country"] = round(float(S.km[S.iso == ""].sum()), 1)
S["iso"] = S.iso.replace("", "SEA")

# main country of each relation (most km)
MS = M.assign(iso=S.iso.values[M.s.values], km=S.km.values[M.s.values])
main_iso = MS.groupby(["r", "iso"]).km.sum().reset_index().sort_values("km", ascending=False).drop_duplicates("r").set_index("r").iso
K["iso"] = ""; K.loc[[rid_list[i] for i in main_iso.index], "iso"] = main_iso.values
niso = MS.groupby("r").iso.nunique()
K["n_iso"] = 0; K.loc[[rid_list[i] for i in niso.index], "n_iso"] = niso.values
# a representative point (the midpoint of the relation's middle segment) for labels and search
mid = MS.groupby("r").s.agg(lambda v: int(np.sort(v.values)[len(v) // 2]))
K["lon"] = np.nan; K["lat"] = np.nan
K.loc[[rid_list[i] for i in mid.index], "lon"] = mx[mid.values]; K.loc[[rid_list[i] for i in mid.index], "lat"] = my[mid.values]

# ---------- Wikidata pilgrimage sites ----------
S0 = pd.read_csv(f"{RAW}/wd_pilgrim_sites.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=csv.QUOTE_NONE)
S0.columns = [c.lstrip("?") for c in S0.columns]
chk["site_rows"] = len(S0)
pt = S0.c.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
S1 = pd.DataFrame({"qid": S0.s.map(qid), "label": S0.sLabel.map(lit), "lon": pt[0], "lat": pt[1], "co": S0.co.map(qid), "rel": S0.rel.map(qid),
                   "en": S0.en.str.strip("<>")})
chk["site_items"] = int(S1.qid.nunique()); chk["site_rows_no_coord"] = int(S1.lon.isna().sum())
g = S1.groupby("qid", sort=False)
SITES = pd.DataFrame({"label": g.label.first(), "lon": g.lon.first(), "lat": g.lat.first(), "en": g.en.agg(lambda v: next((x for x in v if x), "")),
                      "co_q": g.co.agg(lambda v: sorted(set(x for x in v if x))), "rel_q": g.rel.agg(lambda v: sorted(set(x for x in v if x)))}).reset_index()
SITES["iso_pt"] = place(SITES.lon.values, SITES.lat.values, tol=0.05)
SITES["iso_wd"] = SITES.co_q.map(lambda v: [wdiso[q] for q in v if q in wdiso])
# country: the Wikidata country if the point lies in it or there is only one; otherwise the point's country
def pick_iso(r):
    if r.iso_pt and (r.iso_pt in r.iso_wd or not r.iso_wd): return r.iso_pt
    if len(r.iso_wd) == 1: return r.iso_wd[0]
    return r.iso_pt or (r.iso_wd[0] if r.iso_wd else "")
SITES["iso"] = SITES.apply(pick_iso, axis=1)
chk["site_iso_disagree"] = int(((SITES.iso_pt != "") & SITES.iso_wd.map(len).gt(0) & ~SITES.apply(lambda r: r.iso_pt in r.iso_wd, axis=1)).sum())
chk["site_no_iso"] = int((SITES.iso == "").sum())
chk["site_rel_unmapped"] = sorted({q for v in SITES.rel_q for q in v if q not in REL_TRAD})
SITES["trad_rec"] = SITES.rel_q.map(lambda v: next((REL_TRAD[q] for q in v if q in REL_TRAD), "Not recorded"))


def trad_name(r):
    if r.trad_rec != "Not recorded": return r.trad_rec, "recorded"
    nm = norm(r.label)
    if not nm: return "Not recorded", ""
    for t, rx in TRAD_NAME:
        if rx.search(nm): return t, "name"
    if "temple" in nm and r.iso in TRAD_TEMPLE: return TRAD_TEMPLE[r.iso], "name"
    return "Not recorded", ""


tn = SITES.apply(trad_name, axis=1)
SITES["trad"] = tn.map(lambda x: x[0]); SITES["trad_how"] = tn.map(lambda x: x[1])
SITES["unlabelled"] = (SITES.label == "").astype(int)

# ---------- save ----------
K.drop(columns=["subrels"]).to_pickle(f"{WORK}/rels.pkl")
S.to_pickle(f"{WORK}/segs.pkl")
M[["r", "s"]].to_pickle(f"{WORK}/memb.pkl")
pd.Series(rid_list).to_pickle(f"{WORK}/rid_list.pkl")
SITES.to_pickle(f"{WORK}/sites.pkl")
W.to_pickle(f"{WORK}/wdroutes.pkl")
REL.drop(columns=["subrels"]).to_pickle(f"{WORK}/rels_all.pkl")
jsave(cmeta, f"{WORK}/cmeta.json"); jsave(wdiso, f"{WORK}/wdiso.json")
jsave(chk, f"{WORK}/checks.json", indent=1)
print({k: v for k, v in chk.items() if k not in ("family_how", "dropped", "pg")})
print("families:", K.groupby("fam").km_own.agg(["size", "sum"]).round(0).to_dict())
print("how:", chk["family_how"])
print("unique km by owner family:", S.groupby("fam").km.sum().round(0).to_dict())
print("sites", len(SITES), SITES.trad_rec.value_counts().to_dict(), SITES.trad.value_counts().to_dict())
