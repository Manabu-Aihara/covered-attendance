import pytest
from unittest.mock import PropertyMock
from datetime import datetime

from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import Subject, SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry


@pytest.mark.freeze_time(datetime(2024, 3, 31))
def concern_id_from_panda() -> int:
    subject = SubjectImpl()
    return subject.get_concerned_staff()


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


@pytest.fixture(scope="module")
def subject():
    subject = SubjectImpl()
    return subject


@pytest.fixture(name="panda_id")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def concerned_id_from_panda_indirect(app_context):
    # print(f"len: {len(concern_id_from_panda())}\n")
    return concern_id_from_panda()


# とりあえず、この方法しか上手くいかん。
# https://stackoverflow.com/questions/49117806/what-is-the-best-way-to-parameterize-a-pytest-function-using-a-fixture-that-retu
@pytest.fixture(params=range(10, 16))
def get_param(request, panda_id):
    # print(f"expensive-{request.param}")
    return {"ID": panda_id[request.param], "Work": sample_work_count[request.param] * 2}
    # return [panda_id[request.param]]


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
        return id_list


# @pytest.mark.skip
@pytest.fixture
def holiday_obj_mock(get_param, mocker):
    obj_mock = mocker.patch("app.holiday_acquisition.HolidayAcquire", autospec=True)
    property_mock = PropertyMock(side_effect=get_param.get("ID"))
    type(obj_mock).id = property_mock
    type(obj_mock).count_workday = sample_work_count[10:16]
    return obj_mock


# @pytest.mark.skip
# @pytest.mark.parametrize("sample_list", sample_work_count, indirect=["panda_id"])
# @pytest.mark.parametrize(("param", "count"), zip(get_param, sample_work_count[10:16]))
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_refer_observer(app_context, subject, get_param):
    # observer = ObserverCheckType()
    # subject.attach(observer)
    print(get_param.get("ID"))
    print(get_param.get("Work"))
    # for param, count in zip(list(get_param.get("ID")), sample_work_count[10:16]):
    # print(str(param) + " : " + str(count))


# mocker.patch.object(
#     HolidayAcquire,
#     "count_workday",
#     side_effect=count * 2,
# )

# subject.refer_acquire_type(param.get("ID"))

# original_update_func = observer.merge_type

# def dummy_update_db(i: int, past: str, post: str):
#     with open("update_type.log", "a") as f:
#         f.write(
#             f"UPDATE INTO D_RECORD_PAIDHOLIDAY SET ACQUISITION_TYPE={post} WHERE STAFF_ID={get_param.get('ID')}\n"
#         )
#     original_update_func(i, past, post)

# update_mock = mocker.patch.object(
#     observer, "merge_type", side_effect=dummy_update_db
# )

# observer.update(subject)

# print(update_mock.call_count)
