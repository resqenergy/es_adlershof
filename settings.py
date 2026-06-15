import os
import pathlib

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
STORE_FILES_LOCALLY = os.getenv("STORE_FILES_LOCALLY", "False") == "True"

ROOT_DIR = pathlib.Path(__file__).parent
CONFIG_DIR = ROOT_DIR / "config"
RAW_DIR = ROOT_DIR / "raw"
RESULTS_DIR = ROOT_DIR / "results"

if S3_ENDPOINT:
    logger.info(f"Using S3 endpoint: {S3_ENDPOINT}.")
else:
    logger.info("No S3 endpoint set, using local files.")
