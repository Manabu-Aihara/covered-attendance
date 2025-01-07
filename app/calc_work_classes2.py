"""
**********
勤怠システム
2022/04版
**********
"""

import os, math
import syslog
from functools import wraps
from typing import Dict, List, Optional
from dataclasses import dataclass, field, InitVar
from abc import ABCMeta
from functools import lru_cache
from datetime import datetime, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
import calendar
import jpholiday

from flask_login import current_user, login_user

from app import app, db
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


@dataclass
class ContractTimeClass:
    # staff_id: Optional[int]
    # staff_id: InitVar[int]

    @staticmethod
    @lru_cache
    def get_contract_times(staff_id: int) -> tuple[float]:
        # if staff_id is None:
        #     print(f"---Parent func---: {staff_id}")
        #     return
        # 必要なデータを一度のクエリで取得
        you = db.session.get(User, staff_id)
        contract = db.session.get(KinmuTaisei, you.CONTRACT_CODE)

        # 基本の契約時間を設定
        contract_work_time = contract.WORKTIME
        contract_holiday_time = contract.WORKTIME

        if contract.CONTRACT_CODE != 2:
            return contract_work_time, contract_holiday_time

        # パートタイム契約（CONTRACT_CODE == 2）の場合のみ追加処理
        related_holiday = db.session.get(RecordPaidHoliday, staff_id)
        paid_holiday_time = related_holiday.BASETIMES_PAIDHOLIDAY

        # 最新の契約労働・休暇を1回のクエリで取得
        part_contract_work = (
            db.session.query(D_JOB_HISTORY)
            .filter(D_JOB_HISTORY.STAFFID == staff_id)
            .order_by(D_JOB_HISTORY.START_DAY.desc())
            .first()
        )
        part_contract_holiday = (
            db.session.query(D_HOLIDAY_HISTORY)
            .filter(D_HOLIDAY_HISTORY.STAFFID == staff_id)
            .order_by(D_HOLIDAY_HISTORY.START_DAY.desc())
            .first()
        )

        # if related_holiday is None:
        #     raise TypeError("There is not in D_HOLIDAY_HISTORY")
        # 契約時間を更新
        contract_work_time = (
            part_contract_work.PART_WORKTIME
            if part_contract_work.PART_WORKTIME is not None
            else paid_holiday_time
        )
        contract_holiday_time = (
            part_contract_holiday.HOLIDAY_TIME
            if part_contract_holiday is not None
            else paid_holiday_time
        )

        return contract_work_time, contract_holiday_time

    # オブジェクトがハッシュ可能であるか判定する.
    @staticmethod
    def hashable(x):
        try:
            hash(x)
            return True
        except TypeError:
            return False


# ***** 常勤用各勤怠時間計算ひな形 *****#
@dataclass
class CalcTimeClass:
    # staff_id: Optional[int]  # = field(default=None, init=False)
    # sh_starttime: str  # = field(init=False)
    # sh_endtime: str  # = field(init=False)
    # notifications: tuple[str]  # = field(init=False)
    # sh_overtime: str  # = field(init=False)
    # sh_holiday: str  # = field(init=False)
    staff_id: InitVar[int]  # = None

    n_code_list: List[str] = field(
        default_factory=lambda: ["10", "11", "12", "13", "14", "15"]
    )
    n_half_list: List[str] = field(default_factory=lambda: ["4", "9", "16"])
    n_absence_list: List[str] = field(
        default_factory=lambda: ["8", "17", "18", "19", "20"]
    )

    # def pre_method(self, staff_id: int):
    #     return ContractTimeClass.get_contract_times(staff_id)

    # あるとすれば、これはどこのタイミング？
    def __post_init__(self, staff_id: int):
        if staff_id is None:
            return

        # どっちでもいい
        # self.n_code_list: List[str] = ["10", "11", "12", "13", "14", "15"]
        # self.n_half_list: List[str] = ["4", "9", "16"]
        # print(f"---Child init---: {self.pre_method(staff_id=staff_id)}")
        contract_times = ContractTimeClass.get_contract_times(staff_id)

        self.half_work_time = timedelta(hours=contract_times[0] / 2)
        self.half_holiday_time = timedelta(hours=contract_times[1] / 2)
        self.full_work_time = timedelta(hours=contract_times[0])
        self.full_holiday_time = timedelta(hours=contract_times[1])
        self.staff_id = staff_id

    def set_data(
        self,
        sh_starttime: str,
        sh_endtime: str,
        notifications: tuple[str],
        sh_overtime: str,
        sh_holiday: str,
    ):
        self.sh_starttime = sh_starttime
        self.sh_endtime = sh_endtime
        self.notifications = notifications
        self.sh_overtime = sh_overtime
        self.sh_holiday = sh_holiday

    # 今のところお昼だけ採用
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

    """
        労働時間は2パターン
        1. self.full_work_time()
        2. calc_base_work_time() - calc_normal_rest_time(...)
        """

    # 実働時間の算出
    def calc_base_work_time(self) -> timedelta:
        # self.jobtype != 12
        start_time_hm = datetime.strptime(self.sh_starttime, "%H:%M")
        end_time_hm = datetime.strptime(self.sh_endtime, "%H:%M")
        d = datetime.now().date()
        if self.sh_starttime != "00:00" and start_time_hm < datetime.strptime(
            "08:00", "%H:%M"
        ):
            start_time_hm = time(hour=8, minute=0)

            input_work_time = datetime.combine(
                d, end_time_hm.time()
            ) - datetime.combine(d, start_time_hm)

            return input_work_time
        # elif self.sh_starttime != "00:00" and (start_time_hm.minute != 0):
        #     start_time_hm = self.round_up_time()
        else:
            input_work_time = end_time_hm - start_time_hm
            return input_work_time

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
        - 契約時間 / 2 or 0
        if irregular（契約時間未満のとき）:
            契約時間 - 入力時間
        @Return: timedelta
        """

    # 半日出張、半休、生理休暇かつ打刻のある場合
    def provide_half_rest(self) -> timedelta:
        # print(f"Start inner method: {self.full_work_time}")
        input_time = self.calc_base_work_time()
        working_time = input_time - self.calc_normal_rest(input_time)

        # 承認時間のリストを作成する処理を最適化
        approval_count = sum(
            1 for n in self.notifications if n in self.n_half_list or n == "6"
        )

        if approval_count == 0:
            return (
                self.full_work_time - working_time
                # irregular
                if working_time < self.full_work_time
                else timedelta(0)
            )
        elif approval_count == 1:
            return (
                self.full_work_time - input_time
                # irregular
                if input_time < self.half_work_time
                else (
                    self.half_work_time
                    if "6" in self.notifications
                    else self.half_holiday_time
                )
            )
        else:  # approval_count == 2
            return self.half_work_time + self.half_holiday_time

    """
        @Return: timedelta
            1.残業あり → 終業時間 - 開始時間 - 通常の休憩時間
            2.残業なし → 契約時間
            3.残業なしで半日申請あり → 契約時間 - (契約休み時間 / 2)
            4.irregular → 契約時間or入力時間 - (契約時間 - 入力時間)
        """

    def check_over_work(self) -> timedelta:
        input_work_time = self.calc_base_work_time()
        if self.sh_overtime == "0":
            working_time = (
                self.full_work_time
                - self.provide_half_rest()
                # - self.calc_normal_rest(input_work_time)
            )
            # 契約時間 / 2 or 契約時間 or irregular
            return working_time
        elif self.sh_overtime == "1":  # 残業した場合
            work_without_time_rest = input_work_time - self.calc_normal_rest(
                input_work_time
            )
            print(f"△Over without rest: {work_without_time_rest}")
            return work_without_time_rest

    """
        実働時間表示
        遅刻、早退では反映
        欠勤では0時間
        @Return: timedelta
        """

    # 9: 慶弔 congratulations and condolences
    def get_actual_work_time(self) -> timedelta:
        input_work_time = self.calc_base_work_time()
        print(f"△Actual second: {input_work_time.total_seconds()}")
        for notification in self.notifications:
            if notification == "5":
                return self.full_work_time
            elif notification == "3" or (
                notification == "9" and self.sh_starttime == "00:00"
            ):
                return self.full_holiday_time
            elif notification in self.n_absence_list:
                return timedelta(0)
            else:
                print(f"△check!: {self.provide_half_rest()}")
                return (
                    input_work_time
                    + (
                        # 申請貼れば、irregular数値は返さない
                        self.provide_half_rest()
                        if notification in self.n_half_list + ["6"]
                        else timedelta(0)
                    )
                    - self.calc_normal_rest(input_work_time)
                )

    """
        残業分
        @Return: float
        """

    def get_over_time(self) -> float:
        working_time = self.check_over_work()
        # パートはありません
        over_time_in_work = working_time - (
            self.full_work_time - self.provide_half_rest()
        )
        return over_time_in_work.total_seconds()

    """
        @Return: float
            半日申請、残業と諸々処理した後 - 時間休
        """

    # リアル実働時間（労働時間 - 年休、出張、時間休など）
    def get_real_time(self) -> float:
        working_time = self.check_over_work()
        print(f"△Real time: {working_time}")
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
        nurse_member = db.session.get(User, self.staff_id)
        # if self.holiday == "2" or self.holiday == "1"
        # and self.jobtype == 1 and self.u_contract_code == 2:
        if (
            self.sh_holiday == "2"
            or self.sh_holiday == "1"
            and nurse_member.JOBTYPE_CODE == 1
            and nurse_member.CONTRACT_CODE == 2
        ):
            return self.get_real_time()
        else:
            return 9.99


@dataclass
class CalcTimeFactory:
    _instances: Dict[int, "CalcTimeClass"] = field(default_factory=dict)

    def get_instance(self, staff_id: int) -> "CalcTimeClass":
        if staff_id not in self._instances:
            self._instances[staff_id] = CalcTimeClass(staff_id)
        return self._instances[staff_id]


# ************************************** 時間休カウント ********************************************#


# @lru_cache
def output_rest_time(notification_am: Optional[str], notification_pm: Optional[str]):
    # def output_rest_time(*notifications: str) -> Dict[str, int]:
    n_time_list: List[int] = [1, 2, 3]
    n_off_list: List[str] = ["10", "11", "12"]
    n_through_list: List[str] = ["13", "14", "15"]

    # example: output_rest_time("13", "12")
    # リストのなかのリストは、最後のしか残らない
    # for n in notifications:
    #     off_time_list = [
    #         n_time for n_time, n_off in zip(n_time_list, n_off_list) if n == n_off
    #     ]
    #     through_time_list = [
    #         n_time
    #         for n_time, n_through in zip(n_time_list, n_through_list)
    #         if n == n_through
    #     ]
    #     print(f"Throuth: {through_time_list}")
    # !Result: {'Off': 3, 'Through': 0}
    off_time_list = [
        n_time
        for n_time, n_off in zip(n_time_list, n_off_list)
        if notification_am == n_off or notification_pm == n_off
    ]
    through_time_list = [
        n_time
        for n_time, n_through in zip(n_time_list, n_through_list)
        if notification_am == n_through or notification_pm == n_through
    ]

    return {"Off": sum(off_time_list), "Through": sum(through_time_list)}
