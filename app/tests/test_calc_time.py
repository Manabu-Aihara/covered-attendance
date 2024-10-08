import pytest

from app import db
from app.models import User, KinmuTaisei
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


def test_change_notify_method2(calc_work):
    notify_time = calc_work.change_notify_method("4", "13")
    print(f"Test: {notify_time}")


# @pytest.mark.skip
def test_nurse_holiday_works(calc_work):
    nurse_holiday_works = calc_work.calc_nurse_holiday_works("15")
    assert nurse_holiday_works[0] // 3600 == 3
