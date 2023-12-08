from __future__ import annotations
from datetime import datetime
from typing import List
from abc import ABC, abstractmethod

from app.holiday_observer import Observer


class Subject(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        pass

    @abstractmethod
    def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        pass

    def acquire_holidays(self) -> bool:
        raise NotImplementedError

    def execute(self) -> None:
        raise NotImplementedError


class SubjectImpl(Subject):
    """
    The Subject owns some important state and notifies observers when the state
    changes.
    """

    _state: int = None
    """
    For the sake of simplicity, the Subject's state, essential to all
    subscribers, is stored in this variable.
    """

    _observers: List[Observer] = []
    """
    List of subscribers. In real life, the list of subscribers can be stored
    more comprehensively (categorized by event type, etc.).
    """

    def attach(self, observer: Observer) -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    """
    The subscription management methods.
    """

    def notify(self) -> None:
        """
        Trigger an update in each subscriber.
        """

        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    def acquire_holidays(self) -> bool:
        now = datetime.now()
        if (now.month == 10 and now.day == 1) or (now.month == 4 and now.day == 1):
            return True
        else:
            return False
        # return super().acquire_holidays()

    def execute(self) -> None:
        self.notify_observer()
        return super().execute()
