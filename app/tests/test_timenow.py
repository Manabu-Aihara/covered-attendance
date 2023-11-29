import pytest
from datetime import datetime, timezone, timedelta

now = datetime.now()
dt_now_jst = datetime.now(timezone(timedelta(hours=9)))
def test_get_now():
	# with pytest.raises(ValueError) as excinfo:
	# 	now == dt_now_jst
	print(dt_now_jst)
