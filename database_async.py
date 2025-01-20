# Asynchronous SqlAlchemy and multiple databases
# https://makimo.com/blog/asynchronous-sqlalchemy-and-multiple-databases/
import os
from contextlib import asynccontextmanager
from enum import Enum

from sqlalchemy import Column, Integer, String, Insert, Update, Delete, Select, NullPool
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
        # Please ensure that SQLAlchemy pooled connections are returned to the pool explicitly,\
        # either by calling ``close()`` or by using appropriate context managers to manage their lifecycle.
        # https://stackoverflow.com/questions/72468241/exception-closing-connection-using-sqlalchemy-with-asyncio-and-postgresql
        pool_pre_ping=True,
        poolclass=NullPool,
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
        pool_pre_ping=True,
        poolclass=NullPool,
    )


Base = declarative_base()
external_db = SQLAlchemy()


# class Tutorial(Base):
#     __tablename__ = "tutorials"

#     tutorial_id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kw):
        if isinstance(clause, (Insert, Update, Delete)):
            print(f"second pass: ---{clause}---")
            return Engines.SECONDARY.value.sync_engine
        elif isinstance(clause, Select):
            print(f"first pass: ---{clause}---")
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
