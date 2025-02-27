import pytest, pytest_asyncio
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy import select, update, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_async import get_session

from app import db
from app.models import TableOfCount, Shinsei
from app.attendance_query_class import AttendanceQuery
from app.async_db_lib import update_count_table, merge_count_table
from app.select_only_sync import get_query_from_date


@pytest_asyncio.fixture(loop_scope="session")
async def multidb_access_select_one():
    stmt = select(TableOfCount).filter(TableOfCount.id == "194202412")
    async with get_session() as session:
        result = await session.execute(statement=stmt)
        result_one = result.scalar_one()

    return result_one


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


@pytest.fixture(name="aq")
def get_attendance_query_obj(app_context):
    from_day = date(2024, 12, 1)
    to_day = date(2024, 12, 31)
    aq_obj20 = AttendanceQuery(20, from_day, to_day)
    aq_obj201 = AttendanceQuery(201, from_day, to_day)
    return aq_obj20, aq_obj201


@pytest.mark.skip
@pytest.mark.asyncio(loop_scope="session")
async def test_get_clerical_attendance(aq):
    clerical_attendance_list = aq[0].get_clerical_attendance(True)
    cnt: int = 0
    id_list = []
    for test_c_attendace in clerical_attendance_list:
        att = test_c_attendace[0]
        id_list.append(att.STAFFID)
        cnt += 1

    # assert cnt == 5
    id_set = set(id_list)
    print(f"StaffID: {id_set}")
    print(f"Result count: {cnt}")


def get_month_attendance(staff_ids: list[int]) -> list[list[Shinsei]]:
    from_day = datetime(year=2024, month=9, day=1)
    to_day = datetime(year=2024, month=9, day=30)
    attendances: list[list[Shinsei]] = []
    filters = []
    filters.append(Shinsei.WORKDAY.between(from_day, to_day))
    filters.append(Shinsei.STAFFID.in_(staff_ids))
    month_attendance = db.session.query(Shinsei).filter(*filters).all()
    attendances.append(month_attendance)

    return attendances


@pytest.fixture(name="month_attends")
def make_month_attend_info(app_context):
    attendances = get_month_attendance([206, 207, 216, 217, 237])
    return attendances


@pytest.mark.skip
@pytest.mark.asyncio(loop_scope="session")
async def test_merge_count_table(month_attends):
    cnt: int = 0
    for i, month_attend in enumerate(month_attends):
        s = month_attend[i]
        # for target_attend in month_attend:
        toc_obj = TableOfCount(staff_id=s.STAFFID)
        toc_obj.id = f"{s.STAFFID}-20249+"
        toc_obj.YEAR_MONTH = "20249+"
        print(f"{i}: {month_attend[i].STAFFID}")
        # await merge_count_table(toc_obj)
        cnt += 1
    # assert cnt == 5
    # print(f"Loop: {cnt}")


@pytest.mark.skip
def test_get_session(async_session: AsyncSession):
    stmt = select(TableOfCount).filter(TableOfCount.YEAR_MONTH == "202412")
    results = async_session.execute(statement=stmt)
    with results as result:
        print(result.scalar_one().id)


@pytest.mark.skip
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
