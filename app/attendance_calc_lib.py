from datetime import date
from typing import List
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select

from app.models import Shinsei, D_JOB_HISTORY
from app.database_async import get_session
from app.calc_work_classes2 import CalcTimeFactory


@dataclass
class PandaCatPandas:
    staff_id: int
    from_day: date
    to_day: date

    def get_filter(self) -> list:
        attendance_filters = []
        attendance_filters.append(Shinsei.STAFFID == self.staff_id)
        attendance_filters.append(Shinsei.WORKDAY.between(self.from_day, self.to_day))
        return attendance_filters

    async def calc_attendance_of_month(self):

        filter = self.get_filter()
        stmt = (
            select(Shinsei, D_JOB_HISTORY.CONTRACT_CODE)
            .filter(*filter)
            .join(D_JOB_HISTORY, D_JOB_HISTORY.STAFFID == Shinsei.STAFFID)
        )
        async with get_session() as session:
            month_attend_query = await session.execute(statement=stmt)
            month_attend_list = [r for r in month_attend_query.scalars().all()]

        calc_time_factory = CalcTimeFactory()
        n_absence_list: List[str] = ["8", "17", "18", "19", "20"]

        actual_time_sum: float = 0.0
        real_work_times = []
        nurse_holiday_works = []
        over_times = []

        # 【項目7】オンコール平日
        on_call_cnt: int = 0
        # 【項目8】オンコール休日
        on_call_holiday_cnt: int = 0
        # 【項目9】オンコール対応
        on_call_cnt_cnt: int = 0
        # 【項目10】エンゼル対応
        engel_int_cnt: int = 0

        # 【項目15】年休全日
        holiday_cnt: int = 0
        # 【項目16】年休半日
        half_holiday_cnt: int = 0
        # 【項目19】遅刻
        late_cnt: int = 0
        # 【項目20】早退
        leave_early_cnt: int = 0
        # 【項目21】欠勤
        absence_cnt: int = 0
        # 【項目24】出張全日
        trip_cnt: int = 0
        # 【項目25】出張半日
        half_trip_cnt: int = 0
        # 【項目26】リフレッシュ
        reflesh_cnt: int = 0
        # 【項目27】走行距離
        distance_sum: float = 0.0

        # 【項目28】時間休
        timeoff: int = 0
        # 【項目29】中抜け
        halfway_through: int = 0

        for month_attend in month_attend_list:
            on_call_holiday_cnt += (
                1
                if month_attend.ONCALL != "0"
                and month_attend.WORKDAY.weekday() in [5, 6]
                else 0
            )
            on_call_cnt += (
                1
                if month_attend.ONCALL != "0"
                and month_attend.WORKDAY.weekday() not in [5, 6]
                else 0
            )
            on_call_cnt_cnt += (
                int(month_attend.ONCALL_COUNT)
                if not isinstance(month_attend.ONCALL_COUNT, type(None))
                and month_attend.ONCALL_COUNT != ""
                and month_attend.ONCALL_COUNT != "0"
                else 0
            )
            engel_int_cnt += (
                int(month_attend.ENGEL_COUNT)
                if not isinstance(month_attend.ENGEL_COUNT, type(None))
                and month_attend.ENGEL_COUNT != ""
                and month_attend.ENGEL_COUNT != "0"
                else 0
            )
            distance_sum += (
                float(month_attend.MILEAGE)
                if not isinstance(month_attend.MILEAGE, type(None))
                and month_attend.MILEAGE != ""
                and month_attend.MILEAGE != "0.0"
                else 0
            )
            # print(
            #     f"Inner Count log: {on_call_cnt} {on_call_cnt_cnt} {on_call_holiday_cnt} {engel_int_cnt}"
            # )

            holiday_cnt += 1 if month_attend.NOTIFICATION == "3" else 0
            half_holiday_cnt += (
                1
                if month_attend.NOTIFICATION == "4" or month_attend.NOTIFICATION2 == "4"
                else 0
            )
            late_cnt += (
                1
                if month_attend.NOTIFICATION == "1" or month_attend.NOTIFICATION2 == "1"
                else 0
            )
            leave_early_cnt += (
                1
                if month_attend.NOTIFICATION == "2" or month_attend.NOTIFICATION2 == "2"
                else 0
            )
            absence_cnt += 1 if month_attend.NOTIFICATION in n_absence_list else 0
            trip_cnt += 1 if month_attend.NOTIFICATION == "5" else 0
            half_trip_cnt += (
                1
                if month_attend.NOTIFICATION == "6" or month_attend.NOTIFICATION2 == "6"
                else 0
            )
            reflesh_cnt += 1 if month_attend.NOTIFICATION == "7" else 0
            # print(
            #     f"Inner Count log: {holiday_cnt} {half_holiday_cnt} {late_cnt} {leave_early_cnt} {absence_cnt} {trip_cnt} {half_trip_cnt}"
            # )

            real_time_sum_append = real_work_times.append
            over_time_append = over_times.append
            nurse_holiday_append = nurse_holiday_works.append
            # setting_time.staff_id = month_attend.STAFFID
            # setting_time.sh_starttime = month_attend.STARTTIME
            # setting_time.sh_endtime = month_attend.ENDTIME
            # setting_time.notifications = (
            #     month_attend.NOTIFICATION,
            #     month_attend.NOTIFICATION2,
            # )
            # setting_time.sh_overtime = month_attend.OVERTIME
            # setting_time.sh_holiday = month_attend.HOLIDAY
            setting_time = calc_time_factory.get_instance(month_attend.STAFFID)
            setting_time.set_data(
                month_attend.STARTTIME,
                month_attend.ENDTIME,
                (month_attend.NOTIFICATION, month_attend.NOTIFICATION2),
                month_attend.OVERTIME,
                month_attend.HOLIDAY,
            )

            print(f"ID: {month_attend.STAFFID}")
            actual_work_time = setting_time.get_actual_work_time()
            calc_real_time = setting_time.get_real_time()
            over_time = setting_time.get_over_time()
            nurse_holiday_work_time = setting_time.calc_nurse_holiday_work()
            # except TypeError as e:
            #     msg = f"{e}: {month_attend.STAFFID}"
            #     return render_template(
            #         "error/403.html", title="Exception message", message=msg
            #     )
            # else:
            # real_time_sum.append(calc_real_time)
            real_time_sum_append(calc_real_time)
            if month_attend.OVERTIME == "1" and month_attend.CONTRACT_CODE != 2:
                # over_time_0.append(over_time)
                over_time_append(over_time)
            if nurse_holiday_work_time != 9.99:
                # syukkin_holiday_times_0.append(nurse_holiday_work_time)
                nurse_holiday_append(nurse_holiday_work_time)

            print(f"{month_attend.WORKDAY.day} 日")
            print(f"Real time: {calc_real_time}")
            print(f"Actual time: {actual_work_time}")
            print(f"In real time list: {real_work_times}")
            print(f"In over time list: {over_times}")
            print(f"Nurse holiday: {nurse_holiday_works}")

            ##### データベース貯蔵 #####

            # ここで宣言された変数は“+=”不可
            # work_time_sum_60: float = 0.0
            # 🙅 work_time_sum_60 += AttendanceDada[month_attend.WORKDAY.day][14]

            actual_second = actual_work_time.total_seconds()
            workday_count += 1 if actual_second != 0.0 else 0

            actual_time_sum += actual_second
            time_sum_normal = actual_time_sum / 3600
            # 実働時間計：10進数
            time_sum_rnd = Decimal(time_sum_normal).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

            w_h = time_sum // (60 * 60)
            w_m = (time_sum - w_h * 60 * 60) // 60
            # 実労働時間計：60進数
            time_sum60 = w_h + w_m / 100

            # for n in range(len(real_time_sum)):
            #     real_sum += real_time_sum[n]
            real_sum: int = sum(real_time_sum)
            w_h = real_sum // (60 * 60)
            w_m = (real_sum - w_h * 60 * 60) // 60
            # リアル労働時間計：60進数
            real_time = w_h + w_m / 100
            # real_time_10 = real_sum / (60 * 60)

            # for n in range(len(over_time_0)):
            #     if not over_time_0[n]:
            #         sum_over_0 = sum_over_0
            #     else:
            #         sum_over_0 += over_time_0[n]
            sum_over_0: int = sum(over_time_0)
            o_h = sum_over_0 // (60 * 60)
            o_m = (sum_over_0 - o_h * 60 * 60) // 60
            # 残業時間計：60進数
            over_60 = o_h + o_m / 100

            over_10 = sum_over_0 / (60 * 60)
            # 残業時間計：10進数
            over10_rnd = Decimal(over_10).quantize(Decimal("0.01"), ROUND_HALF_UP)

            # for t in syukkin_holiday_times_0:
            #     sum_hol_0 += t
            sum_hol_0: int = sum(syukkin_holiday_times_0)
            h_h = sum_hol_0 // (60 * 60)
            h_m = (sum_hol_0 - h_h * 60 * 60) // 60
            # 看護師休日労働時間計：60進数
            holiday_work_60 = h_h + h_m / 100

            # 看護師休日労働時間計：10進数
            holiday_work_10 = sum_hol_0 / (60 * 60)
            holiday_work10_rnd = Decimal(holiday_work_10).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

            sum_dict: Dict[str, int] = output_rest_time(
                month_attend.NOTIFICATION, month_attend.NOTIFICATION2
            )
            timeoff += sum_dict.get("Off")
            halfway_through += sum_dict.get("Through")
