# -*- coding: utf-8 -*-
# Ritmo FIXO: 2 cards unicos + 1 carrossel (narrativo ou citacao), com cor fluindo.
import csv, json, os, re
from collections import deque
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
def is_carousel(rec):
    fn = cover_of(rec) or ""
    return fn.startswith("narr-") or fn.startswith("cit-")

# ---------- chave de cor (bloco de claros, jornada de matiz, bloco de escuros) ----------
def color_key(cover):
    c = colmap.get(cover)
    if not c:
        return (1, 999, 0)
    L, col, sA, hd = c["light"], c["colorful"], c["sat_all"], c["hue_deg"]
    if L >= 0.55 and col <= 0.33 and sA <= 0.42:
        return (0, -L, 0)
    if L <= 0.26 and col <= 0.14:
        return (2, -L, 0)
    return (1, (hd - 150) % 360, -L)

singles = deque(sorted([r for r in recs if not is_carousel(r)], key=lambda r: color_key(cover_of(r))))
carous  = deque(sorted([r for r in recs if is_carousel(r)],     key=lambda r: color_key(cover_of(r))))
nS, nC = len(singles), len(carous)

# ---------- intercalar 2 cards : 1 carrossel, distribuindo os cards extras ----------
extra = nS - 2*nC          # cards alem do estrito 2:1
if extra < 0: extra = 0
order = []
acc = 0
for _ in range(nC):
    take = 2
    acc += extra
    if nC and acc >= nC:
        acc -= nC
        take = 3           # de vez em quando 3 cards (nunca 2 carrosseis juntos)
    for _ in range(take):
        if singles: order.append(singles.popleft())
    if carous: order.append(carous.popleft())
while singles: order.append(singles.popleft())
while carous:  order.append(carous.popleft())
assert len(order) == len(recs), (len(order), len(recs))

# ---------- gerar feed.html ----------
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
new_p = ("<p>Ritmo 2 cards : 1 carrossel · cor fluindo (claros&rarr;frios&rarr;quentes&rarr;escuros) · "
         "cima&rarr;baixo = mais antigo&rarr;mais novo · 859 posts · "
         "<a href='feed_cronologico.html' style='color:#8a8078'>ver ordem cronol&oacute;gica</a></p>")
prefix = re.sub(r"<p>.*?</p>", new_p, prefix, count=1, flags=re.S)
cells = "\n".join(cell(recs[i], order[i]) for i in range(len(recs)))
open(FEED, "w", encoding="utf-8").write(prefix + cells + suffix)

# ---------- checagens + previa ----------
seq = ["C" if is_carousel(r) else "s" for r in order]
runs_cc = sum(1 for i in range(1, len(seq)) if seq[i] == "C" and seq[i-1] == "C")
print(f"singles={nS} carrosseis={nC} extra_cards={extra}")
print("padrao (primeiros 24):", "".join(seq[:24]))
print("pares de carrossel adjacentes (deve ser 0):", runs_cc)

def sq(path, s):
    im = Image.open(path).convert("RGB"); w, h = im.size; mm = min(w, h)
    return im.crop(((w-mm)//2, (h-mm)//2, (w-mm)//2+mm, (h-mm)//2+mm)).resize((s, s))
COLS, CELL, GAP, SHOW = 3, 200, 6, 72
rn = (SHOW+COLS-1)//COLS
grid = Image.new("RGB", (COLS*CELL+(COLS+1)*GAP, rn*CELL+(rn+1)*GAP), (18, 18, 20))
for i in range(min(SHOW, len(order))):
    rel = order[i].get("Picture Url 1").split("/main/")[1]
    try: th = sq(os.path.join(REPO, *rel.split("/")), CELL)
    except Exception: th = Image.new("RGB", (CELL, CELL), (60, 20, 20))
    grid.paste(th, (GAP+(i % COLS)*(CELL+GAP), GAP+(i//COLS)*(CELL+GAP)))
grid.save(os.path.join(DL, "preview_ritmo_grid.png"))
print("previa: preview_ritmo_grid.png")
