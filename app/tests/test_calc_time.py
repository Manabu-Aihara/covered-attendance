import pytest
import math
from datetime import datetime, timedelta
from typing import List
import cProfile
import pstats

import pandas as pd

from app import db
from app.models import User, KinmuTaisei, Shinsei, D_JOB_HISTORY
from app.calc_work_classes2 import CalcTimeClass, CalcTimeFactory, output_rest_time

id_for_contract: int = 20


@pytest.fixture(name="contract")
def get_contract_work_time(app_context):
    user = db.session.get(User, id_for_contract)
    if user.CONTRACT_CODE != 2:
        contract = db.session.get(KinmuTaisei, user.CONTRACT_CODE)
        contract_time = contract.WORKTIME
    else:
        contract = (
            db.session.query(D_JOB_HISTORY)
            .filter(D_JOB_HISTORY.STAFFID == id_for_contract)
            .first()
        )
        contract_time = contract.PART_WORKTIME
    return contract_time


@pytest.fixture(name="calc_work")
def make_calc_work(app_context):
    calc_factory_object = CalcTimeFactory()
    calc_work_object = calc_factory_object.get_instance(20)
    calc_work_object.set_data("09:00", "18:00", ("13", "10"), "0", "0")
    return calc_work_object


@pytest.mark.skip
def test_calc_actual_work_time(calc_work):
    actual_time: timedelta = calc_work.calc_actual_work_time()
    actual_second = actual_time.total_seconds()
    result_actual = actual_second / 3600
    assert result_actual == 8


# @pytest.mark.skip
def test_get_actual_work_time(contract, calc_work):
    print(f"Contract: {contract}")
    output_time: timedelta = calc_work.get_actual_work_time()
    time_second = output_time.total_seconds()
    result_time = time_second / 3600
    assert result_time == 8


@pytest.mark.skip
def test_get_over_time(calc_work):
    output_time = calc_work.get_over_time()
    # print(f"Over: {output_time}")
    assert output_time / 3600 == 1.5


# @pytest.mark.skip
def test_get_real_time(calc_work):
    time_second = calc_work.get_real_time()
    result_real = time_second / 3600
    assert result_real == 6


def test_output_rest_time():
    sum_dict: dict = output_rest_time("13", "12")
    print(f"Test output_rest_time: {sum_dict}")
    # assert sum_dict.get("Off") == [3]
    # assert sum_dict.get("Through") == [1]


def get_month_attendance(staff_ids: list[int]) -> list[list[Shinsei]]:
    from_day = datetime(year=2024, month=11, day=1)
    to_day = datetime(year=2024, month=11, day=30)
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
    part_members = (
        db.session.query(D_JOB_HISTORY.STAFFID)
        .filter(D_JOB_HISTORY.CONTRACT_CODE == 2)
        .all()
    )
    # part_list = [m.STAFFID for m in part_members]
    attendances = get_month_attendance([79])
    return attendances


@pytest.mark.skip
def test_attendance_count(month_attends):
    assert len(month_attends) == 2
    assert len(month_attends[0]) == 10
    assert len(month_attends[1]) == 9


@pytest.mark.skip
def test_output_month_log(month_attends):
    ct_obj = CalcTimeClass(None, None, None, None, None, None)
    for month_attend in month_attends:
        for target_attend in month_attend:
            # ct_obj = CalcTimeClass(
            #     target_attend.STAFFID,
            #     target_attend.STARTTIME,
            #     target_attend.ENDTIME,
            #     (target_attend.NOTIFICATION, target_attend.NOTIFICATION2),
            #     target_attend.OVERTIME,
            #     target_attend.HOLIDAY,
            # )
            ct_obj.staff_id = target_attend.STAFFID
            ct_obj.sh_starttime = target_attend.STARTTIME
            ct_obj.sh_endtime = target_attend.ENDTIME
            ct_obj.notifications = (
                target_attend.NOTIFICATION,
                target_attend.NOTIFICATION2,
            )
            ct_obj.sh_overtime = target_attend.OVERTIME
            ct_obj.sh_holiday = target_attend.HOLIDAY
            print(f"{target_attend.WORKDAY}")
            print(f"Test actual time: {ct_obj.get_actual_work_time()}")
            print(f"Test real time: {ct_obj.get_real_time()}")
            if target_attend.OVERTIME == "1":
                print(f"Test over time: {ct_obj.get_over_time()}")
            # print(f"Real time list: {ct_obj.real_time_list}")


@pytest.mark.skip
def test_print_list_type(month_attends):
    # ct_obj = CalcTimeClass(None, None, None, None, None, None)
    # ct_obj = CalcTimeClass()
    actual_list = []
    real_list = []
    over_list = []
    for month_attend in month_attends:
        for target_attend in month_attend:
            ct_obj = CalcTimeClass(
                target_attend.STARTTIME,
                target_attend.ENDTIME,
                (target_attend.NOTIFICATION, target_attend.NOTIFICATION2),
                target_attend.OVERTIME,
                target_attend.HOLIDAY,
                target_attend.STAFFID,
            )
            # ct_obj.staff_id = target_attend.STAFFID
            # ct_obj.sh_starttime = target_attend.STARTTIME
            # ct_obj.sh_endtime = target_attend.ENDTIME
            # ct_obj.notifications = (
            #     target_attend.NOTIFICATION,
            #     target_attend.NOTIFICATION2,
            # )
            # ct_obj.sh_overtime = target_attend.OVERTIME
            # ct_obj.sh_holiday = target_attend.HOLIDAY
            actual_list.append(ct_obj.get_actual_work_time().total_seconds())
            real_list.append(ct_obj.get_real_time())
            if target_attend.OVERTIME == "1":
                over_list.append(ct_obj.get_over_time())

        actual_sum = math.fsum(actual_list)
        real_sum = math.fsum(real_list)
        over_sum = math.fsum(over_list)
        # actual_sum = pd.Series(actual_list).sum()
        # real_sum = pd.Series(real_list).sum()
        # over_sum = pd.Series(over_list).sum()
        print(f"Test actual sum: {actual_sum}")
        print(f"Test real sum: {real_sum}")
        print(f"Test over sum: {over_sum}")


@pytest.mark.skip
def test_print_list_factory(month_attends):
    calc_time_factory = CalcTimeFactory()
    actual_list = []
    real_list = []
    over_list = []
    for month_attend in month_attends:
        for target_attend in month_attend:
            time_calcurator = calc_time_factory.get_instance(target_attend.STAFFID)
            time_calcurator.set_data(
                target_attend.STARTTIME,
                target_attend.ENDTIME,
                (target_attend.NOTIFICATION, target_attend.NOTIFICATION2),
                target_attend.OVERTIME,
                target_attend.HOLIDAY,
            )

            actual_list.append(time_calcurator.get_actual_work_time().total_seconds())
            real_list.append(time_calcurator.get_real_time())
            if target_attend.OVERTIME == "1":
                over_list.append(time_calcurator.get_over_time())

        actual_sum = math.fsum(actual_list)
        real_sum = math.fsum(real_list)
        over_sum = math.fsum(over_list)
        # actual_sum = pd.Series(actual_list).sum()
        # real_sum = pd.Series(real_list).sum()
        # over_sum = pd.Series(over_list).sum()
        print(f"Test actual sum: {actual_sum}")
        print(f"Test real sum: {real_sum}")
        print(f"Test over sum: {over_sum}")


@pytest.mark.skip
def test_run_perf(month_attends):
    pr = cProfile.Profile()
    pr.runcall(test_print_list_factory, month_attends)
    # pr.print_stats()
    status = pstats.Stats(pr)
    status.sort_stats("cumtime").print_stats(10)
