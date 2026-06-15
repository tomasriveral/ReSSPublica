from pathlib import Path
import os
import argparse
import logging

from .translations import *

logger = logging.getLogger("resspublica")

from .utils import *
from .federalInitiativesFeeds import *
from .translations import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    CACHE = Path(os.environ.get("RESSPUBLICA_CACHE", ".cache"))
    CACHE.mkdir(parents=True, exist_ok=True)

    logging.info("Starting feed generation")
    generateFederalFeed(CACHE)
    logging.info("Done")
