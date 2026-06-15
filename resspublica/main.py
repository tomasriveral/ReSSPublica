from SPARQLWrapper import SPARQLWrapper, JSON
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

import .utils
import .translations
import .federalInitiativesFeeds

logger = logging.getLogger("resspublica")

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
