import logging

from sqlmodel import create_engine

from src.config import get_settings
from src.models import *
from src.core.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Creating initial data")
    settings = get_settings()
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    init_db(settings, engine)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
