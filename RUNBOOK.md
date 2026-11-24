# Weekly UAE legal & tax digest — runbook

Every Monday at 10:00 Dubai time a scheduled task follows this file to build
one report and publish it. Pushing to `main` deploys the site
through Cloudflare Pages.

## 0. Setup
- Clone this repository and work inside it.
- Run date = today (a Monday, Asia/Dubai). **Period** = the 7 days before the run date,
  from last Monday to Sunday inclusive. Count a publication only if its date falls in the period.
- `sources.json` lists every source. `state/seen.json` lists the URLs that earlier reports already used.
  Never report one of those URLs again.

## 1. Collect candidates
For each source in `sources.json` (`official`, `media`, `firms`):
1. If `news_url` is null, open `url` and find the news/insights/publications page.
   Prefer a page filtered to the Middle East / UAE when the firm is international (`region_filter`).
   Write the URL you found back into `sources.json`.
2. Read `news_url` with WebFetch. If WebFetch is refused, returns nothing useful or has no dates,
   open the page in the person's Chrome (Claude in Chrome) and read it there.
3. **Lexology and Mondaq (`"browser": true`) are always read in Chrome**, where the person is
   already signed in. Lexology: use the hub/newsfeed filtered to United Arab Emirates.
   Mondaq: the United Arab Emirates section. **Never type a password or sign in.** If either site
   shows you as signed out, skip it and add a line to `notes`.
4. Note for each candidate the title, URL, date and source.
5. If a source can't be read at all, add one short line to `notes` and move on. Do not stop the run.

## 2. Select (at most 50 publications in total)
Keep publications that:
- are about tax, corporate law, employment law, banking/finance law, investment, or M&A.
  A new UAE federal or emirate law or regulation that matters to business also counts;
- concern the UAE or the MENA region.

Drop:
- charity, CSR, sponsorships, community events;
- appointments, hires, promotions, lateral moves, new partners;
- events outside the MENA region (also global articles with no MENA angle);
- awards, rankings, firm self-promotion, webinars/event announcements, job posts;
- duplicates: the same news from several outlets. Keep the best source,
  and prefer the official one.

If more than 50 publications pass: official sources come first, then substantive legal changes
over commentary, then a balance across firms and outlets.

## 3. New service sections (law firms only)
For each firm:
1. If `services_url` is null, find its services / practices / expertise page and save it in `sources.json`.
2. Extract the list of services as `[{"title": ..., "url": ...}]`.
3. Compare it with `state/services/<slug>.json`. Entries that weren't there before are **new services**
   and go into `new_services` in the report. Then overwrite the snapshot with the current list.
4. If there is no snapshot yet, save it as the baseline and report nothing for that firm.
   On the first run, add a note that the baseline was recorded.
5. Ignore changes in wording or order only. A service counts as new only if it has a new page or a new name.

## 4. Write the report
Create `reports/data/<run-date>.json` in the format documented at the top of `scripts/build.py`:
- `official`: items from `sources.json → official`.
- `media`: items from `sources.json → media`, including Lexology/Mondaq articles by any author.
- `firms`: items from the firms' own websites.
- `headline`: a **short Russian headline (≤ 15 words)** that says what the publication is about,
  e.g. «Минфин ОАЭ расширил перечень квалифицирующих видов деятельности для свободных зон».
  Don't just translate the original title if it is vague.
- `topic`: one of Налоги, Корпоративное право, Трудовое право, Банковское право, Инвестиции, M&A, Законодательство.
- `source`: the outlet or firm name. `date`: ISO date of the publication.
- Sort each section newest first.

## 5. Publish
```
python3 scripts/build.py --check && python3 scripts/build.py
```
Add every reported URL to `state/seen.json`. Then commit everything
(`Digest <run-date>`) and push to `main`. Cloudflare Pages deploys it automatically.

## 6. Tell the person
Send one short message with the page link (`<SITE_URL>/reports/<run-date>.html`, where SITE_URL is in `site.json`),
the number of publications per section, any new services, and any sources that couldn't be read.
