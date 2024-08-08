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
    def _get_filter(self, *range_number: int):
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == self.staff_id)
        attendance_filters.append(
            Shinsei.WORKDAY.between(self.filter_from_day, self.filter_to_day)
        )
        attendance_filters.append(D_JOB_HISTORY.START_DAY <= Shinsei.WORKDAY)
        attendance_filters.append(D_JOB_HISTORY.END_DAY >= Shinsei.WORKDAY)
        attendance_filters.append(Shinsei.STAFFID == User.STAFFID)
        attendance_filters.append(Shinsei.STAFFID == D_JOB_HISTORY.STAFFID)
        attendance_filters.append(
            D_JOB_HISTORY.JOBTYPE_CODE == M_TIMECARD_TEMPLATE.JOBTYPE_CODE
        )
        attendance_filters.append(
            D_JOB_HISTORY.CONTRACT_CODE == M_TIMECARD_TEMPLATE.CONTRACT_CODE
        )

        return (
            attendance_filters[: range_number[0]]
            if range_number != ()
            else attendance_filters
        )

    def _get_sub_parttime(self):
        attendance_filters = self._get_filter(4)
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

    def get_attendance_query(self):
        attendance_filters = self._get_filter()

        sub_query = self._get_sub_parttime()
        return (
            db.session.query(
                Shinsei,
                User.FNAME,
                User.LNAME,
                D_JOB_HISTORY.JOBTYPE_CODE,
                D_JOB_HISTORY.CONTRACT_CODE,
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
            .order_by(Shinsei.STAFFID, Shinsei.WORKDAY)
        )
