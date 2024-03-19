from __future__ import annotations
from typing import TYPE_CHECKING

from flask_login import LoginManager

from app import db

if TYPE_CHECKING:
    from app.models import StaffLoggin

login_manager = LoginManager()
# login_manager.init_app(app)


class TodoOrm(db.Model):
    __tablename__ = "T_TODO"

    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
    staff_id = db.Column(db.Integer)
    group_id = db.Column(db.Integer, db.ForeignKey("M_TEAM.CODE"), nullable=False)
    summary = db.Column(db.String(50), index=True, nullable=True)
    # owner = db.Column(db.String(20), index=True, nullable=True)
    done = db.Column(db.String(25), index=True, nullable=True)

    def __init__(self, staff_id):
        self.staff_id = staff_id

    # @login_manager.user_loader
    def to_dict(self):
        return {
            "staff_id": self.staff_id,
            "group_id": self.group_id,
            "summry": self.summary,
            # "owner": self.owner,
            "done": self.done,
        }


class EventORM(db.Model):
    __tablename__ = "T_TIMELINE_EVENT"

    id = db.Column(db.Integer, primary_key=True, index=True)
    staff_id = db.Column(
        db.Integer, db.ForeignKey("M_LOGGININFO.STAFFID"), nullable=False
    )
    group_id = db.Column(db.Integer, db.ForeignKey("M_TEAM.CODE"), nullable=False)
    start_time = db.Column(db.Date(), nullable=False)
    end_time = db.Column(db.Date(), nullable=False)
    title = db.Column(db.String(25), index=True, nullable=False)
    summary = db.Column(db.String(50), nullable=True)
    progress = db.Column(db.String(25), index=True, nullable=True)

    def __init__(self, staff_id):
        self.staff_id = staff_id

    def to_dict(self):
        return {
            "staff_id": self.staff_id,
            "group_id": self.group_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "title": self.title,
            "summry": self.summary,
            "progress": self.progress,
        }
