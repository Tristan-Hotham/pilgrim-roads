"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23878608, https://doi.org/10.5281/zenodo.23878608 and https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/ stay as placeholders for the publisher. Reads data/ only."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Pilgrim_Roads"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
C = R["fam"]["camino"]
assert [(c["name"], c["km"]) for c in C["countries"][:3]] == [("Germany", 14814), ("Spain", 9922), ("Poland", 5289)]
assert [c["name"] for c in C["countries"] if c["iso"] != "SEA"][3:14] == ["Austria", "Croatia", "Czechia", "Italy", "Denmark", "Portugal", "Slovenia", "Slovakia", "Hungary", "Switzerland", "France"]
assert C["by_iso"]["FRA"] == 462
assert [b["km"] for b in R["bands"]] == [2243, 3135, 5601, 4564, 17125, 8004, 1003] and round(R["bands"][4]["pct"]) == 41
assert [t[0] for t in R["bands"][6]["top"][:2]] == ["Poland", "Ukraine"] and [t[0] for t in R["bands"][5]["top"][:1]] == ["Poland"]
L = R["longest"]
assert [(l["name"], l["km"]) for l in L[:4]] == [("Via Francigena", 3944), ("Jakobswege Bayern", 2696), ("Jakobswege Baden-Württemberg", 2227), ("Jakobsweg Österreich", 1416)]
assert L[11]["name"] == "Wanderroute Via Nova" and L[11]["km"] == 852 and L[5]["name"] == "Lutherweg"
st = R["sites"]
assert st["n"] == 1330 and st["trad"]["Muslim"] > 0 and st["trad"]["Hindu"] > 0
cy = dict(R["compostela"]["years"]); assert cy[1985] == 690 and cy[2025] == 530772 and cy[2020] == 54144

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23878608", "https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/", "10.5281/zenodo.23878608"}
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s, t = R["source"], R["total"]
meta = {"title": "Pilgrim roads: there is more of the Way of St James in Germany than in Spain",
        "slug": "pilgrim-roads",
        "excerpt": f"I measured every waymarked pilgrim route in OpenStreetMap without counting any stretch twice: {t['km']:,} km. {C['km']:,} km lead to Santiago, and Germany has {C['by_iso']['DEU']:,} km of them against Spain's {C['by_iso']['ESP']:,}.",
        "seo_description": f"A map of {t['km']:,} km of waymarked pilgrim routes and {st['n']:,} pilgrimage sites: the Camino web, the Via Francigena and the St Olav Ways.",
        "tags": ["pilgrimage", "Camino de Santiago", "Way of St James", "Via Francigena", "OpenStreetMap", "Wikidata", "maps", "data visualisation"],
        "header_alt": f"Title card reading 'Pilgrim roads' in orange and black on pale paper, beside a map of Europe covered in coloured route lines: an orange web of Camino routes across Spain, Germany and Poland, a blue Via Francigena down Italy, teal St Olav Ways in Norway and Sweden and purple Marian ways in Hungary, with dashed rings around Santiago de Compostela. Text: {t['km']:,} km of waymarked pilgrim routes, {C['km']:,} km of them signed for Santiago, and {st['n']:,} pilgrimage sites."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/pilgrim-roads_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"pilgrim-roads/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"pilgrim-roads/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "pilgrim-roads/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Pilgrim Roads: Mapping the Waymarked Pilgrimage Routes and Places of OpenStreetMap and Wikidata",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Route data © OpenStreetMap contributors, ODbL 1.0; route files derived from it are released under the ODbL. Pilgrimage sites: Wikidata, CC0.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["pilgrimage", "Camino de Santiago", "Way of St James", "Via Francigena", "St Olav Ways", "OpenStreetMap", "Wikidata", "volunteered geographic information", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "notes": "Text, figures and derived data CC BY 4.0, except files derived from OpenStreetMap (data/routes.json, data/routes.csv, data/km_by_country.csv), which are ODbL 1.0. Code MIT.",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.openstreetmap.org", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.wikidata.org", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
