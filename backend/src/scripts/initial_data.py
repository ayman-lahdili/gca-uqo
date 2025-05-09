import logging

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from src.config import Settings, get_settings
from src.dependencies.session import db_session_dependency

from src.models import *
from src.core.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init(settings: Settings, engine: Engine) -> None:
    init_db(settings, engine)


def main() -> None:
    logger.info("Creating initial data")
    settings = get_settings()
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    init(settings, engine)
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
