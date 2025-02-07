import threading
from typing import List

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database_async import get_session
from app.models import TableOfCount
from app.sync_select_db_lib import get_sync_record


async def get_async_query_from_date(year_and_month: str) -> List[TableOfCount]:
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


async def update_count_table(
    count_table_obj: TableOfCount,
    # staff_id: Optional[int] = None,
    # dateYM: Optional[str] = None,
) -> None:
    # making_id = f"{staff_id}{dateYM}"
    making_id = f"{count_table_obj.STAFFID}{count_table_obj.YEAR_MONTH}"
    # making_id = f"{staff_id}{count_table_obj.YEAR_MONTH}"

    if count_table_obj.__dict__.get("_sa_instance_state"):
        object_dict = count_table_obj.__dict__.pop("_sa_instance_state")
        print(object_dict)

    stmt = (
        update(TableOfCount)
        .where(TableOfCount.id == making_id)
        .values(count_table_obj.__dict__)
    )
    async with get_session() as session:
        async with session.begin():
            await session.execute(statement=stmt)
            await session.flush()


async def insert_count_table(
    count_table_obj: TableOfCount,
):
    object_dict = count_table_obj.__dict__.pop("_sa_instance_state")
    print(object_dict)
    stmt = insert(TableOfCount).values(count_table_obj.__dict__)
    async with get_session() as session:
        async with session.begin():
            await session.execute(statement=stmt)
            await session.flush()


async def merge_count_table(
    count_table_obj: TableOfCount,
    # staff_id: Optional[int] = None,
    # dateYM: Optional[str] = None,
) -> None:
    # making_id = f"{staff_id}{dateYM}"
    making_id = f"{count_table_obj.STAFFID}{count_table_obj.YEAR_MONTH}"
    # making_id = f"{staff_id}{count_table_obj.YEAR_MONTH}"

    # 今読み込む側 local_cat_db -> panda?
    # select_stmt = select(TableOfCount).filter(TableOfCount.id == making_id)
    # target_data: Optional[TableOfCount]
    # async with get_session() as session:
    #     # こっちでも良かった
    #     # target_data = session.get(TableOfCount, making_id)
    #     query_result = await session.execute(statement=select_stmt)
    #     target_data = query_result.scalar_one_or_none()
    target_data = get_sync_record(making_id)

    if count_table_obj.__dict__.get("_sa_instance_state"):
        object_dict = count_table_obj.__dict__.pop("_sa_instance_state")
        print(object_dict)

    if target_data is not None:
        # 今度、書き込む側 panda
        stmt = (
            update(TableOfCount)
            .where(TableOfCount.id == making_id)
            .values(count_table_obj.__dict__)
        )
    else:  # TableOfCount is None
        stmt = insert(TableOfCount).values(count_table_obj.__dict__)

    try:
        async with get_session() as session:
            async with session.begin():
                await session.execute(statement=stmt)
    # except IntegrityError as ie:
    #     print(ie)
    except TypeError as te:
        raise "再度「再集計」ボタンをクリックしてください"
