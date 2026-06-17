from pathlib import Path
import os
import argparse
import logging
logger = logging.getLogger("resspublica")
from datetime import date

from .utils import *
from .federalInitiativesFeeds import *
from .translations import *
from .bernAsianHornet import *
from .bernReligionMap import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--gen_federalInitiatives", action="store_true", help="Generate federal popular initiatives feed")
    parser.add_argument("--gen_bernAsianHornets", action="store_true", help="Generate Asian hornets sightings in Bern feed (only Mondays)")
    parser.add_argument("--force_gen_bernAsianHornets", action="store_true", help="Generate Asian hornets sightings in Bern feed even when not Monday")
    parser.add_argument("--gen_bernReligionMap", action="store_true", help="Generate map of religions in Bern (only start of trimesters)")
    parser.add_argument("--force_gen_bernReligionMap", action="store_true", help="Generate map of religions in Bern even when not start of trimester")


    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    CACHE = Path(os.environ.get("RESSPUBLICA_CACHE", ".cache"))
    CACHE.mkdir(parents=True, exist_ok=True)
    ASSETS = Path(os.environ.get("RESSPUBLICA_ASSETS"))
    ASSETS.mkdir(parents=True, exist_ok=True)

    logging.info("Starting feed generation")
    if args.gen_federalInitiatives:
        generateFederalFeed(CACHE)
    if (date.today().weekday() == 0 and args.gen_bernAsianHornets) or args.force_gen_bernAsianHornets: 
        generateBernAsianHornetFeed(ASSETS, CACHE)
    if ( args.gen_bernReligionMap and date.today().day == 1 and date.today().month in [1, 5, 9]) or args.force_gen_bernReligionMap:
        generateBernReligionMap(ASSETS, CACHE)
    logging.info("Done")
