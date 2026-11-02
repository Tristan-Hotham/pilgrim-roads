"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json).

Definitions:
  * kilometres: great circle length of unique segments (01_clean.py), so a stretch of path used by several relations is
    counted once. A family's kilometres include every segment any relation of that family uses, so the families can
    overlap a little (overlap reported below); the all routes total counts each segment once.
  * country: Natural Earth 1:10m country of the segment midpoint; 'at sea' = midpoints outside every country outline.
  * route (for 'longest routes'): a top-level relation, one that is not the child of another relation in the extract,
    measured with all its descendants, segments counted once.
  * distance from Santiago: great circle distance from the cathedral of Santiago de Compostela to the segment midpoint.
  * pilgrimage sites: unique Wikidata items; tradition from Wikidata's religion values where given, and in a second
    version also from the site's name (common.TRAD_NAME)."""
import numpy as np, pandas as pd, html as _html
from common import *

S = pd.read_pickle(f"{WORK}/segs.pkl")
S["mask"] = S["mask"].astype(int)
K = pd.read_pickle(f"{WORK}/rels.pkl")
M = pd.read_pickle(f"{WORK}/memb.pkl")
RL = pd.read_pickle(f"{WORK}/rid_list.pkl").tolist(); RIDX = {r: i for i, r in enumerate(RL)}
X = pd.read_pickle(f"{WORK}/sites.pkl")
W = pd.read_pickle(f"{WORK}/wdroutes.pkl")
CHK = jload(f"{WORK}/checks.json")
CM = jload(f"{DATA}/countries.json")
CN = lambda i: "at sea or on the shore" if i == "SEA" else CM.get(i, {}).get("name", i)
CONT = lambda i: "" if i == "SEA" else CM.get(i, {}).get("cont", "")
pc = lambda a, b: round(100 * a / b, 2) if b else None
r0 = lambda v: int(round(float(v)))
R = {}

# ---------- source ----------
dup = CHK["km_raw_sum"] - CHK["km_unique"]
R["source"] = {"ids_requested": CHK["ids_requested"], "failed_batches": CHK["failed_batches"], "ids_failed": CHK["ids_failed"],
               "failed_pct": pc(CHK["ids_failed"], CHK["ids_requested"]), "fetched": CHK["relations_fetched"],
               "kept": len(K), "dropped": len(CHK["dropped"]), "dropped_list": CHK["dropped"],
               "containers": int((K.kids.map(len) > 0).sum()), "superroutes": int((K.type == "superroute").sum()),
               "leaves": int((K.kids.map(len) == 0).sum()), "subrels_listed": CHK["subrels_listed"], "subrels_missing": CHK["subrels_missing"],
               "containers_all_missing": CHK["containers_all_missing"], "empty": CHK["empty_relations"],
               "ways": CHK["ways_in_kept"], "points": CHK["points_in_kept"], "seg_raw": CHK["segments_raw"], "seg_unique": CHK["segments_unique"],
               "km_raw": r0(CHK["km_raw_sum"]), "km": r0(CHK["km_unique"]), "km_dup": r0(dup), "dup_pct": pc(dup, CHK["km_raw_sum"]),
               "km_no_country": r0(CHK["km_no_country"]), "osm_year": OSM_YEAR,
               "with_pilgrimage_tag": int((K.pilgrimage != "").sum()), "with_wikidata": int((K.wikidata != "").sum()),
               "site_rows": CHK["site_rows"], "site_items": CHK["site_items"]}
assert R["source"]["ids_failed"] == 100 and R["source"]["fetched"] == 1906

# ---------- totals and families ----------
bit = {f: ((S["mask"].values >> i) & 1) == 1 for i, f in enumerate(FKEYS)}
tot_c = S.groupby("iso").km.sum().sort_values(ascending=False)
R["total"] = {"km": r0(S.km.sum()), "n_countries": int((tot_c[tot_c.index != "SEA"] >= 1).sum()),
              "countries": [{"iso": i, "name": CN(i), "km": r0(v), "pct": pc(v, S.km.sum())} for i, v in tot_c.items() if v >= 1],
              "multi_family_km": r0(S.km[(np.array([bin(x).count("1") for x in S["mask"]]) > 1)].sum())}
cont = S.assign(c=S.iso.map(CONT)).groupby("c").km.sum()
R["total"]["europe_km"] = r0(cont.get("Europe", 0)); R["total"]["europe_pct"] = pc(cont.get("Europe", 0), S.km.sum())
R["total"]["outside_km"] = r0(S.km.sum() - cont.get("Europe", 0) - cont.get("", 0))
R["total"]["by_continent"] = {k or "at sea": r0(v) for k, v in cont.sort_values(ascending=False).items()}
outside = S[~S.iso.map(CONT).isin(["Europe", ""])].groupby("iso").km.sum().sort_values(ascending=False)
R["total"]["outside"] = [{"iso": i, "name": CN(i), "km": round(float(v), 1)} for i, v in outside.items()]
R["total"]["n_outside_countries"] = int((outside >= 1).sum())

fam = {}
for f in FKEYS:
    sub = S[bit[f]]
    bc = sub.groupby("iso").km.sum().sort_values(ascending=False)
    rr = K[K.fam == f]
    fam[f] = {"name": FNAME[f], "km": r0(sub.km.sum()), "pct_of_all": pc(sub.km.sum(), S.km.sum()), "relations": len(rr),
              "n_countries": int((bc[bc.index != "SEA"] >= 1).sum()),
              "countries": [{"iso": i, "name": CN(i), "km": r0(v), "pct": pc(v, sub.km.sum())} for i, v in bc.items() if v >= 1],
              "how": {k.split("|")[1]: v for k, v in CHK["family_how"].items() if k.startswith(f + "|")}}
    fam[f]["by_iso"] = {c["iso"]: c["km"] for c in fam[f]["countries"]}
R["fam"] = fam
cam = fam["camino"]
cam["de_es_ratio"] = round(cam["by_iso"]["DEU"] / cam["by_iso"]["ESP"], 2)
cam["es_pct"] = pc(cam["by_iso"]["ESP"], cam["km"]); cam["de_pct"] = pc(cam["by_iso"]["DEU"], cam["km"])
cam["outside_es_pt_pct"] = pc(cam["km"] - cam["by_iso"]["ESP"] - cam["by_iso"].get("PRT", 0), cam["km"])
cam["fr_km"] = cam["by_iso"].get("FRA", 0)
cam["shell_rel"] = cam["how"].get("shell symbol", 0)
assert cam["countries"][0]["iso"] == "DEU" and cam["countries"][1]["iso"] == "ESP" and cam["countries"][2]["iso"] == "POL"
fr = fam["francigena"]; fr["it_pct"] = pc(fr["by_iso"]["ITA"], fr["km"])
ol = fam["olav"]; ol["no_pct"] = pc(ol["by_iso"]["NOR"], ol["km"])
mr = fam["marian"]; mr["hu_pct"] = pc(mr["by_iso"]["HUN"], mr["km"])
mr["mariaut_km"] = r0(S.km[S.owner.isin([RIDX[r] for r in K.index[K.fam.eq("marian") & K.name.str.contains(r"Mária|Maria|Marij|Via Mariae", case=False, regex=True)
                                                                   & K.iso.isin(["HUN", "ROU", "SVK", "HRV", "BIH", "SRB", "UKR", "SVN", "AUT"])]])].sum())

# ---------- the Camino fans out from Santiago ----------
cs = S[bit["camino"]].copy()
cs["lat"] = (cs.y1 + cs.y2) / 2e4; cs["lon"] = (cs.x1 + cs.x2) / 2e4
cs["d"] = hav(SANTIAGO[0], SANTIAGO[1], cs.lat, cs.lon)
BANDS = [0, 250, 500, 1000, 1500, 2000, 2500, 3000]
cs["band"] = pd.cut(cs.d, BANDS, right=False, labels=[f"{a:,} to {b:,} km" for a, b in zip(BANDS[:-1], BANDS[1:])])
bands = cs.groupby("band", observed=False).km.sum()
bands_c = cs.groupby(["band", "iso"], observed=False).km.sum().unstack(fill_value=0)
R["bands"] = [{"band": str(b), "lo": lo, "hi": hi, "km": r0(v), "pct": pc(v, cs.km.sum()),
               "top": [[CN(i), r0(k)] for i, k in bands_c.loc[b].sort_values(ascending=False).head(3).items() if k >= 1]}
              for (b, v), lo, hi in zip(bands.items(), BANDS[:-1], BANDS[1:])]
far = cs.loc[cs.d.idxmax()]
north = cs.loc[cs.lat.idxmax()]; east = cs.loc[cs.lon.idxmax()]
CITY = pd.DataFrame(jload(f"{DATA}/cities.json"))


def near_city(lat, lon, minpop=50000):
    c = CITY[CITY["pop"] >= minpop]
    d = hav(lat, lon, c.lat.values, c.lon.values); i = int(np.argmin(d))
    return {"city": c.iloc[i]["name"], "km": r0(d[i])}


def rel_of(seg_row):
    return K.loc[RL[int(seg_row.owner)]]


cam["far_km"] = r0(far.d); cam["far_iso"] = far.iso; cam["far_country"] = CN(far.iso); cam["far_lat"] = round(far.lat, 3); cam["far_lon"] = round(far.lon, 3)
cam["far_near"] = near_city(far.lat, far.lon); cam["far_route"] = rel_of(far)["name"]
cam["north_lat"] = round(north.lat, 2); cam["north_country"] = CN(north.iso); cam["north_route"] = rel_of(north)["name"]; cam["north_near"] = near_city(north.lat, north.lon)
cam["east_lon"] = round(east.lon, 2); cam["east_country"] = CN(east.iso); cam["east_route"] = rel_of(east)["name"]
cam["over1000_pct"] = pc(cs.km[cs.d >= 1000].sum(), cs.km.sum()); cam["over2000_pct"] = pc(cs.km[cs.d >= 2000].sum(), cs.km.sum())
cam["within500_pct"] = pc(cs.km[cs.d < 500].sum(), cs.km.sum())
cam["within100_km"] = r0(cs.km[cs.d < 100].sum())
cam["median_d"] = r0(np.interp(.5, np.cumsum(cs.sort_values("d").km) / cs.km.sum(), cs.sort_values("d").d))
mb = max(R["bands"], key=lambda b: b["km"]); cam["max_band"] = mb["band"]; cam["max_band_pct"] = mb["pct"]
assert cam["far_iso"] == "UKR" and 2800 < cam["far_km"] < 3000
pd.DataFrame([{"distance_band": b["band"], "km_camino": b["km"], "pct": b["pct"], "top_countries": "; ".join(f"{n} {k}" for n, k in b["top"])} for b in R["bands"]]).to_csv(f"{DATA}/camino_distance_bands.csv", index=False)

# ---------- longest routes (top-level relations with all their descendants) ----------
seg_of = M.groupby("r").s.apply(lambda v: v.values)
tops = K[K.parents.map(len) == 0].copy()


def tree_km(r):
    idx = [RIDX[d] for d in K.at[r, "desc"]]
    ss = np.unique(np.concatenate([seg_of[i] for i in idx if i in seg_of.index] or [np.array([], int)]))
    return float(S.km.values[ss].sum()) if len(ss) else 0.0, ss


rows = []
for r in tops.index:
    km, ss = tree_km(r)
    if km <= 0: continue
    isos = S.iso.values[ss]; kk = S.km.values[ss]
    bi = pd.Series(kk).groupby(isos).sum().sort_values(ascending=False)
    rows.append({"id": r, "name": K.at[r, "name"] or f"relation {r}", "fam": K.at[r, "fam"], "km": km, "children": len(K.at[r, "desc"]) - 1,
                 "countries": [CN(i) for i, v in bi.items() if v >= 1 and i != "SEA"], "distance_tag": K.at[r, "distance_tag"], "route": K.at[r, "route"],
                 "network": K.at[r, "network"], "wikidata": K.at[r, "wikidata"]})
T = pd.DataFrame(rows).sort_values("km", ascending=False).reset_index(drop=True)
R["n_top_routes"] = len(T)
R["longest"] = [{"id": t.id, "name": t["name"], "fam": t.fam, "family": FNAME[t.fam], "km": r0(t.km), "children": int(t.children), "countries": t.countries,
                 "distance_tag": t.distance_tag, "route": t.route} for _, t in T.head(20).iterrows()]
R["top_routes_over_500"] = int((T.km >= 500).sum()); R["top_routes_over_1000"] = int((T.km >= 1000).sum())
R["top_routes_median_km"] = round(float(T.km.median()), 1)
L1 = R["longest"][0]
assert L1["km"] > 1000 and L1["name"] == "Via Francigena", L1
# single relations: leaves (no child relations), measured on their own ways
LF = K[K.kids.map(len) == 0].sort_values("km_own", ascending=False)
R["longest_leaf"] = [{"id": r, "name": K.at[r, "name"], "fam": K.at[r, "fam"], "family": FNAME[K.at[r, "fam"]], "km": r0(K.at[r, "km_own"]),
                      "country": CN(K.at[r, "iso"]), "n_iso": int(K.at[r, "n_iso"]), "route": K.at[r, "route"], "distance_tag": K.at[r, "distance_tag"],
                      "top": K.at[K.at[r, "top"], "name"] if False else ""} for r in LF.index[:15]]
R["leaf_over_300"] = int((LF.km_own >= 300).sum()); R["leaf_median_km"] = round(float(LF.km_own[LF.km_own > 0].median()), 1)
assert R["longest_leaf"][0]["name"] == "Camino de Santiago del Sureste"

# ---------- Wikidata pilgrim routes ----------
Wu = W.drop_duplicates("qid")
soc = set(W.qid[W.type == "Q231685"])          # stations of the cross
Wr = Wu[~Wu.qid.isin(soc)]
wosm = Wr[Wr.osm != ""]
inx = wosm.osm.isin(set(K.index) | set(CHK["dropped"]))
R["wd"] = {"items": int(Wu.qid.nunique()), "stations_of_cross": len(soc), "routes": len(Wr), "routes_labelled": int((Wr.label != "").sum()),
           "with_osm": len(wosm), "with_osm_in_extract": int(inx.sum()), "with_osm_missing": int((~inx).sum()),
           "missing_named": sorted(set(wosm[~inx & (wosm.label != "")].label))[:40],
           "with_length": int((Wr.len != "").sum()), "with_en": int((Wr.en != "").sum())}
lab = lambda s: Wr[Wr.label == s]
dz = lab("Darb Zubayda"); assert len(dz) and dz.len.iloc[0] == "1300.0" and dz.osm.iloc[0] == ""
R["wd"]["darb_zubayda_km"] = 1300
for nm in ("French Way", "Via Turonensis", "Via Tolosana", "Sanabria Way", "Catalan Way of saint James", "St Olav Romboway"):
    assert nm in R["wd"]["missing_named"], nm

# ---------- pilgrimage sites ----------
X["country"] = X.iso.map(CN); X["cont"] = X.iso.map(CONT)
bc = X.groupby("iso").size().sort_values(ascending=False)
pop = {i: CM.get(i, {}).get("pop", 0) for i in bc.index}
dens = [{"iso": i, "name": CN(i), "n": int(n), "per_m": round(n / pop[i] * 1e6, 2)} for i, n in bc.items() if n >= 10 and pop[i] > 0]
dens.sort(key=lambda d: -d["per_m"])
tr = X.trad_rec.value_counts(); tn = X.trad.value_counts()
shik = X[X.lon.between(132.0, 134.9) & X.lat.between(32.6, 34.6) & (X.iso == "JPN")]
rec = len(X) - int(tr.get("Not recorded", 0))
R["sites"] = {"n": len(X), "rows": CHK["site_rows"], "unlabelled": int(X.unlabelled.sum()), "n_countries": int(len(bc)),
              "top": [{"iso": i, "name": CN(i), "n": int(n), "pct": pc(n, len(X))} for i, n in bc.head(20).items()],
              "by_iso": {i: int(n) for i, n in bc.items()},
              "dens": dens[:12], "dens_n_countries": len(dens),
              "by_cont": {k: int(v) for k, v in X.groupby("cont").size().sort_values(ascending=False).items()},
              "rec": {k: int(v) for k, v in tr.items()}, "rec_n": rec, "rec_pct": pc(rec, len(X)),
              "rec_christian_pct": pc(tr.get("Christian", 0), rec),
              "trad": {k: int(v) for k, v in tn.items()}, "trad_known": len(X) - int(tn.get("Not recorded", 0)),
              "shikoku": len(shik), "shikoku_buddhist": int((shik.trad == "Buddhist").sum()), "japan": int(bc.get("JPN", 0)),
              "philippines": int(bc.get("PHL", 0))}
st = R["sites"]
st["europe_pct"] = pc(st["by_cont"]["Europe"], st["n"]); st["trad_christian_pct"] = pc(st["trad"]["Christian"], st["n"])
st["trad_christian_known_pct"] = pc(st["trad"]["Christian"], st["trad_known"])
st["top3_pct"] = pc(sum(t["n"] for t in st["top"][:3]), st["n"])
st["outside_europe"] = st["n"] - st["by_cont"]["Europe"]
assert [t["iso"] for t in st["top"][:4]] == ["DEU", "ITA", "ESP", "JPN"] and dens[0]["iso"] == "AUT"
# how many sites lie on or near a mapped route (distance to the nearest segment end point, a close approximation at 10 m spacing)
from scipy.spatial import cKDTree
ex = lambda lon, lat: np.column_stack([np.radians(lon) * np.cos(np.radians(lat)), np.radians(lat)]) * 6371.0
pts = np.vstack([S[["x1", "y1"]].values, S[["x2", "y2"]].values]) / 1e4
TR = cKDTree(ex(pts[:, 0], pts[:, 1]))
dd, _ = TR.query(ex(X.lon.values, X.lat.values))
X["d_route"] = dd
eu = X.cont == "Europe"
st["near1"] = int((dd <= 1).sum()); st["near5"] = int((dd <= 5).sum()); st["near1_pct"] = pc(st["near1"], len(X)); st["near5_pct"] = pc(st["near5"], len(X))
st["eu_near1_pct"] = pc(int((dd[eu.values] <= 1).sum()), int(eu.sum())); st["eu_near5_pct"] = pc(int((dd[eu.values] <= 5).sum()), int(eu.sum()))
st["outside_near5"] = int((dd[~eu.values] <= 5).sum())
assert 100 <= st["shikoku"] <= 110 and st["shikoku_buddhist"] >= st["shikoku"] - 4

# ---------- Wikipedia facts (quoted, CC BY-SA) ----------
WP = jload(f"{RAW}/wiki_pages.json")


def wtext(k):
    h = WP[k]["html"]
    h = re.sub(r"<style.*?</style>|<sup.*?</sup>", "", h, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " ").replace("​", "").replace("﻿", ""))


T_ = {k: wtext(k) for k in WP}
need = {"Way of St. James": ["Pope Alexander VI officially declared the Camino de Santiago to be one of the \"three great pilgrimages of Christendom \", along with Jerusalem and the Via Francigena to Rome", "1492", "beginning of the 9th century", "about 800 km", "320 km", "about 610 km", "about 227 km", "minimum of 100 km", "1993", "Year Pilgrims 2025 530,772",
                             "The next Holy Year pilgrimage will occur in 2027", "Frances (47%)", "Sarria (32%)", "93% do the journey on foot"],
        "Via Francigena": ["Canterbury", "80 stages", "some 1,700 km", "around 990"],
        "Shikoku Pilgrimage": ["88 temples", "approximately 1,200 kilometres", "20 bekkaku"],
        "St. Olav's Way": ["approximately 640 kilometres", "Nidaros Cathedral"],
        "Kumano Kodō": ["In July 2004"],
        "Hajj": ["1,707,301 (2026)"],
        "Arba'een Pilgrimage": ["ten to twenty million pilgrims"],
        "Kumbh Mela": ["About 660 million attended the Kumbh Mela in 2025"]}
for k, ss in need.items():
    for s_ in ss:
        assert s_ in T_[k], (k, s_)
tab = re.search(r"Year Pilgrims (.*?) Holy Years", T_["Way of St. James"]).group(1)
series = [(int(y), int(v.replace(",", ""))) for y, v in re.findall(r"(\d{4}) ([\d,]+)\S?", tab)]
series = sorted(series)
assert series[0] == (1985, 690) and series[-1] == (2025, 530772) and len(series) == 41
CY = dict(series)
R["compostela"] = {"years": [[y, v] for y, v in series], "first_year": 1985, "first": CY[1985], "last_year": 2025, "last": CY[2025],
                   "y2019": CY[2019], "y2020": CY[2020], "y2021": CY[2021], "y2010": CY[2010], "y1993": CY[1993], "y2004": CY[2004], "y1999": CY[1999],
                   "x_since_1985": round(CY[2025] / CY[1985]), "x_since_2004": round(CY[2025] / CY[2004], 1), "x_since_2010": round(CY[2025] / CY[2010], 1)}
pd.DataFrame(series, columns=["year", "compostela_certificates"]).to_csv(f"{DATA}/compostelas_by_year.csv", index=False)
R["wiki"] = {"frances_km": 800, "primitivo_km": 320, "portugues_lisbon_km": 610, "portugues_porto_km": 227, "min_walk_km": 100, "min_cycle_km": 200,
             "unesco_es": 1993, "unesco_fr": 1998, "holy_year_next": 2027, "frances_pct_2024": 47, "sarria_pct_2024": 32, "foot_pct_2024": 93,
             "vf_sigeric_km": "1,700", "vf_stages": 80, "vf_year": 990, "shikoku_temples": 88, "shikoku_km": "1,200", "shikoku_bekkaku": 20,
             "olav_km": 640, "kumano_unesco": 2004, "hajj_2026": 1707301, "arbaeen": "ten to twenty million", "kumbh_2025_m": 660,
             "revid": {k: WP[k]["revid"] for k in WP},
             "rev": {s_: WP[k]["revid"] for s_, k in (("camino", "Way of St. James"), ("vf", "Via Francigena"), ("shikoku", "Shikoku Pilgrimage"), ("olav", "St. Olav's Way"), ("kumano", "Kumano Kodō"), ("hajj", "Hajj"), ("arbaeen", "Arba'een Pilgrimage"), ("kumbh", "Kumbh Mela"), ("pilgrimage", "Pilgrimage"))}}

R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "santiago": list(SANTIAGO)}

# ---------- tables out ----------
top_of = {}
for r in K.index:
    a = r
    seen = set()
    while K.at[a, "parents"] and a not in seen:
        seen.add(a); a = K.at[a, "parents"][0]
    top_of[r] = a
K["top"] = pd.Series(top_of)
own_km = S.groupby("owner").km.sum()
K["km_map"] = [float(own_km.get(RIDX[r], 0.0)) for r in K.index]
tree = {r: tree_km(r)[0] for r in K.index}
K["km_tree"] = pd.Series(tree)
out = K.reset_index()[["id", "name", "name_en", "fam", "own_how", "type", "route", "network", "pilgrimage", "religion", "wikidata", "wikipedia",
                       "distance_tag", "from", "to", "operator", "km_own", "km_tree", "iso", "n_iso", "parents", "kids", "kids_missing", "top"]].copy()
out["family"] = out.fam.map(FNAME); out["country"] = out.iso.map(CN)
for c in ("parents", "kids", "kids_missing"):
    out[c] = out[c].map(lambda v: ";".join(v))
out.rename(columns={"id": "osm_relation", "own_how": "family_from", "km_own": "km_unique", "km_tree": "km_with_children", "iso": "main_country_iso",
                    "n_iso": "n_countries", "kids": "child_relations", "kids_missing": "child_relations_not_in_extract", "top": "top_level_relation",
                    "distance_tag": "osm_distance_tag"}).round({"km_unique": 2, "km_with_children": 2}).drop(columns=["fam"]).to_csv(f"{DATA}/routes.csv", index=False)
kc = pd.DataFrame({FNAME[f]: S[bit[f]].groupby("iso").km.sum() for f in FKEYS}).fillna(0)
kc.insert(0, "all_routes", tot_c)
kc.insert(0, "country", [CN(i) for i in kc.index]); kc.index.name = "iso"
kc.sort_values("all_routes", ascending=False).round(1).to_csv(f"{DATA}/km_by_country.csv")
X[["qid", "label", "lon", "lat", "iso", "country", "trad_rec", "trad", "trad_how", "en"]].rename(
    columns={"qid": "wikidata", "trad_rec": "tradition_recorded", "trad": "tradition_recorded_or_from_name", "trad_how": "tradition_source", "en": "english_wikipedia"}
).to_csv(f"{DATA}/pilgrimage_sites.csv", index=False)
sbc = X.groupby("iso").agg(country=("country", "first"), sites=("qid", "size")).sort_values("sites", ascending=False)
sbc["per_million"] = [round(n / pop[i] * 1e6, 2) if pop.get(i) else None for i, n in sbc.sites.items()]
for t, _ in TRADS:
    sbc[t] = X[X.trad == t].groupby("iso").size().reindex(sbc.index).fillna(0).astype(int)
sbc.to_csv(f"{DATA}/sites_by_country.csv")

# ---------- page data ----------
REL = K[(K.km_map > 0) | (K.kids.map(len) > 0)].copy()
REL = REL.sort_values("km_tree", ascending=False)
RI2 = {r: i for i, r in enumerate(REL.index)}
FI = {f: i for i, f in enumerate(FKEYS)}
rels = [[r, K.at[r, "name"] or "", FI[K.at[r, "fam"]], round(K.at[r, "km_own"], 1), round(K.at[r, "km_tree"], 1), K.at[r, "iso"], K.at[r, "route"],
         RI2.get(K.at[r, "top"], -1) if K.at[r, "top"] != r else -1, K.at[r, "wikidata"], K.at[r, "distance_tag"], len(K.at[r, "kids"]),
         None if np.isnan(K.at[r, "lon"]) else round(float(K.at[r, "lon"]), 3), None if np.isnan(K.at[r, "lat"]) else round(float(K.at[r, "lat"]), 3),
         K.at[r, "name_en"] if K.at[r, "name_en"] != K.at[r, "name"] else "",
         RI2.get(K.at[r, "parents"][0], -1) if K.at[r, "parents"] else -1] for r in REL.index]
TI = {t: i for i, (t, _) in enumerate(TRADS)}
sites = [[round(float(s.lon), 4), round(float(s.lat), 4), s.label, s.iso, TI[s.trad], int(s.trad_how == "name"), s.qid, s.en.replace("https://en.wikipedia.org/wiki/", "")]
         for s in X.itertuples()]
cmap = {i: CN(i) for i in set(K.iso) | set(X.iso) | set(S.iso) if i}
site = {"fams": FAMILIES, "trads": TRADS, "rels": rels,
        "rel_cols": ["osm", "name", "fam", "km_own", "km_tree", "iso", "route", "top", "wikidata", "distance_tag", "n_kids", "lon", "lat", "name_en", "parent"],
        "sites": sites, "site_cols": ["lon", "lat", "label", "iso", "trad", "trad_from_name", "qid", "enwiki"],
        "cname": cmap, "cpos": {i: [v["lx"], v["ly"], v["pop"]] for i, v in CM.items() if v.get("lx") is not None},
        "santiago": list(SANTIAGO), "rome": list(ROME), "nidaros": list(NIDAROS), "bands": BANDS}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "results.json", "routes.csv", "pilgrimage_sites.csv")})
print("source", {k: v for k, v in R["source"].items() if k != "dropped_list"})
print("total", {k: v for k, v in R["total"].items() if k not in ("countries", "outside")}, R["total"]["countries"][:12])
for f in FKEYS:
    print(f, {k: v for k, v in fam[f].items() if k not in ("countries", "by_iso")}, fam[f]["countries"][:6])
print("bands", [(b["band"], b["km"], b["pct"], b["top"]) for b in R["bands"]])
print("longest", [(l["name"], l["family"], l["km"], l["countries"], l["distance_tag"]) for l in R["longest"]])
print("wd", R["wd"])
print("sites", {k: v for k, v in st.items() if k not in ("by_iso",)})
print("compostela", {k: v for k, v in R["compostela"].items() if k != "years"})
