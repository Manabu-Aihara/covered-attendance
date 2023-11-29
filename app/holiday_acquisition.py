from datetime import date, datetime
from monthdelta import monthmod
from dataclasses import dataclass
from typing import Tuple, List
from dateutil.relativedelta import relativedelta

from app.models import User

@dataclass
class HolidayAcquire:
	id: int
	# aquisition_days: int

	def __post_init__(self):
		target_user = User.query.filter(User.STAFFID==self.id).first()
		self.in_day: date = target_user.INDAY

	# acquire: 日数
	# get: 日付
	def convert_base_day(self) -> date:
		##### 基準月に変換 #####
		#     入社日が4月〜9月
		#     10月1日に年休付与
		if self.in_day.month >= 4 and self.in_day.month < 10:
			change_day = self.in_day.replace(month=10, day=1) # 基準月
			return change_day  # 初回付与日
		
		#     入社日が10月〜12月
		#     翌年4月1日に年休付与
		elif self.in_day.month >= 10 and self.in_day.month <= 12:
			change_day = self.in_day.replace(month=4, day=1)
			return change_day + relativedelta(months=12)
		
		#     入社日が1月〜3月
		#     4月1日に年休付与
		elif self.in_day.month < 4:
			change_day = self.in_day.replace(month=4, day=1)
			return change_day
	
	# 付与日のリストを返す（一日足りないか？）
	def calcurate_days(self, base_day: date) -> List[datetime]:
		self.holidays_get_list = []
		while base_day < datetime.today():
			self.base_day = base_day + relativedelta(months=12)
			self.holidays_get_list.append(self.base_day)
			# 無限ループ
			if datetime.today() < self.base_day:
				break
			return self.holidays_get_list + self.calcurate_days(self.base_day)

		return self.holidays_get_list
		# return self.holidays_get_list[-1].date()

	# おそらくこれも次回付与日を求める
	def get_next_holiday(self):
		base_day = self.convert_base_day()

		next_acquire_day = date(date.today().year, base_day.month, 1)
		return next_acquire_day
										
	def acquire_start_holidays(self):
		self.given_holidays = []

		base_day = self.convert_base_day()
		if date.today() < base_day: #and monthmod(date.today(), base_day)[0].months < 6:
			if monthmod(self.in_day, base_day)[0].months <= 2:
				self.aquisition_days = 2
			elif monthmod(self.in_day, base_day)[0].months <= 3:
				self.aquisition_days = 1
			elif monthmod(self.in_day, base_day)[0].months > 3:
				self.aquisition_days = 0

		# diff_month_today = monthmod(self.in_day, datetime.today())[0].months
		diff_month_lastday = monthmod(self.in_day, self.calcurate_days(base_day))[0].months
	def plus_holiday(self) -> int:
		base_day = self.convert_base_day()

		if base_day == date.today():
			self.aquisition_days += 10
			