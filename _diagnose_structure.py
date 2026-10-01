import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def dump_outsavvy(name, url):
    print(f"\n{'=' * 60}\n{name}: {url}\n{'=' * 60}")
    res = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    # Find <h5> event titles and walk up to find enclosing <a>
    h5s = soup.find_all("h5")
    print(f"Found {len(h5s)} <h5> tags")
    count = 0
    for h5 in h5s:
        title = h5.get_text(strip=True)
        if not title:
            continue
        anchor = h5.find_parent("a")
        href = anchor.get("href") if anchor else None
        # time/date div is usually a sibling within the same card container
        card = anchor if anchor else h5.parent
        time_span = card.find("span", class_="copy") if card else None
        date_text = time_span.get_text(strip=True) if time_span else None
        print(f"- title={title!r}\n  href={href!r}\n  date_text={date_text!r}")
        count += 1
        if count >= 8:
            break


def dump_dalston():
    url = "https://dalstonsuperstore.com/whats-on/"
    print(f"\n{'=' * 60}\ndalstonsuperstore: {url}\n{'=' * 60}")
    res = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.find_all("li", class_="event-thumbnail")
    print(f"Found {len(items)} event-thumbnail <li> items")
    for li in items[:8]:
        a = li.find("a")
        href = a.get("href") if a else None
        day = li.find("h3", class_="events__event-thumbnail__date")
        weekday = li.find("p", class_="events__event-thumbnail__weekday")
        title = li.find("h2", class_="event-thumbnail__title")
        print(f"- day={day.get_text(strip=True) if day else None!r} "
              f"weekday={weekday.get_text(strip=True) if weekday else None!r} "
              f"title={title.get_text(strip=True) if title else None!r}\n  href={href!r}")

    # Look for month context - check for a time/data attribute anywhere in each li, or month headers
    first_li = items[0] if items else None
    if first_li:
        print("\nFull outerHTML of first event li:")
        print(str(first_li)[:1500])


def dump_oldnunshead():
    url = "https://www.theoldnunshead.co.uk/events"
    print(f"\n{'=' * 60}\noldnunshead: {url}\n{'=' * 60}")
    res = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.find_all("article") or soup.select(".eventlist-event")
    print(f"Found {len(items)} article/.eventlist-event items (trying alt selector if 0)")
    if not items:
        items = soup.select("[class*=eventlist-event]")
        print(f"Alt selector found {len(items)} items")
    for it in items[:6]:
        link = it.find("a", class_="eventlist-title-link")
        time_el = it.find("time", class_="event-date")
        print(f"- title={link.get_text(strip=True) if link else None!r} "
              f"href={link.get('href') if link else None!r} "
              f"date={time_el.get('datetime') if time_el else None!r} "
              f"date_text={time_el.get_text(strip=True) if time_el else None!r}")


dump_outsavvy("la-camionera", "https://www.outsavvy.com/organiser/la-camionera")
dump_outsavvy("the-common-press", "https://www.outsavvy.com/organiser/the-common-press")
dump_dalston()
dump_oldnunshead()
