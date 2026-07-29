from datetime import date
import pandas as pd
import geopandas as gpd
from shapely import wkb
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger("resspublica")

from .translations import *
from .utils import *

station_coordinates = {
    "12500": (47.558, 7.588), # https://luftqualitaet.ch/messnetz/station/blSIB
    "12450": (47.500, 7.620), # https://luftqualitaet.ch/messnetz/station/blSIB
    "12510": (47.450, 7.780), # https://luftqualitaet.ch/messnetz/station/blMUT
}

def generateBaselLuftqualitat(ASSETS):
    logger.info("Generating Luftqualitat map in Basel feed...")
    logger.info("Preparing data...")

    urls = [
        "https://data.bs.ch/api/v2/catalog/datasets/100048/exports/parquet",
        "https://data.bs.ch/api/v2/catalog/datasets/100050/exports/parquet",
        "https://data.bs.ch/api/v2/catalog/datasets/100093/exports/parquet",
        "https://data.bs.ch/api/v2/catalog/datasets/100049/exports/parquet",
        "https://data.bs.ch/api/v2/catalog/datasets/100178/exports/parquet",
        "https://data.bs.ch/api/v2/catalog/datasets/100158/exports/parquet",
        "https://data.bl.ch/api/v2/catalog/datasets/12500/exports/parquet",
        "https://data.bl.ch/api/v2/catalog/datasets/12450/exports/parquet",
        "https://data.bl.ch/api/v2/catalog/datasets/12510/exports/parquet"
    ]

    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------
    dataframes = []

    for url in urls:
        logger.debug(f"Querying {url}...")
        df = pd.read_parquet(url)

        station_id = url.split("/")[-3]
        df["station_id"] = station_id

        # -----------------------------------------------------
        # Normalize datetime to Swiss time
        # -----------------------------------------------------
        possible_dates = [
            "datum_zeit",
            "timestamp",
            "anfangszeit",
            "messbeginn"
        ]

        date_column = next(
            (
                col
                for col in possible_dates
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


        # -----------------------------------------------------
        # Add coordinates for BL datasets
        # -----------------------------------------------------
        if station_id in station_coordinates:

            lat, lon = station_coordinates[station_id]

            df["latitude"] = lat
            df["longitude"] = lon


        # -----------------------------------------------------
        # Convert long format datasets
        # -----------------------------------------------------
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


        # -----------------------------------------------------
        # Pollutant normalization
        # -----------------------------------------------------
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


        # -----------------------------------------------------
        # Melt everything into:
        # date_time | station_id | pollutant | value | geometry
        # -----------------------------------------------------
        parts = []

        for pollutant, candidates in pollutant_mapping.items():

            for column in candidates:

                if column not in df.columns:
                    continue

                keep = [
                    "date_time",
                    "station_id",
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


    # ---------------------------------------------------------
    # Combine datasets
    # ---------------------------------------------------------
    dataframe = pd.concat(
        dataframes,
        ignore_index=True,
        sort=False
    )


    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------
    def safe_load(x):
        try:
            return wkb.loads(x)
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


    # ---------------------------------------------------------
    # Time filter
    # ---------------------------------------------------------
    start = pd.Timestamp(
        "2026-07-29 00:00:00"
    )

    end = pd.Timestamp(
        "2026-07-29 23:59:59"
    )


    geo = geo[
        (geo["date_time"] >= start)
        &
        (geo["date_time"] <= end)
    ]


    # ---------------------------------------------------------
    # Average per station
    # ---------------------------------------------------------
    averaged = (
        geo
        .groupby(
            [
                "station_id",
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
    # ---------------------------------------------------------
    # Boundaries
    # ---------------------------------------------------------
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
    ].to_crs(averaged.crs)

    basel_land = cantons[
        cantons["KANTONSNUMMER"] == 13
    ].to_crs(averaged.crs)

    # ---------------------------------------------------------
    # Plot
    # ---------------------------------------------------------
    pollutants = [
        "pm10",
        "pm2_5",
        "no2",
        "o3"
    ]


    fig, axes = plt.subplots(
        1,
        len(pollutants),
        figsize=(20, 5)
    )


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


        subset.plot(
            ax=ax,
            column="value",
            cmap="hot",
            legend=True,
            markersize=80
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


        for _, row in subset.iterrows():
            ax.annotate(
                row["station_id"],
                (
                    row.geometry.x,
                    row.geometry.y
                ),
                fontsize=8
            )


        ax.set_title(
            pollutant
        )

        ax.axis("off")


    plt.tight_layout()
    plt.show()
