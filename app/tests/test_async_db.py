import pytest, pytest_asyncio
from typing import List

from sqlalchemy import update, insert, and_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from database_async import get_session, async_session_generator

from app import db
from app.models import TableOfCount
from app.async_db_lib import get_query_from_date, get_session_query


@pytest_asyncio.fixture(loop_scope="session")
async def multidb_access_select_one():
    stmt = select(TableOfCount).filter(TableOfCount.id == "194202412")
    async with get_session() as session:
        result = await session.execute(statement=stmt)
        result_one = result.scalar_one()

    return result_one


# @pytest.mark.asyncio(loop_scope="session")
def test_check_fixture(multidb_access_select_one):
    result_one: TableOfCount = multidb_access_select_one
    assert result_one.SUM_REAL_WORKTIME == 15.15


async def insert_objects(async_session: AsyncSession) -> None:
    toc_obj = TableOfCount(42)
    toc_obj.id = "42202412"
    toc_obj.YEAR_MONTH = "202412"
    stmt = insert(TableOfCount).values(id="42202412", STAFFID=201, YEAR_MONTH="1020")
    async with async_session as session:
        async with session.begin():
            result = await session.execute(statement=stmt)
            # session.add(toc_obj)


async def select_objects(async_session: AsyncSession):
    stmt = select(TableOfCount).filter(TableOfCount.YEAR_MONTH == "202412")

    async with async_session as session:
        existing_count_list = await session.execute(statement=stmt)
        for existing_count in existing_count_list.scalars().all():
            print(f"{existing_count.STAFFID}: {existing_count.WORKDAY_COUNT}")


@pytest.mark.asyncio(loop_scope="session")
async def test_db_main():
    sessions = get_session()
    async with sessions as session:
        await get_session_query(session, "202412")


@pytest_asyncio.fixture(loop_scope="session")
async def async_session():
    sessions = get_session()

    async with sessions as session:
        yield session


@pytest.mark.asyncio(loop_scope="session")
async def test_get_query_from_data():
    results = await get_query_from_date("202412")
    assert len(results) == 5


@pytest.mark.skip
def test_get_session(async_session: AsyncSession):
    stmt = select(TableOfCount).filter(TableOfCount.YEAR_MONTH == "202412")
    results = async_session.execute(statement=stmt)
    with results as result:
        print(result.scalar_one().id)
