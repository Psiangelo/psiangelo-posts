# -*- coding: utf-8 -*-
import csv, json, os, re
from collections import defaultdict, deque

BASE = r"C:\Users\gabri\Downloads\Psiangelo_Massa"
REPO = r"C:\Users\gabri\psiangelo-posts"
CSV = os.path.join(BASE, "posts_metricool_BIG_20mes.csv")
COLORS = os.path.join(BASE, "feed_colors.json")
FEED = os.path.join(REPO, "feed.html")

with open(COLORS, encoding="utf-8") as f:
    colmap = json.load(f)

# ---- ler linhas do CSV, ordenar por data ----
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

def type_of(rec):
    return colmap.get(cover_of(rec), {}).get("type", "cartela")

# ---- ordenar cada tipo por cor (jornada com costura no teal) ----
def color_key(rec):
    c = colmap.get(cover_of(rec))
    if not c:
        return (999, 0)
    lin = (c["hue_deg"] - 150) % 360
    return (lin, -c["val"])

by_type = defaultdict(list)
for rec in recs:
    by_type[type_of(rec)].append(rec)
for t in by_type:
    by_type[t].sort(key=color_key)
queues = {t: deque(v) for t, v in by_type.items()}

# ---- preencher cada slot (mesmo tipo de antes) com o proximo do tipo em ordem de cor ----
new_order = [queues[type_of(rec)].popleft() for rec in recs]

# ---- versao de cache das imagens (reaproveita a existente) ----
old = open(FEED, encoding="utf-8").read()
m = re.search(r"\?v=(\d+)", old)
VER = m.group(1) if m else "1"

def badge_kind(rec):
    fn = cover_of(rec) or ""
    if fn.startswith("narr-"):
        return "narr"
    if fn.startswith("cit-"):
        return "cit"
    return "single"

def fmt_date(d):  # YYYY-MM-DD -> DD/MM/YY
    y, mo, da = d.split("-")
    return f"{da}/{mo}/{y[2:]}"

def cell(pos_rec, content_rec):
    dt = fmt_date(pos_rec["Date"])
    src = f"{rel_of(content_rec)}?v={VER}"
    kind = badge_kind(content_rec)
    if kind == "narr":
        return (f'<div class="cell" title="{dt} · narr"><img loading="lazy" src="{src}">'
                f'<div class="badge narr">NARR</div><div class="cic">&#9096;</div><div class="dt">{dt}</div></div>')
    if kind == "cit":
        return (f'<div class="cell" title="{dt} · cit"><img loading="lazy" src="{src}">'
                f'<div class="badge cit">CIT</div><div class="cic">&#9096;</div><div class="dt">{dt}</div></div>')
    return (f'<div class="cell" title="{dt} · single"><img loading="lazy" src="{src}">'
            f'<div class="dt">{dt}</div></div>')

# ---- prefixo (head+header) e sufixo, reaproveitando o estilo existente ----
idx = old.find('<div class="grid">')
prefix = old[:idx] + '<div class="grid">'
suffix = '</div></body></html>'

# atualizar subtitulo do prefixo (organizado por cor)
new_p = ("<p>Organizado por COR mantendo o ritmo de formatos · "
         "cima&rarr;baixo = mais antigo&rarr;mais novo · 859 posts · "
         "<a href='feed_cronologico.html' style='color:#8a8078'>ver ordem cronol&oacute;gica</a></p>")
prefix = re.sub(r"<p>.*?</p>", new_p, prefix, count=1, flags=re.S)

cells = "\n".join(cell(recs[i], new_order[i]) for i in range(len(recs)))
open(FEED, "w", encoding="utf-8").write(prefix + cells + suffix)

# ---- backup cronologico (ordem original), com link pra versao em cor ----
cron_cells = "\n".join(cell(recs[i], recs[i]) for i in range(len(recs)))
cron_prefix = old[:idx] + '<div class="grid">'
cron_p = ("<p>Ordem cronol&oacute;gica (cima&rarr;baixo = mais antigo&rarr;mais novo) · 859 posts · "
          "<a href='feed.html' style='color:#C6A05B'>ver organizado por cor</a></p>")
cron_prefix = re.sub(r"<p>.*?</p>", cron_p, cron_prefix, count=1, flags=re.S)
open(os.path.join(REPO, "feed_cronologico.html"), "w", encoding="utf-8").write(cron_prefix + cron_cells + suffix)

print("feed.html gerado na nova ordem por cor. Celulas:", len(recs))
print("backup: feed_cronologico.html")
# checagem: tipos por posicao identicos ao original?
same = all(type_of(recs[i]) == type_of(new_order[i]) for i in range(len(recs)))
print("Ritmo de formatos preservado (tipo por posicao identico):", same)
