from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import and_

from app import app, db
from app.models import User, Shinsei, RecordPaidHoliday
from app.holiday_acquisition import HolidayAcquire


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

    def make_attendace_filter(self, notification_number: int = 3):
        date_type_workday = datetime.strptime(Shinsei.WORKDAY, "%Y-%m-%d")
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == self.id)
        attendance_filters.append(Shinsei.NOTIFICATION == notification_number)
        if self.search_flesh_flag() is True:
            attendance_filters.append(date_type_workday > User.INDAY)
        else:
            attendance_filters.append(
                date_type_workday
                >= self.holiday_acquire_obj.get_acquisition_list(self.base_day)[-2]
            )
        attendance_filters.append(
            date_type_workday
            < self.holiday_aquire_obj.get_acquisition_list(self.base_day)[-1]
        )

        return attendance_filters

    def count_attend_notification(self):
        filters = self.make_attendace_filter()
        notification_all_day = db.session.query(Shinsei).filter(and_(*filters)).all()
        filters_half = self.make_attendace_filter(4)
        notification_half_day = (
            db.session.query(Shinsei).filter(and_(*filters_half)).all()
        )

        return len(notification_all_day + notification_half_day / 2)


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
