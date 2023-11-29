from app import routes_attendance_option, jimu_oncall_count
from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, SelectMonthForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede, RecordPaidHoliday, CountAttendance, TimeAttendance, D_JOB_HISTORY, M_TIMECARD_TEMPLATE
from flask_login import logout_user
from flask import abort
from functools import wraps
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date, time
from decimal import Decimal, ROUND_HALF_UP
import jpholiday
import os
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod
from app.attendance_classes import AttendanceAnalysys
from app.calender_classes import MakeCalender
from app.calc_work_classes import DataForTable, CalcTimeClass, get_last_date
from sqlalchemy import and_



#***** ユーザリストページ *****#
@app.route('/kinmuhyo')
@login_required
def kinmuhyo():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
       ##### 月選択の有無 #####
    form_month = SelectMonthForm()
    form = SaveForm()





    dsp_page = ""
    
    if "y" in session:
        workday_data = session["workday_data"]
        y = session["y"]
        m = session["m"]

        if datetime.today().month > 2:
            if datetime.today().year > int(session["y"]) or (datetime.today().year == int(session["y"]) and 
                                                             datetime.today().month > int(session["m"]) + 1):
                #dsp_page = "pointer-events: none;"
                dsp_page = ""
        elif datetime.today().month == 1:
            if datetime.today().year > int(session["y"]) or (datetime.today().year - 1 == int(session["y"]) and int(session["m"]) <= 11):
                #dsp_page = "pointer-events: none;"
                dsp_page = ""
        else:
            if datetime.today().year > int(session["y"]):
                #dsp_page = "pointer-events: none;"
                dsp_page = ""
        
    else:
        workday_data = datetime.today().strftime('%Y-%m-%d')
        y = datetime.now().year
        m = datetime.now().month
        
    

    ##### カレンダーの設定 #####
    cal = []
    hld = []
    
    mkc = MakeCalender(cal, hld, y, m)
    mkc.mkcal()
    
    
    

    return render_template('kinmuhyo/kinmuhyo.html', title='ホーム', cal=cal, y=y, m=m, form=form, form_month=form_month,
                        workday_data=workday_data,  stf_login=stf_login)
