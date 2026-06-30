import datetime
from loguru import logger

today = datetime.datetime.now().strftime("%Y-%m-%d")

logger.add(
    f"logs/{today}.json",
    serialize=True,
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
)
logger.add(f"logs/error_logs/{today}.log", level="ERROR")
