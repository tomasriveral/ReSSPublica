from feedgen.feed import FeedGenerator
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
from io import BytesIO
import pycurl
from time import sleep

from .translations import *

import logging
logger = logging.getLogger("resspublica")

def generateFeed(title, description, fileName, language, standards, lastUpdateTime, entries):
    # entries must be a dictionary with the following keys:
    # title, id, date, creationDate, url, source, text (html format)
    # other keys will be ignored

    # Note : if you want to only show an image, but the html code for an image in text

    logger.info(f"Generating feed {title}")
    fg = FeedGenerator()
    fg.title(title)
    # We need to set a different link between atom and rss. As rss links are easier with feedgen we set fg.link for atom and fg.__rss_link for rss
    # See https://github.com/lkiesow/python-feedgen/blob/main/feedgen/feed.py#L542
    fg.link(href="https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/" + language  + "/" + fileName + ".atom", rel='self')
    fg.__rss_link = "https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/" + language  + "/" + fileName + ".xml"
    fg.id("https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/" + language  + "/" + fileName)
    fg.description(description)
    fg.language(language)
    if not isinstance(lastUpdateTime, datetime):
        lastUpdateTime = datetime.fromisoformat(lastUpdateTime).replace(tzinfo=ZoneInfo("Europe/Zurich"))
    fg.updated(lastUpdateTime)
    fg.author({'name': 'ReSSPublica'})
    fg.docs("https://github.com/tomasriveral/ReSSPublica")

    for item in entries:
        fe = fg.add_entry()
        fe.title(item["title"])
        fe.guid(f"initiative-{item['id']}", permalink=False)
        if not isinstance(item["date"], datetime):
            item["date"] = datetime.fromisoformat(item["date"]).replace(tzinfo=ZoneInfo("Europe/Zurich"))
        fe.updated(item["date"])
        if not isinstance(item["creationDate"], datetime):
            item["creationDate"] = datetime.fromisoformat(item["creationDate"]).replace(tzinfo=ZoneInfo("Europe/Zurich"))
        fe.pubDate(item["creationDate"])
        fe.source({'url': item["url"], 'title': item["source"]})
        fe.content(item["text"], type="html")
    if "rss" in standards:
        fg.rss_file("./feed/rss/" + language + "/" + fileName + ".xml", pretty=True)
        logger.debug("Wrote to")
        logger.debug("./feed/rss/" + language + "/" + fileName + ".xml")
    if "atom" in standards:
        fg.atom_file("./feed/atom/" + language + "/" + fileName + ".atom", pretty=True)
        logger.debug("Wrote to")
        logger.debug("./feed/atom/" + language + "/" + fileName + ".atom")

    logger.debug("Finished generating feeds")

def getSignatureInfo(start_date, lang="fr"):
    if not isinstance(start_date, datetime):
        start_date = datetime.fromisoformat(start_date).replace(tzinfo=ZoneInfo("Europe/Zurich"))
    end_date = start_date + relativedelta(months=18)

    def format_full(d):
        if lang == "de":
            return f"{d.day}. {translatedMonths[lang][d.month - 1]} {d.year}"
        return f"{d.day} {translatedMonths[lang][d.month - 1]} {d.year}"

    def format_month_year(d):
        return f"{translatedMonths[lang][d.month - 1]} {d.year}"

    start = format_full(start_date)
    end = format_month_year(end_date)

    return f"""
    <p>
        {translatedSignatureDates[lang][0]} {start} {translatedSignatureDates[lang][1]} {end}.
    </p>
    """.strip()

def getValue(row, key):
    return row.get(key, {}).get("value") or None

def fetchUrlToHtml(url: str) -> str:
    buffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.TIMEOUT, 20)
    c.perform()
    c.close()
    
    sleep(1) # avoid making requests too quickly. This shouldn't slow down much as we should try to cache as much possible

    return buffer.getvalue().decode("utf-8", errors="replace")

def weeklyRangesFrom(start_date: date):
    today = date.today()

    # ISO week start = Monday
    def week_start(d):
        return d - timedelta(days=d.weekday())

    current_week_start = week_start(today)

    # align first week start
    start = week_start(start_date)

    weeks = []

    while start < current_week_start:
        end = start + timedelta(days=6)
        weeks.append((start, end))
        start += timedelta(days=7)

    return weeks


def trimester_start(d: date) -> date:
    if d.month <= 4:
        return date(d.year, 1, 1)
    elif d.month <= 8:
        return date(d.year, 5, 1)
    else:
        return date(d.year, 9, 1)
def next_trimester_start(d: date) -> date:
    if d.month <= 4:
        return date(d.year, 5, 1)
    elif d.month <= 8:
        return date(d.year, 9, 1)
    else:
        return date(d.year + 1, 1, 1)
def trimesterRangesFrom(start_date: date):
    today = date.today()

    current_trimester_start = trimester_start(today)
    start = trimester_start(start_date)

    trimesters = []

    while start < current_trimester_start:
        next_start = next_trimester_start(start)
        end = next_start - timedelta(days=1)

        trimesters.append((start, end))
        start = next_start

    return trimesters
