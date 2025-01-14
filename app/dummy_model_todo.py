from __future__ import annotations
from typing import TYPE_CHECKING
import re
from datetime import datetime

from flask_login import LoginManager

from app import db

# ImportError: cannot import name 'Team' from partially initialized module
# 'app.models' (most likely due to a circular import)
# (/home/nabu_dvl/wade2area/covered_kintai/app/models.py)
# from app.models import Team

# from app.auth_middleware import get_user_group

# NameError: name 'Team' is not defined
# if TYPE_CHECKING:
#     from app.models import StaffLoggin

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

    # def __init__(self, team: Team):
    #     self.team = team

    # SQLAlchemyでクラスオブジェクトを辞書型(dictionary)に変換する方法
    # https://qiita.com/hayashi-ay/items/4dc431003e7866d2aff8
    def to_dict(self):
        # def to_dict(self, group_name: str):
        # rp_start = str(self.start_time).replace(" ", "T")
        # rp_end = str(self.end_time).replace(" ", "T")
        # re_start = re.sub(r"$", ".000Z", rp_start)
        # re_end = re.sub(r"$", ".000Z", rp_end)
        f = "%Y-%m-%dT%H:%M:%S.000Z"
        # group = get_user_group(self.staff_id)
        # group = Team(self.group_id)
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "group": self.group_id,
            # "group": group_name,
            "start": datetime.strftime(self.start_time, f),
            "end": datetime.strftime(self.end_time, f),
            # "start_time": self.start_time,
            # "end_time": self.end_time,
            "title": self.title,
            "summary": self.summary,
            "progress": self.progress,
        }
