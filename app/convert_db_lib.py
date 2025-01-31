import os
from typing import Optional, List

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.models import TableOfCount


def get_panda_url(sql_async_module: str = "asyncmy"):

    return "mysql+{mysql_module}://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4".format(
        **{
            "mysql_module": sql_async_module,
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": "127.0.0.1",
            "port": "3307",
            "db_name": "panda",
        }
    )


""" 一時的なpandaからのSelect """

read_engine = create_engine(url=get_panda_url("pymysql"))
# セッションファクトリーを作成
read_session = scoped_session(sessionmaker(bind=read_engine))


def get_sync_record(primary_key: str) -> Optional[TableOfCount]:
    return read_session.get(TableOfCount, primary_key)


def get_query_from_date(year_and_month: str) -> List[TableOfCount]:
    counter_data_list = (
        read_session.query(TableOfCount)
        .filter(TableOfCount.YEAR_MONTH == year_and_month)
        .all()
    )
    result_query_list = []
    for counter_data in counter_data_list:
        result_query_list.append(counter_data)

    return result_query_list
