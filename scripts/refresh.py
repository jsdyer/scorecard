"""Collect the Bank's quarterly survey table and its dated policy decisions."""
import calendar
import json
import math
import re
from datetime import date, datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "web/data/scorecard.json"
BOC = "https://www.bankofcanada.ca"
POLICY = BOC + "/core-functions/monetary-policy/key-interest-rate/"
ARCHIVE = BOC + "/content_type/publications/market-participants-survey/"
QUARTERS = ["first", "second", "third", "fourth"]
RELEASE = re.compile(re.escape(BOC) + r'/\d{4}/\d{2}/market-participants-survey-(first|second|third|fourth)-quarter-of-(\d{4})/')
FIRST_EDITION = (2025, 1)
FIRST_TARGET = "2025-06"


def fetch(url):
    request = Request(url, headers={"User-Agent": "CoolCode-PolicyRateScorecard/1.0 (+https://coolcode.ca/scorecard/)"})
    with urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8")


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = self.cell = self.row = None
        self.published = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name") == "publication_date":
            self.published = date.fromisoformat(a["content"]).isoformat()
        if tag == "table":
            self.table = {"id": a.get("id"), "caption": "", "rows": []}
            self.tables.append(self.table)
        if self.table is None:
            return
        if tag == "tr":
            self.row = []
            self.table["rows"].append(self.row)
        if tag in ("th", "td", "caption"):
            self.cell = []
        if tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if self.table is None:
            return
        if tag in ("caption", "th", "td") and self.cell is not None:
            content = " ".join("".join(self.cell).split())
            if tag == "caption":
                self.table["caption"] = content
            elif self.row is not None:
                self.row.append(content)
            self.cell = None
        elif tag == "table":
            self.table = self.row = self.cell = None


def survey(html, url, edition):
    page = TableParser()
    page.feed(html)
    table, = (t for t in page.tables if t["caption"].startswith("2.1 What is your forecast") and "policy interest rate" in t["caption"])
    headers = ["25th percentile of responses", "Median of responses", "75th percentile of responses", "Number of responses"]
    if not page.published or not any(row[1:] == headers for row in table["rows"]):
        raise ValueError(f"Unrecognized survey columns or publication date in {url}")
    forecasts = {}
    year = None
    for row in table["rows"]:
        if not row:
            continue
        label = row[0]
        if re.fullmatch(r"20\d\d", label):
            year = int(label)
        if year and label in list(calendar.month_name)[1:]:
            target = f"{year}-{list(calendar.month_name).index(label):02d}"
            if target < FIRST_TARGET:
                continue
            low, median, high = map(float, row[1:4])
            respondents = int(row[4])
            if target in forecasts or not all(math.isfinite(n) for n in (low, median, high)) or not low <= median <= high or respondents < 1:
                raise ValueError(f"Invalid forecast for {target} in {url}")
            forecasts[target] = dict(low=low, median=median, high=high, respondents=respondents)
    if not forecasts:
        raise ValueError(f"No monthly forecasts in {url}")
    return dict(edition=edition, published=page.published, url=url, forecasts=forecasts)


def decisions(html, previous):
    page = TableParser()
    page.feed(html)
    archive = dict(previous)
    current, = (t for t in page.tables if t["id"] == "target-table")
    rows = current["rows"]
    if rows[0][:2] != ["Date*", "Target (%)"] or len(rows) < 3:
        raise ValueError("The Bank's decision table changed")
    for label, target, _change in rows[1:]:
        day = datetime.strptime(label, "%B %d, %Y").date().isoformat()
        rate = float(target)
        if not math.isfinite(rate):
            raise ValueError(f"Invalid target on {day}")
        archive[day] = rate
    return dict(sorted(archive.items()))


def assemble(editions, actuals, today):
    by_month = {}
    for day, actual in actuals.items():
        by_month.setdefault(day[:7], []).append((day, actual))
    receipts = []
    for item in sorted(editions, key=lambda x: x["published"]):
        for target, forecast in item["forecasts"].items():
            matches = by_month.get(target, [])
            if len(matches) > 1:
                raise ValueError(f"Multiple decisions require reconciliation for {target}")
            day, actual = matches[0] if matches else (None, None)
            if day and item["published"] >= day:
                continue
            if not day and target < today[:7]:
                raise ValueError(f"Missing decision for past target {target}")
            if not day and item["published"][:7] >= target:
                continue  # No dated decision yet to establish that the forecast was public beforehand.
            receipts.append(dict(edition=item["edition"], published=item["published"], source=item["url"],
                                 target=target, decision=day, actual=actual, **forecast))
    return receipts


def collect():
    today = datetime.now(timezone.utc).date().isoformat()
    old = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}
    actuals = decisions(fetch(POLICY), old.get("decisions", {}))
    url = ARCHIVE
    editions = {}
    while url:
        archive = fetch(url)
        found = {m.group(): (int(m[2]), QUARTERS.index(m[1]) + 1) for m in RELEASE.finditer(archive)}
        if not found:
            raise ValueError(f"No survey releases at {url}")
        editions.update({key: val for key, val in found.items() if val >= FIRST_EDITION})
        next_link = re.search(r'class="next page-numbers" href="([^"]+)"', archive)
        url = unescape(next_link[1]) if next_link and min(found.values()) > FIRST_EDITION else None
        if url and not url.startswith(ARCHIVE):
            raise ValueError("Unexpected survey archive link")
    ordered = sorted(editions.items(), key=lambda item: item[1])
    sequence = [4 * year + q for _, (year, q) in ordered]
    if not sequence or min(editions.values()) != FIRST_EDITION or sequence != list(range(sequence[0], sequence[-1] + 1)):
        raise ValueError("Missing or duplicate quarterly release")
    releases = [survey(fetch(url), url, f"{year} Q{q}") for url, (year, q) in ordered]
    receipts = assemble(releases, actuals, today)
    old_scored = {(r["edition"], r["target"]) for r in old.get("receipts", []) if r["actual"] is not None}
    scored = {(r["edition"], r["target"]) for r in receipts if r["actual"] is not None}
    if not scored or not old_scored.issubset(scored):
        raise ValueError("Missing historical forecasts")
    result = dict(retrieved=today, source=POLICY, decisions=actuals, receipts=receipts)
    temp = SNAPSHOT.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temp.replace(SNAPSHOT)
    print(f"{len(receipts)} forecasts from {len(releases)} releases")


if __name__ == "__main__":
    collect()
