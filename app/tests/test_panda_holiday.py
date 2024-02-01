import pytest
from unittest.mock import PropertyMock
from datetime import datetime
from typing import List

from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import Subject, SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry
from app.holiday_logging import HolidayLogger


@pytest.mark.freeze_time(datetime(2024, 3, 31))
def concern_id_from_panda() -> List[int]:
    subject = SubjectImpl()
    return subject.get_concerned_staff()


def search_half_flag(concern_id: int) -> bool:
    flag: bool = False
    # list_tank = []
    # for concerned_id in concern_id_list:
    holiday_acquire_obj = HolidayAcquire(concern_id)
    base_day = holiday_acquire_obj.convert_base_day()
    flag = (
        True
        if len(holiday_acquire_obj.get_acquisition_list(base_day)) == 1
        # and (holiday_acquire_obj.get_nth_dow() != 1)
        else flag
    )

    return flag
    #     list_tank.append(flag)

    # return list_tank


def work_count_to_mock() -> List[int]:
    list_tank = []
    for concerned_id in concern_id_from_panda():
        holiday_acquire_obj = HolidayAcquire(concerned_id)
        list_tank.append(holiday_acquire_obj.count_workday())

    return list_tank


@pytest.fixture(scope="module")
def subject():
    subject = SubjectImpl()
    return subject


@pytest.fixture(name="panda_id")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def concerned_id_from_panda_indirect(app_context):
    # print(f"len: {len(concern_id_from_panda())}\n")
    return concern_id_from_panda()


@pytest.fixture(name="panda_count")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def count_workday_from_panda_indirect(app_context):
    return work_count_to_mock()


# とりあえず、この方法しか上手くいかん。
# https://stackoverflow.com/questions/49117806/what-is-the-best-way-to-parameterize-a-pytest-function-using-a-fixture-that-retu
# @pytest.fixture(params=range(0, 25))
@pytest.fixture
def get_param(panda_id, panda_count):
    # print(f"expensive-{request.param}")
    # return {"ID": panda_id[request.param], "Work": sample_work_count[request.param] * 2}
    return {"ID": panda_id, "Work": [x * 3 / 2 for x in panda_count]}


# @pytest.fixture(name="work_flag")
# @pytest.mark.freeze_time(datetime(2024, 3, 31))
# def search_half_flag_indirect(app_context):
#     return search_half_flag()


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


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_print_fixtures(app_context, get_param):
    print(get_param.get("ID"))
    print(get_param.get("Work"))


date_now = datetime.now()
level = [("ERROR", "-err"), ("INFO", "-info")]


@pytest.fixture(params=level)
def fix_level(request):
    return request.param


@pytest.fixture(scope="class")
# @pytest.mark.parametrize("level", [("ERROR", "-err"), ("INFO", "-info")])
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def observer_log(app_context, subject, get_param, fix_level, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    log_args_mock = mocker.MagicMock()
    log_args_mock.__getitem__.side_effect = fix_level

    logger_mock = mocker.MagicMock()
    mocker.patch.object(HolidayLogger, "get_logger", return_value=logger_mock)

    origin_logger = HolidayLogger.get_logger(log_args_mock)

    assert origin_logger == logger_mock

    property_mock = PropertyMock(side_effect=get_param.get("ID"))
    type(origin_logger).id = property_mock

    def dummy_output_error(msg: str):
        # with open("dummy_log_err.log", "a") as f:
        #     f.write("エラー出る予定です\n")
        print("エラーです!!")
        # origin_logger.error(msg)

    log_err_mock = mocker.patch.object(
        origin_logger, "error", side_effect=dummy_output_error
    )

    def dummy_output_info(msg: str):
        # with open("dummy_log_info.log", "a") as f:
        #     f.write("通常です\n")
        print("インフォで〜す")
        # origin_logger.info(msg)

    log_info_mock = mocker.patch.object(
        origin_logger, "info", side_effect=dummy_output_info
    )

    observer.update(subject)

    print(f"---error.COUNT---: {log_err_mock.call_count}")
    print(f"---info.COUNT---: {log_info_mock.call_count}")


# @pytest.mark.skip
@pytest.mark.usefixtures("app_context")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
class TestCheckType:
    @pytest.mark.skip
    def test_select_count(self, subject, mocker):
        observer = ObserverCheckType()
        subject.attach(observer)

        orignal_func = subject.refer_acquire_type

        def dummy_pass_method(i: int):
            # print(f"タイプ: {type(i)}")
            with open(f"pass_method{date_now.strftime('%m%d%H%M')}.log", "a") as f:
                if search_half_flag(i) is False:
                    f.write(f"ID{i}: count_workday\n")
                else:
                    f.write(f"ID{i}: count_workday_half_year\n")
            orignal_func(i)

        refer_mock = mocker.patch.object(
            subject, "refer_acquire_type", side_effect=dummy_pass_method
        )
        # これがヤバかった
        # mocker.patch.object(observer, "update")

        observer.update(subject)
        print(f"---refer.COUNT---: {refer_mock.call_count}")

    # @pytest.mark.skip
    def test_merge_observer(self, subject, get_param, mocker):
        observer = ObserverCheckType()
        subject.attach(observer)

        workday_mock = mocker.patch.object(
            HolidayAcquire, "count_workday", side_effect=get_param.get("Work")
        )
        workday_half_mock = mocker.patch.object(
            HolidayAcquire, "count_workday_half_year", side_effect=get_param.get("Work")
        )

        original_update_func = observer.merge_type

        def dummy_update_db(i: int, past: str, post: str):
            with open(f"update_type{date_now.strftime('%m%d%H%M')}.log", "a") as f:
                f.write(
                    f"UPDATE INTO D_RECORD_PAIDHOLIDAY SET ACQUISITION_TYPE={post} WHERE STAFF_ID={i}\n"
                )
            # print(post)
            original_update_func(i, past, post)

        update_mock = mocker.patch.object(
            observer, "merge_type", side_effect=dummy_update_db
        )

        observer.update(subject)

        print(f"---merge.COUNT---: {update_mock.call_count}")
        print(f"---workday.COUNT---: {workday_mock.call_count}")
