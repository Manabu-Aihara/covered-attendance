import enum
from typing import Tuple
from datetime import date
from dataclasses import dataclass
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

from app.models import RecordPaidHoliday
from app.holiday_acquisition import HolidayAcquire


# コンストラクタを作って、その引数に、各項目に与えた値の
# 1つめ、2つめ、3つめが何を意味しているか名前を与えて、
# インスタンス変数に格納して上げると、特にインスタンスを作らなくても、
# アクセス出来るようになります。
# https://note.com/yucco72/n/ne69ea7fb26e7
class AcquisitionType(enum.Enum):
    A = (list(range(10, 12)) + list(range(12, 20, 2)), 20)  # 以降20
    B = ([7, 8, 9, 10, 12, 13], 15)  # 以降15
    C = ([5, 6, 6, 8, 9, 10], 11)  # 以降11
    D = ([3, 4, 4, 5, 6, 6], 7)  # 以降7
    E = ([1, 2, 2, 2, 3, 3], 3)  # 以降3

    def __init__(self, under5y: list, onward: int):
        super().__init__()
        self.under5y = under5y
        self.onward = onward

    @classmethod
    def name(cls, name: str) -> str:
        return cls._member_map_[name]


@dataclass
class AcquisitionTypeClass:
    # スタッフID
    id: int

    # 勤務形態 Acqisition.Aといった形式で指定
    # work_type: AcquisitionType
    def __post_init__(self):
        self.acquisition_key: str = (
            RecordPaidHoliday.query.with_entities(RecordPaidHoliday.ACQUISITION_TYPE)
            .filter(self.id == RecordPaidHoliday.STAFFID)
            .first()
        )[0]

    """
    入職日＋以降の年休付与日数
    @Param
        frame: AcquisitionType  勤務形態
    @Return
        holiday_pair: OrderedDict<date, int>
    """

    def plus_next_holidays(self) -> OrderedDict[date, int]:
        acquisition_obj = HolidayAcquire(self.id)
        base_day = acquisition_obj.convert_base_day()
        day_list = [
            acquisition_obj.in_day.date()
        ] + acquisition_obj.get_acquisition_list(base_day)
        holiday_pair = acquisition_obj.acquire_start_holidays()

        for i, acquisition_day in enumerate(
            AcquisitionType.name(self.acquisition_key).under5y
        ):
            if i == len(day_list) - 1:
                break
            else:
                holiday_pair[day_list[i + 1]] = acquisition_day

        if len(day_list) > len(AcquisitionType.name(self.acquisition_key).under5y):
            for day in day_list[7:]:
                holiday_pair[day] = AcquisitionType.name(self.acquisition_key).onward

        return holiday_pair

    """
    @Param
        staff_id: int
        carry_days: date
    @Return
        残り時間: float
        """

    def get_sum_holiday(self) -> float:
        holiday_dict = self.plus_next_holidays()
        holiday_list = []
        # holiday_dict.valuesは取得付与日数リスト
        for holiday in holiday_dict.values():
            holiday_list.append(holiday)

        # 2年遡っての日数（2年消滅）
        default_sum_holiday: int = (
            sum(holiday_list[-3:-1])
            if len(holiday_list) >= 3
            else sum(holiday_list[:-1])
        )

        acquisition_obj = HolidayAcquire(self.id)
        # 残り総合計時間
        sum_times: float = default_sum_holiday * (acquisition_obj.job_time)
        return sum_times

    # STARTDAY,ENDDAYのペア
    def print_acquisition_data(self) -> Tuple[list[date], list[date]]:
        # 取得日、日数のペア
        holiday_dict = self.plus_next_holidays()

        end_day_list = [
            end_day + relativedelta(years=1, days=-1) for end_day in holiday_dict.keys()
        ]

        return (list(holiday_dict.keys()), end_day_list)
