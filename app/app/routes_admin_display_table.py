"""
**********
勤怠システム
2022/04版
**********
"""

from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, AddDataUserForm, SelectMonthForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede, RecordPaidHoliday, CountAttendance, TimeAttendance, SystemInfo, CounterForTable
from flask_login import logout_user
from flask import abort
from functools import wraps
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
import jpholiday
import os
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod
from app.calc_work_classes import DataForTable, CalcTimeClass, TimeOffClass


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


#***** 管理者か判断 *****#

def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view



