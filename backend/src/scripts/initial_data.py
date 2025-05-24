import os
import logging

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from src.config import Settings, settings
from src.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(settings: Settings, engine: Engine):
    if os.path.exists(settings.SQLLITE_FILE_NAME):
        os.remove(settings.SQLLITE_FILE_NAME)
        print(f"Database {settings.SQLLITE_FILE_NAME} deleted.")
    print("Creating database", settings.SQLLITE_FILE_NAME)
    SQLModel.metadata.create_all(engine)


def main() -> None:
    logger.info("Creating initial data")
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    init_db(settings, engine)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
