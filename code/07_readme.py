"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json. Reads data/ only."""
from common import *

R = jload(f"{DATA}/results.json")
s, t, F, st, cp = R["source"], R["total"], R["fam"], R["sites"], R["compostela"]
C = F["camino"]
N = lambda v: f"{round(v):,}"
readme = f"""# Pilgrim roads: the waymarked pilgrimage routes and places of OpenStreetMap and Wikidata

A map and analysis of {N(t['km'])} km of waymarked pilgrim routes mapped in OpenStreetMap, each stretch counted once, and {N(st['n'])} pilgrimage sites in Wikidata: the Camino de Santiago web across {C['n_countries']} countries, the Via Francigena, the St Olav Ways, the Marian ways of central Europe, the longest routes, and what the open data leave out.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Routes: {N(t['km'])} km of unique waymarked pilgrim route in {t['n_countries']} countries (the naive sum of all relations is {N(s['km_raw'])} km, {s['dup_pct']:.1f}% more). Germany {N(t['countries'][0]['km'])} km, Spain {N(t['countries'][1]['km'])} km, Italy {N(t['countries'][2]['km'])} km.
- Camino de Santiago: {N(C['km'])} km ({C['pct_of_all']:.0f}% of all routes) in {C['n_countries']} countries. Germany {N(C['by_iso']['DEU'])} km, {C['de_es_ratio']:.2f} times Spain's {N(C['by_iso']['ESP'])} km; Poland {N(C['by_iso']['POL'])} km.
- Fanning out: only {C['within500_pct']:.0f}% of the Camino lies within 500 km of Santiago; half is more than {N(C['median_d'])} km away; the farthest stretch ({C['far_route']}, {C['far_country']}) is {N(C['far_km'])} km from the cathedral.
- Other families: Via Francigena {N(F['francigena']['km'])} km ({F['francigena']['it_pct']:.0f}% in Italy; the longest system, {N(R['longest'][0]['km'])} km with branches); St Olav Ways {N(F['olav']['km'])} km; Marian ways {N(F['marian']['km'])} km ({F['marian']['hu_pct']:.0f}% in Hungary); other routes {N(F['other']['km'])} km.
- Sites: {N(st['n'])} Wikidata pilgrimage sites in {st['n_countries']} countries; Germany {st['by_iso']['DEU']}, Italy {st['by_iso']['ITA']}, Spain {st['by_iso']['ESP']}, Japan {st['by_iso']['JPN']} ({st['shikoku']} on Shikoku). Austria has most per head ({st['dens'][0]['per_m']:.1f} per million).
- Pilgrims: Compostela certificates rose from {N(cp['first'])} in 1985 to {N(cp['last'])} in 2025 (Wikipedia).
- Coverage: {t['europe_pct']:.1f}% of route km and {st['europe_pct']:.0f}% of sites are in Europe. {s['ids_failed']} of {N(s['ids_requested'])} relation ids failed to download, and {R['wd']['with_osm_missing']} of {R['wd']['with_osm']} OpenStreetMap relations named by Wikidata pilgrim route items are missing (including the Camino Francés super-route, the Via Turonensis and the Via Tolosana). All totals are lower bounds.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/routes.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/routes.csv` | All {N(s['kept'])} kept OpenStreetMap relations: id, names, family and why, tags, unique km, km with children, main country, parents and children (including children missing from the extract). ODbL. |
| `data/routes.json` | Simplified route lines per relation (delta encoded, 1e-4 degrees), for the map and figures. ODbL. |
| `data/km_by_country.csv` | Unique km by country, for all routes and each family. ODbL. |
| `data/camino_distance_bands.csv` | Camino km by straight line distance from Santiago. |
| `data/pilgrimage_sites.csv` | The {N(st['n'])} Wikidata sites: id, label, coordinates, country, tradition recorded and read from the name. |
| `data/sites_by_country.csv` | Sites per country, per million people and by tradition. |
| `data/compostelas_by_year.csv` | Compostela certificates per year, 1985 to 2025, from Wikipedia. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/world.json`, `data/countries.json`, `data/cities.json` | Page and figure data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Relations: {N(s['fetched'])} OpenStreetMap route relations tagged as pilgrimage routes or linked to Wikidata pilgrim route items, from the Overpass API ({s['osm_year']}). {s['dropped']} left out: road, bus, piste and fitness routes, network relations, and six relations that are not pilgrimage routes (listed in `code/common.py`).
- No double counting: every way split into point pairs (coordinates to 4 decimal places, about 10 m); each segment counted once whichever relations use it. Country from the segment midpoint (Natural Earth 1:10m).
- Families: keyword rules on names in many languages, pilgrimage, symbol and Wikipedia tags, Wikidata ids and the scallop shell symbol; stages inherit from their route. The family and the reason are in `data/routes.csv`.
- Distance from Santiago: great circle distance from the cathedral (42.8806 N, 8.5446 W) to each segment's midpoint.
- Sites: unique Wikidata items; country from Wikidata checked against the point; tradition from Wikidata's religion, and a rough second reading from the name.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely 2, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Steps 01 to 03 read the raw inputs in `raw/` (not published: the Overpass extract, the two Wikidata query results and the Wikipedia pages) and Natural Earth in `/home/claude/newdata/raw/geo/`; steps 04 onward read `data/` only. Intermediate files go to `/dev/shm/pilgrimroads/work` (set `PRTMP` to change).

```
python3 code/01_clean.py        # relations, families, unique segments, countries; Wikidata sites
python3 code/02_geo.py          # outlines, city labels, simplified route lines
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- OpenStreetMap route relations, © OpenStreetMap contributors, Open Database License (ODbL) 1.0 (https://www.openstreetmap.org/copyright). The route geometry and tables derived from them (`data/routes.json`, `data/routes.csv`, `data/km_by_country.csv`) are released under the ODbL.
- Wikidata pilgrimage sites and pilgrim route items, CC0.
- Wikipedia articles listed in the paper, CC BY-SA 4.0, for facts quoted in the text and the yearly certificate counts.
- Natural Earth countries, land and populated places, public domain.
- Optional relief tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Pilgrim roads: mapping the waymarked pilgrimage routes and places of OpenStreetMap and Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/meteorite-falls/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0, except as follows. The route data
are derived from OpenStreetMap, (c) OpenStreetMap contributors, and the files
derived from it (data/routes.json, data/routes.csv, data/km_by_country.csv and
the route figures) are made available under the Open Database License (ODbL)
1.0: https://opendatacommons.org/licenses/odbl/1-0/. Wikidata is CC0.
Wikipedia facts and certificate counts are from articles under CC BY-SA 4.0.
Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every waymarked pilgrim route in OpenStreetMap: {N(t['km'])} km. More than half lead to Santiago de Compostela, and there is more of the Way of St James in Germany ({N(C['by_iso']['DEU'])} km) than in Spain ({N(C['by_iso']['ESP'])} km)

## Body

I took {N(s['fetched'])} OpenStreetMap route relations tagged as pilgrimage routes and measured them without counting any stretch twice (stages, super-routes and cycling versions overlap a lot: the naive total is {N(s['km_raw'])} km). {N(C['km'])} km are signed for Santiago, in {C['n_countries']} countries, and only {C['within500_pct']:.0f}% of that lies within 500 km of the cathedral: half is more than {N(C['median_d'])} km away, mostly in Germany, Poland and Austria, and the farthest stretch is in Ukraine, {N(C['far_km'])} km away. Also mapped: the Via Francigena to Rome ({N(F['francigena']['km'])} km), the St Olav Ways to Trondheim ({N(F['olav']['km'])} km), the Marian ways of Hungary ({N(F['marian']['km'])} km) and {N(st['n'])} pilgrimage sites from Wikidata. Caveats: this is what volunteers have mapped, not where pilgrims walk; it is {t['europe_pct']:.0f}% European (the Hajj, Arba'een and Kumbh Mela do not appear as routes); and some famous routes, including the last stretch of the Camino Francés and most French routes, are missing from the download, so every total is a lower bound. Interactive map with search and distance rings: {PAGE}

## Source comment

Sources: OpenStreetMap route relations tagged pilgrimage, via the Overpass API (© OpenStreetMap contributors, ODbL); Wikidata pilgrimage sites (CC0); Compostela certificate counts and historical facts from Wikipedia (CC BY-SA); outlines from Natural Earth. Kilometres = unique way segments (coordinates to about 10 m), each counted once; families from route names, Wikidata links and the scallop shell symbol; distances from Santiago are straight lines.

Tools: Python (pandas, shapely, pyproj, scipy, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for tx in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in tx.replace("```", "").replace("|---|---|", ""), bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
