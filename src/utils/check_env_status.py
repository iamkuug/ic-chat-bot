from utils.logger import *
from constants import ENV_VARS
import os


def check_env_status():
    for var in ENV_VARS:
        value = os.getenv(var)
        status = "✅ loaded" if value else "❌ not loaded"
        logger.info(f"ENV {var}: {status}")
