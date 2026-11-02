"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/routes.json (the simplified
route lines, ODbL) is loaded by the page. Facts stated in words are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23878608 and https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/ stay as placeholders for the publisher.
Reads data/ only."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
F, ST, CAM = R["fam"], R["sites"], R["fam"]["camino"]

# facts stated in words (page, blog, paper, collage)
c = [x["iso"] for x in CAM["countries"]]
assert c[:6] == ["DEU", "ESP", "POL", "AUT", "HRV", "CZE"], c[:6]                         # order of the Camino countries
assert CAM["by_iso"]["DEU"] > CAM["by_iso"]["ESP"] and CAM["fr_km"] < 500                  # "more of it in Germany than in Spain", France "almost empty"
assert R["longest"][1]["name"] == "Jakobswege Bayern"                                      # "Bavaria alone carries a network of"
assert R["longest"][0]["name"] == "Via Francigena" and R["longest"][0]["fam"] == "francigena"
b = max(R["bands"], key=lambda x: x["km"]); assert [t[0] for t in b["top"]] == ["Germany", "Austria", "Croatia"]   # "mostly in Germany, Austria and Croatia"
assert CAM["far_route"] == "Camino Podolico" and CAM["north_country"] == "Denmark" and "Nordjylland" in CAM["north_route"]
assert 50 < F["camino"]["pct_of_all"] < 60                                                 # "just over half"
assert ST["top"][0]["iso"] == "DEU" and ST["shikoku"] >= ST["japan"] - 6                     # "Japan's are almost all on one island"
assert [d["iso"] for d in ST["dens"][:3]] == ["AUT", "PRT", "CZE"]
assert ST["rec_christian_pct"] > 90 and R["sites"]["rec"].get("Christian", 0) > 0
assert R["wiki"]["sarria_pct_2024"] == 32                                                  # "nearly a third started at Sarria"
assert [o["iso"] for o in R["total"]["outside"][:2]] == ["BRA", "JPN"] and {o["iso"] for o in R["total"]["outside"][2:]} <= {"ISR", "IND", "TWN", "PSE", "KGZ"}
assert len(DROP) == 6 and R["source"]["dropped"] == 13
for nm in ("French Way", "Via Turonensis", "Via Tolosana", "Sanabria Way", "Catalan Way of saint James", "St Olav Romboway"):
    assert nm in R["wd"]["missing_named"], nm
assert {f["iso"] for f in F["marian"]["countries"][:8]} >= {"HUN", "ROU", "AUT", "SVK", "BIH"}
assert F["olav"]["countries"][0]["iso"] == "NOR" and F["olav"]["countries"][1]["iso"] == "SWE"
assert R["compostela"]["last"] > max(v for y, v in R["compostela"]["years"] if y < 2025)      # "a record"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23878608", "https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json") if x["pop"] >= 200000]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
