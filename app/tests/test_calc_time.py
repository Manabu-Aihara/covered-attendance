import pytest
import math
from datetime import datetime, timedelta
from typing import List
import cProfile
import pstats

from app import db
from app.models import User, KinmuTaisei, Shinsei
from app.calc_work_classes_diff import CalcTimeClass


@pytest.fixture(name="contract")
def get_contract_work_time(app_context):
    user = db.session.get(User, 3)
    contract = db.session.get(KinmuTaisei, user.CONTRACT_CODE)
    return contract.WORKTIME


@pytest.fixture(name="calc_work")
def make_calc_work(app_context):
    calc_work_object = CalcTimeClass(20, "12:56", "18:26", ("4", "10"), "1", "0")
    return calc_work_object


@pytest.mark.skip
def test_check_over_work(contract, calc_work):
    actual_time = calc_work.calc_actual_work_time()
    print(f"timedalta: {actual_time}")
    output_time: timedelta = calc_work.check_over_work()
    time_second = output_time.total_seconds()
    assert time_second / 3600 == 5.5


@pytest.mark.skip
def test_get_over_time(calc_work):
    output_time = calc_work.get_over_time()
    # print(f"Over: {output_time}")
    assert output_time / 3600 == 1.5


@pytest.mark.skip
def test_get_real_time(calc_work):
    time_second = calc_work.get_real_time()
    assert time_second / 3600 == 4.5


def get_month_attendance(*staff_ids: int) -> List[Shinsei]:
    from_day = datetime(year=2024, month=10, day=1)
    to_day = datetime(year=2024, month=10, day=31)
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
    attendances = get_month_attendance(201, 20)
    return attendances


# @pytest.mark.skip
def test_attendance_count(month_attends):
    assert len(month_attends) == 2
    assert len(month_attends[0]) == 10
    assert len(month_attends[1]) == 9


# @pytest.mark.skip
def test_output_month_log(month_attends):
    for month_attend in month_attends:
        for target_attend in month_attend:
            ct_obj = CalcTimeClass(
                target_attend.STAFFID,
                target_attend.STARTTIME,
                target_attend.ENDTIME,
                (target_attend.NOTIFICATION, target_attend.NOTIFICATION2),
                target_attend.OVERTIME,
                target_attend.HOLIDAY,
            )
            print(f"{target_attend.WORKDAY}")
            print(f"Actual time: {ct_obj.get_actual_work_time()}")
            print(f"Real time: {ct_obj.get_real_time()}")
            if target_attend.OVERTIME == "1":
                print(f"Over time: {ct_obj.get_over_time()}")
            # print(f"Real time list: {ct_obj.real_time_list}")


@pytest.mark.skip
def test_print_list_type(month_attends):
    actual_list = []
    real_list = []
    over_list = []
    for month_attend in enumerate(month_attends):
        for target_attend in month_attend:
            ct_obj = CalcTimeClass(
                target_attend.STAFFID,
                target_attend.STARTTIME,
                target_attend.ENDTIME,
                (target_attend.NOTIFICATION, target_attend.NOTIFICATION2),
                target_attend.OVERTIME,
                target_attend.HOLIDAY,
            )
            actual_list.append(ct_obj.get_actual_work_time().total_seconds())
            real_list.append(ct_obj.get_real_time())
            if target_attend.OVERTIME == "1":
                over_list.append(ct_obj.get_over_time())

        actual_sum = math.fsum(actual_list)
        real_sum = math.fsum(real_list)
        over_sum = math.fsum(over_list)
        print(f"Actual time: {actual_sum}")
        print(f"Real time: {real_sum}")
        print(f"Over time: {over_sum}")


@pytest.mark.skip
def test_run_perf(month_attends):
    pr = cProfile.Profile()
    pr.runcall(test_print_list_type, month_attends)
    # pr.print_stats()
    status = pstats.Stats(pr)
    status.sort_stats("cumtime").print_stats(10)
