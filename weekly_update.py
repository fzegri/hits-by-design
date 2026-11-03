#!/usr/bin/env python3
"""Weekly update for Hits by Design.

Downloads Omar Courtz's song list from kworb.net, checks every number,
and rewrites data.js and history.js with a new weekly snapshot.

Exit codes: 0 = updated, 2 = nothing new (kworb hasn't changed), 1 = check failed (nothing written).
Run from the repository root:  python3 scripts/weekly_update.py
Test with a saved page:        python3 scripts/weekly_update.py --html saved_page.html
"""
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser

KWORB_URL = "https://kworb.net/spotify/artist/3E12tRURRvPfHz0hAMCFYc_songs.html"
ALBUM2 = "POR SI MAÑANA NO ESTOY"


def load_js(path, var):
    txt = open(path, encoding="utf-8").read().strip()
    prefix = f"window.{var} = "
    assert txt.startswith(prefix), f"{path} does not start with {prefix}"
    return json.loads(txt[len(prefix):].rstrip(";"))


def save_js(path, var, obj):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"window.{var} = " + json.dumps(obj, ensure_ascii=False) + ";\n")


def norm(s):
    # ignore spacing and invisible characters (Spotify titles sometimes carry zero-width marks)
    return re.sub(r"[\s\u00a0\u200b-\u200f\u2060\ufeff]+", "", s).casefold()


class TableRows(HTMLParser):
    """Collects the text of every table cell, row by row."""

    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell, self.in_cell = [], None, "", False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.in_cell, self.cell = True, ""

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.row is not None and self.in_cell:
            self.row.append(self.cell.strip())
            self.in_cell = False
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.in_cell:
            self.cell += data


def parse_kworb(page):
    m = re.search(r"Last updated:?\s*(\d{4})/(\d{2})/(\d{2})", page)
    asof = dt.date(int(m[1]), int(m[2]), int(m[3])) if m else dt.datetime.utcnow().date()
    p = TableRows()
    p.feed(page)
    songs = {}
    for cells in p.rows:
        if len(cells) < 3:
            continue
        title = html.unescape(cells[0]).lstrip("*").strip()
        nums = [int(c.replace(",", "")) for c in cells[1:] if re.fullmatch(r"[\d,]+", c.strip() or "x")]
        if title and len(nums) >= 2 and norm(title) not in songs:
            songs[norm(title)] = (nums[0], nums[1])  # (total streams, daily streams)
    return asof, songs


def main():
    if "--html" in sys.argv:
        page = open(sys.argv[sys.argv.index("--html") + 1], encoding="utf-8").read()
    else:
        req = urllib.request.Request(KWORB_URL, headers={"User-Agent": "hits-by-design-weekly-update"})
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")

    status = load_js("status.js", "OC_STATUS")
    if status.get("final"):
        print("Series has ended (status.js final). Nothing to do.")
        return 2

    data = load_js("data.js", "OC_DATA")
    hist = load_js("history.js", "OC_HISTORY")
    asof, songs = parse_kworb(page)
    last = dt.date.fromisoformat(data[0]["AsOf"])
    if asof <= last:
        print(f"NOTHING NEW: kworb date {asof} is not after current data {last}")
        return 2

    gap = (asof - last).days
    problems, new = [], []
    for d in data:
        key = norm(d["SpotifyTitle"])
        if key not in songs:
            problems.append(f"missing on kworb: {d['SpotifyTitle']}")
            continue
        tot, daily = songs[key]
        ot, od = d["TotalStreams"], d["DailyStreams"]
        if tot < ot:
            problems.append(f"{d['Title']}: total went down {ot} -> {tot}")
        if tot - ot > (gap + 3) * max(od, daily) * 3:
            problems.append(f"{d['Title']}: total jumped too much {ot} -> {tot}")
        if od > 0 and not (od * 0.2 <= daily <= od * 5):
            problems.append(f"{d['Title']}: daily streams out of range {od} -> {daily}")
        new.append((d, tot, daily))
    if problems:
        print("CHECK FAILED, nothing written:\n" + "\n".join(problems))
        return 1

    for d, tot, daily in new:
        start = dt.date.fromisoformat(d["SingleReleaseDate"] if d["PreReleaseSingle"] == "Yes" else d["AlbumReleaseDate"])
        d["TotalStreams"], d["DailyStreams"], d["AsOf"] = tot, daily, asof.isoformat()
        d["DaysSinceAlbum"] = (asof - dt.date.fromisoformat(d["AlbumReleaseDate"])).days
        d["DaysSinceRelease"] = (asof - start).days
        d["StreamsPerDay"] = round(tot / d["DaysSinceRelease"])
    hist.append({"date": asof.isoformat(), "rows": {d["TrackID"]: [d["TotalStreams"], d["DailyStreams"]] for d in data}})
    save_js("data.js", "OC_DATA", data)
    save_js("history.js", "OC_HISTORY", hist)

    a2 = [x for x in data if x["Album"] == ALBUM2]
    ratios = sorted(x["DailyStreams"] / x["StreamsPerDay"] for x in a2)
    n = len(ratios)
    med = ratios[n // 2] if n % 2 else (ratios[n // 2 - 1] + ratios[n // 2]) / 2
    print(f"UPDATED to {asof} ({len(hist)} weekly snapshots). Album 2 median momentum ratio: {med:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
