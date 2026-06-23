import pathlib

from loguru import logger
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = pathlib.Path(__file__).parent
CONFIG_DIR = ROOT_DIR / "config"
RAW_DIR = ROOT_DIR / "raw"
DATASETS_DIR = ROOT_DIR / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

logger.info("Settings")
logger.info(f"Config: {CONFIG_DIR.absolute()}")
logger.info(f"Raw data: {RAW_DIR.absolute()}")
logger.info(f"Datasets: {DATASETS_DIR.absolute()}")
