from SPARQLWrapper import SPARQLWrapper, JSON
from feedgen.feed import FeedGenerator
from importlib.resources import files
from datetime import datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
from tinydb import TinyDB, Query
from pathlib import Path
import os
import copy
import argparse
import logging

logger = logging.getLogger("resspublica")

def getSignatureInfo(start_date, lang="fr"):
    MONTHS = {
        "fr": ["janvier","février","mars","avril","mai","juin",
               "juillet","août","septembre","octobre","novembre","décembre"],
        "de": ["Januar","Februar","März","April","Mai","Juni",
               "Juli","August","September","Oktober","November","Dezember"],
        "it": ["gennaio","febbraio","marzo","aprile","maggio","giugno",
               "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    }

    texts = {
        "fr": ("<p>La collecte des signatures a commencé le", "et se terminera vers</p>"),
        "de": ("<p>Die Unterschriftensammlung begann am", "und endet ungefähr im</p>"),
        "it": ("<p>La raccolta delle firme è iniziata il", "e terminerà circa nel</p>"),
    }
    if not isinstance(start_date, datetime):
        start_date = datetime.fromisoformat(start_date).replace(tzinfo=ZoneInfo("Europe/Zurich"))
    end_date = start_date + relativedelta(months=18)

    def format_full(d):
        if lang == "de":
            return f"{d.day}. {MONTHS[lang][d.month - 1]} {d.year}"
        return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"

    def format_month_year(d):
        return f"{MONTHS[lang][d.month - 1]} {d.year}"

    start = format_full(start_date)
    end = format_month_year(end_date)

    return f"""
    <p>
        {texts[lang][0]} {start} {texts[lang][1]} {end}.
    </p>
    """.strip()
def getValue(row, key):
    return row.get(key, {}).get("value") or None
def generateFeed(title, description, fileName, language, standards, entries):
    time = datetime.now(ZoneInfo("Europe/Zurich"))
    fg = FeedGenerator()
    fg.title(title)
    # We need to set a different link between atom and rss. As rss links are easier with feedgen we set fg.link for atom and fg.__rss_link for rss
    # See https://github.com/lkiesow/python-feedgen/blob/main/feedgen/feed.py#L542
    fg.link(href="https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/" + language  + "/" + fileName, rel='self')
    fg.__rss_link = "https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/rss/" + language  + "/" + fileName
    fg.id("https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/feed/atom/" + language  + "/" + fileName)
    fg.description(description)
    fg.language(language)
    fg.updated(time)
    fg.author({'name': 'ReSSPublica'})
    fg.docs("https://github.com/tomasriveral/ReSSPublica")

    for item in entries:
        fe = fg.add_entry()
        fe.title(item["title"])
        fe.guid(f"initiative-{item['id']}", permalink=False)
        fe.pubDate(item["date"])
        fe.source({'url': item["url"], 'title': item["source"]})
        fe.content(item["text"], type="html")
    if "rss" in standards:
        fg.rss_file("./feed/rss/" + language + "/" + fileName + ".xml", pretty=True)
    if "atom" in standards:
        fg.atom_file("./feed/atom/" + language + "/" + fileName + ".atom", pretty=True)

def generateFederalFeed():

    logger.info("Making th SPARQL query")
    sparql = SPARQLWrapper("https://cached.lindas.admin.ch/query")
    query = files("resspublica.queries").joinpath("federalPopularInitiatives.sparql").read_text()
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()

    logger.info("Query succesfully returned. Processing the feeds.")
    logger.info(f"Lenght of the return: {len(results["results"]["bindings"])}\nShould be greater or equal than 550 if the query limit wasn't overriden.")
    
    now = datetime.now(ZoneInfo("Europe/Zurich"))

    # remove some of useless json data such as "head": {"vars": [...]}
    data = results["results"]["bindings"]

    feeds = {
      "fr": [],
      "de": [],
      "it": []
    }

    BASE_URLS = {
        "fr": "https://www.bk.admin.ch/fr/details-initiatives-populaires/?initiative=",
        "de": "https://www.bk.admin.ch/de/details-volksinitiativen/?initiative=",
        "it": "https://www.bk.admin.ch/it/dettagli-iniziative-popolari/?initiative="
    }
    BASE_SOURCE = {
        "fr": "Chancellerie fédérale ChF",
        "de": "Bundeskanzlei BK",
        "it": "Cancelleria federale CaF"
    }
    BASE_PAGE = {
        "fr": "Page officielle",
        "de": "Offizielle Seite",
        "it": "Pagina ufficiale"
    }

    message_collecting = {
        "fr": "<p>La collecte des signatures a commencé et est en cours.</p>",
        "de": "<p>Die Sammlung der Unterschriften hat begonnen und läuft noch.</p>",
        "it": "<p>La raccolta delle firme è iniziata ed è in corso.</p>"
    }
    
    message_threshold_reached_waiting_vote = {
        "fr": "<p>L’initiative a atteint 100'000 signatures et attend la votation.</p>",
        "de": "<p>Die Initiative hat 100'000 Unterschriften erreicht und wartet auf die Abstimmung.</p>",
        "it": "<p>L’iniziativa ha raggiunto 100'000 firme ed è in attesa della votazione.</p>"
    }
    
    message_finished_insufficient_signatures = {
        "fr": "<p>L’initiative n’a pas atteint les 100'000 signatures et la procédure est terminée.</p>",
        "de": "<p>Die Initiative hat das erforderliche Quorum nicht erreicht und das Verfahren ist abgeschlossen.</p>",
        "it": "<p>L’iniziativa non ha raggiunto il numero richiesto di firme e la procedura è conclusa.</p>"
    }
    
    message_withdrawn = {
        "fr": "<p>L’initiative a été retirée.</p>",
        "de": "<p>Die Initiative wurde zurückgezogen.</p>",
        "it": "<p>L’iniziativa è stata ritirata.</p>"
    }
    
    message_invalid = {
        "fr": "<p>L’initiative a été déclarée invalide.</p>",
        "de": "<p>Die Initiative wurde für ungültig erklärt.</p>",
        "it": "<p>L’iniziativa è stata dichiarata non valida.</p>"
    }
    
    message_accepted_vote = {
        "fr": "<p>L’initiative a été acceptée en votation.</p>",
        "de": "<p>Die Initiative wurde in der Abstimmung angenommen.</p>",
        "it": "<p>L’iniziativa è stata accettata in votazione.</p>"
    }
    
    message_rejected_vote = {
        "fr": "<p>L’initiative a été rejetée en votation.</p>",
        "de": "<p>Die Initiative wurde in der Abstimmung abgelehnt.</p>",
        "it": "<p>L’iniziativa è stata respinta in votazione.</p>"
    }
    message_opened = {
        "fr": "<p>L’initiative a été lancée le {date}.</p>",
        "de": "<p>Die Initiative wurde am {date} gestartet.</p>",
        "it": "<p>L’iniziativa è stata lanciata il {date}.</p>"
    }

    FEDERAL_DB_PATH = CACHE / "federalInitiatives.json"
    db = TinyDB(FEDERAL_DB_PATH)
    q = Query()

    for entry in data:
        logger.debug(f"Popular initiative {getValue(entry, "title_fr")}")
        creationDate = datetime.strptime(getValue(entry, "date"), "%Y-%m-%d").replace(tzinfo=ZoneInfo("Europe/Zurich"))
        item = {
            "id": getValue(entry, "id"),
            # For status, zustand, zurueckgezogen, ungueltig and angenommen, we just get the URI as we can deduce the info we need from it and it makes queries faster.
            # status_uri erledigt/haengig main lifecycle state
            "finished": "erledigt" in getValue(entry, "status_uri"),
            "date": getValue(entry, "date")
        }
        logger.debug(f"status_uri {getValue(entry, "status_uri")}")
        logger.debug(f"finished {str(item["finished"])}")

        # zustand_uri nein/ja/Undefined valid initiative reached threshold
        zustand = getValue(entry, "zustand_uri")
        logger.debug(f"zustand_uri: {zustand}")
        if "Undefined" in zustand:
            item["collectedSignature"] = None
        elif "ja" in zustand:
            item["collectedSignature"] = True
        elif "nein" in zustand:
            item["collectedSignature"] = False
        else:
            raise ValueError("Unexpected value in zustand_uri: " + zustand + " (Expected are [...]nein, [...]ja and [...]Undefined)")
        
        logger.debug(f"collectedSignature {str(item["collectedSignature"])}")

        # zurueckgezogen_uri nein/ja/Undefined withdrawal
        zurueckgezogen = getValue(entry, "zurueckgezogen_uri")
        logger.debug(f"zurueckgezogen_uri {getValue(entry, "zurueckgezogen_uri")}")
        if "Undefined" in zurueckgezogen:
            item["withdrawn"] = None
        elif "ja" in zurueckgezogen:
            item["withdrawn"] = True
        elif "nein" in zurueckgezogen:
            item["withdrawn"] = False
        else:
            raise ValueError("Unexpected value in zurueckgezogen_uri: " + zurueckgezogen + " (Expected are [...]nein, [...]ja and [...]Undefined)")
        logger.debug(f"withdrawn {str(item["withdrawn"])}")

        # I couldn't find an example for invalided initiatives. So if it is not Undefined we set to true. invalid initiative
        logger.debug(f"ungueltig_uri {getValue(entry, "ungueltig_uri")}")
        item["invalid"] = "Undefined" not in getValue(entry, "ungueltig_uri")
        logger.debug(f"invalid {str(item["invalid"])}")

        # angenommen_uri nein/ja/Undefined/undefiniert For some reason two types of undefined. accepted in vote
        angenommen  = getValue(entry, "angenommen_uri")
        logger.debug(f"angenommen_uri {getValue(entry, "angenommen_uri")}")
        if "Undefined" in angenommen or "undefiniert" in angenommen:
            item["acceptedInVote"] = None
        elif  "ja" in angenommen:
            item["acceptedInVote"] = True
        elif "nein" in angenommen:
            item["acceptedInVote"] = False
        else:
            raise ValueError("Unexpected value in angenommen_uri: " + angenommen + " (Expected are [...]nein, [...]ja, [...]Undefined and [...]undefiniert)")
        
        logger.debug(f"acceptedInVote {str(item["acceptedInVote"])}")

        # if we already got the initiative in the db
        if db.contains(q.id == item["id"]):
            oldStatus = db.get(q.id == item["id"])
            needsUpdate = False

            if {k: oldStatus.get(k) for k in oldStatus if k != "date"} != {k: item.get(k) for k in item if k != "date"}:
                needsUpdate = True

            if needsUpdate:
                item["date"] = now.isoformat()
            else:
                item["date"] = oldStatus["date"]
            db.upsert(item, q.id == item["id"])
            item["date"] = datetime.fromisoformat(item["date"]).replace(tzinfo=ZoneInfo("Europe/Zurich"))
        else:
            # if we don't have it:
            # if still in signature phase -> creationDate
            # if not -> now
            item["date"] = creationDate.isoformat()

            db.upsert(item, q.id == item["id"])
            item["date"] = datetime.fromisoformat(item["date"]).replace(tzinfo=ZoneInfo("Europe/Zurich"))

            logger.debug(f"date {item["date"].isoformat()}")
        for lang in ["fr", "de", "it"]:
            item["title"] = getValue(entry, "title_" + lang)
            if item["title"] == None:
                item["title"] = "Missing data"
            item["url"] = BASE_URLS.get(lang, BASE_URLS["de"]) + str(getValue(entry, "id"))
            item["source"] = BASE_SOURCE[lang]

            # We need to construct the text part in three phases:
            # 1. Hyperlink to official page and initial start date
            # 2. status phrase
            # 3. constitutional change


            # Hyperlink to official page and initial start date
            item["text"] = "<p><a href=\""+item["url"]+"\">" + BASE_PAGE[lang] +"</a></p>" 
            if item["collectedSignature"] == None: # avoid being redundant with the start date
                item["text"] += getSignatureInfo(creationDate, lang)
            else:
                item["text"] += message_opened[lang].format(date=creationDate.date())
            
            # Status phrase
            if item["withdrawn"] == True:
                item["text"] += message_withdrawn[lang]
            
            elif item["invalid"] == True:
                item["text"] += message_invalid[lang]
            
            elif item["acceptedInVote"] == False:
                item["text"] += message_rejected_vote[lang]
            
            elif item["acceptedInVote"] == True:
                item["text"] += message_accepted_vote[lang]
            
            elif item["collectedSignature"] == True:
                item["text"] += message_threshold_reached_waiting_vote[lang]
            
            elif item["collectedSignature"] == False:
                item["text"] += message_finished_insufficient_signatures[lang]
            
            elif item["collectedSignature"] == None:
                item["text"] += getSignatureInfo(creationDate, lang)
            
            else:
                raise ValueError(
                    "Invalid initiative state combination: "
                    f"item[\"withdrawn\"]={item["withdrawn"]}, "
                    f"item[\"invalid\"]={item["invalid"]}, "
                    f"item[\"acceptedInVote\"]={item["acceptedInVote"]}, "
                    f"item[\"collectedSignature\"]={item["collectedSignature"]}, "
                    f"item[\"finished\"]={item["finished"]}"
                )

            # Constitutional change
            item["text"] += getValue(entry, "text_" + lang)

            feeds[lang].append(copy.deepcopy(item))


    generateFeed(
        "Initiatives populaires fédérales",
        "Flux RSS des initiatives populaires fédérales",
        "initiativesPopulairesFederales",
        "fr",
        ["rss", "atom"],
        feeds["fr"]
    )
    
    generateFeed(
        "Eidgenössisch Volksinitiativen",
        "RSS-Feed der föderalen Volksinitiativen",
        "eidgenossischVolksinitiativen",
        "de",
        ["rss", "atom"],
        feeds["de"]
    )
    
    generateFeed(
        "Iniziative popolari federali",
        "Feed RSS delle iniziative popolari federali",
        "iniziativePopolariFederali",
        "it",
        ["rss", "atom"],
        feeds["it"]
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    global CACHE
    CACHE = Path(os.environ.get("RESSPUBLICA_CACHE", ".cache"))
    CACHE.mkdir(parents=True, exist_ok=True)

    logging.info("Starting feed generation")
    generateFederalFeed()
    logging.info("Done")
