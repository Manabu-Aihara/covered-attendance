import pytest
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


def get_month_attendance(staff_id: int) -> List[Shinsei]:
    filters = []
    from_day = datetime(year=2024, month=9, day=1)
    to_day = datetime(year=2024, month=9, day=30)
    filters.append(Shinsei.WORKDAY.between(from_day, to_day))
    filters.append(Shinsei.STAFFID == staff_id)
    attendances = db.session.query(Shinsei).filter(*filters).all()
    return attendances


@pytest.fixture(name="month_attends")
def make_month_attend_info(app_context):
    attendances = get_month_attendance(20)
    return attendances


@pytest.mark.skip
def test_attendance_count(month_attends):
    assert len(month_attends) == 7


def test_output_month_log(month_attends):
    for month_attend in month_attends:
        ct_obj = CalcTimeClass(
            month_attend.STAFFID,
            month_attend.STARTTIME,
            month_attend.ENDTIME,
            (month_attend.NOTIFICATION, month_attend.NOTIFICATION2),
            month_attend.OVERTIME,
            month_attend.HOLIDAY,
        )
        print(f"{month_attend.WORKDAY}")
        print(f"Actual time: {ct_obj.get_actual_work_time()}")
        print(f"Real time: {ct_obj.get_real_time()}")
        if month_attend.OVERTIME == "1":
            print(f"Over time: {ct_obj.get_over_time()}")
        # ct_obj.get_actual_work_time()
        # ct_obj.get_real_time()
        # if month_attend.OVERTIME == "1":
        #     ct_obj.get_over_time()


@pytest.mark.skip
def test_run_perf(month_attends):
    pr = cProfile.Profile()
    pr.runcall(test_output_month_log, month_attends)
    # pr.print_stats()
    status = pstats.Stats(pr)
    status.sort_stats("cumtime").print_stats(10)
