import pytest
from datetime import date

from app.holiday_acquisition import HolidayAcquire
from app.new_calendar import NewCalendar

@pytest.fixture
def get_official_user(app_context):
	acquisition_object = HolidayAcquire(20)
	return acquisition_object

def test_convert_base_day(get_official_user):
	conv_date = get_official_user.convert_base_day()
	# print(conv_date)
	assert conv_date.month == 10

# @pytest.mark.skip
def test_calcurate_days(get_official_user):
	conv_date = get_official_user.convert_base_day()
	test_date1 = get_official_user.calcurate_days(conv_date)
	print(test_date1)

# おニューカレンダーテスト
@pytest.fixture
def make_new_calendar():
	new_calendar = NewCalendar(2023, 9)
	return new_calendar

@pytest.mark.skip
def test_get_itermonthdays(make_new_calendar):
	result = make_new_calendar.get_itermonthdays()
	print(result)

@pytest.mark.skip
def test_get_month_holidays_num(make_new_calendar):
	print(make_new_calendar.__get_jp_holidays_num())

def test_get_weekday(make_new_calendar):
	print(make_new_calendar.get_weekday())
