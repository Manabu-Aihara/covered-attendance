from datetime import datetime
from app import db


class Approval(db.Model):
    __tablename__ = "M_APPROVAL"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    STAFFID = db.Column(
        db.Integer, db.ForeignKey("M_STAFFINFO.STAFFID"), index=True, nullable=False
    )
    TEAM_CODE = db.Column(
        db.Integer, db.ForeignKey("M_TEAM.CODE"), index=True, nullable=False
    )
    TYPE = db.Column(db.String(10), index=True, nullable=False)
    GROUPNAME = db.Column(db.String(50), nullable=False)

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID
        # self.TYPE = TYPE
        # self.GROUPNAME = GROUPNAME


class NotificationList(db.Model):
    __tablename__ = "D_NOTIFICATION_LIST"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    STAFFID = db.Column(
        db.Integer, db.ForeignKey("M_STAFFINFO.STAFFID"), index=True, nullable=False
    )
    NOTICE_DAYTIME = db.Column(db.DateTime(), index=True, default=datetime.now())
    N_CODE = db.Column(
        db.Integer, db.ForeignKey("M_NOTIFICATION.CODE"), index=True, nullable=False
    )
    STATUS = db.Column(db.Integer, index=True, nullable=False, default=0)
    START_DAY = db.Column(db.Date)
    START_TIME = db.Column(db.Time, nullable=True)
    END_DAY = db.Column(db.Date, nullable=True)
    END_TIME = db.Column(db.Time, nullable=True)
    REMARK = db.Column(db.String(255))

    def __init__(
        self,
        STAFFID,
        NOTICE_DAYTIME,
        N_CODE,
        START_DAY,
        START_TIME,
        END_DAY,
        END_TIME,
        REMARK,
    ):
        self.STAFFID = STAFFID
        self.NOTICE_DAYTIME = NOTICE_DAYTIME
        self.N_CODE = N_CODE
        self.START_DAY = START_DAY
        self.START_TIME = START_TIME
        self.END_DAY = END_DAY
        self.END_TIME = END_TIME
        self.REMARK = REMARK


class PaidHolidayModel(db.Model):
    __tablename__ = "M_PAIDHOLIDAY"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    STARTDAY = db.Column(db.Date, primary_key=True, nullable=False)
    ENDDAY = db.Column(db.Date, primary_key=True, nullable=False)
    paid_holiday = db.Column(db.Integer, nullable=False)
    carry_forward = db.Column(db.Integer)

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID
