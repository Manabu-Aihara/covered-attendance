import pytest
from datetime import datetime
from typing import List

from sqlalchemy import and_

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
    calc_work_object = CalcTimeClass(3, "08:56", "16:16", "0", "1")
    return calc_work_object


# @pytest.mark.skip
def test_change_notify_method(calc_work):
    actual_time = calc_work.calc_actual_work_time()
    print(f"timedalta: {actual_time}")
    notify_time = calc_work.change_notify_method("10")
    time_second = notify_time.total_seconds()
    assert time_second // 3600 == 5


@pytest.mark.skip
def test_change_notify_con2(calc_work, contract):
    notify_time = calc_work.change_notify_method("9")
    time_second = notify_time.total_seconds()
    assert time_second // 3600 == contract


# @pytest.mark.skip
def test_change_notify_method2(calc_work):
    notify_time = calc_work.change_notify_method("4", "13")
    print(f"Test: {notify_time}")


# @pytest.mark.skip
def test_nurse_holiday_works(calc_work):
    nurse_holiday_works = calc_work.calc_nurse_holiday_works("15")
    assert nurse_holiday_works[0] // 3600 == 3


def get_month_attendance(staff_id: int) -> List[Shinsei]:
    filters = []
    from_day = datetime(year=2024, month=9, day=1)
    to_day = datetime(year=2024, month=9, day=30)
    filters.append(Shinsei.WORKDAY.between(from_day, to_day))
    filters.append(Shinsei.STAFFID == staff_id)
    attendances = db.session.query(Shinsei).filter(*filters).all()
    return attendances


@pytest.fixture(name="month_attend")
def make_month_attend_info(app_context):
    type_attendances = get_month_attendance(20)
    instance_list: List[CalcTimeClass] = []
    for attendance in type_attendances:
        instance_list.append(
            CalcTimeClass(
                attendance.STAFFID,
                attendance.STARTTIME,
                attendance.ENDTIME,
                attendance.OVERTIME,
                attendance.HOLIDAY,
            )
        )
    return instance_list


def test_class_count(month_attend):
    print(f"Object count: {len(month_attend)}")


def test_real_times(month_attend, mocker):
    # real_work_mock = mocker.patch.object(
    #     CalcTimeClass,
    #     "get_real_times",
    #     sideeffect=[x.get_real_times() for x in month_attend],
    # )

    count = 0
    for o in month_attend:
        print(f"Real time list: {o.get_real_times()}")
        count += 1

    print(f"Actual count: {count}")
    # print(f"Mock count: {real_work_mock.call_count}")
