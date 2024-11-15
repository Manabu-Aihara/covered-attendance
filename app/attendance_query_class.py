from dataclasses import dataclass
from datetime import date

from sqlalchemy import and_

from app import db
from app.models import (
    User,
    Shinsei,
    D_HOLIDAY_HISTORY,
    D_JOB_HISTORY,
    M_TIMECARD_TEMPLATE,
)


@dataclass
class AttendanceQuery:
    staff_id: int
    filter_from_day: date
    filter_to_day: date

    # sub_query: T = None
    # def __init__(self, staff_id: str, sub_query: T) -> None:
    #     self.staff_id = staff_id
    def _get_filter(self) -> list:
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == self.staff_id)
        attendance_filters.append(
            Shinsei.WORKDAY.between(self.filter_from_day, self.filter_to_day)
        )
        attendance_filters.append(Shinsei.STAFFID == User.STAFFID)
        return attendance_filters

    @staticmethod
    def _get_job_filter():
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == D_JOB_HISTORY.STAFFID)
        attendance_filters.append(D_JOB_HISTORY.START_DAY <= Shinsei.WORKDAY)
        attendance_filters.append(D_JOB_HISTORY.END_DAY >= Shinsei.WORKDAY)
        # attendance_filters.append(D_JOB_HISTORY.CONTRACT_CODE != 2)
        return attendance_filters

    @staticmethod
    def _get_holiday_filter():
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == D_HOLIDAY_HISTORY.STAFFID)
        attendance_filters.append(D_HOLIDAY_HISTORY.START_DAY <= Shinsei.WORKDAY)
        attendance_filters.append(D_HOLIDAY_HISTORY.END_DAY >= Shinsei.WORKDAY)
        return attendance_filters

    def _get_template_filter(self):
        attendance_filters = []
        attendance_filters.append(D_JOB_HISTORY.START_DAY <= self.filter_from_day)  # 2
        attendance_filters.append(D_JOB_HISTORY.END_DAY >= self.filter_to_day)  # 3
        attendance_filters.append(
            D_JOB_HISTORY.JOBTYPE_CODE == M_TIMECARD_TEMPLATE.JOBTYPE_CODE
        )
        attendance_filters.append(
            D_JOB_HISTORY.CONTRACT_CODE == M_TIMECARD_TEMPLATE.CONTRACT_CODE
        )
        return attendance_filters

        # Max attendance_filters[0:8] index7まで取り出す
        # return (
        #     attendance_filters[array_number[0] : array_number[1]]
        #     if array_number != ()
        #     else attendance_filters
        # )

    def db_error_handler(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return e

        return wrapper

    @db_error_handler
    def get_templates(self):
        template_filters = [D_JOB_HISTORY.STAFFID == self.staff_id]
        template_filters += self._get_template_filter()
        return db.session.query(M_TIMECARD_TEMPLATE.TEMPLATE_NO).filter(
            and_(*template_filters)
        )

    @db_error_handler
    def _get_sub_parttime(self):
        attendance_filters = self._get_filter()[0:2] + self._get_holiday_filter()
        attendance_filters.append(Shinsei.STAFFID == D_HOLIDAY_HISTORY.STAFFID)

        return (
            db.session.query(
                D_HOLIDAY_HISTORY.STAFFID,
                Shinsei.WORKDAY,
                D_HOLIDAY_HISTORY.HOLIDAY_TIME,
            )
            .filter(and_(*attendance_filters))
            .subquery()
        )

    @db_error_handler
    def get_attendance_query(self):
        attendance_filters = (
            self._get_filter()
            + self._get_job_filter()
            + self._get_template_filter()[-2:]
        )

        sub_query = self._get_sub_parttime()
        return (
            db.session.query(
                Shinsei,
                User.FNAME,
                User.LNAME,
                D_JOB_HISTORY.JOBTYPE_CODE,
                D_JOB_HISTORY.CONTRACT_CODE,
                D_JOB_HISTORY.PART_WORKTIME,
                M_TIMECARD_TEMPLATE.TEMPLATE_NO,
                # getattr(self.sub_query.c, "HOLIDAY_TIME"),
                sub_query.c.HOLIDAY_TIME,
            )
            .filter(and_(*attendance_filters))
            .outerjoin(
                sub_query,
                and_(
                    sub_query.c.STAFFID == Shinsei.STAFFID,
                    sub_query.c.WORKDAY == Shinsei.WORKDAY,
                ),
            )
        )

    # 対象年月日の職種や契約時間をスタッフごとに纏める(サブクエリ)
    def _get_sub_clerk_query(self):
        return (
            db.session.query(D_HOLIDAY_HISTORY.STAFFID, D_HOLIDAY_HISTORY.HOLIDAY_TIME)
            .filter(
                D_HOLIDAY_HISTORY.START_DAY <= self.filter_to_day,
                D_HOLIDAY_HISTORY.END_DAY >= self.filter_to_day,
            )
            .subquery()
        )

    @db_error_handler
    def get_clerical_attendance(self):
        clerk_filters = self._get_filter()[1:] + self._get_job_filter()

        sub_clerk_query = self._get_sub_clerk_query()
        return (
            db.session.query(
                Shinsei,
                User.FNAME,
                User.LNAME,
                D_JOB_HISTORY.JOBTYPE_CODE,
                D_JOB_HISTORY.CONTRACT_CODE,
                D_JOB_HISTORY.PART_WORKTIME,
                sub_clerk_query.c.HOLIDAY_TIME,
            )
            .filter(and_(*clerk_filters))
            .outerjoin(sub_clerk_query, sub_clerk_query.c.STAFFID == User.STAFFID)
            .order_by(Shinsei.STAFFID, Shinsei.WORKDAY)
        )
