from datetime import date, timedelta, datetime
import pandas as pd
import geopandas as gpd
from shapely import wkb
import matplotlib.pyplot as plt
from pathlib import Path
import copy

import logging
logger = logging.getLogger("resspublica")

from .translations import *
from .utils import *

startDate = pd.Timestamp("2026-01-01")
startDateDatetimeFormat = date.fromisoformat("2026-01-01") # a bit dumb we need those two formats
endDate = pd.Timestamp((date.today() - timedelta(days=1)).isoformat())
 

stationInformation = {
    "100048": {
        "name": "Basel Chrischona",
        "coordinates": (47.571709338, 7.687073826)
    },
    "100050": {
        "name": "Basel Feldbergstrasse",
        "coordinates": (47.567022213, 7.594722533)
    },
    "100049": {
        "name": "Basel St. Johannplatz",
        "coordinates": (47.565950312, 7.582002453)
    },
    
    "12450": {
        "name": "Sissach-Bützenen",
        "coordinates": (47.465037653, 7.815429278)
    },
    "12510": {
        "name": "A2 Hard",
        "coordinates": (47.538075849, 7.648985359)
    },
}

pollutants = [
    "pm10",
    "pm2_5",
    "no2",
    "o3"
]

pollutantUnits = {
"pm10": "µg/m³",
"pm2_5": "µg/m³",
"no2": "µg/m³",
"o3": "µg/m³",
}


# Fixed scale per pollutant so colors remain comparable day-to-day
pollutantScales = {
"pm10": (0, 50),
"pm2_5": (0, 30),
"no2": (0, 100),
"o3": (0, 200),
}

def generateBaselLuftqualitat(ASSETS, CACHE):
    
    urls = [ 
        "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100048/exports/parquet?where=datum_zeit>2026-01-01",
        "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100050/exports/parquet?where=datum_zeit>2026-01-01",
        "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100093/exports/parquet", # if we use where with this one it 400: Bad Request
        "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100049/exports/parquet?where=datum_zeit>2026-01-01",
        "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100178/exports/parquet",
        "https://data.bl.ch/api/v2/catalog/datasets/12450/exports/parquet",
        "https://data.bl.ch/api/v2/catalog/datasets/12510/exports/parquet"
    ]
    
    dataframes = []
    
    for url in urls:
        logger.debug(f"Querying {url}...")
        df = pd.read_parquet(url)
    
        stationId = url.split("/")[-3]
    
        df["stationId"] = stationId
        
        # Always define station name
        # Use dataset id as fallback until manually mapped
        df["stationName"] = stationId
        
        if stationId in stationInformation:
            df["stationName"] = stationInformation[stationId]["name"]
    
        possibleVariableNameForDates = [
            "datum_zeit",
            "timestamp",
            "anfangszeit",
            "messbeginn"
        ]
    
        date_column = next(
            (
                col
                for col in possibleVariableNameForDates
                if col in df.columns
            ),
            None
        )
    
        if date_column is None:
            logger.warning(
                f"No date column found in {url}, skipping"
            )
            continue
    
        df["date_time"] = pd.to_datetime(
            df[date_column],
            errors="coerce",
            utc=True
        )
    
        df["date_time"] = (
            df["date_time"]
            .dt.tz_convert("Europe/Zurich")
            .dt.tz_localize(None)
        )
    
    
        if stationId in stationInformation:
        
            lat, lon = stationInformation[stationId]["coordinates"]
        
            df["latitude"] = lat
            df["longitude"] = lon
        
            df["stationName"] = (
                stationInformation[stationId]["name"]
            )
    
        if (
            "parameter" in df.columns
            and "messwert" in df.columns
        ):
    
            df = df.pivot_table(
                index=[
                    "date_time",
                    "geo_point_2d"
                ],
                columns="parameter",
                values="messwert",
                aggfunc="mean"
            ).reset_index()
    
    
        pollutant_mapping = {
    
            "pm10": [
                "pm10",
                "pm10_stundenmittelwerte_ug_m3"
            ],
    
            "pm2_5": [
                "pm2_5",
                "pm2.5",
                "pm25",
                "pm2_5_stundenmittelwerte_ug_m3",
                "g107_pm25",
                "g125_pm25",
                "g131_pm25",
                "a2hard_pm25",
                "feldbergstr2_pm25",
                "stjohann2_pm25"
            ],
    
            "no2": [
                "no2",
                "no2_stundenmittelwerte_ug_m3",
                "g107_no2",
                "g125_no2",
                "g131_no2",
                "a2hard_no2",
                "feldbergstr2_no2",
                "stjohann2_no2"
            ],
    
            "o3": [
                "o3",
                "o3_stundenmittelwerte_ug_m3",
                "g107_o3",
                "g107_03",
                "g125_o3",
                "g131_o3",
                "a2hard_o3",
                "feldbergstr2_o3",
                "stjohann2_o3"
            ]
        }
    
        parts = []
    
        for pollutant, candidates in pollutant_mapping.items():
    
            for column in candidates:
    
                if column not in df.columns:
                    continue
    
                keep = [
                    "date_time",
                    "stationId",
                    "stationName",
                    column
                ]
    
                for extra in [
                    "geo_point_2d",
                    "latitude",
                    "longitude"
                ]:
                    if extra in df.columns:
                        keep.append(extra)
    
    
                tmp = df[keep].copy()
    
                tmp = tmp.rename(
                    columns={
                        column: "value"
                    }
                )
    
                tmp["pollutant"] = pollutant
    
                parts.append(tmp)
    
    
        if not parts:
            logger.warning(
                f"No pollutants found in {url}"
            )
            continue
    
    
        df = pd.concat(
            parts,
            ignore_index=True
        )
    
        dataframes.append(df)
    
    dataframe = pd.concat(
        dataframes,
        ignore_index=True,
        sort=False
    )
    
    def safe_load(x):
        try:
            geom = wkb.loads(x)
            if geom.is_empty:
                return None
            return geom
        except Exception:
            return None
    
    dataframe["geometry"] = None
    
    if "geo_point_2d" in dataframe.columns:
    
        dataframe["geometry"] = dataframe[
            "geo_point_2d"
        ].apply(
            safe_load
        )
    
    
    # Fill missing geometry from coordinates
    missing_geometry = dataframe["geometry"].isna()
    
    dataframe.loc[
        missing_geometry,
        "geometry"
    ] = gpd.points_from_xy(
        dataframe.loc[missing_geometry, "longitude"],
        dataframe.loc[missing_geometry, "latitude"]
    )
    
    
    geo = gpd.GeoDataFrame(
        dataframe,
        geometry="geometry",
        crs="EPSG:4326"
    )
    
    gdb = (
        ASSETS /
        "swissBOUNDARIES3D_1_5_LV95_LN02.gdb"
    )
    
    cantons = gpd.read_file(
        gdb,
        layer="TLM_KANTONSGEBIET"
    )
    
    basel_stadt = cantons[
        cantons["KANTONSNUMMER"] == 12
    ].to_crs("EPSG:4326")
    
    basel_land = cantons[
        cantons["KANTONSNUMMER"] == 13
    ].to_crs("EPSG:4326")
    
    logger.info("Generating daily image...")
    for day in pd.date_range(startDate, endDate, freq="D"):

        if Path( CACHE / f"baselAirQuality-{day.strftime("%Y-%m-%d")}.png").exists():
            logger.debug(f"Day {day.strftime("%Y-%m-%d")} is already cached. Skipping...")
            continue
        logger.debug(f"Handling day {day.strftime("%Y-%m-%d")}...")
    
        next_day = day + pd.Timedelta(days=1)
    
        geo_day = geo[
            (geo["date_time"] >= day)
            &
            (geo["date_time"] < next_day)
        ]
        
        averaged = (
            geo_day.groupby(
                [
                    "stationId",
                    "stationName",
                    "pollutant",
                    "geometry"
                ],
                as_index=False
            )
            ["value"]
            .mean()
        )
        
        
        averaged = gpd.GeoDataFrame(
            averaged,
            geometry="geometry",
            crs="EPSG:4326"
        )

        fig, axes = plt.subplots(
            2,
            2,
            figsize=(14, 14)
        )
        
        axes = axes.flatten()
        
        
        for ax, pollutant in zip(
            axes,
            pollutants
        ):
        
            subset = averaged[
                averaged["pollutant"] == pollutant
            ]
        
        
            if subset.empty:
                ax.set_visible(False)
                continue
        
            vmin, vmax = pollutantScales[pollutant]
        
            subset.plot(
                ax=ax,
                column="value",
                cmap="hot_r",
                legend=True,
                markersize=150,
                vmin=vmin,
                vmax=vmax
            )
        
        
            basel_land.plot(
                ax=ax,
                facecolor="none",
                edgecolor="black",
                linewidth=2
            )
        
        
            basel_stadt.plot(
                ax=ax,
                facecolor="none",
                edgecolor="black",
                linewidth=1
            )
        
            ax.set_xlim(
                7.45,
                7.90
            )
            
            ax.set_ylim(
                47.35,
                47.70
            )
        
        
            # these offsets exist to avoid collision between names
            label_offsets = {
                "Basel Feldbergstrasse": (10, 8),
                "Basel St. Johannplatz": (-10, -12),
                "Basel Chrischona": (0, 8),
                "Sissach-Bützenen": (0, 8),
                "A2 Hard": (0, 8),
            }
            
            for _, row in subset.iterrows():
            
                dx, dy = label_offsets.get(
                    row["stationName"],
                    (0, 8)
                )
            
                ax.annotate(
                    row["stationName"],
                    xy=(
                        row.geometry.x,
                        row.geometry.y
                    ),
                    xytext=(dx, dy),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9,
                    bbox=dict(
                        facecolor="white",
                        alpha=0.7,
                        edgecolor="none",
                        pad=1
                    )
                )
        
            ax.set_title(
                f"{pollutant} ({pollutantUnits[pollutant]})"
            )
        
            ax.axis("off")
        
        for ax in axes[len(pollutants):]:
            ax.set_visible(False)
        fig.suptitle(day.strftime("%Y-%m-%d"))
        
        plt.tight_layout()
        plt.savefig(CACHE / f"baselAirQuality-{day.strftime("%Y-%m-%d")}.png", dpi=120, bbox_inches="tight")
        plt.close()

    feeds = {
        "fr": [],
        "de": [],
        "it": [],
        "rm": [],
        "en": []
    }

    yesterday = date.today() - timedelta(days=1)
    current = startDateDatetimeFormat
    
    while current <= yesterday:
        dailyEntry = {}
        dailyEntry["id"] = f"air-quality-basel-{current.isoformat()}"
        dailyEntry["creationDate"]  = current.isoformat()
        dailyEntry["date"] = current.isoformat()
        dailyEntry["source"] = "https://luftqualitaet.ch/"
        dailyEntry["url"] = "https://luftqualitaet.ch/"
        dailyEntry["text"] = f"<img src=\"https://resspublica.tomasrivera.ch/images/baselAirQuality-{current.isoformat()}.png\"alt=\"basel air quality {current.isoformat()}\">"

        for lang in ["fr", "de", "it", "rm", "en"]:
            dailyEntry["title"] = f"{translatedAirQualityInBasel[lang]} {current.isoformat()}"
            feeds[lang].append(copy.deepcopy(dailyEntry))

        current += timedelta(days=1)

    generateFeed(
        translatedAirQualityInBasel["fr"],
        f"Flux RSS des {translatedAirQualityInBasel["fr"]}",
        translatedAirQualityInBaselCamelCase["fr"],
        "fr",
        ["rss", "atom"],
        datetime.fromisoformat(f"{yesterday.isoformat()} 23:59:59").replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["fr"]
    )
    generateFeed(
        translatedAirQualityInBasel["de"],
        f"RSS-Feed für {translatedAirQualityInBasel['de']}",
        translatedAirQualityInBaselCamelCase["de"],
        "de",
        ["rss", "atom"],
        datetime.fromisoformat(f"{yesterday.isoformat()} 23:59:59").replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["de"]
    )
    
    generateFeed(
        translatedAirQualityInBasel["en"],
        f"RSS feed for {translatedAirQualityInBasel['en']}",
        translatedAirQualityInBaselCamelCase["en"],
        "en",
        ["rss", "atom"],
        datetime.fromisoformat(f"{yesterday.isoformat()} 23:59:59").replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["en"]
    )
    
    generateFeed(
        translatedAirQualityInBasel["it"],
        f"Feed RSS per {translatedAirQualityInBasel['it']}",
        translatedAirQualityInBaselCamelCase["it"],
        "it",
        ["rss", "atom"],
        datetime.fromisoformat(f"{yesterday.isoformat()} 23:59:59").replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["it"]
    )
    
    generateFeed(
        translatedAirQualityInBasel["rm"],
        f"Feed RSS per {translatedAirQualityInBasel['rm']}",
        translatedAirQualityInBaselCamelCase["rm"],
        "rm",
        ["rss", "atom"],
        datetime.fromisoformat(f"{yesterday.isoformat()} 23:59:59").replace(tzinfo=ZoneInfo("Europe/Zurich")),
        feeds["rm"]
    )
