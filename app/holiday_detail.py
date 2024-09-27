import math
from typing import List
from dataclasses import dataclass

from sqlalchemy import and_, or_

from app import db
from app.models import User, Shinsei, RecordPaidHoliday
from app.holiday_acquisition import HolidayAcquire
from app.holiday_subject import error_handler


@dataclass
class AttendaceNotice:
    id: int

    def __post_init__(self):
        self.holiday_acquire_obj = HolidayAcquire(self.id)

        self.base_day = HolidayAcquire(self.id).convert_base_day(
            self.holiday_acquire_obj.in_day
        )

    def search_flesh_flag(self) -> bool:
        flag: bool = False
        flag = (
            True
            if len(self.holiday_acquire_obj.get_acquisition_list(self.base_day)) == 1
            # and (holiday_acquire_obj.get_nth_dow() != 1)
            else flag
        )

        return flag

    def make_attendace_filter(self, *notification: str):
        # InstrumentedAttribute!
        # date_type_workday = datetime.strptime(Shinsei.WORKDAY, "%Y-%m-%d")
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == self.id)
        attendance_filters.append(
            or_(
                Shinsei.NOTIFICATION.in_(notification),
                Shinsei.NOTIFICATION2.in_(notification),
            )
        )
        # attendance_filters.append(Shinsei.NOTIFICATION2 == notification)
        if self.search_flesh_flag() is True:
            attendance_filters.append(Shinsei.WORKDAY > User.INDAY)
        else:
            attendance_filters.append(
                Shinsei.WORKDAY
                >= self.holiday_acquire_obj.get_acquisition_list(self.base_day)[-2]
            )
        attendance_filters.append(
            Shinsei.WORKDAY
            < self.holiday_acquire_obj.get_acquisition_list(self.base_day)[-1]
        )

        return attendance_filters

    def count_attend_notification(self) -> float:
        filters = self.make_attendace_filter("3")
        notification_all_day = db.session.query(Shinsei).filter(and_(*filters)).all()
        filters_half = self.make_attendace_filter("4")
        notification_half_day = (
            db.session.query(Shinsei).filter(and_(*filters_half)).all()
        )

        return len(notification_all_day) + len(notification_half_day) / 2

    @error_handler
    def acquire_holidays(self) -> int:
        holiday_acquire_obj = HolidayAcquire(self.id)
        dict_data = holiday_acquire_obj.plus_next_holidays()
        dict_value = dict_data.values()
        # dict_valuesのリスト化
        acquisition_days: int = list(dict_value)[-1]
        return acquisition_days

    """
    有休申請に対する、時間休の合計
    @Param
        notification: str 申請コード range(10, 16)
    @Return
        : float
        """

    def sum_attend_time_rest(self) -> float:
        rp_holiday = db.session.get(RecordPaidHoliday, self.id)
        # 年休対象項目ID（M_NOTIFICATION）
        n_code_list: List[str] = ["10", "11", "12", "13", "14", "15"]
        filter_1 = self.make_attendace_filter(n_code_list[0], n_code_list[3])
        filter_2 = self.make_attendace_filter(n_code_list[1], n_code_list[4])
        filter_3 = self.make_attendace_filter(n_code_list[2], n_code_list[5])
        notification_time = db.session.query(Shinsei).filter(*filter_1).all()
        notification_2_times = db.session.query(Shinsei).filter(*filter_2).all()
        notification_3_times = db.session.query(Shinsei).filter(*filter_3).all()
        sum_time_rest: int = (
            notification_time + notification_2_times * 2 + notification_3_times * 3
        )

        return len(sum_time_rest)
        # return math.ceil(sum_time_rest / rp_holiday.BASETIMES_PAIDHLIDAY)


"""
@app.route('/admin/users_holiday', methods=['GET', 'POST'])
@login_required
@admin_login_required
def acquire_users_holiday():

    specification = ["readonly", "checked", "selected", "hidden", "disabled"]

    date_str = datetime.today().strftime("%Y-%m-%d")
    today = datetime.today()
    
    team_disp = ["全職員"]
    team_names = db.session.query(Team.NAME).all()
    team_list = list(team_names)
    team_disp.append(team_list)

    all_user = db.session.query(User).all()

    for user in all_user:
"""
