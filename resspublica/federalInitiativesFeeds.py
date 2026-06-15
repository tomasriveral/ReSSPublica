from SPARQLWrapper import SPARQLWrapper, JSON
import copy
from importlib.resources import files
from tinydb import TinyDB, Query
from datetime import datetime
from zoneinfo import ZoneInfo
from .utils import *
from .translations import *

import logging
logger = logging.getLogger("resspublica")

def generateFederalFeed(CACHE):

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


    FEDERAL_DB_PATH = CACHE / "federalInitiatives.json"
    db = TinyDB(FEDERAL_DB_PATH)
    q = Query()

    for entry in data:
        logger.debug(f"Popular initiative {getValue(entry, "title_fr")}")
        item = {
            "id": getValue(entry, "id"),
            # For status, zustand, zurueckgezogen, ungueltig and angenommen, we just get the URI as we can deduce the info we need from it and it makes queries faster.
            # status_uri erledigt/haengig main lifecycle state
            "finished": "erledigt" in getValue(entry, "status_uri"),
            "date": getValue(entry, "date"),
            "creationDate": getValue(entry, "date") 
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
            item["date"] = item["creationDate"]

            db.upsert(item, q.id == item["id"])
            item["date"] = datetime.fromisoformat(item["date"]).replace(tzinfo=ZoneInfo("Europe/Zurich"))

            logger.debug(f"date {item["date"].isoformat()}")
        for lang in ["fr", "de", "it"]:
            item["title"] = getValue(entry, "title_" + lang)
            if item["title"] == None:
                item["title"] = "Missing data"
            item["url"] = translatedFederalPopularInitiativesUrls.get(lang, translatedFederalPopularInitiativesUrls["de"]) + str(getValue(entry, "id"))
            item["source"] = translatedFederalChancellery[lang]

            # We need to construct the text part in three phases:
            # 1. Hyperlink to official page and initial start date
            # 2. status phrase
            # 3. constitutional change


            # Hyperlink to official page and initial start date
            item["text"] = "<p><a href=\""+item["url"]+"\">" + translatedOfficialPage[lang] +"</a></p>" 
            if item["collectedSignature"] == None: # avoid being redundant with the start date
                item["text"] += getSignatureInfo(item["creationDate"], lang)
            else:
                item["text"] += translatedInitiativeStarted[lang].format(date=item["creationDate"])
            
            # Status phrase
            if item["withdrawn"] == True:
                item["text"] += translatedInititiveWithdrawn[lang]
            
            elif item["invalid"] == True:
                item["text"] += translatedInvalidInitiative[lang]
            
            elif item["acceptedInVote"] == False:
                item["text"] += translatedRejectedInVote[lang]
            
            elif item["acceptedInVote"] == True:
                item["text"] += translatedAcceptedInVote[lang]
            
            elif item["collectedSignature"] == True:
                item["text"] += translatedSignatureThresholdReachedWaitingVote[lang]
            
            elif item["collectedSignature"] == False:
                item["text"] += translatedEndDateAndInsufficientSignatures[lang]
            
            elif item["collectedSignature"] == None:
                item["text"] += getSignatureInfo(item["creationDate"], lang)
            
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

    logging.info("Parsed query. Generating feeds...")
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
