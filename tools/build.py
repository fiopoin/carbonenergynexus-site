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
       "description": "Sourced daily intelligence on carbon, energy and capital: projects, policy, markets and research.",
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
    ftr = env.get_template("footer.html.j2").render(root=root)
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
<description>Sourced daily intelligence on carbon, energy and capital.</description>{entries}</channel></rss>""")

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
L = [f"# {NAME}", "", "> A free daily publication at carbonenergynexus.com on where carbon, energy and capital meet: CO2 capture and storage, carbon markets and removals, energy policy, project finance and research. Each edition sorts news by electrons (power), molecules (fuels) and pore space (the subsurface), tracks projects on a seven step ladder from announcement to operation, and says what each story means for investors, regulators, industry and founders. Facts are sourced and dated; stages and outlooks are labeled as our judgment. General information, not investment advice.", "",
     "## Tools", f"- [Energy and carbon footprint calculator]({SITE}calculator.html): households and companies, EPA and EIA factors, transparent Nexus Score",
     f"- [Frameworks]({SITE}frameworks.html): how projects, policy and carbon claims are judged", "",
     "## Today's edition", f"- [{latest['lead']['headline']}]({SITE}): {latest['date_long']}. {summary(latest)}"]
L += [f"- [{b['lane']}: {b['headline']}]({SITE}#{b['id']})" for b in latest.get("briefs", [])]
L += ["", "## Archive and feeds", f"- [Past editions]({SITE}archive/)", f"- [RSS feed]({SITE}feed.xml)", f"- [Sitemap]({SITE}sitemap.xml)", "", "## Recent editions"]
L += [f"- [{d['date_long']}: {d['lead']['headline']}]({page_url(d, True)})" for d in list(reversed(data))[:30]]
open("llms.txt", "w").write("\n".join(L) + "\n")

# Social graphics
G, PAPER, VOLT, EMBER, AQ, MUTE, LINE = (26, 34, 38), (238, 242, 241), (242, 193, 78), (228, 87, 46), (43, 138, 158), (174, 185, 183), (58, 70, 76)
def F(w, s): return ImageFont.truetype(f"tools/fonts/{w}.ttf", s)
SERIF, SERIFB, SANS, SANSM, SANSB = "SourceSerif4-SemiBold", "SourceSerif4-Bold", "IBMPlexSans-Regular", "IBMPlexSans-Medium", "IBMPlexSans-SemiBold"
lock = Image.open("brand/cen-lockup-white-1200.png").convert("RGBA")
mark = Image.open("brand/cen-mark-white-400.png").convert("RGBA")

def wrap(dr, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines

def card(d, s, W, H, path, pad=0):
    im = Image.new("RGB", (W, H), G); dr = ImageDraw.Draw(im); M = 84
    lg = lock.resize((620, int(620 * lock.height / lock.width)), Image.LANCZOS); im.paste(lg, (M, M), lg)
    y = M + lg.height + 70 + pad
    dr.text((M, y), s["kicker"], font=F(SANSB, 34), fill=VOLT); y += 72
    hf = F(SERIFB, 88 if H > W * 1.5 else 78)
    for line in wrap(dr, s["headline"], hf, W - 2 * M):
        dr.text((M, y), line, font=hf, fill=PAPER); y += int(hf.size * 1.13)
    y += 44
    seg = (W - 2 * M) // 3
    for i, c in enumerate((VOLT, EMBER, AQ)):
        dr.rectangle((M + i * seg, y, M + (i + 1) * seg - (8 if i < 2 else 0), y + 8), fill=c)
    y += 62
    pf = F(SANSM, 44)
    for i, p in enumerate(s["points"]):
        c = (VOLT, EMBER, AQ)[i % 3]
        dr.ellipse((M, y + 16, M + 20, y + 36), fill=c)
        for line in wrap(dr, p, pf, W - 2 * M - 50):
            dr.text((M + 48, y), line, font=pf, fill=PAPER); y += 58
        y += 24
    if s.get("watch"):
        y += 22
        dr.text((M, y), "What to watch", font=F(SANSB, 30), fill=AQ if False else (126, 195, 209)); y += 50
        wf = F(SANS, 38)
        for line in wrap(dr, s["watch"], wf, W - 2 * M):
            dr.text((M, y), line, font=wf, fill=PAPER); y += 52
    end = y
    dr.line((M, H - M - 96, W - M, H - M - 96), fill=LINE, width=2)
    dr.text((M, H - M - 70), d["date_long"], font=F(SANS, 28), fill=MUTE)
    dr.text((M, H - M - 30), "carbonenergynexus.com", font=F(SANSB, 36), fill=PAPER)
    mk = mark.resize((120, 120), Image.LANCZOS); im.paste(mk, (W - M - 120, H - M - 112), mk)
    im.save(path, optimize=True)
    return end

def render_slot(d, s, base):
    card(d, s, 1080, 1350, f"social/{base}.png")
    end = card(d, s, 1080, 1920, f"social/{base}-story.png")
    free = (1920 - 84 - 150) - end
    if free > 80:
        card(d, s, 1080, 1920, f"social/{base}-story.png", pad=free // 2)

for d in data:
    if "social" not in d: continue
    if d is latest or not os.path.exists(f"social/{d['date']}.png"):
        render_slot(d, d["social"], d["date"])
        open(f"social/{d['date']}.txt", "w").write(d["social"]["caption"] + "\n")
        for slot, ss in d.get("social_slots", {}).items():
            render_slot(d, ss, f"{d['date']}-{slot}")
            open(f"social/{d['date']}-{slot}.txt", "w").write(ss["caption"] + "\n")

slots = {"morning": {"image": f"{SITE}social/{latest['date']}.png", "story": f"{SITE}social/{latest['date']}-story.png", "caption": latest["social"]["caption"]}}
for slot, ss in latest.get("social_slots", {}).items():
    slots[slot] = {"image": f"{SITE}social/{latest['date']}-{slot}.png", "story": f"{SITE}social/{latest['date']}-{slot}-story.png", "caption": ss["caption"]}
json.dump({"date": latest["date"], "slots": slots}, open("social/today.json", "w"), indent=1)
Image.open(f"social/{latest['date']}.png").save("social/latest.png")
print("built", latest["date"], "editions:", len(data))
