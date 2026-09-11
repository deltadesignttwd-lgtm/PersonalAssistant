# PersonalAssistant

Sends a daily morning briefing (Octopus Agile electricity price, Lewisham
weather, and a commute route check) to Telegram, plus extra high-frequency
route pings on Saturday mornings.

## What it sends

**Daily, 07:00 BST/GMT** (`morning_briefing.py`, `MODE=full`):

- Current + next-24h-lowest Octopus Agile electricity price (region `_C`,
  London/Lewisham)
- Lewisham weather (current temp, today's range, rain warning)
- A link to London's WLW (women loving women) events on Eventbrite - not
  scraped/checked programmatically (see note below), just a direct link to
  open and check yourself
- **Monday-Friday only:** Office Route Check - TfL status for the `dlr` and
  `elizabeth` lines (the actual commute: home -> Canary Wharf via DLR ->
  Liverpool Street via Elizabeth line, decoded from the Citymapper links
  originally supplied)
- **Saturday only:** Route Check for Lewisham -> Charing Cross (Southeastern),
  closest station to Virgin Active Strand

**Saturday only, high-frequency route-only pings** (`morning_briefing.py`,
`MODE=route_only`, no weather/price content):

- 10:30-10:55 BST, every 5 minutes
- 11:00-11:15 BST, every 3 minutes

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

All three call the GitHub Actions "create a workflow dispatch event" API:
`POST https://api.github.com/repos/deltadesignttwd-lgtm/PersonalAssistant/actions/workflows/{workflow_file}/dispatches`

Common settings for all three jobs:
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

### GitHub token for cron-job.org

A fine-grained Personal Access Token, scoped to **only** this repository,
with **Actions: Read and write** permission and nothing else. Fine-grained
PATs expire after at most 1 year - **set a renewal reminder**, since expiry
will silently break delivery (cron-job.org will start getting 401s) unless
you've also enabled cron-job.org's failure-notification emails.

## Manual testing

Both workflows accept manual `workflow_dispatch` runs from the Actions tab
(or via the API). `morning-briefing.yml` additionally takes two boolean
inputs for testing outside their normal day-of-week:

- `force_route_check` - include the Saturday gym route check even on a
  non-Saturday
- `force_office_check` - include the office route check even on a
  non-weekday

## Notes on the route checks

- `check_office_route_disruption()` and `check_route_disruption()` both query
  the TfL Line Status API directly by line id
  (`https://api.tfl.gov.uk/Line/{ids}/Status`) rather than by "mode," since
  mode-based queries for some lines (e.g. `elizabeth-line` as a mode name)
  have been unreliable on TfL's API historically.
- The Citymapper links in `morning_briefing.py` are decorative/fallback links
  for the user to open manually if the TfL check itself fails - they are not
  queried programmatically (Citymapper has no public routing-status API).
- The Eventbrite WLW-events link is also decorative only: `eventbrite.co.uk`
  sits behind AWS WAF bot-challenge protection (a CAPTCHA "Human
  Verification" page) that blocks both plain HTTP requests and a headless
  Playwright browser, and Eventbrite's official public API was deprecated in
  2019 and only supports querying events you organize yourself. There's no
  lightweight way to programmatically check which events are on today, so
  the message just links to the search page instead.
