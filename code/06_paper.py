"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23878608 placeholder.
Reads data/ only."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Pilgrim_Roads"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert [c["iso"] for c in R["total"]["countries"][:6]] == ["DEU", "ESP", "ITA", "POL", "HUN", "AUT"]
assert R["bands"][5]["lo"] == 2000 and R["bands"][5]["top"][0][0] == "Poland"
assert R["longest"][2]["name"] == "Jakobswege Baden-Württemberg"
assert R["total"]["outside"][0]["iso"] == "BRA" and R["total"]["outside"][1]["iso"] == "JPN"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


F = R["fam"]
hw = lambda f, k: F[f]["how"].get(k, 0)
rows = "".join(f"{tex(F[f]['name'])} & {F[f]['relations']:,} & {F[f]['km']:,} & {F[f]['pct_of_all']:.1f}\\% & {F[f]['n_countries']} & {tex(F[f]['countries'][0]['name'])} ({F[f]['countries'][0]['pct']:.0f}\\%) & {hw(f, 'name') + hw(f, 'wikidata') + hw(f, 'wikidata part of')} & {hw(f, 'shell symbol')} & {hw(f, 'parent') + hw(f, 'children')}\\\\\n" for f in FKEYS)
TF = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{Route families: relations, unique kilometres, share of all route kilometres, countries, the leading country, and how the relations were placed (by name or Wikidata link, by scallop shell symbol, or from a parent or children).}\\label{tab:fams}"
      "\\begin{tabular}{lrrrrlrrr}\\toprule Family & Relations & km & Share & Countries & Leading country & Name/WD & Shell & Inherited\\\\\\midrule\n" + rows +
      f"\\midrule All routes & {R['source']['kept']:,} & {R['total']['km']:,} & & {R['total']['n_countries']} & {tex(R['total']['countries'][0]['name'])} ({R['total']['countries'][0]['pct']:.0f}\\%) & & & \\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
cc = [c for c in F["camino"]["countries"] if c["iso"] != "SEA"][:15]
rows = "".join(f"{tex(c['name'])} & {c['km']:,} & {c['pct']:.1f}\\%\\\\\n" for c in cc)
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Waymarked Camino de Santiago by country (top 15): unique kilometres and share of the Camino total.}\\label{tab:camino}"
      "\\begin{tabular}{lrr}\\toprule Country & km & Share\\\\\\midrule\n" + rows + f"\\midrule All {F['camino']['n_countries']} countries & {F['camino']['km']:,} & 100\\%\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(l['name'][:46])} & {tex(l['family'])} & {l['km']:,} & {tex(l['distance_tag']) or ''} & {tex(', '.join(l['countries'][:4]) + (' and others' if len(l['countries']) > 4 else ''))}\\\\\n" for l in R["longest"][:15])
TL = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The fifteen longest top-level route systems: unique kilometres with all descendants, the length in the relation's distance tag where given, and countries in order of length.}\\label{tab:longest}"
      "\\begin{tabular}{p{4.6cm}p{2.6cm}rrp{4.4cm}}\\toprule System & Family & km & Tag & Countries\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("FAMS", TF), ("CAMINO", TC), ("LONGEST", TL)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
