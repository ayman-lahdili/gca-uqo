import os

import structlog
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from src.config import Settings, settings
from src.models import *

logger = structlog.get_logger("tests")


def init_db(settings: Settings, engine: Engine):
    if os.path.exists(settings.SQLLITE_FILE_NAME):
        os.remove(settings.SQLLITE_FILE_NAME)
        logger.info(f"Database {settings.SQLLITE_FILE_NAME} deleted.")
    logger.info(f"Creating database f{settings.SQLLITE_FILE_NAME}")
    SQLModel.metadata.create_all(engine)


def main() -> None:
    logger.info("Creating initial data")
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    init_db(settings, engine)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
