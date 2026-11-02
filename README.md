# Pilgrim roads: the waymarked pilgrimage routes and places of OpenStreetMap and Wikidata

A map and analysis of 77,804 km of waymarked pilgrim routes mapped in OpenStreetMap, each stretch counted once, and 1,330 pilgrimage sites in Wikidata: the Camino de Santiago web across 22 countries, the Via Francigena, the St Olav Ways, the Marian ways of central Europe, the longest routes, and what the open data leave out.

Interactive page: https://maps.tristanhotham.com/pilgrim-roads/
Paper: https://doi.org/10.5281/zenodo.23878608
Blog post: https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/

## Headline results

- Routes: 77,804 km of unique waymarked pilgrim route in 34 countries (the naive sum of all relations is 83,037 km, 6.3% more). Germany 21,446 km, Spain 10,367 km, Italy 10,127 km.
- Camino de Santiago: 41,674 km (54% of all routes) in 22 countries. Germany 14,814 km, 1.49 times Spain's 9,922 km; Poland 5,289 km.
- Fanning out: only 13% of the Camino lies within 500 km of Santiago; half is more than 1,659 km away; the farthest stretch (Camino Podolico, Ukraine) is 2,911 km from the cathedral.
- Other families: Via Francigena 5,120 km (74% in Italy; the longest system, 3,944 km with branches); St Olav Ways 3,011 km; Marian ways 6,750 km (36% in Hungary); other routes 22,862 km.
- Sites: 1,330 Wikidata pilgrimage sites in 70 countries; Germany 239, Italy 225, Spain 163, Japan 114 (108 on Shikoku). Austria has most per head (5.4 per million).
- Pilgrims: Compostela certificates rose from 690 in 1985 to 530,772 in 2025 (Wikipedia).
- Coverage: 99.2% of route km and 73% of sites are in Europe. 100 of 2,028 relation ids failed to download, and 25 of 41 OpenStreetMap relations named by Wikidata pilgrim route items are missing (including the Camino Francés super-route, the Via Turonensis and the Via Tolosana). All totals are lower bounds.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/routes.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/routes.csv` | All 1,893 kept OpenStreetMap relations: id, names, family and why, tags, unique km, km with children, main country, parents and children (including children missing from the extract). ODbL. |
| `data/routes.json` | Simplified route lines per relation (delta encoded, 1e-4 degrees), for the map and figures. ODbL. |
| `data/km_by_country.csv` | Unique km by country, for all routes and each family. ODbL. |
| `data/camino_distance_bands.csv` | Camino km by straight line distance from Santiago. |
| `data/pilgrimage_sites.csv` | The 1,330 Wikidata sites: id, label, coordinates, country, tradition recorded and read from the name. |
| `data/sites_by_country.csv` | Sites per country, per million people and by tradition. |
| `data/compostelas_by_year.csv` | Compostela certificates per year, 1985 to 2025, from Wikipedia. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/world.json`, `data/countries.json`, `data/cities.json` | Page and figure data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Relations: 1,906 OpenStreetMap route relations tagged as pilgrimage routes or linked to Wikidata pilgrim route items, from the Overpass API (2026). 13 left out: road, bus, piste and fitness routes, network relations, and six relations that are not pilgrimage routes (listed in `code/common.py`).
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

Hotham, T. (2026) Pilgrim roads: mapping the waymarked pilgrimage routes and places of OpenStreetMap and Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23878608

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
