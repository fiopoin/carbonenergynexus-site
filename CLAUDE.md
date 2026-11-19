# carbonenergynexus.com: Carbon Energy Nexus

Static site on GitHub Pages (repo fiopoin/carbonenergynexus-site, branch main, custom domain carbonenergynexus.com via GoDaddy DNS). Same process as fiopoin.com.

## Build
- One JSON file per edition in `content/YYYY-MM-DD.json`; the newest becomes the homepage. Copy the latest file and replace every field.
- `python3 tools/build.py` writes index.html, archive/, calculator.html, frameworks.html, privacy.html, feed.xml, sitemap.xml, robots.txt, llms.txt and the social graphics (social/<date>.png, -story.png, -midday, -evening, captions, social/today.json). Never hand edit generated files; never block crawlers.
- Needs jinja2 and Pillow. Fonts: tools/fonts (Source Serif 4, IBM Plex Sans, OFL).

## Content schema
date, date_long, edition, lead{kicker, headline (under 110 chars), dek, body[3], nexus{electrons, molecules, pore, water}, use[4]{who,text}, sources[]}, signals[6]{label,value,note,source{name,url}}, briefs[4 to 6]{id, lane: Regulation|Capital|Projects|Markets|Water, headline, text, use[2]{who,text}, sources[]}, tracker[]{name, where, type, sector (Carbon storage|Geothermal|Minerals|Hydrogen|Power|Water), stage 1-7, last, url (the project's own official site, verified), source}, voices[2 to 3]{name, role, text (paraphrase), source}, research[2 to 4]{title, by, date, text, url}, minerals{intro, items[5 to 6]{symbol (element symbol such as Nd, Cu, Li, Co, U, Ni, C for graphite; § for policy), name, headline, text, sources[]}}, innovation[3 to 5]{name, org, kind: Academia|Private|Academia and private, date, text, url}, events[]{date (YYYY-MM-DD for sorting), when, type: Carbon|Renewables|Hydrogen|Power|Minerals|Policy|Markets|Water, what, where, url}, calendar[] and calendar_sources[] (legacy; the page shows events when present), social{kicker "Morning: the nexus", headline, points[3], watch, caption}, social_slots{midday{kicker "Midday: the money",...}, evening{kicker "Evening: the world",...}}.
Brief ids "money" and "world" must exist. Tracker stages: 1 Announced, 2 Feasibility, 3 Engineering (FEED), 4 Permits and contracts, 5 FID, 6 Construction, 7 Operating; move a project up only on public evidence. Keep tracked projects day to day and update their "last" line when news moves them. Every tracked project carries its official site in url (WebFetch it once to confirm), so readers can tap through. Track projects beyond CCS too: geothermal, hydrogen, nuclear, storage and mines or refineries for critical minerals.

## Sections added Nov 18, 2026 (fill every day)
- minerals: critical minerals and mining. Cover rare earths every day, plus the biggest moves among copper, lithium, nickel, cobalt, graphite, uranium and minerals policy (export controls, quotas, deals, stockpiles). Each item is sourced and dated.
- innovation: three to five items mixing academia (peer reviewed papers, university releases) and private sector (company launches, first of a kind plants, funding rounds tied to a real milestone). Link straight to the paper or announcement.
- events: upcoming conferences, deadlines and market dates across carbon, renewables (solar, wind, storage), hydrogen, power and minerals, sorted by date, each linked to the organizer's page or a source. Drop past dates each day; keep 12 to 18 entries running at least a year ahead.

## Editorial rules
- Niche: where carbon, energy, water and capital meet (CCS and storage, carbon markets and removals, hydrogen and low-carbon fuels, power and data center load, produced water, brine and the water footprint of energy and carbon, subsurface, policy, project finance, research). Audience: investors, regulators, industry, founders, the public.
- Every fact sourced, dated and linked. Never invent numbers. Paraphrase; at most one short quote per source.
- No em or en dashes as punctuation. Plain, direct, human prose. Politically neutral. General information, not investment advice.
- Social headline under 60 chars, points under 40, caption under 600 with 4 to 6 hashtags; caption first paragraph is the page description (under 300 chars).

## Brand
Wordmark colors: on light, Carbon #1A2226, Energy #D0481E, Nexus #1F7A8C; on dark, Carbon #EEF2F1, Energy #E4572E, Nexus #4FB0C2. Mark: light benzene ring with alternating double bonds; six energy forms at the carbon positions (solar and wind in volt #F2C14E, nuclear and oil and gas in ember #E4572E, hydrogen and geothermal in aquifer #2B8A9E); a water drop (#5FB8E6) at the center. Favicon uses the simple ring with six colored dots and the center drop. Every edition carries a water angle in the lead. Graphite #1A2226, paper #F4F6F5. Files in brand/.

## Schedule
Daily edition publishes at 06:37 Europe/Berlin (23:37 Chicago the evening before). Social posts are scheduled in America/Chicago time (Raj, Nov 19, 2026) and use the Chicago date's edition:
- Midday "the money": 05:37 Chicago. Europe at lunch, the Middle East, Africa and Asia later in the day.
- Evening "the world": 13:47 Chicago. Europe in the evening, the Americas in the afternoon.
- Morning "the nexus" (the lead story): 20:17 Chicago. US evening reading, Asia early morning.
Combined daily order, Chicago time: 05:37 CEN midday, 06:42 FIOPO, 09:27 Utica, 11:42 FIOPO, 12:47 Utica, 13:47 CEN evening, 16:37 Utica, 20:17 CEN morning, 22:32 FIOPO. Keep every post at least 60 minutes from any other brand's.

## Publish and verify
Commit as user "fiopoin" and push to main. Verify the live site in a browser (desktop and phone) after every update before reporting done.
