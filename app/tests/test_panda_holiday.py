import pytest
from unittest.mock import PropertyMock
from datetime import datetime

from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import Subject, SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry
from app.holiday_logging import HolidayLogger


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
# @pytest.fixture(params=range(0, 25))
@pytest.fixture
def get_param(panda_id):
    # print(f"expensive-{request.param}")
    # return {"ID": panda_id[request.param], "Work": sample_work_count[request.param] * 2}
    return {"ID": panda_id, "Work": [x * 2 for x in sample_work_count]}


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
# @pytest.fixture
# def holiday_obj_mock(get_param, mocker):
#     obj_mock = mocker.patch("app.holiday_acquisition.HolidayAcquire", autospec=True)
#     property_mock = PropertyMock(side_effect=get_param.get("ID"))
#     type(obj_mock).id = property_mock
#     type(obj_mock).count_workday = sample_work_count[10:16]
#     return obj_mock


# @pytest.mark.skip
# @pytest.mark.parametrize("sample_list", sample_work_count, indirect=["panda_id"])
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_refer_observer(app_context, subject, get_param, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    print(get_param.get("ID"))
    print(get_param.get("Work"))

    original_update_func = observer.merge_type
    original_logger = HolidayLogger.get_logger
    # original_log_func = original_logger.info

    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", side_effect=get_param.get("Work")
    )

    def dummy_logger(level: str):
        print("---info---")
        output_info = original_logger(level)
        output_info.error("5時です!!")
        output_info.info("5時です")
        # original_log_func("5時です")

    # mocker.patch.object(HolidayLogger, "get_logger", side_effect=dummy_logger)

    def dummy_update_db(i: int, past: str, post: str):
        with open("update_type01251715.log", "a") as f:
            f.write(
                f"UPDATE INTO D_RECORD_PAIDHOLIDAY SET ACQUISITION_TYPE={post} WHERE STAFF_ID={i}\n"
            )
        # print(post)
        original_update_func(i, past, post)

    update_mock = mocker.patch.object(
        observer, "merge_type", side_effect=dummy_update_db
    )

    # print(subject.refer_acquire_type(get_param.get("ID")))
    observer.update(subject)

    assert workday_mock.call_count == 25
