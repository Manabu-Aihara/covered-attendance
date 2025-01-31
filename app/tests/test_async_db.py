import pytest, pytest_asyncio
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy import update, insert, and_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from database_async import get_session, async_session_generator

from app import db
from app.models import TableOfCount, Shinsei
from app.async_db_lib import (
    get_query_from_date,
    get_record,
    get_session_query,
    update_count_table,
    insert_count_table,
    merge_count_table,
)


@pytest_asyncio.fixture(loop_scope="session")
async def multidb_access_select_one():
    stmt = select(TableOfCount).filter(TableOfCount.id == "194202412")
    async with get_session() as session:
        result = await session.execute(statement=stmt)
        result_one = result.scalar_one()

    return result_one


# @pytest.mark.asyncio(loop_scope="session")
@pytest.mark.skip
def test_check_fixture(multidb_access_select_one):
    result_one: TableOfCount = multidb_access_select_one
    assert result_one.SUM_REAL_WORKTIME == 15.15


async def insert_objects(async_session: AsyncSession) -> None:
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


@pytest.mark.skip
@pytest.mark.asyncio(loop_scope="session")
async def test_db_main():
    sessions = get_session()
    async with sessions as session:
        await get_session_query(session, "202412")


@pytest_asyncio.fixture(scope="session")
async def depend_session():
    sessions = get_session()

    try:
        async with sessions as session:
            yield session
    except Exception as e:
        print(e)
    finally:
        session.close()


def get_month_attendance(staff_ids: list[int]) -> list[list[Shinsei]]:
    from_day = datetime(year=2025, month=1, day=1)
    to_day = datetime(year=2025, month=1, day=31)
    attendances: list[list[Shinsei]] = []
    for staff_id in staff_ids:
        filters = []
        filters.append(Shinsei.WORKDAY.between(from_day, to_day))
        filters.append(Shinsei.STAFFID == staff_id)
        month_attendance = db.session.query(Shinsei).filter(*filters).all()
        attendances.append(month_attendance)

    return attendances


@pytest.fixture(name="month_attends")
def make_month_attend_info(app_context):
    attendances = get_month_attendance([3, 20, 31, 201])
    return attendances


@pytest.mark.skip
@pytest.mark.asyncio(loop_scope="session")
async def test_merge_count_table(month_attends):
    cnt: int = 0
    for month_attend in month_attends:
        for target_attend in month_attend:
            toc_obj = TableOfCount(target_attend.STAFFID)
            toc_obj.id = f"{target_attend.STAFFID}2025+"
            toc_obj.YEAR_MONTH = "2025+"
            toc_obj.ONCALL = 1
            # target_data: Optional[TableOfCount] = (
            #     db.session.query(TableOfCount).filter(TableOfCount.id == toc_obj.id).first()
            # )
            # print(f"{target_data}: このあとInsert")
            # async with session.begin():
            #     if target_data is None:
            #         await insert_count_table(session, toc_obj)
            #     else:
            #         print(f"Update! {cnt}")
            cnt += 1
            await merge_count_table(toc_obj)
            print(f"Loop: {cnt}")


@pytest.mark.skip
def test_get_session(async_session: AsyncSession):
    stmt = select(TableOfCount).filter(TableOfCount.YEAR_MONTH == "202412")
    results = async_session.execute(statement=stmt)
    with results as result:
        print(result.scalar_one().id)


# @pytest.mark.skip
@pytest.mark.asyncio(loop_scope="session")
async def test_get_query_from_data():
    results = await get_query_from_date("202412")
    assert len(results) == 5


@pytest.mark.skip
@pytest.mark.asyncio(loop_scope="session")
async def test_update_count_table(app_context):
    toc_obj = TableOfCount(42)
    # toc_obj.id = "422501"
    toc_obj.YEAR_MONTH = "2501"
    toc_obj.KEKKIN = 1
    # toc_obj.ONCALL = 1
    toc_obj.WORKDAY_COUNT = 15
    # print(toc_obj.__dict__)
    await update_count_table(toc_obj, 42)


# @pytest.mark.skip
def test_get_record(app_context):
    query = get_record("42202501")
    assert isinstance(query, TableOfCount)
