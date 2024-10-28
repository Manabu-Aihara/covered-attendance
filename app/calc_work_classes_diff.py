"""
**********
勤怠システム
2022/04版
**********
"""

import os, math
from functools import wraps
from typing import Tuple, List, Callable
from datetime import datetime, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
import calendar
import jpholiday
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod

from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login.utils import login_required
from flask_login import current_user, login_user
from flask_login import logout_user
from flask import abort
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash
from sqlalchemy import and_

from app import app, db
from app.forms import (
    LoginForm,
    AdminUserCreateForm,
    ResetPasswordForm,
    DelForm,
    UpdateForm,
    SaveForm,
    AddDataUserForm,
    SelectMonthForm,
)
from app.models import (
    User,
    Shinsei,
    StaffLoggin,
    Todokede,
    Jobtype,
    KinmuTaisei,
    RecordPaidHoliday,
    D_JOB_HISTORY,
    D_HOLIDAY_HISTORY,
    CountAttendance,
    TimeAttendance,
    SystemInfo,
    CounterForTable,
)

# from tkinter import messagebox

os.environ.get("SECRET_KEY") or "you-will-never-guess"
app.permanent_session_lifetime = timedelta(minutes=360)


# ***** 管理者か判断 *****#


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)

    return decorated_view


# ***** 年月から最終日を返す*****#
def get_last_date(year, month):
    return calendar.monthrange(year, month)[1]


# ***** 各勤怠カウント計算ひな形（１日基準） *****#
class DataForTable:
    def __init__(
        self,
        y,
        m,
        d,
        sh_workday,
        sh_oncall,
        sh_holiday,
        sh_oncall_count,
        sh_engel_count,
        sh_notification,
        sh_notification_pm,
        sh_mileage,
        oncall,
        oncall_holiday,
        oncall_cnt,
        engel_cnt,
        nenkyu,
        nenkyu_half,
        tikoku,
        soutai,
        kekkin,
        syuttyou,
        syuttyou_half,
        reflesh,
        s_kyori,
        startday,
        today,
    ):
        self.y = y
        self.m = m
        self.d = d
        self.sh_workday = sh_workday
        self.sh_oncall = sh_oncall
        self.sh_holiday = sh_holiday
        self.sh_oncall_count = sh_oncall_count
        self.sh_engel_count = sh_engel_count
        self.sh_notification = sh_notification
        self.sh_notification_pm = sh_notification_pm
        self.sh_mileage = sh_mileage
        self.oncall = oncall
        self.oncall_holiday = oncall_holiday
        self.oncall_cnt = oncall_cnt
        self.engel_cnt = engel_cnt
        self.nenkyu = nenkyu
        self.nenkyu_half = nenkyu_half
        self.tikoku = tikoku
        self.soutai = soutai
        self.kekkin = kekkin
        self.syuttyou = syuttyou
        self.syuttyou_half = syuttyou_half
        self.reflesh = reflesh
        self.s_kyori = s_kyori
        self.startday = startday
        self.today = today

    def other_data(self):
        if self.startday <= self.sh_workday and self.today >= self.sh_workday:
            # オンコール当番
            if self.sh_oncall == "1":

                if self.sh_workday.weekday() == 5 or self.sh_workday.weekday() == 6:
                    # 土日オンコール当番
                    self.oncall_holiday.append("cnt")
                else:
                    self.oncall.append("cnt")

            # オンコール対応件数
            if self.sh_oncall_count:
                self.oncall_cnt.append(str(self.sh_oncall_count))
            # エンゼルケア対応件数
            if self.sh_engel_count:
                self.engel_cnt.append(str(self.sh_engel_count))
            # 年休日数（全日）
            if self.sh_notification == "3":
                self.nenkyu.append("cnt")
            # 年休日数（半日）
            if self.sh_notification == "4" or self.sh_notification == "16":
                self.nenkyu_half.append("cnt")
            # 年休日数（半日）
            if self.sh_notification_pm == "4" or self.sh_notification_pm == "16":
                self.nenkyu_half.append("cnt")
            # 遅刻回数
            if self.sh_notification == "1":
                self.tikoku.append("cnt")
            # 遅刻回数
            if self.sh_notification_pm == "1":
                self.tikoku.append("cnt")
            # 早退回数
            if self.sh_notification == "2":
                self.soutai.append("cnt")
            # 早退回数
            if self.sh_notification_pm == "2":
                self.soutai.append("cnt")
            # 欠勤日数
            if (
                self.sh_notification == "8"
                or self.sh_notification == "17"
                or self.sh_notification == "18"
                or self.sh_notification == "19"
                or self.sh_notification == "20"
            ):
                self.kekkin.append("cnt")
            # 出張（全日）回数
            if self.sh_notification == "5":
                self.syuttyou.append("cnt")
            # 出張（半日）回数
            if self.sh_notification == "6":
                self.syuttyou_half.append("cnt")
            # 出張（半日）回数
            if self.sh_notification_pm == "6":
                self.syuttyou_half.append("cnt")
            # リフレッシュ休暇日数
            if self.sh_notification == "7":
                self.reflesh.append("cnt")
            # 走行距離
            if self.sh_mileage:
                self.s_kyori.append(str(self.sh_mileage))


# ***** 常勤用各勤怠時間計算ひな形 *****#
class CalcTimeClass:
    def __init__(
        self,
        staffid: int,
        sh_starttime: str,
        sh_endtime: str,
        notifications: tuple[str],
        sh_overtime: str,
        sh_holiday: str,
    ):
        self.staffid = staffid
        self.sh_starttime = sh_starttime
        self.sh_endtime = sh_endtime
        self.notifications = notifications
        self.sh_overtime = sh_overtime
        self.sh_holiday = sh_holiday

    n_code_list: List[str] = ["10", "11", "12", "13", "14", "15"]
    n_half_list: List[str] = ["4", "9", "16"]

    # 今のところお昼だけ採用、勤務時間影響なし
    @staticmethod
    def round_up_time(which_time: str) -> datetime:
        select_time_hm = datetime.strptime(which_time, "%H:%M")
        h_split = select_time_hm.hour
        m_split = select_time_hm.minute
        if m_split == 0:
            return select_time_hm
        elif m_split > 30:
            h_integer = h_split + 1
            h_string_time = f"{h_integer}:00"
            return datetime.strptime(h_string_time, "%H:%M")
        else:
            h_string_time = f"{h_split}:30"
            return datetime.strptime(h_string_time, "%H:%M")

    # 実働時間の算出
    def calc_actual_work_time(self) -> timedelta:
        # self.jobtype != 12
        start_time_hm = datetime.strptime(self.sh_starttime, "%H:%M")
        end_time_hm = datetime.strptime(self.sh_endtime, "%H:%M")
        d = datetime.now().date()
        if self.sh_starttime != "00:00" and start_time_hm < datetime.strptime(
            "08:00", "%H:%M"
        ):
            start_time_hm = time(hour=8, minute=0)

            actual_work_time = datetime.combine(
                d, end_time_hm.time()
            ) - datetime.combine(d, start_time_hm)

            return actual_work_time
        # elif self.sh_starttime != "00:00" and (start_time_hm.minute != 0):
        #     start_time_hm = self.round_up_time()
        else:
            actual_work_time = end_time_hm - start_time_hm
            return actual_work_time

    def get_work_and_holiday_time(self) -> Tuple[float, float]:
        you = db.session.get(User, self.staffid)
        contract = db.session.get(KinmuTaisei, you.CONTRACT_CODE)

        result_work_time = contract.WORKTIME
        related_holiday = db.session.get(RecordPaidHoliday, self.staffid)
        # related_holiday = db.session.get(D_HOLIDAY_HISTORY, self.staffid)
        if contract.CONTRACT_CODE == 2:
            contract = (
                db.session.query(D_JOB_HISTORY)
                .filter(D_JOB_HISTORY.STAFFID == self.staffid)
                .first()
            )
            result_work_time = contract.PART_WORKTIME
            return result_work_time, related_holiday.BASETIMES_PAIDHOLIDAY
            # return work_time, related_holiday.HOLIDAY_TIME
        else:
            return result_work_time, related_holiday.BASETIMES_PAIDHOLIDAY
            # return work_time, related_holiday.HOLIDAY_TIME

    """
        - 時間休
        @Params: str 申請ナンバー
        @Return: timedelta
        """

    def get_times_rest(self, notification: str) -> timedelta:
        if self.n_code_list[0] == notification or self.n_code_list[3] == notification:
            return timedelta(hours=1)
        elif self.n_code_list[1] == notification or self.n_code_list[4] == notification:
            return timedelta(hours=2)
        elif self.n_code_list[2] == notification or self.n_code_list[5] == notification:
            return timedelta(hours=3)

    """
        - 契約時間 / 2 or 0
        if irregular:
            契約時間 - 入力時間
        @Return: timedelta
        """

    # 半日出張、半休、生理休暇かつ打刻のある場合
    # 9: 慶弔 congratulations and condolences
    def provide_half_rest(self) -> timedelta:
        actual_time = self.calc_actual_work_time()
        contract_work_time, contract_holiday_time = self.get_work_and_holiday_time()
        # working_plus_half_time = actual_time + timedelta(
        #     hours=contract_holiday_time / 2
        # )
        approval_times: list[timedelta] = []
        for half_notice in self.notifications:
            if half_notice in self.n_half_list:
                print("Half rest pass")
                approval_times.append(timedelta(hours=contract_holiday_time / 2))
            elif half_notice == "6":
                print("Half trip pass")
                approval_times.append(timedelta(hours=contract_work_time / 2))

        if len(approval_times) == 0:
            if actual_time < timedelta(hours=contract_work_time):
                # raise ValueError("入力に誤りがあります。申請はありせんか？")
                return timedelta(hours=contract_work_time) - actual_time
            else:
                return timedelta(0)
        elif len(approval_times) == 1:
            if actual_time < timedelta(hours=contract_work_time / 2):
                return timedelta(hours=contract_work_time) - actual_time
            else:
                return approval_times[0]
        elif len(approval_times) == 2:
            return timedelta(hours=contract_work_time / 2) + timedelta(
                hours=contract_holiday_time / 2
            )

    # 通常一日の時間休
    def calc_normal_rest(self, input_work_time: timedelta) -> timedelta:
        round_up_start = self.round_up_time(self.sh_starttime)

        # 今のところ私の判断、追加・変更あり
        if round_up_start.strftime("%H:%M") >= "13:00" or self.sh_endtime < "13:00":
            return timedelta(0)
        else:
            if input_work_time >= timedelta(hours=6):
                return timedelta(hours=1)
            else:
                return timedelta(minutes=45)

    """
        @Return: timedelta
            1.残業あり → 終業時間 - 開始時間
            2.残業なし → 契約時間
            3.残業なしで半日申請あり → 契約時間 / 2
            4.irregular → 終業時間 - 開始時間
        """

    def check_over_work(self) -> timedelta:
        actual_work_time = self.calc_actual_work_time()
        contract_work_time, contract_holiday_time = self.get_work_and_holiday_time()
        # 1.残業あり → 終業時間 - 開始時間
        # 2.残業なし → 契約時間
        # 3.残業なしで半日申請あり → 契約時間 / 2
        if self.sh_overtime == "0":
            working_time = (
                timedelta(hours=contract_work_time)
                - self.provide_half_rest()  # 契約時間 / 2 or 0
            )
            # 契約時間 / 2 or 契約時間
            return working_time
        elif self.sh_overtime == "1":  # 残業した場合
            work_time_without_rest = actual_work_time - self.calc_normal_rest(
                actual_work_time
            )
            print(f"Overtime pass: {work_time_without_rest}")
            return work_time_without_rest

    def get_actual_work_time(self) -> timedelta:
        actual_work_time = self.calc_actual_work_time()
        contract_work_time, contract_holiday_time = self.get_work_and_holiday_time()
        for notification in self.notifications:
            if notification in ["1", "2"] or self.sh_overtime == "1":
                return (
                    actual_work_time
                    + self.provide_half_rest()
                    - self.calc_normal_rest(actual_work_time)
                )
            elif notification not in ["1", "2", "8"]:
                return timedelta(hours=contract_work_time)
            elif notification == "8":
                return timedelta(0)

    """
        残業分
        @Return: float
        """

    def get_over_time(self) -> float:
        contract_work_time, contract_holiday_time = self.get_work_and_holiday_time()
        working_time = self.check_over_work()
        over_time = working_time - (
            timedelta(hours=contract_work_time) - self.provide_half_rest()
        )
        return over_time.total_seconds()

    """
        @Return: float
            半日申請、残業と諸々処理した後 - 時間休
        """

    # リアル実働時間（労働時間 - 年休、出張、時間休など）
    def get_real_time(self) -> float:
        working_time = self.check_over_work()
        print(f"Work time in real: {working_time}")
        for one_notification in self.notifications:
            if one_notification in self.n_code_list:
                working_time -= self.get_times_rest(one_notification)

        return working_time.total_seconds()

    """
        看護師限定、休日出勤
        @Return: float
        """

    def calc_nurse_holiday_work(self) -> float:
        # 祝日(2)、もしくはNSで土日(1)
        nurse_member = db.session.get(User, self.staffid)
        job_type = db.session.get(Jobtype, nurse_member.JOBTYPE_CODE)
        # if self.holiday == "2" or self.holiday == "1"
        # and self.jobtype == 1 and self.u_contract_code == 2:
        if (
            self.sh_holiday == "2"
            or self.sh_holiday == "1"
            and job_type.JOBTYPE_CODE == 1
            and nurse_member.CONTRACT_CODE == 2
        ):
            return self.get_real_time()
        else:
            return 9.99

    # なくても機能するみたいだ
    # 打刻は00:00で
    def get_zero_time_notification(self, notification: str) -> float:
        contract_work_time, contract_holiday_time = self.get_work_and_holiday_time()
        if self.sh_starttime == "00:00" and self.sh_endtime == "00:00":
            # 全日年休、出張全日の場合
            if notification == "3" or notification == "5" or notification == "9":
                return contract_work_time
            else:
                raise ValueError("入力に誤りがあります。申請はありせんか？")


# ************************************** 時間休カウント ********************************************#
class TimeOffClass:
    def __init__(
        self,
        y,
        m,
        d,
        sh_workday,
        sh_notification,
        sh_notification_pm,
        timeoff1,
        timeoff2,
        timeoff3,
        halfway_through1,
        halfway_through2,
        halfway_through3,
        FromDay,
        ToDay,
    ):
        self.y = y
        self.m = m
        self.d = d
        self.sh_workday = sh_workday
        self.sh_notification = sh_notification
        self.sh_notification_pm = sh_notification_pm
        self.timeoff1 = timeoff1
        self.timeoff2 = timeoff2
        self.timeoff3 = timeoff3
        self.halfway_through1 = halfway_through1
        self.halfway_through2 = halfway_through2
        self.halfway_through3 = halfway_through3
        self.FromDay = FromDay
        self.ToDay = ToDay

    def cnt_time_off(self):
        if self.FromDay <= self.sh_workday and self.ToDay >= self.sh_workday:
            if self.sh_notification == "10" or self.sh_notification_pm == "10":
                self.timeoff1.append("cnt1")
            if self.sh_notification == "11" or self.sh_notification_pm == "11":
                self.timeoff2.append("cnt2")
            if self.sh_notification == "12" or self.sh_notification_pm == "12":
                self.timeoff3.append("cnt3")
            if self.sh_notification == "13" or self.sh_notification_pm == "13":
                self.halfway_through1.append("cnt01")
            if self.sh_notification == "14" or self.sh_notification_pm == "14":
                self.halfway_through2.append("cnt02")
            if self.sh_notification == "15" or self.sh_notification_pm == "15":
                self.halfway_through3.append("cnt03")
