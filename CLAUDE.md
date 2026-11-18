# carbonenergynexus.com: Carbon Energy Nexus

Static site on GitHub Pages (repo fiopoin/carbonenergynexus-site, branch main, custom domain carbonenergynexus.com via GoDaddy DNS). Same process as fiopoin.com.

## Build
- One JSON file per edition in `content/YYYY-MM-DD.json`; the newest becomes the homepage. Copy the latest file and replace every field.
- `python3 tools/build.py` writes index.html, archive/, calculator.html, frameworks.html, privacy.html, feed.xml, sitemap.xml, robots.txt, llms.txt and the social graphics (social/<date>.png, -story.png, -midday, -evening, captions, social/today.json). Never hand edit generated files; never block crawlers.
- Needs jinja2 and Pillow. Fonts: tools/fonts (Source Serif 4, IBM Plex Sans, OFL).

## Content schema
date, date_long, edition, lead{kicker, headline (under 110 chars), dek, body[3], nexus{electrons, molecules, pore, water}, use[4]{who,text}, sources[]}, signals[6]{label,value,note,source{name,url}}, briefs[4 to 6]{id, lane: Regulation|Capital|Projects|Markets|Water, headline, text, use[2]{who,text}, sources[]}, tracker[]{name, where, type, stage 1-7, last, source}, voices[2 to 3]{name, role, text (paraphrase), source}, research[2 to 4]{title, by, date, text, url}, calendar[]{when, what}, calendar_sources[], social{kicker "Morning: the nexus", headline, points[3], watch, caption}, social_slots{midday{kicker "Midday: the money",...}, evening{kicker "Evening: the world",...}}.
Brief ids "money" and "world" must exist. Tracker stages: 1 Announced, 2 Feasibility, 3 Engineering (FEED), 4 Permits and contracts, 5 FID, 6 Construction, 7 Operating; move a project up only on public evidence. Keep tracked projects day to day and update their "last" line when news moves them.

## Editorial rules
- Niche: where carbon, energy, water and capital meet (CCS and storage, carbon markets and removals, hydrogen and low-carbon fuels, power and data center load, produced water, brine and the water footprint of energy and carbon, subsurface, policy, project finance, research). Audience: investors, regulators, industry, founders, the public.
- Every fact sourced, dated and linked. Never invent numbers. Paraphrase; at most one short quote per source.
- No em or en dashes as punctuation. Plain, direct, human prose. Politically neutral. General information, not investment advice.
- Social headline under 60 chars, points under 40, caption under 600 with 4 to 6 hashtags; caption first paragraph is the page description (under 300 chars).

## Brand
Wordmark colors: on light, Carbon #1A2226, Energy #D0481E, Nexus #1F7A8C; on dark, Carbon #EEF2F1, Energy #E4572E, Nexus #4FB0C2. Mark: light benzene ring with alternating double bonds; six energy forms at the carbon positions (solar and wind in volt #F2C14E, nuclear and oil and gas in ember #E4572E, hydrogen and geothermal in aquifer #2B8A9E); a water drop (#5FB8E6) at the center. Favicon uses the simple ring with six colored dots and the center drop. Every edition carries a water angle in the lead. Graphite #1A2226, paper #F4F6F5. Files in brand/.

## Publish and verify
Commit as user "fiopoin" and push to main. Verify the live site in a browser (desktop and phone) after every update before reporting done.
