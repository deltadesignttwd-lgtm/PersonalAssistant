# PersonalAssistant

Sends a daily morning briefing (Octopus Agile electricity price, Lewisham
weather, and a commute route check) to Telegram, plus extra high-frequency
route pings on Saturday and Sunday mornings and a weekday evening commute
check. Telegram is also a two-way channel: sending `/briefing` to the bot
triggers an on-demand copy of the full briefing instead of waiting for the
07:00 run.

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
- **Saturday and Sunday:** Route Check for Lewisham -> Charing Cross
  (Southeastern), closest station to Virgin Active Strand - also checks
  whether Lewisham station itself is closed for rail replacement buses, and
  if so reports a suggested alternative route from Hither Green (see notes
  below)
- **Saturday only, and only if any are found:** Planned Road Events Near
  Route - checks TfL's Road Disruption API for demonstrations/marches,
  concerts, filming, or sporting events near the Strand/Charing Cross area
  (see notes below). Skipped entirely if none are found. (Sunday doesn't get
  its own planned-events check - the Friday evening warning already covers
  the Saturday trip, and there's no equivalent day-ahead warning for Sunday)
- **Sunday only, and only if any are found:** Upcoming Thu/Fri Events - checks
  two queer/community event venues (La Camionera, Old Nun's Head) plus two
  recurring Eventbrite event series (The Lesbian Pub Quiz, Lesbian Speed
  Dating) for events on the coming Thursday and Friday, and lists whatever
  is found with a link to each event (see notes below). If none of the four
  sources have anything on either day, this section is skipped entirely

**Saturday and Sunday, high-frequency route-only pings** (`morning_briefing.py`,
`MODE=route_only`, no weather/price content):

- 10:30-10:55 BST, every 5 minutes
- 11:00-11:15 BST, every 3 minutes

**Monday-Friday, 17:30 BST/GMT** (`morning_briefing.py`, `MODE=evening`):

- Office -> Home Route Check (Old Street [Northern line] -> Bank ->
  Lewisham [DLR], the reverse of the morning Office Route Check) - and
  **only if disrupted**.
- **Fridays only, and only if any are found:** the same Planned Road Events
  check as the Saturday morning briefing, run a day ahead as an early
  warning for the upcoming Saturday gym trip (see notes below for a caveat
  on how much real lead time this gives).
- If neither the route check nor (on Fridays) the planned-events check has
  anything to report, no message is sent at all that run.

**On demand, any time** (`morning_briefing.py`, `MODE=poll_commands`,
polled every 1-2 minutes by an external scheduler - see notes below):

- Sending `/briefing` (or `briefing`, case-insensitive) from the configured
  Telegram chat triggers the exact same full briefing as the 07:00 run -
  all the usual day-of-week sections (Office Route Check Mon-Fri, Gym Route
  Check on Saturday/Sunday, Planned Road Events on Saturday only, Upcoming
  Thu/Fri Events on Sunday) react to whatever day it actually is when you
  send the command.
- Sending `/wlw` (or `wlw`) triggers just the Upcoming Thu/Fri Events check
  on its own, without the rest of the briefing - useful for checking
  outside Sunday without waiting a week. Unlike the Sunday section (which
  disappears entirely from that day's briefing when nothing is found),
  `/wlw` always replies with something, even if that's just "no events
  found" - a command you asked for shouldn't look like it silently failed.
- Messages from any chat other than the configured one, or text that
  doesn't match a recognized command, are silently ignored.

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

All five jobs (now covering both Saturday and Sunday via the day-of-week
field on the two high-frequency ping jobs) call the GitHub Actions "create a
workflow dispatch event" API:
`POST https://api.github.com/repos/deltadesignttwd-lgtm/PersonalAssistant/actions/workflows/{workflow_file}/dispatches`

Common settings for all five jobs:
- **Method:** POST
- **Headers:**
  - `Authorization: Bearer <PAT>` (see below)
  - `Accept: application/vnd.github+json`
  - `X-GitHub-Api-Version: 2022-11-28`
  - `Content-Type: application/json`
- **Body:** `{"ref":"main"}`
- **Timezone:** `Europe/London` (so BST/GMT is handled automatically - no
  twice-yearly manual offset adjustment needed, unlike GitHub's UTC-only cron)
  - except the Telegram command poll, which can just run every N minutes
    around the clock in UTC - there's no day/time gating to get right since
    it only ever *acts* when a `/briefing` message is actually waiting

| Job | Workflow file | Schedule (Europe/London time) |
|---|---|---|
| Daily briefing | `morning-briefing.yml` | Every day, 07:00 |
| Weekend ping (5 min) | `saturday-route-pings.yml` | Sat + Sun, 10:30-10:55, every 5 min |
| Weekend ping (3 min) | `saturday-route-pings.yml` | Sat + Sun, 11:00-11:15, every 3 min |
| Evening commute check | `evening-briefing.yml` | Weekdays (Mon-Fri), 17:30 |
| Telegram command poll | `telegram-poll.yml` | Every day, every 1-2 minutes, all day |

### GitHub token for cron-job.org

A fine-grained Personal Access Token, scoped to **only** this repository,
with **Actions: Read and write** permission and nothing else. Fine-grained
PATs expire after at most 1 year - **set a renewal reminder**, since expiry
will silently break delivery (cron-job.org will start getting 401s) unless
you've also enabled cron-job.org's failure-notification emails.

## Manual testing

All workflows accept manual `workflow_dispatch` runs from the Actions
tab (or via the API). `morning-briefing.yml` additionally takes four inputs
for testing outside their normal day-of-week:

- `force_route_check` (boolean) - include the gym route check, and also the
  planned-events check (two separate `if` blocks, but both also keyed off
  this same flag) even on a day that's neither Saturday nor Sunday. Note
  the gym route check itself runs on Saturday *or* Sunday, but the
  planned-events check stays Saturday-only regardless of this flag's day -
  it only widens which day you can force it on manually
- `force_office_check` (boolean) - include the office route check even on a
  non-weekday
- `force_wlw_check` (boolean) - include the Thu/Fri events check even on a
  non-Sunday
- `simulated_now` (string, ISO datetime e.g. `2026-09-28T07:00:00`) -
  simulate "now" as this date/time instead of the real current time, so
  day-of-week-specific sections (office Mon-Fri, gym Saturday/Sunday, events
  Sunday) react as if it were actually that day - unlike the three `force_*`
  flags above (which only add a section on top of whatever the real day
  already shows), this lets you see, for example, exactly what a genuine
  Monday 07:00 run would send, with no weekend-only content mixed in just
  because today happens to be a Saturday. Leave blank to use the real
  current time.

`evening-briefing.yml` takes one input, `simulated_now` (same format as
`morning-briefing.yml`'s `simulated_now`) - the route check itself has no
day-of-week gating in the script (that's left entirely to when cron-job.org
triggers it), but the planned-events section only runs when "now" is a
Friday, so this input is how to test that section on any other day. Leave
it blank to use the real current time. If neither the route check nor (on a
simulated or real Friday) the planned-events check has anything to report,
nothing is sent to Telegram, but the Actions job log always prints both
judgements (`check_home_from_office_route_disruption()`'s and
`check_planned_events()`'s debug prints), so a test run's outcome is visible
either way.

`telegram-poll.yml` takes no inputs - a manual run just polls Telegram right
now with whatever `telegram_offset.json` currently holds. Send `/briefing`
to the bot first, then manually dispatch the workflow, to see it trigger a
briefing without waiting for the real cron-job.org poll interval.

## Notes on the Telegram on-demand briefing command

- `poll_telegram_commands()` calls Telegram's `getUpdates` API with
  `offset = last_update_id + 1`. Telegram's own semantics mean passing that
  offset also *confirms* every update below it - there's no separate
  "mark as read" call needed. The one piece of state that has to survive
  between runs is `last_update_id` itself, and since every GitHub Actions
  run starts from a brand new container, it's persisted the simplest way
  available without adding new infrastructure: committed to
  `telegram_offset.json` in this repo. The workflow only runs `git commit`
  when that file actually changed (i.e. only when a new Telegram message
  was actually waiting) - the overwhelming majority of polls see zero new
  messages and touch git not at all.
- Only messages whose `chat.id` matches the `TG_CHAT_ID` secret can trigger
  anything - every other sender's message is read (so its `update_id` still
  advances the offset, meaning it won't be looked at again) but otherwise
  completely ignored. This matters because the bot token technically lets
  *anyone* who discovers the bot's username message it; without this check
  a stranger could spam `/briefing` and burn Actions minutes/API calls on
  the account owner's behalf.
- Recognized command text is `/briefing`/`briefing` or `/wlw`/`wlw`
  (case-insensitive, whitespace-trimmed) - anything else from the right
  chat is logged and ignored, not treated as an error.
- `/wlw` calls `send_wlw_events_update()`, which wraps the same
  `check_wlw_events()` the Sunday briefing section uses, but replies
  explicitly even when it returns `None` ("no events found") rather than
  sending nothing - the Sunday section's silent-skip behavior makes sense
  there because it's one optional piece of a larger message that still
  has other content, but a command the user explicitly sent needs *some*
  reply, or it looks like the bot never saw it.
- On first-ever activation, `telegram_offset.json` starts at
  `{"last_update_id": 0}`, which makes the very first poll fetch *any*
  already-pending update Telegram is holding for this bot. Since this bot
  has only ever sent messages (never received any), that backlog should be
  empty in practice - but if you'd previously sent anything to it before
  this feature existed, the first real poll after deploying would process
  that backlog once.
- Short polling (`timeout=0` in the `getUpdates` call) is used instead of
  Telegram's long-polling option, which would hold the HTTP connection open
  waiting for a new message to arrive - the opposite of what a
  run-once-and-exit GitHub Actions job wants.

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
  'elizabeth', 'northern'])` and reuses the same relevance logic (see below)
  rather than duplicating it. It also returns `None` when clear, but unlike
  the morning check (which is just one section of a larger message), a
  `None` here means `send_evening_update()` sends no Telegram message at all
  for that run - this was a deliberate choice (confirmed with the user) over
  always pinging with a "clear" status.
- **2026-10-08 bug and fix - relevance logic for the office/home route
  checks.** `_get_tfl_line_disruptions()` now returns structured
  `{"line", "severity", "reason"}` dicts (using TfL's own
  `statusSeverityDescription` field) instead of pre-formatted strings, so
  callers can reason about severity and text separately.
  `_is_office_route_disruption_relevant()` replaced the old
  `_mentions_irrelevant_office_location()`-only filter, which had a real
  bug: on 2026-10-08 the Northern line reported "Severe delays due to an
  earlier signal failure at Stockwell" with no scoping - a line-wide severe
  delay that did affect the Bank branch this route uses - but the old logic
  silently dropped it just because "Stockwell" (a Morden/Battersea-branch
  station) appeared in `_IRRELEVANT_OFFICE_ROUTE_KEYWORDS`, so the 17:30
  evening ping never fired. The fix changes the default from "assume
  irrelevant unless proven relevant" to "assume relevant unless explicitly
  proven otherwise":
  1. If the text names a station actually on this route
     (`_RELEVANT_OFFICE_ROUTE_KEYWORDS` - Bank, Old Street, Moorgate,
     Lewisham, and the DLR stations between them) it's always relevant,
     regardless of what else the sentence mentions (handles cases like
     "severe delays between Kennington and Bank", where Kennington alone
     would look excludable but the scoped range still covers Bank).
  2. Otherwise, the keyword exclusion list is only trusted when the text
     carries an explicit scoping qualifier (`_LINE_SCOPE_QUALIFIER_RE` -
     "between X and Y" or "GOOD SERVICE on the rest of the line"; TfL does
     write this when a disruption is genuinely confined to one section -
     compare the same day's Elizabeth line notice, which had this qualifier
     and was correctly excluded).
  3. With no scoping qualifier at all, the disruption is treated as
     relevant by default - unlike before, this is no longer limited to
     "Severe Delays" specifically; any non-good-service severity with no
     qualifier now surfaces, since an unscoped "Minor Delays" is just as
     ambiguous as an unscoped "Severe Delays".
  Keyword matching uses `_text_mentions_any()` (word-boundary regex, not
  plain substring `in`) so "Bank" doesn't spuriously match inside
  "Embankment".
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
- **Planned Road Events check (`check_planned_events()`)**, added after a
  real miss on 2026-10-10: a central London demonstration disrupted the
  Saturday gym trip (the Lewisham station closure that day triggered the
  rail-replacement-bus alternative route, but the bus itself then had to
  improvise a diversion mid-journey because of the march) with no advance
  warning in that morning's briefing. `tfl.gov.uk/traffic/status` (the page
  with the `dateTypeSelect`/`corridorIds` query params) is blocked by a bot
  challenge for plain `requests` (403 "Verification required", the same
  WAF pattern as Eventbrite's search pages) and can't be scraped directly.
  Instead, `_get_planned_road_events()` calls TfL's Road Disruption API
  (`https://api.tfl.gov.uk/Road/all/Disruption`) directly - no API key
  needed - and filters to `category == "Planned events"` (covering
  `Demonstration/March`, `Concert`, `Filming`, `Sporting` in `subCategory`).
  `_is_planned_event_relevant()` then keeps only entries whose `location`
  or `comments` mention a road/landmark on or near the Saturday gym walk
  (Strand, Trafalgar Square, Whitehall, Charing Cross, Northumberland
  Avenue, Embankment, Waterloo/Westminster Bridge, Aldwych, etc. - see
  `_RELEVANT_PLANNED_EVENT_KEYWORDS`), matched with the same word-boundary
  `_text_mentions_any()` used by the office-route relevance check (so
  "Strand" doesn't spuriously match inside an unrelated longer word).
  Confirmed against the actual 2026-10-10 demonstration (Victoria
  Embankment -> Whitehall via Westminster Bridge/Waterloo Bridge/Strand/
  Trafalgar Square) - it has `category: "Planned events"`,
  `subCategory: "Demonstration/March"`, and its `location`/`comments` match
  several of the keywords above.
  **Known limitation (honestly unresolved):** every one of the ~126
  disruptions live in the feed at diagnostic time had already started
  (`startDateTime <= now`); none were more than 2 hours in the future. This
  API looks like a "what's happening right now" feed rather than a forward
  calendar, so there's no proof yet that querying it Friday evening or
  Saturday 07:00 will actually surface a Saturday-afternoon event before it
  starts - it may only appear once already under way. It's wired into both
  the Friday evening briefing and the Saturday morning briefing anyway
  (better than nothing, and the real lead time it provides can only be
  determined by watching it run for real over the following weeks), with a
  manual-check fallback link to the (bot-walled) TfL page if the API call
  itself fails.

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
