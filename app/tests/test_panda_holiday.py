import pytest
from datetime import datetime
from typing import List

from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import Subject, SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry


@pytest.fixture(scope="module")
def subject():
    subject = SubjectImpl()
    return subject


@pytest.mark.freeze_time(datetime(2024, 3, 31))
def concern_id_from_panda():
    subject = SubjectImpl()
    return subject.get_concerned_staff()


@pytest.fixture(name="panda_id")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def concerned_id_from_panda_indirect(app_context):
    subject = SubjectImpl()
    # print(f"len: {len(subject.get_concerned_staff())}\n")
    return subject.get_concerned_staff()


# とりあえず、この方法しか上手くいかん。
# https://stackoverflow.com/questions/49117806/what-is-the-best-way-to-parameterize-a-pytest-function-using-a-fixture-that-retu
@pytest.fixture(params=range(3))
def get_param(request, panda_id):
    print("expensive")
    return panda_id[request.param]


# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_plus_next_holidays(get_param):
    # for member_id in panda_staff:
    holiday_acquire_obj = HolidayAcquire(get_param)
    # assert isinstance(holiday_acquire_obj, HolidayAcquire)
    result_count = holiday_acquire_obj.count_workday()
    # print(f"ID{member_id}: 付与日数: {result_dict.values()[-1]}")
    print(result_count)


# @pytest.mark.skip
# これもダメ
# @pytest.mark.parametrize("id_list", concern_id_from_panda(), indirect=["panda_id"])
@pytest.mark.usefixtures("app_context")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
class IdArgs:
    @staticmethod
    def setup():
        id_list = concern_id_from_panda()
        # self.subject = SubjectImpl()
        return id_list


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_print_param(get_param):
    print(f"ID: {get_param}")


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_refer_type(app_context, subject, get_param, mocker):
    # origin_func = holiday_acquire_obj.count_workday

    def count_quote_workday():
        holiday_acquire_obj = HolidayAcquire(get_param)
        return holiday_acquire_obj.count_workday() * 4 / 3

    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", side_effect=count_quote_workday
    )

    # holiday_acquire_obj.count_workday()
    # origin_func()
    print(f"-{subject.refer_acquire_type(get_param)}-")
    assert workday_mock.call_count == 3

    # observer = ObserverCheckType()
    # subject.attach(observer)

    # observer.update(subject)

    # print(member_mock.call_count)
    # print(refer_mock.call_count)


@pytest.mark.skip
def test_check_type(subject, get_panda_staff, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    def count_quote_workday(i: int):
        holiday_acquire_obj = HolidayAcquire(i)
        return holiday_acquire_obj.count_workday() * 4 / 3

    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", side_effect=count_quote_workday
    )
    # workday_half_mock = mocker.patch.object(HolidayAcquire, "count_workday_half_year")

    print(workday_mock.call_count)
    # print(workday_half_mock.call_count)
