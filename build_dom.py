# -*- coding: utf-8 -*-
import csv, json, os, re, colorsys, shutil
from PIL import Image

DL = r"C:\Users\gabri\Downloads\Psiangelo_Massa"
REPO = r"C:\Users\gabri\psiangelo-posts"
CSV = os.path.join(DL, "posts_metricool_BIG_20mes.csv")
COLORS = os.path.join(DL, "feed_colors.json")
FEED = os.path.join(REPO, "feed.html")

colmap = json.load(open(COLORS, encoding="utf-8"))
recs = []
with open(CSV, encoding="utf-8", newline="") as f:
    for rec in csv.DictReader(f):
        recs.append(rec)
recs.sort(key=lambda r: (r["Date"], r["Time"]))

def cover_of(rec):
    url = rec.get("Picture Url 1", "") or ""
    return url.split("/main/")[1].split("/")[-1] if "/main/" in url else None
def rel_of(rec):
    url = rec.get("Picture Url 1", "") or ""
    return url.split("/main/")[1] if "/main/" in url else ""

# ---------- chave de cor dominante (peel brancos e escuros; resto por matiz) ----------
def block_and_key(cover):
    c = colmap.get(cover)
    if not c:
        return (1, 999, 0)
    L, col, sA, hd = c["light"], c["colorful"], c["sat_all"], c["hue_deg"]
    if L >= 0.55 and col <= 0.33 and sA <= 0.42:      # BLOCO CLARO/BRANCO
        return (0, -L, 0)
    if L <= 0.26 and col <= 0.14:                      # BLOCO ESCURO/NEUTRO
        return (2, -L, 0)
    lin = (hd - 150) % 360                              # jornada de matiz frio->quente
    return (1, lin, -L)

order = sorted(recs, key=lambda r: block_and_key(cover_of(r)))

# ---------- versao de cache ----------
old = open(FEED, encoding="utf-8").read()
m = re.search(r"\?v=(\d+)", old); VER = m.group(1) if m else "1"

def badge_kind(rec):
    fn = cover_of(rec) or ""
    if fn.startswith("narr-"): return "narr"
    if fn.startswith("cit-"): return "cit"
    return "single"
def fmt_date(d):
    y, mo, da = d.split("-"); return f"{da}/{mo}/{y[2:]}"
def cell(pos_rec, content_rec):
    dt = fmt_date(pos_rec["Date"]); src = f"{rel_of(content_rec)}?v={VER}"; k = badge_kind(content_rec)
    if k == "narr":
        return (f'<div class="cell" title="{dt} · narr"><img loading="lazy" src="{src}">'
                f'<div class="badge narr">NARR</div><div class="cic">&#9096;</div><div class="dt">{dt}</div></div>')
    if k == "cit":
        return (f'<div class="cell" title="{dt} · cit"><img loading="lazy" src="{src}">'
                f'<div class="badge cit">CIT</div><div class="cic">&#9096;</div><div class="dt">{dt}</div></div>')
    return f'<div class="cell" title="{dt} · single"><img loading="lazy" src="{src}"><div class="dt">{dt}</div></div>'

idx = old.find('<div class="grid">')
prefix = old[:idx] + '<div class="grid">'
suffix = '</div></body></html>'
new_p = ("<p>Organizado por COR DOMINANTE (bloco claro, jornada frio&rarr;quente, bloco escuro) · "
         "cima&rarr;baixo = mais antigo&rarr;mais novo · 859 posts · "
         "<a href='feed_cronologico.html' style='color:#8a8078'>ver ordem cronol&oacute;gica</a></p>")
prefix = re.sub(r"<p>.*?</p>", new_p, prefix, count=1, flags=re.S)
cells = "\n".join(cell(recs[i], order[i]) for i in range(len(recs)))
open(FEED, "w", encoding="utf-8").write(prefix + cells + suffix)
print("feed.html gerado por cor dominante. Celulas:", len(recs))

# ---------- PREVIA local: fita de cor dominante REAL + grade de thumbs ----------
N = len(order); sw = 2; H1 = 150
ribbon = Image.new("RGB", (N*sw, H1), (18, 18, 20))
for i, rec in enumerate(order):
    c = colmap.get(cover_of(rec))
    rgb = tuple(c["dom_rgb"]) if c else (40, 40, 40)
    for x in range(i*sw, (i+1)*sw):
        for y in range(H1):
            ribbon.putpixel((x, y), rgb)
ribbon.save(os.path.join(DL, "preview_dom_flow.png"))

def sq(path, s):
    im = Image.open(path).convert("RGB"); w, h = im.size; m = min(w, h)
    return im.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m)).resize((s, s))
COLS, CELL, GAP, SHOW = 3, 200, 6, 72
rn = (SHOW+COLS-1)//COLS
grid = Image.new("RGB", (COLS*CELL+(COLS+1)*GAP, rn*CELL+(rn+1)*GAP), (18, 18, 20))
for i in range(min(SHOW, N)):
    rel = order[i].get("Picture Url 1").split("/main/")[1]
    try: th = sq(os.path.join(REPO, *rel.split("/")), CELL)
    except Exception: th = Image.new("RGB", (CELL, CELL), (60, 20, 20))
    grid.paste(th, (GAP+(i % COLS)*(CELL+GAP), GAP+(i//COLS)*(CELL+GAP)))
grid.save(os.path.join(DL, "preview_dom_grid.png"))

# contagem por bloco
from collections import Counter
bl = Counter(block_and_key(cover_of(r))[0] for r in recs)
print("Blocos -> claro:", bl[0], " cor:", bl[1], " escuro:", bl[2])
print("Previews: preview_dom_flow.png / preview_dom_grid.png")
