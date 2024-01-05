import pytest
import datetime

from app import db
from app.models import Todokede, User
from app.models_aprv import NotificationList, Approval
from app.routes_approvals import get_notification_list
from app.approval_util import toggle_notification_type, select_zero_date, NoZeroTable
from app.pulldown_util import get_pulldown_list


@pytest.mark.skip
def test_sample_add_notification_data(app_context):
    notification_1 = NotificationList(
        30,
        8,
        datetime.datetime.now().date(),
        datetime.datetime.now().time(),
        datetime.datetime.now().date() + datetime.timedelta(days=3),
        datetime.datetime.now().time(),
        "軒下の雪で",
    )
    db.session.add(notification_1)
    db.session.commit()


@pytest.mark.skip
def test_select_notification_data(app_context):
    one_notification_data = NotificationList.query.filter(
        NotificationList.STAFFID == 20
    ).all()
    assert len(one_notification_data) == 2


@pytest.mark.skip
def test_get_staff_data(app_context):
    # 所属コード
    team_code = (
        User.query.with_entities(User.TEAM_CODE).filter(User.STAFFID == 201).first()
    )

    approval_member: Approval = Approval.query.filter(
        Approval.TEAM_CODE == team_code[0]
    ).first()

    assert isinstance(approval_member, Approval)
    # assert team_code == 2


@pytest.mark.skip
def test_get_notificatin_list(app_context):
    # todokede_list = GetPullDownList(Todokede, Todokede.CODE, Todokede.NAME, Todokede.CODE)
    todokede_list = get_notification_list()
    assert todokede_list[0] == ["", ""]
    assert todokede_list[1] == [1, "遅刻"]


@pytest.mark.skip
def test_get_pulldown_list():
    result_tuple = get_pulldown_list()
    assert result_tuple[0][1] == (1, "本社")
    assert result_tuple[3][1] == (1, "看護師")
    print(result_tuple[2])


@pytest.mark.skip
def test_toggle_notification_type(app_context):
    result = toggle_notification_type(Todokede, 3)
    print(result)
    assert result == "年休全日"


@pytest.mark.skip
def test_get_empty_object(app_context):
    approval_member = Approval.query.filter(Approval.STAFFID == 20).first()
    print(f"ちゃんとオブジェクト：{approval_member.__dict__}")
    approval_non_member = Approval.query.filter(Approval.STAFFID == 201).first()
    # print(f'ちゃんとじゃないオブジェクト：{approval_non_member.__dict__}')
    assert isinstance(approval_member, Approval)
    assert isinstance(approval_non_member, Approval)


"""
    時刻表示関連ユーティリティ
    """


@pytest.mark.skip
def test_select_zero_date(app_context):
    result_query = select_zero_date(
        NotificationList, NotificationList.START_TIME, NotificationList.END_TIME
    )
    print(f"00：00：00オブジェクト：　{result_query}")


@pytest.mark.skip
def test_select_same_date_tables(app_context):
    target_table = NoZeroTable(NotificationList)
    retrieve_table_objects = target_table.select_same_date_tables(
        "START_DAY", "END_DAY"
    )
    print(retrieve_table_objects)


# @pytest.mark.skip
def test_convert_zero_to_none(app_context):
    target_table = NoZeroTable(NotificationList)
    target_table.convert_value_to_none(
        target_table.select_zero_date_tables("START_TIME", "END_TIME"),
        "START_TIME",
        "END_TIME",
    )
