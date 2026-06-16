import pandas as pd
import copy
import geopandas as gpd
from shapely import wkb
import matplotlib.pyplot as plt
import datetime
from datetime import date, time
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
from time import sleep
from zoneinfo import ZoneInfo
from pathlib import Path


import logging
logger = logging.getLogger("resspublica")

from .translations import *
from .utils import *



# The data set doesn't show directly the day/month only the year. But it does link to a webpage where we can fetch the date
# We cache the date by id to avoid making too much requests
def extract_announcement_date(observationId, observationUrl):
    if db.contains(q.id == observationId):
        logger.debug(f"observation {str(observationId)} was already in db.")
        return date.fromisoformat(db.get(q.id == observationId)["date"])
    else:
        logger.debug(f"observation {str(observationId)} is a new observation.")
        html = fetchUrlToHtml(observationUrl)
        soup = BeautifulSoup(html, "html.parser")
    
        for row in soup.select("table tbody tr"):
            cells = row.find_all("td")
            if cells:
                raw_date = cells[0].get_text(strip=True)
                dt = date.strptime(raw_date, "%d.%m.%Y")
                db.upsert({"id": observationId, "date": dt.isoformat()}, q.id == observationId)
                return dt

def generateBernAsianHornetFeed(ASSETS, CACHE):

    arbitraryStartDate = date.fromisoformat("2026-01-01") # start date for weekly image generation

    logger.info("Generating Asian Hornets sightings in Bern feed...")
    ASIAN_HORNETS_DB_PATH = CACHE / "bernAsianHornet.json"
    global db
    global q
    db = TinyDB(ASIAN_HORNETS_DB_PATH)
    q = Query()


    # 1. Load sightings
    url = "https://geofiles.be.ch/geoportal/pub/download/ASHORNIS/ashornis_sichtnet.parquet"
    df = pd.read_parquet(url)

    # 2. Convert WKB geometry safely
    def safe_load(x):
        try:
            return wkb.loads(x)
        except Exception:
            return None

    df["geometry"] = df["geometry"].apply(safe_load)
    df = df.dropna(subset=["geometry"])

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:2056")

    # We create a weekly image
    # We just need to check if we haven't already created it
    for start, end in weeklyRangesFrom(arbitraryStartDate): # arbitrary start date
        if Path( CACHE / f"bernAsianHornets-fr-{start.isoformat()}-{end.isoformat()}.png").exists(): # we only check french, but if one language exists the other ones should also
            logger.debug(f"Week {start.isoformat()}-{end.isoformat()} was already cached. Skipping...")
            continue
        logger.debug(f"Generating week {start.isoformat()}-{end.isoformat()} ...")
    
        weeklySubsetIdList = [] # we can only select a subset by giving a list of id
    
        logger.debug(f"{str(len(gdf))} observations found")
        for observations in gdf.itertuples():
            # each observation is a tuple similar to 
            #Pandas(Index=0, objectid=6178, meldjahr=2026, anzsichd=nan, anzsichy=1, urlinf_de='https://www.inforama.ch/images/global/beratung/PflanzenbauTierhaltung/Bienen/Asiatische-Hornisse/Sichtungen-von-Asiatischen-Hornissen.pdf', urlinf_fr='https://www.inforama.ch/images/global/beratung/PflanzenbauTierhaltung/Bienen/Asiatische-Hornisse/Observations-de-frelons-asiatiques.pdf', urlah_de='https://geofiles.be.ch/geoportal/pub/zusatzdaten/ASHORNIS/ASHORNIS_22_25_DE.html', urlah_fr='https://geofiles.be.ch/geoportal/pub/zusatzdaten/ASHORNIS/ASHORNIS_22_25_FR.html', katanzsid=0, katanzsiy=1, geometry=<POLYGON ((2594000 1180000, 2594000 1182000, 2596000 1182000, 2596000 118000...>, bbox={'min_x': 2594000.0, 'min_y': 1180000.0, 'max_x': 2596000.0, 'max_y': 1182000.0})

            if start < extract_announcement_date(observations[1],observations[8]) < end:
                weeklySubsetIdList.append(observations[1])
            else:
                logger.debug(f"observation {str(observations[1])} {extract_announcement_date(observations[1], observations[8]).isoformat()} is not in the range ({start.isoformat()} - {end.isoformat()})")
        weeklySubset = gdf[gdf["objectid"].isin(weeklySubsetIdList)]

        # as the canton borders do not change (frequently), we just download once the data
        gdbPathToCantonBoundariesDirectory = ASSETS / "swissBOUNDARIES3D_1_5_LV95_LN02.gdb"

        cantonsBoundariesData = gpd.read_file(
            gdbPathToCantonBoundariesDirectory,
            layer="TLM_KANTONSGEBIET"
        )
    
        bernBoundaries = cantonsBoundariesData[cantonsBoundariesData["KANTONSNUMMER"] == 2].to_crs(gdf.crs)
    
        fig, ax = plt.subplots(figsize=(10, 10))
    
        bernBoundaries.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2)
    
        weeklySubset.plot(
            ax=ax,
            markersize=5,
            color="red",
            alpha=0.6
        )
        for lang in ["fr", "de", "rm", "it", "en"]:
            plt.title(f"{translatedBernAsianHornetSightings[lang]} {start.isoformat()} - {end.isoformat()}")
            plt.axis("off")
            #plt.show()
            plt.savefig(CACHE / f"bernAsianHornets-{lang}-{start.isoformat()}-{end.isoformat()}.png", dpi=120, bbox_inches="tight")
        logger.info("Finished creating images for Bern Asian Hornet Feeds. Preparing feed...")
    feeds = {
        "fr": [],
        "it": [],
        "de": [],
        "rm": [],
        "en": []
    }
    for start, end in weeklyRangesFrom(arbitraryStartDate): # arbitrary start date
        weeklyEntry = {}

        weeklyEntry["id"] = datetime.combine(start, time(12, 0)).timestamp() # we use epoch time as the id
        weeklyEntry["creationDate"] = end.isoformat()
        weeklyEntry["date"] = end.isoformat() # there is no point of updating it later, as (I think) data isn't retroactively put
        weeklyEntry["source"] = "opendata.swiss"

        for lang in ["fr", "it", "de", "rm", "en"]:
            if lang == "rm":
                weeklyEntry["url"] = "https://opendata.swiss/en/dataset/asiatische-hornisse" # there is no Romansh translation
            else:
                weeklyEntry["url"] = f"https://opendata.swiss/{lang}/dataset/asiatische-hornisse"
            weeklyEntry["title"] = translatedBernAsianHornetSightings[lang] + f" {start.isoformat()}-{end.isoformat()}"
            weeklyEntry["text"] = f"<img src=\"https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/.cache/bernAsianHornets-{lang}-{start.isoformat()}-{end.isoformat()}.png\" alt=\"{translatedBernAsianHornetSightings[lang]} {start.isoformat()}-{end.isoformat()}\">" # yes there is an error in filename. the s in asian is capitalized. I don't really want to regenerate all the images...
            feeds[lang].append(copy.deepcopy(weeklyEntry))

    generateFeed(
        "Asian Hornet sightings in Bern",
        "RSS feed of Asian Hornet sightings in Bern",
        "asianHornetSightingsInBern",
        "en",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["en"]
    )
    
    generateFeed(
        "Observations de frelons asiatiques à Berne",
        "Flux RSS des observations de frelons asiatiques à Berne",
        "observationsFrelonsAsiatiquesBerne",
        "fr",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["fr"]
    )
    
    generateFeed(
        "Sichtungen von Asiatischen Hornissen in Bern",
        "RSS-Feed der Sichtungen von Asiatischen Hornissen in Bern",
        "sichtungenAsiatischerHornissenBern",
        "de",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["de"]
    )
    
    generateFeed(
        "Avvistamenti di calabroni asiatici a Berna",
        "Feed RSS degli avvistamenti di calabroni asiatici a Berna",
        "avvistamentiCalabroniAsiaticiBerna",
        "it",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["it"]
    )
    
    generateFeed(
        "Observaziuns da vespras asiaticas a Berna",
        "Feed RSS da las observaziuns da vespras asiaticas a Berna",
        "observaziunsVesprasAsiaticasBerna",
        "rm",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["rm"]
    )
