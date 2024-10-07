import pytest

from app import db
from app.models import User, KinmuTaisei
from app.calc_work_classes_diff import CalcTimeClass


@pytest.fixture(name="contract")
def get_contract_work_time(app_context):
    user = db.session.get(User, 201)
    contract = db.session.get(KinmuTaisei, user.CONTRACT_CODE)
    return contract.WORKTIME


@pytest.fixture(name="cw_obj")
def make_calc_work(app_context):
    calc_work_object = CalcTimeClass(201, "07:56", "17:16", "0", "0")
    return calc_work_object


def test_change_notify_method(cw_obj):
    actual_time = cw_obj.calc_actual_work_time()
    print(f"timedalta: {actual_time}")
    notify_time = cw_obj.change_notify_method("10")
    time_second = notify_time.total_seconds()
    assert time_second // 3600 == 8


def test_change_notify_con2(cw_obj, contract):
    notify_time = cw_obj.change_notify_method("9")
    time_second = notify_time.total_seconds()
    assert time_second // 3600 == contract
