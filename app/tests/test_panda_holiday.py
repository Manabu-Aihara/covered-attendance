import pytest
from unittest.mock import PropertyMock
from datetime import datetime

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
    # print(f"len: {len(concern_id_from_panda())}\n")
    return concern_id_from_panda()


# とりあえず、この方法しか上手くいかん。
# https://stackoverflow.com/questions/49117806/what-is-the-best-way-to-parameterize-a-pytest-function-using-a-fixture-that-retu
@pytest.fixture(params=range(25))
def get_param(request, panda_id):
    # print(f"expensive-{request.param}")
    return {"No": request.param, "ID": panda_id[request.param]}


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_plus_next_holidays(get_param):
    # for member_id in panda_staff:
    holiday_acquire_obj = HolidayAcquire(get_param.get("ID"))
    assert isinstance(holiday_acquire_obj, HolidayAcquire)
    result_count = holiday_acquire_obj.count_workday()
    print(result_count)


# これもダメ ↓
# @pytest.mark.parametrize("id_list", concern_id_from_panda(), indirect=["panda_id"])
@pytest.mark.skip
@pytest.mark.usefixtures("app_context")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
class IdArgs:
    @staticmethod
    def setup():
        id_list = concern_id_from_panda()
        # self.subject = SubjectImpl()
        return id_list


@pytest.fixture
def holiday_obj_mock(get_param, mocker):
    obj_mock = mocker.patch("app.holiday_acquisition.HolidayAcquire", autospec=True)
    property_mock = PropertyMock(return_value=get_param.get("ID"))
    type(obj_mock).id = property_mock
    return obj_mock


sample_work_count = [
    98,
    96,
    0,
    62,
    0,
    97,
    95,
    99,
    96,
    106,
    0,
    109,
    111,
    105,
    99,
    0,
    104,
    0,
    0,
    122,
    0,
    58,
    113,
    90,
    102,
]


# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_confirm_mock(app_context, subject, get_param, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    holiday_obj = HolidayAcquire(get_param.get("ID"))
    result_test = holiday_obj.count_workday()

    # def dummy_count_workday():
    #     # しょせんモック、何も出やしない
    #     # print(holiday_obj.count_workday() * 4 / 3)
    #     return holiday_obj.count_workday() * 4 / 3

    # count_mock = mocker.patch.object(
    #     HolidayAcquire, "count_workday", side_effect=dummy_count_workday
    # )
    # # RecursionError: maximum recursion depth exceeded
    # # subject.refer_acquire_type(get_param.get("ID"))
    # assert count_mock.call_count == 3

    # print(member_mock.call_count)
    # print(refer_mock.call_count)
