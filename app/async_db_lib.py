import threading
from typing import List, Optional

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database_async import get_session
from app.models import TableOfCount


async def get_query_from_date(year_and_month: str) -> List[TableOfCount]:
    stmt = select(TableOfCount).filter(TableOfCount.YEAR_MONTH == year_and_month)
    result_query_list = []
    # func_tss = threading.local()
    # func_tss = 0
    async with get_session() as session:
        query_all = await session.execute(statement=stmt)
        for query in query_all.scalars().all():
            result_query_list.append(query)
    #     func_tss += 1

    # print(f"Func thread: {func_tss}")
    return result_query_list


async def get_session_query(async_session: AsyncSession, year_and_month: str):
    stmt = select(TableOfCount).filter(TableOfCount.YEAR_MONTH == year_and_month)
    result_query_list = []
    async with async_session as session:
        existing_count_list = await session.execute(statement=stmt)
        for existing_count in existing_count_list.scalars().all():
            #     print(f"{existing_count.STAFFID}: {existing_count.WORKDAY_COUNT}")
            result_query_list.append(existing_count)

    return result_query_list


async def update_count_table(
    count_table_obj: TableOfCount,
    staff_id: Optional[int] = None,
    dateYM: Optional[str] = None,
):
    making_id = f"{staff_id}{dateYM}"
    object_dict = count_table_obj.__dict__.pop("_sa_instance_state")
    print(object_dict)
    stmt = (
        update(TableOfCount)
        .where(TableOfCount.id == making_id)
        .values(count_table_obj.__dict__)
    )
    async with get_session() as session:
        async with session.begin():
            existing_count = await session.execute(statement=stmt)
