import pytest
from datetime import datetime
from typing import List, Tuple

from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverRegist, ObserverCheckType, ObserverCarry
from app.models_aprv import PaidHolidayLog


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
    return [x * 12 / 11 for x in work_count_to_mock()[0]]


@pytest.fixture(name="panda_half_count")
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def count_half_workday_from_panda_indirect(app_context):
    return [x * 12 / 11 for x in work_count_to_mock()[1]]


# とりあえず、この方法しか上手くいかん。
# https://stackoverflow.com/questions/49117806/what-is-the-best-way-to-parameterize-a-pytest-function-using-a-fixture-that-retu
# @pytest.fixture(params=range(0, 25))
@pytest.fixture
def get_param(panda_id, panda_count, panda_half_count):
    # print(f"expensive-{request.param}")
    print(f"調整後{panda_count}日")
    print(f"調整後{panda_half_count}日")
    return {"ID": panda_id, "Work": panda_count, "Work_H": panda_half_count}


# @pytest.fixture(name="work_flag")
# @pytest.mark.freeze_time(datetime(2024, 3, 31))
# def search_half_flag_indirect(app_context):
#     return search_half_flag()


@pytest.mark.skip
def test_print_fixtures(app_context, get_param):
    print(f"{get_param.get('ID')}: {get_param.get('Work_H')}")
    print(len(get_param.get("ID")))
    print(len(get_param.get("Work_H")))


date_now = datetime.now()


# @pytest.mark.skip
# @pytest.mark.usefixtures("app_context")
# class TestCheckType:
# これはあまり意味をなさなくなった…
# @pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_divide_observer(app_context, subject, get_param, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    orignal_ref_func = subject.refer_acquire_type

    def dummy_pass_method(i: int):
        # print(f"タイプ: {type(i)}")
        with open(f"pass_method{date_now.strftime('%m%d%H%M')}.log", "a") as f:
            if search_half_flag(i) is False:
                f.write(f"ID{i}: count_workday\n")
            else:
                f.write(f"ID{i}: count_workday_half_year\n")
        orignal_ref_func(i)

    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", side_effect=get_param.get("Work")
    )
    workday_half_mock = mocker.patch.object(
        HolidayAcquire, "count_workday_half_year", side_effect=get_param.get("Work_H")
    )

    def dummy_ref_method(i: int):
        print("---refのダミー---")
        orignal_ref_func(i)

    original_divide_func = subject.divide_acquire_type

    def dummy_divide_method(count: float):
        print("---divideのダミー---")
        print(f"念のため: {count}")
        print(f"「 {original_divide_func(count)} 」")

    divide_mock = mocker.patch.object(
        subject, "divide_acquire_type", side_effect=dummy_divide_method
    )

    refer_mock = mocker.patch.object(
        subject, "refer_acquire_type", side_effect=dummy_ref_method
    )

    # これがヤバかった
    # mocker.patch.object(observer, "update")

    # observer.update(subject)
    subject.execute()

    print(f"---divide.ARGS---: {divide_mock.call_args_list}")
    print(f"---divide.COUNT---: {divide_mock.call_count}")
    print(f"---workday.COUNT---: {workday_mock.call_count}")
    print(f"---workday_half.COUNT---: {workday_half_mock.call_count}")
    print(f"---refer.COUNT---: {refer_mock.call_count}")


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_merge_observer(app_context, subject, get_param, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    workday_mock = mocker.patch.object(
        HolidayAcquire, "count_workday", side_effect=get_param.get("Work")
    )
    # get_param.get("Work")の重複になる！
    workday_half_mock = mocker.patch.object(
        HolidayAcquire, "count_workday_half_year", side_effect=get_param.get("Work_H")
    )

    original_update_func = observer.merge_type

    def dummy_update_db(i: int, past: str, post: str):
        print(f"---{search_half_flag(i)}---")
        # if search_half_flag(i) is False:
        with open(f"update_type_cat{date_now.strftime('%m%d%H%M')}.log", "a") as f:
            f.write(
                f"UPDATE INTO D_RECORD_PAIDHOLIDAY SET ACQUISITION_TYPE={post} WHERE STAFF_ID={i}\n"
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


# ダミー関数を初めてやってみた
@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_check_observer(app_context, subject, mocker):
    observer = ObserverCheckType()
    subject.attach(observer)

    acquisition_type_mock = mocker.patch.object(
        subject,
        "refer_acquire_type",
        side_effect=[(None, "F"), (None, ""), (None, "F")],
    )

    # Save original function
    original_trigger_fail = observer.trigger_fail

    def mock_for_fail(i):
        """Mock throwing an exception when i == 2."""
        print(f"mock_insert_id called with i={i}")
        if i == 31:
            raise ValueError("failed")
        original_trigger_fail(i)

    mock_fail = mocker.patch.object(observer, "trigger_fail", side_effect=mock_for_fail)
    observer.update(subject)

    assert acquisition_type_mock.call_count == 3
    assert mock_fail.called


@pytest.mark.skip
@pytest.mark.freeze_time(datetime(2024, 3, 31))
def test_carry_observer(app_context, subject, mocker):
    observer = ObserverCarry()
    subject.attach(observer)

    # 結局、session.addの引数にならなかった
    phl_mock = mocker.MagicMock(spec=PaidHolidayLog)
    dummy_obj = mocker.patch("app.models_aprv.PaidHolidayLog", phl_mock)

    assert isinstance(dummy_obj, PaidHolidayLog)

    # original_func = db.session.add
    original_insert_func = observer.insert_data

    def dummy_add_db(i: int, carri_days: float = subject.calcurate_carry_days):
        with open("insert_carry.log", "a") as f:
            f.write(
                f"INSERT INTO D_PAIDHOLIDAY_LOG VALUES({i}, 0, None, None, {carri_days}, '前回からの繰り越し')\n"
            )
        original_insert_func(i, carri_days)

    # add_mock = mocker.patch.object(db.session, "add", side_effect=dummy_add_db)
    add_mock = mocker.patch.object(observer, "insert_data", side_effect=dummy_add_db)
    observer.update(subject)

    print(add_mock.call_args_list)
    assert add_mock.call_count == 2
