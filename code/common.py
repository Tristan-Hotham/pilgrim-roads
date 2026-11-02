"""Shared paths, groupings and helpers for the pilgrim-roads project.

Raw inputs (read in place by steps 01 to 03 only, never modified; steps 04 onward read data/ only):
  raw/osm_pilgrim_routes.json   OpenStreetMap route relations tagged as pilgrimage routes or linked to Wikidata pilgrim
                                route items, fetched from the Overpass API: {pg: progress log, geo: {relation id:
                                {tags, ways: [[[lon, lat], ...], ...] (coordinates rounded to 4 dp), subrels: [ids]}}}.
                                (c) OpenStreetMap contributors, ODbL 1.0.
  raw/wd_pilgrim_routes.tsv     Wikidata items that are pilgrim routes or parts of the Way of St James (Q41150), from a
                                QLever SPARQL query: label, type, OSM relation id, length, start, destination, part of,
                                country, English Wikipedia. CC0.
  raw/wd_pilgrim_sites.tsv      Wikidata pilgrimage sites (Q15135589 and similar) with coordinates, country and religion.
                                CC0.
  raw/wiki_pages.json           English Wikipedia articles (HTML with revision ids): Pilgrimage, Way of St. James, Via
                                Francigena, Kumano Kodo, Shikoku Pilgrimage, St. Olav's Way, Pilgrims' Way, Hajj,
                                Arba'een Pilgrimage, Kumbh Mela, Char Dham. CC BY-SA 4.0. Used for facts quoted in the
                                text and the yearly count of Compostela certificates.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson, ne_50m_land.geojson,
      ne_10m_populated_places_simple.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PR_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("PR_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("PR_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("PRTMP", "/dev/shm/pilgrimroads"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "pilgrim-roads"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23878608"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/pilgrim-roads/"          # filled in by the publisher
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
OSM_YEAR = "2026"              # year of the Overpass extract (year only in public copy)

# Santiago de Compostela cathedral, Rome (St Peter's), Trondheim (Nidaros Cathedral)
SANTIAGO = (42.8806, -8.5446)
ROME = (41.9022, 12.4539)
NIDAROS = (63.4269, 10.3969)

# Route families, in priority order (a relation that matches two takes the first). Name, colour.
FAMILIES = [("camino", "Camino de Santiago", "#D2541B"),
            ("francigena", "Via Francigena", "#2F5FA7"),
            ("olav", "St Olav Ways", "#1E8C7E"),
            ("marian", "Marian ways", "#8A55B0"),
            ("other", "Other pilgrim routes", "#7D756A")]
FKEYS = [f[0] for f in FAMILIES]; FNAME = {f[0]: f[1] for f in FAMILIES}; FCOL = {f[0]: f[2] for f in FAMILIES}

# Keyword rules, applied to a relation's names (name, name:*, int_name, alt_name, official_name, short_name), its
# pilgrimage, symbol and wikipedia tags, and its Wikidata id. Matching is on lower case text without accents.
FAM_RE = {
    "camino": re.compile(r"santiago|compostel|jakob|jacob|jacques|jaume|jacu\b|giacomo|jakub|jakab|jokub|jakov|iacob|"
                         r"st\.? ?james|saint james|sant ?iago|camino portugu|caminho portugu|via de la plata|via podiensis|"
                         r"via turonensis|via lemovicensis|via tolosana|via jutlandica|camino frances|camino primitivo|"
                         r"camino del norte|camino ingles|camino sanabres|camino mozarabe|camino de levante|camino de invierno"),
    "francigena": re.compile(r"francigen"),
    "olav": re.compile(r"\bolav|\bolaf|\bolof|olavs|pilegrim|gudbrandsdal|osterdalsled|borgleden|nordleden|valldalsled|tunsbergled|"
                       r"kystpilegrim|\brombo|jamt norgevagen|strasjoleden|vestfoldveien|ingegerd|olavinpolku|nidaros"),
    "marian": re.compile(r"\bmari[aeä]\b|\bmaria[- ]|mariae|marija|marijin|marien|mariazell|marian|our lady|notre dame|"
                         r"madonna|lauretan|czestoch|guadalupe|fatima|lourdes|marians|maria ut|\bmaria\b|svata hora|"
                         r"nossa senhora|virgen|\bmarii\b"),
}
FAM_WD = {"Q41150": "camino", "Q542830": "francigena", "Q18448597": "olav", "Q12008536": "olav"}
SHELL_RE = re.compile(r"shell|muschel|coquille|vieira|concha")
# OSM route values that are not walking, cycling or riding routes
BAD_ROUTE = {"road", "bus", "piste", "fitness_trail"}
# Relations left out after inspection, with the reason
DROP = {"19854819": "a forest trail named after the Pilgrim River (Michigan), not a pilgrimage route",
        "9379732": "a proposed recreational rail trail in Texas, tagged pilgrimage by mistake",
        "2812858": "a short park walk in Canberra named Pilgrim Walk, with no pilgrimage tag",
        "17326168": "an ecological trail in a Colombian paramo, tagged pilgrimage by mistake",
        "17571428": "an ecological trail in a Colombian paramo, tagged pilgrimage by mistake",
        "9182185": "a running and walking route in York named after St Olave's church"}

# Pilgrimage site traditions from Wikidata's religion values (P140). Labels for the QIDs were checked against the sites
# that carry them (for example the Japanese Buddhist school ids all sit on Shikoku temples).
REL_TRAD = {"Q1841": "Christian", "Q597526": "Christian", "Q9592": "Christian", "Q5043": "Christian", "Q194253": "Christian",
            "Q5169816": "Christian", "Q7970362": "Christian", "Q589856": "Christian",
            "Q748": "Buddhist", "Q132265": "Buddhist", "Q3077357": "Buddhist", "Q420739": "Buddhist", "Q550182": "Buddhist",
            "Q3077351": "Buddhist", "Q10437874": "Buddhist", "Q10437754": "Buddhist", "Q11442373": "Buddhist",
            "Q11583514": "Buddhist", "Q674374": "Buddhist", "Q696966": "Buddhist", "Q749085": "Buddhist",
            "Q432": "Muslim", "Q9232": "Jain"}
TRADS = [("Christian", "#2F5FA7"), ("Buddhist", "#D2541B"), ("Muslim", "#1E8C7E"), ("Hindu", "#C0397A"), ("Jain", "#B8860B"), ("Jewish", "#4A6B8A"),
         ("Other", "#6B6257"), ("Not recorded", "#BDB6A8")]
# Name rules for sites with no religion recorded (used only for the "recorded or from the name" split)
TRAD_NAME = [("Buddhist", re.compile(r"\bji\b|\bin temple|\bbou\b|\bwat\b|pagoda|stupa|kyaik|vihara")),
             ("Jewish", re.compile(r"synagog|bar yochai|rabbi|\bkever\b")),
             ("Muslim", re.compile(r"mosque|masjid|mausoleum|turbe|dargah|imamzadeh|\bmazar\b|\bata\b|\bana\b|\bbibi\b|\bbab\b")),
             ("Hindu", re.compile(r"mandir|devi\b|\bdham\b|ghat|\bmata\b|baithak|tirtha|shiva|vishnu|krishna|ganesh|jyotirlinga")),
             ("Christian", re.compile(r"church|kirche|kerk|kirke|kyrka|eglise|iglesia|igreja|chiesa|kosciol|kostel|kaple|kapel|"
                                      r"chapel|basilic|cathedral|sanctuar|santuar|santuari|sanktuar|svatyn|wallfahrt|abbey|abbaye|"
                                      r"abtei|kloster|klooster|monast|convent|our lady|notre dame|nossa senhora|virgen|madonna|"
                                      r"mare de deu|maria|marie|marien|mariae|marija|saint|sankt|\bst\b|san |santa |sao |santo |"
                                      r"shrine of|christ|calvar|kalvar|crucifi|cross|kreuz|kruis|croce|chapelle|capela|capilla|capella|"
                                      r"cappella|heilig|pilgrim|pelegri|pellegrin|peregrin|ermita|hermitage|pustelnia|parish|pfarr|"
                                      r"\bdom\b|duomo|lourdes|fatima|guadalupe|czestochowa|loreto|jasna gora|mariazell|altotting|knock|walsingham|schoenstatt"))]
# country specific: a "temple" in Japan is Buddhist, in India or Nepal Hindu
TRAD_TEMPLE = {"JPN": "Buddhist", "IND": "Hindu", "NPL": "Hindu"}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower().replace("ł", "l").replace("ø", "o").replace("æ", "ae")
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    if f == "r100": return f"{int(round(float(v), -2)):,}"
    if f == "r1000": return f"{int(round(float(v), -3)):,}"
    raise ValueError(f)


def hav(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


def qid(s):
    m = re.search(r"(Q\d+)>?$", s or "")
    return m.group(1) if m else ""


def lit(s):
    """'"label"@en' -> label; '"8436154"' -> 8436154; '' -> ''."""
    s = (s or "").strip()
    m = re.match(r'^"(.*)"(@\w+|\^\^.*)?$', s)
    return m.group(1).replace('\\"', '"') if m else s
