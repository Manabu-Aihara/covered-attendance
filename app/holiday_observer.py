# 循環参照回避
# https://ryry011.hatenablog.com/entry/2021/08/27/155026
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app import db

# 循環参照回避
if TYPE_CHECKING:
    from app.holiday_subject import Subject


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        raise NotImplementedError


class ObserverNotice(Observer):
    def update(self, subject: Subject) -> None:
        notification_state: int = subject.notice_month()
        print(f"Notify!---{notification_state}月年休付与の処理が入ります。---")
        # return super().update(subject)


class ObserverParse(Observer):
    def update(self, subject: Subject) -> None:
        for concerned_id in subject.get_concerned_staff():
            print(subject.acquire_holidays(concerned_id))
        #     db.session.add(subject.acquire_holidays(concerned_id))

        # db.session.commit()
