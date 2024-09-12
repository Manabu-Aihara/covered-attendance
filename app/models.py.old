from enum import unique

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous.url_safe import URLSafeTimedSerializer as Serialize

from app import login
from app import db, app
from app.models_aprv import NotificationList


class User(db.Model):
    __tablename__ = "M_STAFFINFO"
    STAFFID = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    DEPARTMENT_CODE = db.Column(db.Integer, index=True, nullable=True)
    TEAM_CODE = db.Column(db.Integer, index=True, nullable=True)
    CONTRACT_CODE = db.Column(db.Integer, index=True, nullable=True)
    JOBTYPE_CODE = db.Column(db.Integer, index=True, nullable=True)
    POST_CODE = db.Column(db.Integer, index=True, nullable=True)
    LNAME = db.Column(db.String(50), index=True, nullable=True)
    FNAME = db.Column(db.String(50), index=True, nullable=True)
    LKANA = db.Column(db.String(50), index=True, nullable=True)
    FKANA = db.Column(db.String(50), index=True, nullable=True)
    POST = db.Column(db.String(10), index=True, nullable=True)
    ADRESS1 = db.Column(db.String(50), index=True, nullable=True)
    ADRESS2 = db.Column(db.String(50), index=True, nullable=True)
    TEL1 = db.Column(db.String(50), index=True, nullable=True)
    TEL2 = db.Column(db.String(50), index=True, nullable=True)
    BIRTHDAY = db.Column(db.DateTime(), index=True, nullable=True)
    INDAY = db.Column(db.DateTime(), index=True, nullable=True)
    OUTDAY = db.Column(db.DateTime(), index=True, nullable=True)
    STANDDAY = db.Column(db.DateTime(), index=True, nullable=True)
    SOCIAL_INSURANCE = db.Column(db.Integer, index=True, nullable=True)
    EMPLOYMENT_INSURANCE = db.Column(db.Integer, index=True, nullable=True)
    EXPERIENCE = db.Column(db.Integer, index=True, nullable=True)
    TABLET = db.Column(db.Integer, index=True, nullable=True)
    SINGLE = db.Column(db.Integer, index=True, nullable=True)
    SUPPORT = db.Column(db.Integer, index=True, nullable=True)
    HOUSE = db.Column(db.Integer, index=True, nullable=True)
    DISTANCE = db.Column(db.Float, index=True, nullable=True)
    REMARK = db.Column(db.String(100), index=True, nullable=True)
    DISPLAY = db.Column(db.Boolean(), index=True, nullable=False)
    M_LOGGININFOs = db.relationship(
        "StaffLoggin", backref="M_STAFFINFO", lazy="dynamic"
    )
    M_RECORD_PAIDHOLIDAYs = db.relationship(
        "RecordPaidHoliday", backref="M_STAFFINFO", lazy="dynamic"
    )
    D_COUNT_ATTENDANCEs = db.relationship(
        "CountAttendance", backref="M_STAFFINFO", lazy="dynamic"
    )
    D_TIME_ATTENDANCEs = db.relationship(
        "TimeAttendance", backref="M_STAFFINFO", lazy="dynamic"
    )
    D_COUNTER_FOR_TABLEs = db.relationship(
        "CounterForTable", backref="M_STAFFINFO", lazy="dynamic"
    )
    M_SYSTEMINFOs = db.relationship("SystemInfo", backref="M_STAFFINFO", lazy="dynamic")

    """ 2024/8/9 リレーション機能追加 """
    # contract = db.relationship("KinmuTaisei")

    def __init__(self, STAFFID):
        self.STAFFID = STAFFID


class StaffLoggin(UserMixin, db.Model):
    __tablename__ = "M_LOGGININFO"
    id = db.Column(db.Integer, primary_key=True)
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        unique=True,
        index=True,
        nullable=False,
    )
    PASSWORD_HASH = db.Column(db.String(128), index=True, nullable=True)
    ADMIN = db.Column(db.Boolean(), index=True, nullable=True)
    shinseis = db.relationship("Shinsei", backref="M_LOGGININFO", lazy="dynamic")

    def __init__(self, STAFFID, PASSWORD, ADMIN):
        self.STAFFID = STAFFID
        self.PASSWORD_HASH = generate_password_hash(PASSWORD)
        self.ADMIN = ADMIN

    def check_password(self, PASSWORD):
        return check_password_hash(self.PASSWORD_HASH, PASSWORD)

    def is_admin(self):
        return self.ADMIN

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config["SECRET_KEY"], expires_sec)
        return s.dumps({"user_id": self.STAFFID}).decode("utf-8")

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)["user_id"]
        except:
            return None
        return StaffLoggin.query.filter_by(STAFFID=user_id)


class Todokede(db.Model):
    __tablename__ = "M_NOTIFICATION"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(32), index=True, nullable=False)

    def __init__(self, CODE, NAME):
        self.CODE = CODE
        self.NAME = NAME


class Busho(db.Model):
    __tablename__ = "M_DEPARTMENT"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=True)

    def __init__(self, CODE):
        self.CODE = CODE


class KinmuTaisei(db.Model):
    __tablename__ = "M_CONTRACT"
    CONTRACT_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    # CONTRACT_CODE = db.Column(
    #     db.Integer,
    #     db.ForeignKey("M_STAFFINFO.CONTRACT_CODE"),
    #     primary_key=True,
    #     index=True,
    #     nullable=False,
    # )
    NAME = db.Column(db.String(50), index=True, nullable=True)
    SHORTNAME = db.Column(db.String(50), index=True, nullable=False)
    WORKTIME = db.Column(db.Float, nullable=True)

    def __init__(self, CONTRACT_CODE):
        self.CODE = CONTRACT_CODE


class M_TIMECARD_TEMPLATE(db.Model):
    __tablename__ = "M_TIMECARD_TEMPLATE"
    JOBTYPE_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    CONTRACT_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    TEMPLATE_NO = db.Column(db.Integer, index=True, nullable=False)

    def __init__(self, JOBTYPE_CODE, CONTRACT_CODE, TEMPLATE_NO):
        self.JOBTYPE_CODE = JOBTYPE_CODE
        self.CONTRACT_CODE = CONTRACT_CODE
        self.TEMPLATE_NO = TEMPLATE_NO


class D_JOB_HISTORY(db.Model):
    __tablename__ = "D_JOB_HISTORY"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    JOBTYPE_CODE = db.Column(db.Integer, index=True, nullable=False)
    CONTRACT_CODE = db.Column(db.Integer, index=True, nullable=False)
    PART_WORKTIME = db.Column(db.Integer, index=True, nullable=False)
    START_DAY = db.Column(db.Date(), primary_key=True, index=True, nullable=True)
    END_DAY = db.Column(db.Date(), index=True, nullable=True)

    def __init__(
        self, STAFFID, JOBTYPE_CODE, CONTRACT_CODE, PART_WORKTIME, START_DAY, END_DAY
    ):
        self.STAFFID = STAFFID
        self.JOBTYPE_CODE = JOBTYPE_CODE
        self.CONTRACT_CODE = CONTRACT_CODE
        self.PART_WORKTIME = PART_WORKTIME
        self.START_DAY = START_DAY
        self.END_DAY = END_DAY


class D_HOLIDAY_HISTORY(db.Model):
    __tablename__ = "D_HOLIDAY_HISTORY"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    HOLIDAY_TIME = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    START_DAY = db.Column(db.Date(), index=True, nullable=True)
    END_DAY = db.Column(db.Date(), index=True, nullable=True)

    def __init__(self, HOLIDAY_TIME, START_DAY, END_DAY):
        self.HOLIDAY_TIME = HOLIDAY_TIME
        self.START_DAY = START_DAY
        self.END_DAY = END_DAY


class Post(db.Model):
    __tablename__ = "M_POST"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=True)

    def __init__(self, CODE):
        self.CODE = CODE


class Team(db.Model):
    __tablename__ = "M_TEAM"
    CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=False)
    SHORTNAME = db.Column(db.String(50), index=True, nullable=False)

    def __init__(self, CODE):
        self.CODE = CODE


class Jobtype(db.Model):
    __tablename__ = "M_JOBTYPE"
    JOBTYPE_CODE = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    NAME = db.Column(db.String(50), index=True, nullable=False)
    SHORTNAME = db.Column(db.String(50), index=True, nullable=False)

    def __init__(self, JOBTYPE_CODE, NAME, SHORTNAME):
        self.JOBTYPE_CODE = JOBTYPE_CODE
        self.NAME = NAME
        self.SHORTNAME = SHORTNAME


class Shinsei(db.Model):
    __tablename__ = "M_ATTENDANCE"
    id = db.Column(db.Integer, primary_key=True)
    STAFFID = db.Column(db.Integer, db.ForeignKey("M_LOGGININFO.STAFFID"), index=True)
    WORKDAY = db.Column(db.String(32), index=True, nullable=True)
    HOLIDAY = db.Column(db.String(32), index=True, nullable=True)
    STARTTIME = db.Column(db.String(32), index=True, nullable=True)  # 出勤時間
    ENDTIME = db.Column(db.String(32), index=True, nullable=True)  # 退勤時間
    MILEAGE = db.Column(db.String(32), index=True, nullable=True)  # 走行距離
    ONCALL = db.Column(db.String(32), index=True, nullable=True)  # オンコール当番
    ONCALL_COUNT = db.Column(db.String(32), index=True, nullable=True)  # オンコール回数
    ENGEL_COUNT = db.Column(db.String(32), index=True, nullable=True)  # エンゼルケア
    NOTIFICATION = db.Column(db.String(32), index=True, nullable=True)  # 届出（午前）
    NOTIFICATION2 = db.Column(db.String(32), index=True, nullable=True)  # 届出（午後）
    OVERTIME = db.Column(db.String(32), index=True, nullable=True)  # 残業時間申請
    ALCOHOL = db.Column(db.Integer, index=True, nullable=True)
    REMARK = db.Column(db.String(100), index=True, nullable=True)  # 備考

    def __init__(
        self,
        STAFFID,
        WORKDAY,
        HOLIDAY,
        STARTTIME,
        ENDTIME,
        MILEAGE,
        ONCALL,
        ONCALL_COUNT,
        ENGEL_COUNT,
        NOTIFICATION,
        NOTIFICATION2,
        OVERTIME,
        ALCOHOL,
        REMARK,
    ):
        self.STAFFID = STAFFID
        self.WORKDAY = WORKDAY
        self.HOLIDAY = HOLIDAY
        self.STARTTIME = STARTTIME
        self.ENDTIME = ENDTIME
        self.MILEAGE = MILEAGE
        self.ONCALL = ONCALL
        self.ONCALL_COUNT = ONCALL_COUNT
        self.ENGEL_COUNT = ENGEL_COUNT
        self.NOTIFICATION = NOTIFICATION
        self.NOTIFICATION2 = NOTIFICATION2
        self.OVERTIME = OVERTIME
        self.ALCOHOL = ALCOHOL
        self.REMARK = REMARK


class RecordPaidHoliday(db.Model):  # 年休関連
    __tablename__ = "M_RECORD_PAIDHOLIDAY"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    # リレーションが好ましいと思う
    DEPARTMENT_CODE = db.Column(db.Integer, index=True, nullable=True)  # Busho
    LNAME = db.Column(db.String(50), index=True, nullable=True)  # User
    FNAME = db.Column(db.String(50), index=True, nullable=True)  # User
    LKANA = db.Column(db.String(50), index=True, nullable=True)  # User
    FKANA = db.Column(db.String(50), index=True, nullable=True)  # User
    # 入社日
    INDAY = db.Column(db.DateTime(), index=True, nullable=True)  # User

    LAST_DATEGRANT = db.Column(
        db.DateTime(), index=True, nullable=True
    )  # 今回付与年月日
    NEXT_DATEGRANT = db.Column(
        db.DateTime(), index=True, nullable=True
    )  # 次回付与年月日
    USED_PAIDHOLIDAY = db.Column(db.Float, index=True, nullable=True)  # 使用日数
    REMAIN_PAIDHOLIDAY = db.Column(db.Float, index=True, nullable=True)  # 残日数
    TEAM_CODE = db.Column(db.Integer, index=True, nullable=True)
    CONTRACT_CODE = db.Column(db.Integer, index=True, nullable=True)
    LAST_CARRIEDOVER = db.Column(db.Float, index=True, nullable=True)  # 前回繰越日数
    ATENDANCE_YEAR = db.Column(
        db.Integer, index=True, nullable=True
    )  # 年間出勤日数（年休べース）
    WORK_TIME = db.Column(db.Float, index=True, nullable=True)  # 職員勤務時間
    BASETIMES_PAIDHOLIDAY = db.Column(
        db.Float, index=True, nullable=True
    )  # 規定の年休時間


class CountAttendance(db.Model):  ##### 年休用設定での勤務日数ダンプ(ページ表示用)
    __tablename__ = "D_COUNT_ATTENDANCE"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    MONTH_4 = db.Column(db.Float, index=True, nullable=True)
    MONTH_5 = db.Column(db.Float, index=True, nullable=True)
    MONTH_6 = db.Column(db.Float, index=True, nullable=True)
    MONTH_7 = db.Column(db.Float, index=True, nullable=True)
    MONTH_8 = db.Column(db.Float, index=True, nullable=True)
    MONTH_9 = db.Column(db.Float, index=True, nullable=True)
    MONTH_10 = db.Column(db.Float, index=True, nullable=True)
    MONTH_11 = db.Column(db.Float, index=True, nullable=True)
    MONTH_12 = db.Column(db.Float, index=True, nullable=True)
    MONTH_1 = db.Column(db.Float, index=True, nullable=True)
    MONTH_2 = db.Column(db.Float, index=True, nullable=True)
    MONTH_3 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_4 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_5 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_6 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_7 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_8 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_9 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_10 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_11 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_12 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_1 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_2 = db.Column(db.Float, index=True, nullable=True)
    MONTH_HOLIDAY_3 = db.Column(db.Float, index=True, nullable=True)


class TimeAttendance(db.Model):  ##### 実働時間計算結果ダンプ
    __tablename__ = "D_TIME_ATTENDANCE"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    TIME_4 = db.Column(db.Float, index=True, nullable=True)
    TIME_5 = db.Column(db.Float, index=True, nullable=True)
    TIME_6 = db.Column(db.Float, index=True, nullable=True)
    TIME_7 = db.Column(db.Float, index=True, nullable=True)
    TIME_8 = db.Column(db.Float, index=True, nullable=True)
    TIME_9 = db.Column(db.Float, index=True, nullable=True)
    TIME_10 = db.Column(db.Float, index=True, nullable=True)
    TIME_11 = db.Column(db.Float, index=True, nullable=True)
    TIME_12 = db.Column(db.Float, index=True, nullable=True)
    TIME_1 = db.Column(db.Float, index=True, nullable=True)
    TIME_2 = db.Column(db.Float, index=True, nullable=True)
    TIME_3 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_4 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_5 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_6 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_7 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_8 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_9 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_10 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_11 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_12 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_1 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_2 = db.Column(db.Float, index=True, nullable=True)
    TIME_HOLIDAY_3 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_4 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_5 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_6 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_7 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_8 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_9 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_10 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_11 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_12 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_1 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_2 = db.Column(db.Float, index=True, nullable=True)
    OVER_TIME_3 = db.Column(db.Float, index=True, nullable=True)


class CounterForTable(db.Model):
    __tablename__ = "D_COUNTER_FOR_TABLE"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    ONCALL = db.Column(db.Integer, index=True, nullable=True)
    ONCALL_HOLIDAY = db.Column(db.Integer, index=True, nullable=True)
    ONCALL_COUNT = db.Column(db.Integer, index=True, nullable=True)
    ENGEL_COUNT = db.Column(db.Integer, index=True, nullable=True)
    NENKYU = db.Column(db.Integer, index=True, nullable=True)
    NENKYU_HALF = db.Column(db.Integer, index=True, nullable=True)
    TIKOKU = db.Column(db.Integer, index=True, nullable=True)
    SOUTAI = db.Column(db.Integer, index=True, nullable=True)
    KEKKIN = db.Column(db.Integer, index=True, nullable=True)
    SYUTTYOU = db.Column(db.Integer, index=True, nullable=True)
    SYUTTYOU_HALF = db.Column(db.Integer, index=True, nullable=True)
    REFLESH = db.Column(db.Integer, index=True, nullable=True)
    MILEAGE = db.Column(db.Float, index=True, nullable=True)
    SUM_WORKTIME = db.Column(db.Float, index=True, nullable=True)
    SUM_REAL_WORKTIME = db.Column(db.Float, index=True, nullable=True)
    OVERTIME = db.Column(db.Float, index=True, nullable=True)
    HOLIDAY_WORK = db.Column(db.Float, index=True, nullable=True)
    WORKDAY_COUNT = db.Column(db.Integer, index=True, nullable=True)
    SUM_WORKTIME_10 = db.Column(db.Float, index=True, nullable=True)
    OVERTIME_10 = db.Column(db.Float, index=True, nullable=True)
    HOLIDAY_WORK_10 = db.Column(db.Float, index=True, nullable=True)
    TIMEOFF = db.Column(db.Integer, index=True, nullable=True)
    HALFWAY_THROUGH = db.Column(db.Integer, index=True, nullable=True)


class SystemInfo(db.Model):
    __tablename__ = "M_SYSTEMINFO"
    STAFFID = db.Column(
        db.Integer,
        db.ForeignKey("M_STAFFINFO.STAFFID"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    MAIL = db.Column(db.String(50), index=True, nullable=True)
    MAIL_PASS = db.Column(db.String(50), index=True, nullable=True)
    MICRO_PASS = db.Column(db.String(50), index=True, nullable=True)
    SKYPE_ID = db.Column(db.String(50), index=False, nullable=True)
    PAY_PASS = db.Column(db.String(50), index=True, nullable=True)
    KANAMIC_PASS = db.Column(db.String(50), index=True, nullable=True)
    ZOOM_PASS = db.Column(db.String(50), index=True, nullable=True)


@login.user_loader
def load_user(STAFFID):
    return StaffLoggin.query.get(int(STAFFID))


def is_integer_num(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()
