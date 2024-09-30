"""
**********
勤怠システム
2022/04版
**********
"""

import os
from functools import wraps
from typing import Tuple, List, Union
from datetime import datetime, timedelta
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
    RecordPaidHoliday,
    D_HOLIDAY_HISTORY,
    CountAttendance,
    TimeAttendance,
    SystemInfo,
    CounterForTable,
)
from app.models import D_JOB_HISTORY, D_HOLIDAY_HISTORY, KinmuTaisei

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
        staffid,
        double_notification_flag,
        sh_starttime,
        sh_endtime,
        sh_overtime,
        sh_holiday,
    ):
        self.staffid = staffid
        self.notification_flag = double_notification_flag
        self.sh_starttime = sh_starttime
        self.sh_endtime = sh_endtime
        self.sh_overtime = sh_overtime
        # ちょっと待って
        # self.over_time_0 = over_time_0
        # ちょっと待って
        # self.syukkin_holiday_times_0 = holiday_work_list
        self.sh_holiday = sh_holiday
        self.n_code_list: List[str] = ["10", "11", "12", "13", "14", "15"]
        self.n_half_list: List[str] = ["4", "6", "16"]
        notification_items: list = [db.session.get(Todokede, i) for i in range(1, 21)]
        exclude_list = [3, 5, 7, 8, 17, 18, 19, 20]
        self.notification_pm_list: list = [
            n for i, n in enumerate(notification_items, 1) if i not in exclude_list
        ]
        self.real_time_sum: list = []

    # 実働時間の算出
    def calc_actual_work_time(self) -> timedelta:
        # self.jobtype != 12
        start_time_hm = datetime.strptime(self.sh_starttime, "%H:%M")
        end_time_hm = datetime.strptime(self.sh_endtime, "%H:%M")
        if self.sh_starttime != "00:00" and start_time_hm < datetime.strptime(
            "08:00", "%H:%M"
        ):
            start_time_hm = datetime(hour=8, minute=0)

        actual_work_time = end_time_hm - start_time_hm
        # 残業判断の基準となる時間
        return actual_work_time

    def get_work_and_holiday_time(self) -> Tuple[float, float]:
        contract = db.session.get(KinmuTaisei, self.staffid)
        related_holiday = db.session.get(RecordPaidHoliday, self.staffid)
        # related_holiday = db.session.get(D_HOLIDAY_HISTORY, self.staffid)
        if contract.CONTRACT_CODE == 2:
            work_time = (
                db.session.query(D_JOB_HISTORY.PART_WORKTIME)
                .filter(
                    and_(
                        D_JOB_HISTORY.CONTRACT_CODE == 2,
                        D_JOB_HISTORY.STAFFID == self.staffid,
                    )
                )
                .first()
            )
            return work_time, related_holiday.BASETIMES_PAIDHOLIDAY
            # return work_time, related_holiday.HOLIDAY_TIME
        else:
            work_time = db.session.get(KinmuTaisei.WORKTIME, self.staffid)
            return work_time, related_holiday.BASETIMES_PAIDHOLIDAY
            # return work_time, related_holiday.HOLIDAY_TIME

    # 今だけ暫定
    # if intHolidaytime == 0 or worktime == 0:
    #     messagebox.showerror('エラー', '社員番号:' + str(self.staffid) + '\nのD_JOB_HISTORYのCONTRACT_CODEが登録されていません')

    """
        終業時間 - 開始時間 - 時間休
        @Return: timedelta
        """

    def get_times_rest(self) -> timedelta:
        work_time = self.calc_actual_work_time()
        if self.n_node_list[0] or self.n_code_list[3]:
            return work_time - timedelta(hours=1)
        elif self.n_node_list[1] or self.n_code_list[4]:
            return work_time - timedelta(hours=2)
        elif self.n_node_list[2] or self.n_code_list[5]:
            return work_time - timedelta(hours=3)

    """ ここが課題 """
    # 休憩分を引く
    # if self.t - timedelta(hours=rest) >= timedelta(hours=6):
    #     self.t = self.t - timedelta(hours=1)  # ６時間以上は休憩１時間を引く
    #     self.real_time = self.real_time - timedelta(hours=1)
    # elif self.t - timedelta(hours=rest) >= timedelta(hours=5):
    #     self.t = self.t - timedelta(minutes=45)  # ５時間以上は休憩４５分を引く
    #     self.real_time = self.real_time - timedelta(minutes=45)

    """
        (終業時間 - 開始時間) + 契約時間
        or 契約時間
        @Return: timedelta
        """

    # 半日出張、半休、生理休暇かつ打刻のある場合
    def get_half_rest(self) -> timedelta:
        contract = db.session.get(KinmuTaisei, self.staffid)
        # 有休と実働合わせて契約時間より上
        working_time = self.calc_actual_work_time()
        working_plus_half_time = working_time + timedelta(hours=contract.WORKTIME / 2)
        if working_plus_half_time > timedelta(hours=contract.WORKTIME):
            if self.sh_overtime == "1":  # 残業した場合
                return working_plus_half_time
                # self.over_time_0.append(self.t.seconds - worktime / 2 * 60 * 60)
                # self.real_time_sum.append(self.real_time.seconds)
            else:
                return contract.WORKTIME
                # self.real_time_sum.append(self.real_time.seconds)
        else:
            return working_plus_half_time
            # self.real_time_sum.append(self.real_time.seconds)

    """
        残業なし: 契約時間
        残業あり: 終業時間 - 開始時間
        @Return: timedelta
        """

    def check_over_work(self) -> Union[float, timedelta]:
        input_working_time = self.calc_actual_work_time()
        contract_work_time, contract_holiday_time = self.get_work_and_holiday_time()
        if input_working_time > timedelta(hours=contract_work_time):
            if self.sh_overtime == "0":
                return contract_work_time
            elif self.sh_overtime == "1":  # 残業した場合
                return input_working_time
                # self.over_time_0.append(self.t.seconds - worktime * 60 * 60)
        else:
            raise Exception("申請あり")

    # 実働時間
    # check_over_work() - get_times_rest()

    # def convert_second(self, *notification: str) -> Tuple[timedelta, timedelta]:
    #     # 契約時間及び終業時間 - 開始時間
    #     the_working_time = self.check_over_work()
    #     # 所謂リアル実働時間（ - 時間休[10, 11, 12, 13, 14, 15]）
    #     the_real_time = the_working_time - self.get_times_rest(notification)

    #     second_work_time = the_working_time * 60 * 60

    #     return second_work_time, the_real_time.seconds

    # if "申請なしの場合":
    #     self.real_time_sum.append(second_work_time)
    # else:
    #     self.real_time_sum.append(the_real_time.seconds)
    # 残業分リスト
    # over_time_list = []
    # over_time_list.append(the_real_time.seconds - second_work_time)

    def calc_nurse_holiday_working(self) -> List[timedelta]:
        # 祝日(2)、もしくはNSで土日(1)
        holiday_work_list = []
        job_type = db.session.get(Jobtype, self.staffid)
        contract = db.session.get(KinmuTaisei, self.staffid)
        the_working_time = self.check_over_work()
        if (
            self.sh_holiday == "2"
            or self.sh_holiday == "1"
            and job_type.JOBTYPE_CODE == 1
            and contract.CONTRACT_CODE == 2
        ):
            holiday_work_list.append(the_working_time * 60 * 60)

            return holiday_work_list

    # 9: 慶弔 congratulations and condolences
    def change_notify_method(self, *notification: str) -> Union[timedelta, float]:
        contract = db.session.get(KinmuTaisei, self.staffid)
        if notification.in_(self.n_code_list):
            self.get_times_rest()
        elif notification.in_(self.n_half_list):
            self.get_half_rest()
        elif notification == "9":
            return contract.WORKTIME

    # 打刻は00:00で
    def get_zero_time_notification(self) -> float:
        contract = db.session.get(KinmuTaisei, self.staffid)
        if self.sh_starttime == "00:00" and self.sh_endtime == "00:00":
            # 全日年休、出張全日の場合
            if self.sh_notification == "3" or self.sh_notification == "5":
                return contract.WORKTIME
            else:
                raise Exception("契約勤務時間未満です")


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
