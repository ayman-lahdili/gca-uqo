import os

from sqlmodel import Session, SQLModel, create_engine

from src.config import settings

connect_args = {"check_same_thread": False}

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, connect_args=connect_args)


def init_db(session: Session):
    if os.path.exists(settings.SQLLITE_FILE_NAME):
        os.remove(settings.SQLLITE_FILE_NAME)
        print(f"Database {settings.SQLLITE_FILE_NAME} deleted.")
    SQLModel.metadata.create_all(engine)
