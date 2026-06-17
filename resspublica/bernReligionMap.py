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
from seaborn import color_palette


import logging
logger = logging.getLogger("resspublica")

from .translations import *
from .utils import *

# We don't have a date fields in this dataset.
# What we do i create a snapshot (an image) each trimester to see the evolution

def generateBernReligionMap(ASSETS, CACHE):

    arbitraryStartDate = date.fromisoformat("2026-01-01") # start date for weekly image generation. The data source starts at 2021-05-22, but as there is no date information, we must start at today

    logger.info("Generating Religion map in Bern feed...")
    logger.info("Preparing data...")
    #ASIAN_HORNETS_DB_PATH = CACHE / "bernAsianHornet.json"
    #global db
    #global q
    #db = TinyDB(ASIAN_HORNETS_DB_PATH)
    #q = Query()


    # 1. Load data
    url = "https://geofiles.be.ch/geoportal/pub/download/RELIGION/religion_relstaet.parquet"
    dataframe = pd.read_parquet(url)

    # 2. Convert WKB geometry safely
    def safe_load(x):
        try:
            return wkb.loads(x)
        except Exception:
            return None

    dataframe["geometry"] = dataframe["geometry"].apply(safe_load)
    dataframe = dataframe.dropna(subset=["geometry"])

    religionGeoDataFrame = gpd.GeoDataFrame(dataframe, geometry="geometry", crs="EPSG:2056")

    # We create a trimesterly image
    # We just need to check if we haven't already created it

    # Each row is of the form Pandas(Index=127, objectid=23, uuid='D7CF8B83-4CD0-4F9E-9126-603BCCC0A42D', e_koord=2585316, n_koord=1221326, adresse='Rue de la Source 27', plz_ort='2502 Biel/Bienne', name_staet='Christkatholische Kirchgemeinde Biel', bez_staet='Christkatholische Kirchgemeinde Biel', symbol=8, reltra_id=1, reltrat_reltra_de='christlich', reltrat_reltra_fr='Christianisme', nkenn_id=6.0, nkennt_nkenn_de='christkatholisch', nkennt_nkenn_fr='catholique chrétien', kontakt_id=1, kontaktt_kontakt_de='offiziell', kontaktt_kontakt_fr='officiel', url='https://christkatholisch.ch/biel', adresse_k='Sekretariat und Pfarramt, General-Dufourstrasse 105', plz_ort_k='2502 Biel/Bienne', telefon='032 341 21 16', email='sekretariat.biel@christkatholisch.ch', jur_id=1, jurt_jur_de='öffentlich-rechtlich anerkannte Körperschaft', jurt_jur_fr='Collectivité reconnue de droit public', geometry=<POINT (2585316 1221326)>, bbox={'min_x': 2585316.0, 'min_y': 1221326.0, 'max_x': 2585316.0, 'max_y': 1221326.0})
    
    # Note : some religion don't have subdivision in this dataset (ex: Judaisme) and as such don't have nkennt_* keys for them we set nkenn_id to 0

    # Generate a dictionary that contains all (available) religions :
    logger.info("Gathering information on the religions...")
    df = religionGeoDataFrame.copy()
    
    # ensure nkenn_id exists even when NaN
    df['nkenn_id_filled'] = df['nkenn_id'].fillna(0).astype(int)
    
    # build composite key "reltra-nkenn"
    df['key'] = df['reltra_id'].astype(int).astype(str) + "-" + df['nkenn_id_filled'].astype(str)
    
    # keep only relevant columns
    cols = [
        'key',
        'reltra_id',
        'nkenn_id',
        'nkennt_nkenn_fr',
        'nkennt_nkenn_de',
        'reltrat_reltra_fr',
        'reltrat_reltra_de'
    ]
    
    df = df[cols].drop_duplicates(subset=['key'])

    # sort by reltra_id so that religion groups are contiguous
    df = df.sort_values(by=["reltra_id", "nkenn_id"], na_position="last")
    # build dictionary
    religions = (
        df.set_index('key')
        .apply(lambda row: {
            k: v for k, v in {
                "nkenn_id": row["nkenn_id"],
                "nkennt_nkenn_fr": row["nkennt_nkenn_fr"],
                "nkennt_nkenn_de": row["nkennt_nkenn_de"],
                "reltra_id": row["reltra_id"],
                "reltrat_reltra_fr": row["reltrat_reltra_fr"],
                "reltrat_reltra_de": row["reltrat_reltra_de"],
            }.items()
            if pd.notna(v)
        }, axis=1)
        .to_dict()
    )
    logger.debug(religions)

    # generate color palette (1 color by religion with similar religion similar color)
    palette = color_palette("husl", len(religions.keys()))
    color_map = {
        key: palette[i]
        for i, key in enumerate(religions.keys())
    }

    # as the canton borders do not change (frequently), we just download once the data
    gdbPathToCantonBoundariesDirectory = ASSETS / "swissBOUNDARIES3D_1_5_LV95_LN02.gdb"
    
    cantonsBoundariesData = gpd.read_file(
        gdbPathToCantonBoundariesDirectory,
        layer="TLM_KANTONSGEBIET"
    )
    
    bernCantonBoundaries = cantonsBoundariesData[
        cantonsBoundariesData["KANTONSNUMMER"] == 2
    ].to_crs(religionGeoDataFrame.crs)

    religionGeoDataFrame = religionGeoDataFrame[religionGeoDataFrame.geometry.notnull()].copy()

    municipialitiesBoundaries = gpd.read_file(
        gdbPathToCantonBoundariesDirectory,
        layer="TLM_HOHEITSGEBIET"
    )
    
    bernCityBoundaries = municipialitiesBoundaries[
        municipialitiesBoundaries["NAME"] == "Bern"
    ].to_crs(religionGeoDataFrame.crs)

    bernCityPolygon = bernCityBoundaries.geometry.iloc[0]
    
    # subset of the scatter points of religion within the boundaries of the city of Bern
    religionGeoDataFrameSubsetInBernCity = religionGeoDataFrame[religionGeoDataFrame.within(bernCityPolygon)].copy()
    
    for start, end in trimesterRangesFrom(arbitraryStartDate):
        if Path( CACHE / f"bernReligionMap-fr-{start.isoformat()}-{end.isoformat()}.png").exists(): # we only check french, but if one language exists the other ones should also exist
            logger.debug(f"Trimester {start.isoformat()}-{end.isoformat()} was already cached. Skipping...")
            continue
        logger.debug(f"Handling trimester {start.isoformat()}-{end.isoformat()}...")
        
        for lang in ["fr", "de"]:
            fig, (pltAxBernCanton, pltAxBernCity) = plt.subplots(
                2, 1,
                figsize=(12, 16),
                gridspec_kw={"height_ratios": [1.2, 1]}
            )
            bernCantonBoundaries.plot(
                ax=pltAxBernCanton,
                facecolor="none",
                edgecolor="black",
                linewidth=2
            )

            for religion_key in religions.keys():
                logger.info(f"Handling religion {religion_key}")
                reltra_id_str, nkenn_id_str = religion_key.split("-")
            
                reltra_id = int(reltra_id_str)
                nkenn_id = int(nkenn_id_str)
            
                subset = religionGeoDataFrame[religionGeoDataFrame["reltra_id"] == reltra_id]
            
                if nkenn_id == 0:
                    subset.plot(
                        ax=pltAxBernCanton,
                        color=color_map[religion_key],
                        markersize=5,
                        alpha=0.6,
                        label=religions[religion_key][f"reltrat_reltra_{lang}"]
                    )
                else:
                    subset = subset[subset["nkenn_id"] == nkenn_id]
            
                    subset.plot(
                        ax=pltAxBernCanton,
                        color=color_map[religion_key],
                        markersize=5,
                        alpha=0.6,
                        label=religions[religion_key][f"nkennt_nkenn_{lang}"]
                        + f" ({religions[religion_key][f'reltrat_reltra_{lang}'].strip(" ")})"
                    ) # for some reason the reltrat_reltra_fr for bouddisme has a final " " so we need to strip it
            handles, labels = pltAxBernCanton.get_legend_handles_labels()
            
            fig.legend(
                handles,
                labels,
                loc="upper right",
                ncol=1,
                fontsize=10,
                title=translatedPlacesOfWorshipInBern[lang]
            )
            fig.subplots_adjust(right=0.8)
            
            pltAxBernCanton.set_title("")
            pltAxBernCanton.set_axis_off()
            
            bernCantonBoundaries.plot(
                ax=pltAxBernCity,
                facecolor="none",
                edgecolor="black",
                linewidth=2
            )
            
            bernCityBoundaries.boundary.plot(ax=pltAxBernCity, color="black", linewidth=1)
            

            
            for religion_key in religions.keys():
                reltra_id_str, nkenn_id_str = religion_key.split("-")
            
                reltra_id = int(reltra_id_str)
                nkenn_id = int(nkenn_id_str)
            
                subset = religionGeoDataFrameSubsetInBernCity[religionGeoDataFrameSubsetInBernCity["reltra_id"] == reltra_id]
            
                if nkenn_id != 0:
                    subset = subset[subset["nkenn_id"] == nkenn_id]
            
                subset.plot(
                    ax=pltAxBernCity,
                    color=color_map[religion_key],
                    markersize=5,
                    alpha=0.7
                )
            xmin, ymin, xmax, ymax = bernCityBoundaries.total_bounds
    
            pltAxBernCity.set_xlim(xmin, xmax)
            pltAxBernCity.set_ylim(ymin, ymax)
            pltAxBernCity.set_title(translatedCityOfBern[lang])
            pltAxBernCity.set_axis_off()
            
            plt.tight_layout()
            plt.savefig(CACHE / f"bernReligionMap-{lang}-{start.isoformat()}-{end.isoformat()}.png", dpi=120, bbox_inches="tight")
            logger.debug(f"Generated bernReligionMap-{lang}-{start.isoformat()}-{end.isoformat()}.png")
            plt.close()
    feeds = {
        "fr": [],
        "de": []
    }
    for start, end in trimesterRangesFrom(arbitraryStartDate):
        trimestrialEntry = {}
        trimestrialEntry["id"] = datetime.combine(start, time(12, 0)).timestamp() # we use timestamp as ids
        trimestrialEntry["creationDate"] = start.isoformat()
        trimestrialEntry["date"] = start.isoformat() # there is no point have them different. On other feeds it's used for update date
        trimestrialEntry["source"] = "opendata.swiss"

        for lang in ["fr", "de"]:
            trimestrialEntry["url"] = f"https://opendata.swiss/{lang}/dataset/religionslandkarte"
            trimestrialEntry["title"] = f"{translatedPlacesOfWorshipInBern[lang]}-{start.isoformat()}"
            trimestrialEntry["text"] = f"<img src=\"https://raw.githubusercontent.com/tomasriveral/ReSSPublica/refs/heads/main/.cache/bernReligionMap-{lang}-{start.isoformat()}-{end.isoformat()}.png\" alt=\"{translatedPlacesOfWorshipInBern[lang]} {start.isoformat()}\">"
            feeds[lang].append(copy.deepcopy(weeklyEntry))
    generateFeed(
        translatedPlacesOfWorshipInBern["fr"],
        f"Flux RSS des {translatedPlacesOfWorshipInBern["fr"]}",
        translatedPlacesOfWorshipInBernCamelCase["fr"],
        "fr",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["fr"]
    )
    generateFeed(
        translatedPlacesOfWorshipInBern["de"],
        f"RSS-Feed der {translatedPlacesOfWorshipInBern["de"]}",
        translatedPlacesOfWorshipInBernCamelCase["de"],
        "de",
        ["rss", "atom"],
        datetime.now().replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["de"]
    )
