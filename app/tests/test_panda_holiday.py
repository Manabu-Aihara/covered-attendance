import pytest
from datetime import datetime
from typing import List, Tuple

from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry
from app.models_aprv import PaidHolidayLog


def concern_id_from_panda() -> List[int]:
    subject = SubjectImpl()
    return subject.get_concerned_staff()


def search_half_flag(concern_id: int) -> bool:
    flag: bool = False
    # list_tank = []
    # for concerned_id in concern_id_list:
    holiday_acquire_obj = HolidayAcquire(concern_id)
    base_day = HolidayAcquire(concern_id).convert_base_day(holiday_acquire_obj.in_day)
    flag = (
        True
        if len(holiday_acquire_obj.get_acquisition_list(base_day)) == 1
        # and (holiday_acquire_obj.get_nth_dow() != 1)
        else flag
    )

    return flag
    #     list_tank.append(flag)

    # return list_tank


def work_count_to_mock() -> Tuple[List[int], List[int]]:
    count_list = []
    count_half_list = []
    for concerned_id in concern_id_from_panda():
        holiday_acquire_obj = HolidayAcquire(concerned_id)
        if search_half_flag(concerned_id) is False:
            count_list.append(holiday_acquire_obj.count_workday())
        else:
            count_half_list.append(holiday_acquire_obj.count_workday_half_year())

    return count_list, count_half_list


def plus_holidays_to_mock() -> List[float]:
    subject = SubjectImpl()
    plus_time_list = []
    for concerned_id in concern_id_from_panda():
        # holiday_acquire_obj = HolidayAcquire(concerned_id)
        # dict_data = holiday_acquire_obj.plus_next_holidays()
        # dict_value = dict_data.values()
        # # dict_valuesのリスト化
        # acquisition_days: int = list(dict_value)[-1]
        # acquisition_times: float = (
        #     acquisition_days * holiday_acquire_obj.holiday_base_time
        # )
        acquisition_times = subject.acquire_holidays(concerned_id)
        plus_time_list.append(acquisition_times)
    # return acquisition_times

    return plus_time_list


@pytest.fixture(scope="module")
def subject():
    subject = SubjectImpl()
    return subject


@pytest.fixture(name="panda_id")
@pytest.mark.freeze_time(datetime(2024, 4, 1))
def concerned_id_from_panda_indirect(app_context):
    # print(f"len: {len(concern_id_from_panda())}\n")
    return concern_id_from_panda()


@pytest.fixture(name="panda_count")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def count_workday_from_panda_indirect(app_context):
    return [x for x in work_count_to_mock()[0]]
    # return [round(x * 12 / 11) for x in work_count_to_mock()[0]]


@pytest.fixture(name="panda_half_count")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def count_half_workday_from_panda_indirect(app_context):
    return [x for x in work_count_to_mock()[1]]
    # return [round(x * 12 / 11) for x in work_count_to_mock()[1]]


@pytest.fixture(name="panda_plus")
@pytest.mark.freeze_time(datetime(2024, 4, 1))
def plus_holidays_indirect(app_context):
    return plus_holidays_to_mock()
    # 以下不可
    # holiday_acquire_obj = HolidayAcquire(panda_id)
    # days = holiday_acquire_obj.plus_next_holidays().values()
    # return panda_id, days * holiday_acquire_obj.holiday_base_time


# とりあえず、この方法しか上手くいかん。
# https://stackoverflow.com/questions/49117806/what-is-the-best-way-to-parameterize-a-pytest-function-using-a-fixture-that-retu
# @pytest.fixture(params=range(0, 25))
@pytest.fixture
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def get_work_param(panda_id, panda_count, panda_half_count):
    # print(f"{panda_id}")
    # print(f"調整後{panda_count}")
    # print(f"調整後{panda_half_count}")
    return {"ID": panda_id, "Work": panda_count, "Work_H": panda_half_count}


@pytest.fixture
@pytest.mark.freeze_time(datetime(2024, 4, 1))
def get_acquire_param(panda_id, panda_plus):
    # print(f"{panda_id}")
    return {"ID": panda_id, "Holiday": panda_plus}


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_print_fixtures(get_work_param):
    print("expensive")
    print(f"{get_work_param.get('ID')}: {get_work_param.get('Work')}日")
    print(len(get_work_param.get("ID")))
    print(len(get_work_param.get("Work")))
    print(len(get_work_param.get("Work_H")))


# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 4, 1))
def test_print_fixture_plus(get_acquire_param):
    print("expensive")
    print(f"{get_acquire_param.get('ID')}: {get_acquire_param.get('Holiday')}")
    print(len(get_acquire_param.get("ID")))
    print(len(get_acquire_param.get("Holiday")))


date_now = datetime.now()


# @pytest.mark.skip
# @pytest.mark.usefixtures("app_context")
# class TestCheckType:


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_merge_observer(app_context, subject, get_work_param, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", side_effect=get_work_param.get("Work")
    )
    # get_work_param.get("Work")の重複になる！
    workday_half_mock = mocker.patch.object(
        HolidayAcquire,
        "count_workday_half_year",
        side_effect=get_work_param.get("Work_H"),
    )

    original_update_func = observer.merge_type

    def dummy_update_db(i: int, past: str, post: str):
        # print(f"---{search_half_flag(i)}---")
        # if search_half_flag(i) is True:
        with open(f"update_type_cat{date_now.strftime('%m%d%H%M')}.log", "a") as f:
            f.write(
                f"UPDATE panda.M_RECORD_PAIDHOLIDAY SET ACQUISITION_TYPE='{post}' WHERE STAFFID={i};\n"
            )

        original_update_func(i, past, post)

    update_mock = mocker.patch.object(
        observer, "merge_type", side_effect=dummy_update_db
    )

    # observer.update(subject)
    subject.execute()

    print(f"---merge.COUNT---: {update_mock.call_count}")
    print(f"---workday.COUNT---: {workday_mock.call_count}")
    print(f"---workday_half.COUNT---: {workday_half_mock.call_count}")


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 9, 30))
def test_carry_observer(app_context, subject, mocker):
    observer = ObserverCarry()
    subject.attach(observer)

    # 結局、session.addの引数にならなかった
    phl_mock = mocker.MagicMock(spec=PaidHolidayLog)
    dummy_obj = mocker.patch("app.models_aprv.PaidHolidayLog", phl_mock)

    assert isinstance(dummy_obj, PaidHolidayLog)

    # original_func = db.session.add
    original_insert_func = observer.insert_carry

    def dummy_add_db(i: int, carri_days: float = subject.calcurate_carry_days):
        with open("insert_carry.log", "a") as f:
            f.write(
                f"INSERT INTO D_PAIDHOLIDAY_LOG VALUES({i}, 0, None, None, {carri_days}, '前回からの繰り越し')\n"
            )
        original_insert_func(i, carri_days)

    # add_mock = mocker.patch.object(db.session, "add", side_effect=dummy_add_db)
    add_mock = mocker.patch.object(observer, "insert_carry", side_effect=dummy_add_db)
    observer.update(subject)

    print(add_mock.call_args_list)


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 4, 1))
def test_acquire_holidays(app_context, subject, get_acquire_param, mocker):
    observer = ObserverRegist()
    subject.attach(observer)

    plus_mock = mocker.patch.object(
        subject,
        "acquire_holidays",
        side_effect=get_acquire_param.get("Holiday"),
    )

    original_insert_func = observer.insert_data

    def dummy_add_db(i: int, carri_times: float):
        print(f"ID: 「{i}」")
        with open("insert_holidays.log", "a") as f:
            f.write(
                f"INSERT INTO panda.D_PAIDHOLIDAY_LOG VALUES({i}, {carri_times}, NULL, NULL, 0, '{carri_times}時間付与');\n"
            )
        original_insert_func(i, carri_times)

    insert_mock = mocker.patch.object(observer, "insert_data", side_effect=dummy_add_db)
    # observer.update(subject)
    subject.execute()

    print(f"---acquire.COUNT---: {plus_mock.call_count}")
    print(f"---insert.ARGS---: {insert_mock.call_args_list}")
