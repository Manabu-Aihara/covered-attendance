# Asynchronous SqlAlchemy and multiple databases
# https://makimo.com/blog/asynchronous-sqlalchemy-and-multiple-databases/
import os
from contextlib import asynccontextmanager
from enum import Enum

from sqlalchemy import Column, Integer, String, Insert, Update, Delete, Select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session

# from flask.ext.sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

from app import app

from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Engines(Enum):
    PRIMARY = create_async_engine(
        url=(
            "mysql+asyncmy://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4".format(
                **{
                    "user": os.getenv("DB_USER"),
                    "password": os.getenv("DB_PASSWORD"),
                    "host": os.getenv("DB_HOST"),
                    "port": os.getenv("DB_PORT"),
                    "db_name": os.getenv("DB_NAME"),
                }
            )
        ),
        echo=False,
    )
    SECONDARY = create_async_engine(
        url=(
            "mysql+asyncmy://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4".format(
                **{
                    "user": os.getenv("DB_USER"),
                    "password": os.getenv("DB_PASSWORD"),
                    "host": "127.0.0.1",
                    "port": "3307",
                    "db_name": "panda",
                }
            )
        ),
        echo=True,
    )


Base = declarative_base()
external_db = SQLAlchemy()


# class Tutorial(Base):
#     __tablename__ = "tutorials"

#     tutorial_id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kw):
        print(f"first pass: ---{clause}---")
        if isinstance(clause, (Insert, Update, Delete)):
            return Engines.SECONDARY.value.sync_engine
        elif isinstance(clause, Select):
            print(f"second pass: ---{clause}---")
            return Engines.PRIMARY.value.sync_engine


def async_session_generator():
    return async_sessionmaker(sync_session_class=RoutingSession)


@asynccontextmanager
async def get_session():
    try:
        async_session = async_session_generator()

        async with async_session() as session:
            yield session
    except RuntimeError as e:
        print(f"!!Async session error: {e}!!")
        await session.rollback()
        raise "再度ボタンクリックしてください"
    finally:
        await session.close()
