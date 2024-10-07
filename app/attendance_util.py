from typing import Tuple, TypeVar
from datetime import datetime

from flask import session

from app import db
from app.models import Busho, KinmuTaisei, Post, Team, Jobtype, D_JOB_HISTORY


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


def get_user_role(query_name, table_code, user_code: int = 0) -> tuple:
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


def check_table_member(staff_id: int):
    # neccesary_object = db.session.get(D_JOB_HISTORY, self.staff_id)
    neccesary_object = (
        db.session.query(D_JOB_HISTORY)
        .filter(D_JOB_HISTORY.STAFFID == staff_id)
        .first()
    )
    object_attributes = [n for n in neccesary_object.__dict__]
    return object_attributes
    # attr_list = []
    # for neccesary_attr in object_attributes[1:]:
    #     attr_list.append(getattr(neccesary_object, neccesary_attr))
    # if (
    #     getattr(neccesary_object, neccesary_attr) is None
    #     or getattr(neccesary_object, neccesary_attr) == ""
    # ):
    #     print("ここ通ります")
    #     return neccesary_attr
    # raise ValueError(f"There is not {neccesary_attr} value of {staff_id}")
    # else:
    #     return 0
    # return attr_list
