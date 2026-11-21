#!/usr/bin/env python3
"""Build carbonenergynexus.com from content/*.json.

Usage: python3 tools/build.py   (the newest edition becomes the homepage)
Writes: index.html, archive/<date>.html, archive/index.html, calculator.html, frameworks.html,
        privacy.html, feed.xml, sitemap.xml, robots.txt, llms.txt,
        social/<date>[-midday|-evening][-story].png, captions and social/today.json
"""
import json, glob, os, html, hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

editions = sorted(p for p in glob.glob("content/*.json") if os.path.basename(p)[:4].isdigit())
if not editions:
    raise SystemExit("no content files")
data = [json.load(open(p)) for p in editions]
latest = data[-1]
CFG = json.load(open("site.json")) if os.path.exists("site.json") else {}
_ga = "https://www.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com" if CFG.get("ga_id") else ""
CSP = (f"default-src 'self'; script-src 'self' {('https://www.googletagmanager.com' if _ga else '')}; style-src 'self' 'unsafe-inline'; "
       f"img-src 'self' data: https://upload.wikimedia.org {_ga}; font-src 'self'; connect-src 'self' {_ga}; object-src 'none'; "
       "base-uri 'self'; form-action 'self'; upgrade-insecure-requests").replace("  ", " ").replace(" ;", ";")
V = hashlib.md5("".join(open(f).read() for f in ["assets/style.css", "assets/calc.css", "assets/calc.js", "assets/ga.js"]).encode()).hexdigest()[:8]
STAGES = ["Announced", "Feasibility", "Engineering (FEED)", "Permits and contracts", "Final investment decision", "Construction", "Operating"]
os.makedirs("archive", exist_ok=True)
os.makedirs("social", exist_ok=True)

SITE = "https://carbonenergynexus.com/"
NAME = "Carbon Energy Nexus"
ORG = {"@type": "NewsMediaOrganization", "@id": SITE + "#org", "name": NAME, "url": SITE,
       "logo": {"@type": "ImageObject", "url": SITE + "brand/cen-icon-512.png", "width": 512, "height": 512},
       "description": "Sourced daily intelligence on carbon, energy, water and capital: projects, policy, markets and research.",
       "sameAs": CFG.get("same_as", [])}

def published(d):
    return datetime.strptime(d["date"] + " " + CFG.get("publish_time", "05:30"), "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("America/Chicago")).isoformat()
def summary(d):
    t = d.get("social", {}).get("caption", "").split("\n")[0].strip() or d["lead"]["dek"]
    if len(t) > 300:
        t = t[:300].rsplit(". ", 1)[0] + "."
    return t
def page_url(d, archived):
    return SITE + (f"archive/{d['date']}.html" if archived else "")
def ld_for(d, archived):
    url = page_url(d, archived)
    art = {"@type": "NewsArticle", "@id": url + "#article", "headline": d["lead"]["headline"][:110],
           "description": summary(d), "url": url, "mainEntityOfPage": url,
           "image": [SITE + f"social/{d['date']}.png"], "datePublished": published(d), "dateModified": published(d),
           "inLanguage": "en-US", "isAccessibleForFree": True,
           "articleSection": [d["lead"]["kicker"]] + [b["lane"] for b in d.get("briefs", [])],
           "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"}}
    graph = [ORG, art]
    if not archived:
        graph.append({"@type": "WebSite", "@id": SITE + "#site", "name": NAME, "url": SITE, "publisher": {"@id": SITE + "#org"}, "inLanguage": "en-US"})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")

page = env.get_template("page.html.j2")
common = dict(v=V, cfg=CFG, csp=CSP, stages=STAGES)
open("index.html", "w").write(page.render(d=latest, root="", archived=False, url=SITE, published=published(latest), desc=summary(latest), ld=ld_for(latest, False), **common))
for d in data:
    open(f"archive/{d['date']}.html", "w").write(page.render(d=d, root="../", archived=True, url=page_url(d, True), published=published(d), desc=summary(d), ld=ld_for(d, True), **common))

calc_ld = json.dumps({"@context": "https://schema.org", "@type": "WebApplication", "name": "Energy and carbon footprint calculator",
                      "url": SITE + "calculator.html", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any",
                      "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                      "publisher": {"@id": SITE + "#org"}}).replace("</", "<\\/")
open("calculator.html", "w").write(env.get_template("calculator.html.j2").render(ld=calc_ld, **common))
open("frameworks.html", "w").write(env.get_template("frameworks.html.j2").render(**common))

# Simple pages share the header and footer
def simple(title, desc, canonical, body, root=""):
    hdr = env.get_template("header.html.j2").render(root=root)
    ftr = env.get_template("footer.html.j2").render(root=root, cfg=CFG)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin">
<title>{html.escape(title)} | {NAME}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{canonical}"><meta name="robots" content="index, follow"><link rel="icon" type="image/svg+xml" href="{root}brand/cen-icon.svg"><link rel="stylesheet" href="{root}assets/style.css?v={V}"></head>
<body>{hdr}<main id="main" class="page"><div class="wrap">{body}</div></main>{ftr}</body></html>"""

items = "\n".join(f'<li><a href="{d["date"]}.html">{html.escape(d["date_long"])}</a><br><span>{html.escape(d["lead"]["headline"])}</span></li>' for d in reversed(data))
open("archive/index.html", "w").write(simple("Past editions", "Every Carbon Energy Nexus edition, kept so readers can check what we reported against what happened.", SITE + "archive/",
    f'<h1>Past editions</h1><p class="dek">Every edition, kept so you can check what we reported against what happened next.</p><ul class="archive-list">{items}</ul>', root="../"))

_ga_text = ("""<h2>Analytics</h2><p>We use Google Analytics 4 to count visits and learn which pages are useful. It records pages viewed, the referring site, general location (city or region), and device and browser type, and it uses cookies to tell new visitors from returning ones. We see totals and trends, not who you are. You can block it with Google's <a href="https://tools.google.com/dlpage/gaoptout">opt-out add-on</a> or by blocking cookies; the site works the same.</p>"""
    if CFG.get("ga_id") else "<h2>Analytics</h2><p>We do not run analytics or tracking on this site. If we add visitor analytics, this page will say so first.</p>")
open("privacy.html", "w").write(simple("Privacy", "How Carbon Energy Nexus handles visitor data.", SITE + "privacy.html",
    f"""<div class="prose"><h1>Privacy</h1><p>Last updated {latest['date_long']}.</p><p>Carbon Energy Nexus is free to read. You do not need an account, and we do not sell, rent or share personal information.</p>{_ga_text}
<h2>The calculator</h2><p>The footprint calculator runs entirely in your browser. Nothing you type is sent to us or stored.</p>
<h2>Hosting</h2><p>The site is hosted on GitHub Pages, which keeps standard server logs, including IP addresses, for security. See <a href="https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages#data-collection">GitHub's note on data collection</a>.</p></div>"""))

# RSS
def rfc822(ds):
    return datetime.strptime(ds, "%Y-%m-%d").replace(hour=11, minute=30).strftime("%a, %d %b %Y %H:%M:%S +0000")
entries = "".join(f"""<item><title>{html.escape(d['lead']['headline'])}</title><link>{page_url(d, True)}</link><guid>{page_url(d, True)}</guid>
<pubDate>{rfc822(d['date'])}</pubDate><description>{html.escape(summary(d))}</description><enclosure url="{SITE}social/{d['date']}.png" type="image/png" length="0"/></item>""" for d in reversed(data[-30:]))
open("feed.xml", "w").write(f"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{NAME}</title><link>{SITE}</link>
<description>Sourced daily intelligence on carbon, energy, water and capital.</description>{entries}</channel></rss>""")

# Search and AI discovery
urls = [(SITE, latest["date"], "daily", "1.0"), (SITE + "calculator.html", latest["date"], "monthly", "0.9"), (SITE + "frameworks.html", latest["date"], "monthly", "0.7"),
        (SITE + "archive/", latest["date"], "daily", "0.6")] + [(page_url(d, True), d["date"], "monthly", "0.7") for d in reversed(data)] + [(SITE + "privacy.html", latest["date"], "yearly", "0.2")]
open("sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(f"<url><loc>{u}</loc><lastmod>{m}</lastmod><changefreq>{c}</changefreq><priority>{p}</priority></url>" for u, m, c, p in urls) + "\n</urlset>\n")
bots = ["Googlebot", "Bingbot", "Applebot", "DuckDuckBot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
        "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "meta-externalagent", "Meta-ExternalFetcher",
        "FacebookBot", "CCBot", "Amazonbot", "cohere-ai"]
open("robots.txt", "w").write("# Carbon Energy Nexus welcomes search engines and AI assistants.\n# Quote and link freely; please credit Carbon Energy Nexus and link to carbonenergynexus.com.\n\n"
    + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n")
L = [f"# {NAME}", "", "> A free daily publication at carbonenergynexus.com on where carbon, energy, water and capital meet: CO2 capture and storage, carbon markets and removals, energy policy, produced water and the water footprint of energy, project finance and research. Each edition sorts news by electrons (power), molecules (fuels), pore space (the subsurface) and water, tracks projects on a seven step ladder from announcement to operation, and says what each story means for investors, regulators, industry and founders. Facts are sourced and dated; stages and outlooks are labeled as our judgment. General information, not investment advice.", "",
     "## Tools", f"- [Energy and carbon footprint calculator]({SITE}calculator.html): households and companies, EPA and EIA factors, transparent Nexus Score",
     f"- [Frameworks]({SITE}frameworks.html): how projects, policy and carbon claims are judged", "",
     "## Today's edition", f"- [{latest['lead']['headline']}]({SITE}): {latest['date_long']}. {summary(latest)}"]
L += [f"- [{b['lane']}: {b['headline']}]({SITE}#{b['id']})" for b in latest.get("briefs", [])]
L += ["", "## Archive and feeds", f"- [Past editions]({SITE}archive/)", f"- [RSS feed]({SITE}feed.xml)", f"- [Sitemap]({SITE}sitemap.xml)", "", "## Recent editions"]
L += [f"- [{d['date_long']}: {d['lead']['headline']}]({page_url(d, True)})" for d in list(reversed(data))[:30]]
open("llms.txt", "w").write("\n".join(L) + "\n")

# Social graphics: layouts and palettes rotate by date and slot so posts never look copy pasted
import re, datetime
G, PAPER, VOLT, EMBER, AQ, MUTE, LINE, WAT = (26, 34, 38), (238, 242, 241), (242, 193, 78), (228, 87, 46), (43, 138, 158), (174, 185, 183), (58, 70, 76), (95, 184, 230)
NEXUS, ENERGY = (31, 122, 140), (208, 72, 30)
def F(w, s): return ImageFont.truetype(f"tools/fonts/{w}.ttf", s)
SERIF, SERIFB, SANS, SANSM, SANSB = "SourceSerif4-SemiBold", "SourceSerif4-Bold", "IBMPlexSans-Regular", "IBMPlexSans-Medium", "IBMPlexSans-SemiBold"
LOGO = {True: Image.open("brand/cen-lockup-white-1200.png").convert("RGBA"), False: Image.open("brand/cen-lockup-light-1200.png").convert("RGBA")}
_w = LOGO[True]; LOGO["solid"] = Image.merge("RGBA", (*[Image.new("L", _w.size, 255)] * 3, _w.split()[3]))
MARK = {True: Image.open("brand/cen-mark-white-400.png").convert("RGBA"), False: Image.open("brand/cen-mark-dark-400.png").convert("RGBA")}
THEMES = {  # alternating dark and light so each day mixes both
    "graphite": dict(bg=G, fg=PAPER, mute=MUTE, acc=VOLT, acc2=(79, 176, 194), line=LINE, dark=True),
    "paper": dict(bg=(244, 246, 245), fg=G, mute=(92, 104, 108), acc=ENERGY, acc2=NEXUS, line=(208, 214, 212), dark=False),
    "deepteal": dict(bg=(14, 58, 68), fg=PAPER, mute=(160, 196, 202), acc=VOLT, acc2=WAT, line=(40, 88, 98), dark=True),
    "sand": dict(bg=(250, 243, 228), fg=G, mute=(110, 100, 86), acc=ENERGY, acc2=AQ, line=(228, 216, 190), dark=False),
    "navy": dict(bg=(18, 30, 52), fg=PAPER, mute=(160, 172, 192), acc=EMBER, acc2=WAT, line=(44, 58, 84), dark=True),
    "mist": dict(bg=(226, 240, 243), fg=G, mute=(84, 108, 114), acc=NEXUS, acc2=ENERGY, line=(196, 220, 226), dark=False),
}
THEME_ORDER = list(THEMES)
SLOT_IX = {"morning": 0, "midday": 1, "evening": 2}

def wrap(dr, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines

def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def paste_logo(im, dark, x, y, w):
    lg = LOGO[dark].resize((w, int(w * LOGO[dark].height / LOGO[dark].width)), Image.LANCZOS); im.paste(lg, (x, y), lg); return lg.height
def text_block(dr, x, y, text, font, fill, width, lead=1.13):
    for line in wrap(dr, text, font, width):
        dr.text((x, y), line, font=font, fill=fill); y += int(font.size * lead)
    return y
def watch_block(dr, s, th, x, y, width, label="What to watch"):
    if not s.get("watch"): return y
    dr.text((x, y), label, font=F(SANSB, 30), fill=th["acc2"]); y += 50
    return text_block(dr, x, y, s["watch"], F(SANS, 38), th["fg"], width, 1.37)
def footer(im, dr, d, th, W, H, M):
    dr.line((M, H - M - 96, W - M, H - M - 96), fill=th["line"], width=2)
    dr.text((M, H - M - 70), d["date_long"], font=F(SANS, 28), fill=th["mute"])
    dr.text((M, H - M - 30), "carbonenergynexus.com", font=F(SANSB, 36), fill=th["fg"])
    mk = MARK[th["dark"]].resize((120, 120), Image.LANCZOS); im.paste(mk, (W - M - 120, H - M - 112), mk)

def lay_classic(im, dr, d, s, th, W, H, M, pad, n):
    y = M + paste_logo(im, th["dark"], M, M, 620) + 70 + pad
    dr.text((M, y), s["kicker"], font=F(SANSB, 34), fill=th["acc"]); y += 72
    y = text_block(dr, M, y, s["headline"], F(SERIFB, 88 if H > W * 1.5 else 78), th["fg"], W - 2 * M) + 44
    seg = (W - 2 * M) // 4
    for i, c in enumerate((VOLT, EMBER, AQ, WAT)):
        dr.rectangle((M + i * seg, y, M + (i + 1) * seg - (8 if i < 3 else 0), y + 8), fill=c)
    y += 62
    pf = F(SANSM, 44)
    for i, p in enumerate(s["points"]):
        dr.ellipse((M, y + 16, M + 20, y + 36), fill=(VOLT, EMBER, AQ)[i % 3])
        y = text_block(dr, M + 48, y, p, pf, th["fg"], W - 2 * M - 50, 1.32) + 24
    return watch_block(dr, s, th, M, y + 22, W - 2 * M)

def lay_split(im, dr, d, s, th, W, H, M, pad, n):
    blocks = [ENERGY, NEXUS] if th["dark"] else [ENERGY, NEXUS, G]
    blk = blocks[n % len(blocks)]
    hf = F(SERIFB, 92 if H > W * 1.5 else 82)
    hl = wrap(dr, s["headline"], hf, W - 2 * M)
    top = M + 160 + pad
    bh = top + 64 + len(hl) * int(hf.size * 1.12) + 56
    dr.rectangle((0, 0, W, bh), fill=blk)
    paste_logo(im, "solid", M, M, 460)
    dr.text((M, top), s["kicker"].upper(), font=F(SANSB, 30), fill=mix(blk, (255, 255, 255), 0.8))
    y = top + 64
    for line in hl:
        dr.text((M, y), line, font=hf, fill=(255, 255, 255)); y += int(hf.size * 1.12)
    y = bh + 60
    nf, pf = F(SERIFB, 64), F(SANSM, 42)
    for i, p in enumerate(s["points"]):
        dr.text((M, y - 10), f"0{i + 1}", font=nf, fill=(th["acc"], th["acc2"], blk if not th["dark"] else th["acc"])[i % 3])
        y = text_block(dr, M + 120, y, p, pf, th["fg"], W - 2 * M - 120, 1.3) + 30
    return watch_block(dr, s, th, M, y + 16, W - 2 * M, "Next")

NUM = re.compile(r"[€$£]?\d[\d,.]*(?:%|\s?(?:GWh|GW|MW|Mt|bn|km|M|B|t)\b)?")
def stat_of(s):
    for i, p in enumerate(s["points"]):
        m = NUM.search(p)
        if m and len(m.group().strip()) >= 2: return i, m.group().strip()
    return None
def lay_stat(im, dr, d, s, th, W, H, M, pad, n):
    st = stat_of(s)
    if not st: return None
    i0, num = st
    y = M + paste_logo(im, th["dark"], M, M, 480) + 48 + pad
    dr.text((M, y), s["kicker"], font=F(SANSB, 32), fill=th["acc2"]); y += 54
    sz = 230 if H > W * 1.5 else 200
    while dr.textlength(num, font=F(SERIFB, sz)) > W - 2 * M: sz -= 10
    nf = F(SERIFB, sz)
    dr.text((M, y - int(sz * 0.12)), num, font=nf, fill=th["acc"]); y += int(sz * 1.02)
    y = text_block(dr, M, y, s["points"][i0], F(SANSM, 44), th["fg"], W - 2 * M, 1.3) + 26
    dr.rectangle((M, y, M + 140, y + 10), fill=th["acc"]); y += 44
    y = text_block(dr, M, y, s["headline"], F(SERIFB, 70 if H > W * 1.5 else 58), th["fg"], W - 2 * M, 1.12) + 22
    pf = F(SANS, 38)
    for i, p in enumerate(s["points"]):
        if i == i0: continue
        dr.rectangle((M, y + 22, M + 22, y + 28), fill=th["acc2"])
        y = text_block(dr, M + 44, y, p, pf, th["fg"], W - 2 * M - 44, 1.3) + 10
    return watch_block(dr, s, th, M, y + 14, W - 2 * M)

def lay_editorial(im, dr, d, s, th, W, H, M, pad, n):
    paste_logo(im, th["dark"], M, M, 440)
    y = M + 150 + pad
    kf = F(SANSB, 30)
    kw = int(dr.textlength(s["kicker"], font=kf))
    dr.rounded_rectangle((M, y, M + kw + 44, y + 54), radius=27, fill=th["acc"])
    dr.text((M + 22, y + 9), s["kicker"], font=kf, fill=(255, 255, 255) if th["acc"] != VOLT else G); y += 84
    hf = F(SERIFB, 96 if H > W * 1.5 else 80)
    y1 = text_block(dr, M + 44, y, s["headline"], hf, th["fg"], W - 2 * M - 44, 1.1)
    dr.rectangle((M, y + 10, M + 14, y1 - 14), fill=th["acc"])
    y = y1 + 40
    cw, gap = (W - 2 * M - 2 * 28) // 3, 28
    pf, nf = F(SANSM, 34), F(SERIFB, 54)
    tint = mix(th["bg"], th["fg"], 0.07)
    hts = [len(wrap(dr, p, pf, cw - 44)) for p in s["points"]]
    ch = 100 + max(hts) * 46 + 26
    for i, p in enumerate(s["points"][:3]):
        x = M + i * (cw + gap)
        dr.rounded_rectangle((x, y, x + cw, y + ch), radius=22, fill=tint)
        dr.text((x + 22, y + 14), str(i + 1), font=nf, fill=(th["acc"], th["acc2"], th["acc"])[i])
        text_block(dr, x + 22, y + 92, p, pf, th["fg"], cw - 44, 1.35)
    y += ch + 40
    if s.get("watch"):
        y = text_block(dr, M, y, s["watch"], F(SERIF, 40), th["fg"], W - 2 * M, 1.3)
    return y

def lay_tiles(im, dr, d, s, th, W, H, M, pad, n):
    y = M + paste_logo(im, th["dark"], M, M, 500) + 48 + pad
    dr.text((M, y), s["kicker"], font=F(SANSB, 34), fill=th["acc"]); y += 60
    y = text_block(dr, M, y, s["headline"], F(SERIFB, 84 if H > W * 1.5 else 72), th["fg"], W - 2 * M, 1.12) + 36
    tint = mix(th["bg"], th["fg"], 0.08)
    pf = F(SANSM, 42)
    for i, p in enumerate(s["points"]):
        ls = wrap(dr, p, pf, W - 2 * M - 80)
        h = 36 + len(ls) * 52
        dr.rounded_rectangle((M, y, W - M, y + h), radius=18, fill=tint)
        dr.rounded_rectangle((M, y, M + 14, y + h), radius=7, fill=(VOLT, EMBER, AQ)[(i + n) % 3])
        yy = y + 16
        for line in ls:
            dr.text((M + 48, yy), line, font=pf, fill=th["fg"]); yy += 52
        y += h + 16
    y += 12
    if s.get("watch"):
        wf = F(SANS, 38)
        ls = wrap(dr, s["watch"], wf, W - 2 * M - 64)
        h = 90 + len(ls) * 50
        dr.rounded_rectangle((M, y, W - M, y + h), radius=18, outline=th["acc2"], width=3)
        dr.text((M + 32, y + 20), "What to watch", font=F(SANSB, 30), fill=th["acc2"])
        text_block(dr, M + 32, y + 68, s["watch"], wf, th["fg"], W - 2 * M - 64, 1.32)
        y += h
    return y

LAYOUTS = {"classic": lay_classic, "split": lay_split, "stat": lay_stat, "editorial": lay_editorial, "tiles": lay_tiles}
LAYOUT_ORDER = list(LAYOUTS)
FORCE = False

def design_for(d, s, slot):
    n, k = datetime.date.fromisoformat(d["date"]).toordinal(), SLOT_IX.get(slot, 0)
    li = (2 * n + k) % len(LAYOUT_ORDER)
    ti = (n + (0, 3, 1)[k]) % len(THEME_ORDER)
    lays = [s.get("design", {}).get("layout")] if s.get("design", {}).get("layout") in LAYOUTS else []
    lays += [LAYOUT_ORDER[(li + j) % len(LAYOUT_ORDER)] for j in range(len(LAYOUT_ORDER))]
    th = s.get("design", {}).get("theme")
    return n + k, lays, THEMES[th if th in THEMES else THEME_ORDER[ti]]

def card(d, s, W, H, path, lay, th, n, pad=0):
    im = Image.new("RGB", (W, H), th["bg"]); dr = ImageDraw.Draw(im); M = 84
    end = LAYOUTS[lay](im, dr, d, s, th, W, H, M, pad, n)
    if end is None or (end > H - M - 130 and not FORCE): return None
    footer(im, dr, d, th, W, H, M)
    im.save(path, optimize=True)
    return end

def render_slot(d, s, base, slot):
    n, lays, th = design_for(d, s, slot)
    for lay in lays:
        if card(d, s, 1080, 1350, f"social/{base}.png", lay, th, n) is None: continue
        end = card(d, s, 1080, 1920, f"social/{base}-story.png", lay, th, n)
        free = (1920 - 84 - 150) - (end or 0)
        if end and free > 80:
            card(d, s, 1080, 1920, f"social/{base}-story.png", lay, th, n, pad=free // 2)
        return lay
    raise SystemExit(f"social card for {base} does not fit any layout; shorten the headline or points")

for d in data:
    if "social" not in d: continue
    if d is latest or not os.path.exists(f"social/{d['date']}.png"):
        render_slot(d, d["social"], d["date"], "morning")
        open(f"social/{d['date']}.txt", "w").write(d["social"]["caption"] + "\n")
        for slot, ss in d.get("social_slots", {}).items():
            render_slot(d, ss, f"{d['date']}-{slot}", slot)
            open(f"social/{d['date']}-{slot}.txt", "w").write(ss["caption"] + "\n")

slots = {"morning": {"image": f"{SITE}social/{latest['date']}.png", "story": f"{SITE}social/{latest['date']}-story.png", "caption": latest["social"]["caption"]}}
for slot, ss in latest.get("social_slots", {}).items():
    slots[slot] = {"image": f"{SITE}social/{latest['date']}-{slot}.png", "story": f"{SITE}social/{latest['date']}-{slot}-story.png", "caption": ss["caption"]}
json.dump({"date": latest["date"], "slots": slots}, open("social/today.json", "w"), indent=1)
Image.open(f"social/{latest['date']}.png").save("social/latest.png")
print("built", latest["date"], "editions:", len(data))
