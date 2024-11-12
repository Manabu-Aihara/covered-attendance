from typing import Tuple, TypeVar
from datetime import datetime
import time
import pstats
import cProfile

from flask import session

from app import db
from app.models import Busho, KinmuTaisei, Post, Team, Jobtype


def get_month_workday(selected_date: str = "") -> Tuple[int, int, str]:
    if selected_date:
        select_year = datetime.strptime(selected_date, "%Y-%m").year
        select_month = datetime.strptime(selected_date, "%Y-%m").month
        session["workday_data"] = selected_date
        workday_date = session["workday_data"]
    else:
        select_year = datetime.today().year
        select_month = datetime.today().month
        workday_date = datetime.today().strftime("%Y-%m")

    return select_year, select_month, workday_date


"""
    @Params:
        query_name: str 実質返すクエリーのカラム名
        table_code: int DBテーブルコード
        user_code: int User内コード
    @Return:
        result_query: str DBテーブルコードから返す名称
        """


def get_user_role(query_name, table_code, user_code: int = 0) -> str:
    result_query = db.session.query(query_name).filter(table_code == user_code).first()
    if result_query is None:
        # リスト対応させるため、空の場合は空文字を返す
        result_query = ""
        return result_query
    else:
        return result_query[0]


T = TypeVar("T")


def convert_null_role(db_obj: T) -> T:
    disp_department = get_user_role(Busho.NAME, Busho.CODE, db_obj.DEPARTMENT_CODE)
    disp_team = get_user_role(Team.SHORTNAME, Team.CODE, db_obj.TEAM_CODE)
    disp_contract = get_user_role(
        KinmuTaisei.NAME, KinmuTaisei.CONTRACT_CODE, db_obj.CONTRACT_CODE
    )
    disp_jobtype = get_user_role(
        Jobtype.SHORTNAME, Jobtype.JOBTYPE_CODE, db_obj.JOBTYPE_CODE
    )
    disp_post = get_user_role(Post.NAME, Post.CODE, db_obj.POST_CODE)

    db_obj.department = disp_department
    db_obj.team = disp_team
    db_obj.contract = disp_contract
    db_obj.job_type = disp_jobtype
    db_obj.post = disp_post
    return db_obj


"""
    例: 第2引数（退職日）が今日を過ぎていても、今月なら対象とする
    @Params:
        query_instances: list<T>
        date_columns: tuple<str>
    @Return
        result_data_list: list<T> 
    """


def get_more_condition_users(query_instances: list[T], *date_columun: str) -> list[T]:
    today = datetime.today()
    result_data_list = []
    for query_instance in query_instances:
        try:
            # 入職日
            date_c_name0: datetime = getattr(query_instance, date_columun[0])
            # 退職日
            date_c_name1: datetime = getattr(query_instance, date_columun[1])
            # if date_c_name0 is None:
            #     TypeError出してくれる
            if date_c_name0 <= today:
                if (
                    date_c_name1 is None
                    or date_c_name1 > today
                    or (
                        date_c_name1.year == today.year
                        # ここの == だね
                        and date_c_name1.month == today.month
                    )
                ):
                    result_data_list.append(query_instance)
        except TypeError:
            (
                print(f"{query_instance.STAFFID}: 入職日の入力がありません")
                if query_instance.STAFFID
                else print("入職日の入力がありません")
            )
            result_data_list.append(query_instance)

    return result_data_list


# date_c_name0.year == today.year and date_c_name0.month <= today.month


def check_table_member(staff_id: int, table_model: T):
    neccesary_object = db.session.get(table_model, staff_id)
    object_attributes = [n for n in neccesary_object.__dict__]
    attr_list = []
    for neccesary_attr in object_attributes[1:]:
        attribute_value = getattr(neccesary_object, neccesary_attr)
        if attribute_value is None or attribute_value == "":
            attr_list.append(neccesary_attr)
            # raise ValueError(f"There is not {neccesary_attr} value of {staff_id}")
    if len(attr_list) != 0:
        return attr_list
    else:
        return "無問題"


# Pythonの実行速度を測定(プロファイル)
# https://zenn.dev/timoneko/articles/16f9ee7113f3cd
def execution_speed_lib(func):
    """
    実行速度計測用のデコレータ
    """

    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        # 実行処理の計測
        pr.runcall(func, *args, **kwargs)

        stats = pstats.Stats(pr)
        stats.print_stats()

    return wrapper


def execution_speed(func):
    """
    実行速度計測用のデコレータ
    """

    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print("実行時間" + str(run_time) + "秒")

    return wrapper
