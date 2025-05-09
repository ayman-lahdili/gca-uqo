import os

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from src.config import Settings

connect_args = {"check_same_thread": False}


def init_db(settings: Settings, engine: Engine):
    if os.path.exists(settings.SQLLITE_FILE_NAME):
        os.remove(settings.SQLLITE_FILE_NAME)
        print(f"Database {settings.SQLLITE_FILE_NAME} deleted.")
    print("asad", settings.SQLLITE_FILE_NAME)
    SQLModel.metadata.create_all(engine)
