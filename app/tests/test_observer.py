import pytest

from app.holiday_subject import SubjectImpl
from app.holiday_observer import ObserverImpl


def test_observer():
    subject = SubjectImpl()
    observer = ObserverImpl()

    subject.attach(observer)

    print(subject.acquire_holidays())
