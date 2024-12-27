import pytest, pytest_asyncio

import sys

# sys.path.append(os.path.abspath(".."))
import pathlib
from os.path import join, dirname

from dotenv import load_dotenv

packagedir = pathlib.Path(__file__).resolve().parent.parent.parent
print(packagedir)
sys.path.append(str(packagedir))

dotenv_path = join(str(packagedir), ".env")
load_dotenv(dotenv_path)

from app import db, app

"""
  https://stackoverflow.com/questions/31444036/runtimeerror-working-outside-of-application-context
  """


@pytest.fixture
def app_context():
    with app.app_context():
        db.create_all()
        yield


# from app import app2
from database_async import Base, external_db, Engines, async_session_generator


@pytest_asyncio.fixture
async def async_session():
    # Base.metadata.create_all()
    # Base.metadata.create_all(bind=Engines)
    external_db.create_all(bind_key=Engines.PRIMARY)
    async with async_session_generator():
        yield
    # async with get_session():
    #     yield
