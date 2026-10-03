# PersonalAssistant

Sends a daily morning briefing (Octopus Agile electricity price, Lewisham
weather, and a commute route check) to Telegram, plus extra high-frequency
route pings on Saturday mornings and a weekday evening commute check.

## What it sends

**Daily, 07:00 BST/GMT** (`morning_briefing.py`, `MODE=full`):

- Current Octopus Agile electricity price (region `_C`, London/Lewisham),
  plus two things about the next 24h: the single cheapest half-hour/hour
  slot, and every period below `OCTOPUS_CHEAP_THRESHOLD_P_PER_KWH`
  (currently 20.0 p/kWh) - contiguous cheap slots are merged into one
  window each (e.g. a run of cheap half-hours shows as one time range),
  separate cheap periods are listed separately, and "None" is shown if
  nothing in the next 24h is under the threshold
- Lewisham weather (current temp, today's range, rain warning)
- **Only when Bank Buy >= 10.5:** GBP/HKD TT (telegraphic transfer) exchange
  rate from Hang Seng Bank - Bank Buy/Sell rates plus the bank's
  last-updated timestamp (see note below). Below that threshold, this
  section is skipped entirely (a genuine fetch failure still shows a
  "couldn't fetch" fallback, since that's a different situation from the
  rate simply being below the threshold)
- **Monday-Friday only, and only if disrupted:** Office Route Check - checks
  the commute route home -> Bank via DLR -> Old Street via Northern line
  (decoded from the Citymapper link originally supplied), by querying TfL
  status for the `dlr`, `elizabeth`, and `northern` lines - the `elizabeth`
  line query is kept even though the current route doesn't use it (see note
  below). This section is only included in the briefing when the route is
  actually disrupted (or the check itself fails) - a clear route adds
  nothing to the message at all
- **Saturday only:** Route Check for Lewisham -> Charing Cross (Southeastern),
  closest station to Virgin Active Strand - also checks whether Lewisham
  station itself is closed for rail replacement buses, and if so reports a
  suggested alternative route from Hither Green (see notes below)
- **Sunday only, and only if any are found:** Upcoming Thu/Fri Events - checks
  two queer/community event venues (La Camionera, Old Nun's Head) plus two
  recurring Eventbrite event series (The Lesbian Pub Quiz, Lesbian Speed
  Dating) for events on the coming Thursday and Friday, and lists whatever
  is found with a link to each event (see notes below). If none of the four
  sources have anything on either day, this section is skipped entirely

**Saturday only, high-frequency route-only pings** (`morning_briefing.py`,
`MODE=route_only`, no weather/price content):

- 10:30-10:55 BST, every 5 minutes
- 11:00-11:15 BST, every 3 minutes

**Monday-Friday, 17:30 BST/GMT** (`morning_briefing.py`, `MODE=evening`):

- Office -> Home Route Check only (Old Street [Northern line] -> Bank ->
  Lewisham [DLR], the reverse of the morning Office Route Check) - and
  **only if disrupted**. If the route is clear, no message is sent at all
  (see notes below)

## Required repository secrets

Set under **Settings -> Secrets and variables -> Actions**:

| Secret | Purpose |
|---|---|
| `TG_BOT_TOKEN` | Telegram bot token (from @BotFather) |
| `TG_CHAT_ID` | Telegram chat ID to send messages to |

## Scheduling architecture - why there's no `schedule:` in the workflow files

GitHub Actions' native `schedule` (cron) trigger is **best-effort with no
delivery-time guarantee**. In practice this repo's daily briefing was observed
firing 1-3 hours late, and the delay was worsening over several days of
testing - not just occasional jitter.

By contrast, every `workflow_dispatch` run fired in testing started within
5-20 seconds, regardless of how it was triggered (manually, or via the GitHub
REST API). So instead of relying on GitHub's internal cron, **timing is owned
by an external scheduler (cron-job.org, free tier)** that calls the GitHub
REST API to fire `workflow_dispatch` at the exact intended time. Both
workflow files intentionally have no `schedule:` block - if GitHub's cron were
also left in as a "backup," a late GitHub-cron firing could show up as a
confusing duplicate message hours after the real one.

### cron-job.org jobs required

All four call the GitHub Actions "create a workflow dispatch event" API:
`POST https://api.github.com/repos/deltadesignttwd-lgtm/PersonalAssistant/actions/workflows/{workflow_file}/dispatches`

Common settings for all four jobs:
- **Method:** POST
- **Headers:**
  - `Authorization: Bearer <PAT>` (see below)
  - `Accept: application/vnd.github+json`
  - `X-GitHub-Api-Version: 2022-11-28`
  - `Content-Type: application/json`
- **Body:** `{"ref":"main"}`
- **Timezone:** `Europe/London` (so BST/GMT is handled automatically - no
  twice-yearly manual offset adjustment needed, unlike GitHub's UTC-only cron)

| Job | Workflow file | Schedule (Europe/London time) |
|---|---|---|
| Daily briefing | `morning-briefing.yml` | Every day, 07:00 |
| Saturday ping (5 min) | `saturday-route-pings.yml` | Saturdays, 10:30-10:55, every 5 min |
| Saturday ping (3 min) | `saturday-route-pings.yml` | Saturdays, 11:00-11:15, every 3 min |
| Evening commute check | `evening-briefing.yml` | Weekdays (Mon-Fri), 17:30 |

### GitHub token for cron-job.org

A fine-grained Personal Access Token, scoped to **only** this repository,
with **Actions: Read and write** permission and nothing else. Fine-grained
PATs expire after at most 1 year - **set a renewal reminder**, since expiry
will silently break delivery (cron-job.org will start getting 401s) unless
you've also enabled cron-job.org's failure-notification emails.

## Manual testing

All three workflows accept manual `workflow_dispatch` runs from the Actions
tab (or via the API). `morning-briefing.yml` additionally takes four inputs
for testing outside their normal day-of-week:

- `force_route_check` (boolean) - include the Saturday gym route check even
  on a non-Saturday
- `force_office_check` (boolean) - include the office route check even on a
  non-weekday
- `force_wlw_check` (boolean) - include the Thu/Fri events check even on a
  non-Sunday
- `simulated_now` (string, ISO datetime e.g. `2026-09-28T07:00:00`) -
  simulate "now" as this date/time instead of the real current time, so
  day-of-week-specific sections (office Mon-Fri, gym Saturday, events Sunday)
  react as if it were actually that day - unlike the three `force_*` flags
  above (which only add a section on top of whatever the real day already
  shows), this lets you see, for example, exactly what a genuine Monday
  07:00 run would send, with no Saturday-only content mixed in just because
  today happens to be a Saturday. Leave blank to use the real current time.

`evening-briefing.yml` takes no inputs - it has no day-of-week gating in the
script itself (that's left entirely to when cron-job.org triggers it), so a
manual run just checks the route right now. If the route is clear, nothing
is sent to Telegram, but the Actions job log always prints the judgement
(`check_home_from_office_route_disruption()`'s debug print), so a test run's
outcome is visible either way.

## Notes on the route checks

- `check_office_route_disruption()` and `check_route_disruption()` both query
  the TfL Line Status API directly by line id
  (`https://api.tfl.gov.uk/Line/{ids}/Status`) rather than by "mode," since
  mode-based queries for some lines (e.g. `elizabeth-line` as a mode name)
  have been unreliable on TfL's API historically.
- The office commute used to have two route options: home -> Canary Wharf
  (DLR) -> Liverpool Street (Elizabeth line), or home -> Bank (DLR) -> Old
  Street (Northern line). The user settled on the Bank/Old Street route as
  the only one now shown (`CITYMAPPER_OFFICE_URL`), so the Canary
  Wharf/Liverpool Street link and its two Citymapper leg URLs were removed.
  `check_office_route_disruption()` still queries all three TfL lines
  (`dlr`, `elizabeth`, `northern`) and keeps the full
  `_IRRELEVANT_OFFICE_ROUTE_KEYWORDS` filtering list unchanged - the
  `elizabeth` line query is now unused by the displayed route but was left
  in place on request rather than trimmed.
- `check_office_route_disruption()` returns `None` when the route is clear -
  `send_full_briefing()` only appends the "🚇 Office Route Check" section
  (header, status line, and link) when the return value isn't `None`, so a
  clear route contributes nothing to the message at all, not even a "clear"
  line. A genuine check failure (TfL API error) still returns a fallback
  message and is still shown, since that's a different, actionable
  situation from "nothing wrong".
- `check_home_from_office_route_disruption()` (the 17:30 evening check) is
  the reverse direction of the morning Office Route Check - decoded from a
  separate Citymapper signature link the user supplied, confirming
  Frank Reynolds Architects -> walk to Old Street -> Old Street [Northern
  line] -> Bank -> Bank [DLR] -> Lewisham -> home. Since it's the same two
  TfL lines (`dlr`/`northern`) as the morning check, just travelled in the
  opposite direction, it queries the same `_get_tfl_line_disruptions(['dlr',
  'elizabeth', 'northern'])` and reuses the existing
  `_mentions_irrelevant_office_location()` keyword filter rather than
  duplicating it. It also returns `None` when clear, but unlike the morning
  check (which is just one section of a larger message), a `None` here
  means `send_evening_update()` sends no Telegram message at all for that
  run - this was a deliberate choice (confirmed with the user) over always
  pinging with a "clear" status.
- Most Citymapper links in `morning_briefing.py` are decorative/fallback links
  for the user to open manually if the TfL check itself fails - they are not
  queried programmatically (Citymapper has no public routing-*status* API).
  The one exception is `get_hither_green_to_strand_route()` (see note below),
  which does call a real Citymapper journey-planning endpoint.
- The Hang Seng GBP/HKD TT rate is fetched from a genuine public JSON API
  (`HANGSENG_TT_RATES_API_URL`), not scraped from HTML. The bank's own TT
  rates page doesn't render the numbers into static HTML - they're loaded
  client-side by `clientlib-rates/ttTable.js`, which calls
  `https://rbwm-api.hsbc.com.hk/pws-hk-hase-rates-papi-prod-proxy/v1/fxtt-exchange-rates`.
  That endpoint returns plain JSON (all currencies, no auth needed) and is
  called directly by `get_gbp_hkd_tt_rate()`.
- The GBP/HKD section only shows up in the daily briefing when the fetched
  Bank Buy rate is `>= GBP_HKD_BUY_RATE_THRESHOLD` (currently `10.5`) - this
  is a user-set business threshold, not a technical concern. A genuine fetch
  failure (`get_gbp_hkd_tt_rate()` returns `None`) still shows the existing
  "couldn't fetch" fallback with a manual-check link; only a successfully
  fetched rate below the threshold causes the section to be skipped
  entirely, with no message at all.
- `check_route_disruption()` also checks whether Lewisham station itself is
  closed (rail replacement buses running instead of trains) by scraping
  nationalrail.co.uk's live departures board for Lewisham
  (`NATIONALRAIL_LEWISHAM_URL`). The page renders fine with a plain
  `requests.get()` and embeds its live data as JSON in a
  `<script id="__NEXT_DATA__">` tag - `check_lewisham_replacement_buses()`
  extracts that JSON and looks for a "replacement" signal in two places: the
  station's live `nrccMessages` announcements, and any scheduled departure
  in `services` whose `serviceType.category` is `BusReplacement`. It
  deliberately does NOT do a blind text search across the whole page,
  because the page's JS bundle also contains generic UI label strings (e.g.
  `journeySummaryMicrocopy__replacementBusService`) that are always present
  regardless of whether there's an actual disruption right now - matching
  those would make the check permanently report "closed". When either
  signal is found, `check_route_disruption()` reports Lewisham as closed
  ahead of (and instead of) the usual TfL Southeastern line status check.
- When Lewisham is reported closed, `check_route_disruption()` also calls
  `get_hither_green_to_strand_route()` to report a suggested alternative
  route (Hither Green -> Virgin Active Strand, the next station south on the
  same line). Citymapper's own `/directions` page is a pure client-side SPA
  with no server-rendered data at all - confirmed by checking for
  `__NEXT_DATA__`/`__NUXT__`/any embedded JSON, none of which exist; all
  content is rendered by its JS bundle after the page loads. But that JS
  calls a plain, unauthenticated JSON API
  (`citymapper.com/api/7/journeys?start=...&end=...`) to fetch the actual
  route data. Calling that endpoint with no headers gets a Cloudflare 403,
  but a normal browser-like `User-Agent` + `Referer` + `Accept: application/json`
  (`_CITYMAPPER_HEADERS`) is enough to get a clean 200 with full journey
  data (legs, modes, live departure times, price) - no browser, cookies, or
  session needed. `get_hither_green_to_strand_route()` picks the first
  journey in the `SUGGESTED` section and summarises its legs.

## Notes on the Sunday Thu/Fri events check

- `check_wlw_events()` scrapes four separate sources and reports any events
  on the coming Thursday and Friday. Each of the four scrapers
  (`_scrape_outsavvy_organiser()`, `_scrape_old_nunshead()`,
  `_scrape_eventbrite_collection()` x2) is wrapped in its own try/except, so
  one source failing doesn't block the others - the fallback "couldn't
  fetch, check manually" message with all four links only shows up if *all
  four* fail.
- La Camionera's listing (`outsavvy.com/organiser/la-camionera`) is scraped
  via `_scrape_outsavvy_organiser()` - each event is an `<h5>` title inside
  an `<a href>`, with a sibling `<span class="copy">` holding a date string
  like "Thursday 8th October 2026 (+ 1 other date)". `_parse_outsavvy_date()`
  parses out the first (soonest) date and ignores any "+N other dates"
  suffix.
- Old Nun's Head's listing (`theoldnunshead.co.uk/events`, a Squarespace
  site) has a full ISO date in each `<time class="event-date"
  datetime="2026-10-01">`. The page does render every event twice (a grid
  view and a list view sharing the same markup), so `_scrape_old_nunshead()`
  de-duplicates by the event's link.
- `check_wlw_events()` returns `None` when neither Thursday nor Friday has
  any events across all four sources, so (like the office route check) a
  quiet week adds nothing to the briefing at all.
- The Lesbian Pub Quiz and Lesbian Speed Dating are recurring Eventbrite
  event series, scraped from their Eventbrite "collection" pages
  (`eventbrite.com/cc/<slug>-<id>/`, `PUB_QUIZ_EVENTS_URL` /
  `SPEED_DATING_EVENTS_URL`) rather than Eventbrite's generic search pages -
  those sit behind AWS WAF bot-challenge protection and block plain
  `requests.get()`, but these specific collection pages return a clean 200
  with no challenge at all. Each page embeds a `@type=ItemList` block in its
  JSON-LD with every occurrence of that series, past and upcoming, mixed
  together with no particular sort order - each occurrence has a
  timezone-aware `startDate` (e.g. `"2026-10-08T19:00:00+0100"`) where the
  offset is already the correct London BST/GMT for that date, so
  `_scrape_eventbrite_collection()` just takes `.date()` directly with no
  further timezone conversion needed. Since `check_wlw_events()` already
  only keeps events matching the exact target Thursday/Friday dates, past
  occurrences are naturally filtered out without any extra "upcoming only"
  logic. Cancelled occurrences are titled `CANCELLED: ...` by Eventbrite
  itself and are excluded by that prefix.
