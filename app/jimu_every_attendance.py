from app import routes_attendance_option
from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, SelectMonthForm, EditForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede, RecordPaidHoliday, CountAttendance, TimeAttendance, CounterForTable, D_JOB_HISTORY, M_TIMECARD_TEMPLATE, D_HOLIDAY_HISTORY
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
from app.attendance_admin_classes import AttendanceAdminAnalysys
from app.calender_classes import MakeCalender, MakeCalender26
from app.calc_work_classes import DataForTable, CalcTimeClass, TimeOffClass, get_last_date
import math
from sqlalchemy import and_


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


@app.route('/jimu_every_dl/<STAFFID>/<int:startday>', methods=['GET', 'POST'])
@login_required
def jimu_every_dl(STAFFID, startday):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "angel対応件数",
               "開始時間", "終了時間", "走行距離", "届出<br>（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden", "disabled"]
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    textLock = ''
   

    textLock = 'readonly'
    selectLock = 'disabled'

    ##### 月選択の有無 #####
    if "y" in session:
        workday_data = session["workday_data"]
        y = session["y"]
        m = session["m"]
    else:
        workday_data = datetime.today().strftime('%Y-%m')
        y = datetime.now().year
        m = datetime.now().month

    d = get_last_date(y, m)

    if int(startday) != 1:
        #1日開始以外の場合
        FromDay = date(y, m, int(startday))  - relativedelta(months=1)
        ToDay = date(y, m, 25)
    else:
        #1日開始の場合
        FromDay = date(y, m, int(startday))
        ToDay = date(y, m, d)  

    
    shinseis = (
            db.session.query(Shinsei)
            .filter(and_(Shinsei.STAFFID == STAFFID, 
                         Shinsei.WORKDAY.between(FromDay,ToDay))
            ).all()
        )
    Parttime = db.session.query(D_HOLIDAY_HISTORY.STAFFID, Shinsei.WORKDAY,D_HOLIDAY_HISTORY.HOLIDAY_TIME).filter(
                                    and_(Shinsei.STAFFID == STAFFID, 
                                         Shinsei.STAFFID == D_HOLIDAY_HISTORY.STAFFID,
                                         Shinsei.WORKDAY.between(FromDay,ToDay),
                                         Shinsei.STAFFID == D_HOLIDAY_HISTORY.STAFFID,
                                         D_HOLIDAY_HISTORY.START_DAY <= Shinsei.WORKDAY,
                                         D_HOLIDAY_HISTORY.END_DAY >= Shinsei.WORKDAY)).subquery()

    shinseis = (
        db.session.query(Shinsei.STAFFID,Shinsei.STARTTIME,Shinsei.ENDTIME,Shinsei.WORKDAY,Shinsei.HOLIDAY,
                            Shinsei.OVERTIME,Shinsei.NOTIFICATION, Shinsei.NOTIFICATION2, 
                            Shinsei.ONCALL, Shinsei.ENGEL_COUNT, Shinsei.MILEAGE,
                            Shinsei.ONCALL_COUNT, Shinsei.ENGEL_COUNT, User.FNAME, User.LNAME,
                            D_JOB_HISTORY.JOBTYPE_CODE, D_JOB_HISTORY.CONTRACT_CODE, Parttime.c.HOLIDAY_TIME,
                            M_TIMECARD_TEMPLATE.TEMPLATE_NO)
        .filter(and_(Shinsei.STAFFID == STAFFID, 
                     Shinsei.STAFFID == User.STAFFID, 
                        Shinsei.WORKDAY.between(FromDay,ToDay),
                        Shinsei.STAFFID == D_JOB_HISTORY.STAFFID,
                        D_JOB_HISTORY.START_DAY <= Shinsei.WORKDAY, D_JOB_HISTORY.END_DAY >= Shinsei.WORKDAY,
                        D_JOB_HISTORY.JOBTYPE_CODE == M_TIMECARD_TEMPLATE.JOBTYPE_CODE, 
                        D_JOB_HISTORY.CONTRACT_CODE == M_TIMECARD_TEMPLATE.CONTRACT_CODE))
        ).outerjoin(Parttime, and_(Parttime.c.STAFFID == Shinsei.STAFFID, Parttime.c.WORKDAY == Shinsei.WORKDAY)).order_by(Shinsei.STAFFID, Shinsei.WORKDAY)

    u = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    form_month = SelectMonthForm()
    
    dwl_today = datetime.today()    
    template1 = 0
    template2 = 0
        
    ##### カレンダーとM_NOTIFICATION土日出勤の紐づけ関数 #####

    def get_day_of_week_jp(dt):
        w_list = ['', '', '', '', '', '1', '1']
        return(w_list[dt.weekday()])

    ##### 社員職種・勤務形態によるページ振り分け #####
    if STAFFID == 10000:
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = "hidden"
        bk = "hidden"
        othr = "hidden"
    elif u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
        oc = ""
        oc_cnt = ""
        eg = ""
        sk = "hidden"
        bk = ""
        othr = ""
        
    elif u.CONTRACT_CODE != 2 and (u.JOBTYPE_CODE == 3 or u.JOBTYPE_CODE == 4 or u.JOBTYPE_CODE == 5 or \
        u.JOBTYPE_CODE == 6 or u.JOBTYPE_CODE == 7 or u.JOBTYPE_CODE == 8):
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = "hidden"
        othr = ""
        bk = "" 

    else:
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = ""
        othr = ""
        bk = ""
        
    ##### M_NOTIFICATIONとindexの紐づけ #####
    td1 = Todokede.query.get(1)
    td2 = Todokede.query.get(2)
    td3 = Todokede.query.get(3)  # 年休（全日）はNOTIFICATION2にはない
    td4 = Todokede.query.get(4)
    td5 = Todokede.query.get(5)  # 出張（全日）はNOTIFICATION2にはない
    td6 = Todokede.query.get(6)
    td7 = Todokede.query.get(7)  # リフレッシュ休暇はNOTIFICATION2にはない
    td8 = Todokede.query.get(8)  # 欠勤はNOTIFICATION2にはない
    td9 = Todokede.query.get(9)
    td10 = Todokede.query.get(10)
    td11 = Todokede.query.get(11)
    td12 = Todokede.query.get(12)
    td13 = Todokede.query.get(13)
    td14 = Todokede.query.get(14)
    td15 = Todokede.query.get(15)
    td16 = Todokede.query.get(16)    
    td17 = Todokede.query.get(17)
    td18 = Todokede.query.get(18)
    td19 = Todokede.query.get(19)
    td20 = Todokede.query.get(20)



    ##### カレンダーの設定 #####
    
    cal = []
    hld = []
    
    if int(startday) != 1:
        mkc = MakeCalender26(cal, hld, y, m)
    else:
        mkc = MakeCalender(cal, hld, y, m)
    mkc.mkcal()
    
    
    oncall = []
    oncall_holiday = []
    oncall_cnt = []
    engel_cnt = []

    nenkyu = []
    nenkyu_half = []
    tikoku = []
    soutai = []
    kekkin = []
    syuttyou = []
    syuttyou_half = []
    reflesh = []
    s_kyori = []  ################################################## 使用

    syukkin_times_0 = []  ################################################# 使用
    syukkin_holiday_times_0 = []  ################################################# 使用
    over_time_0 = []
    
    timeoff1 = []
    timeoff2 = []
    timeoff3 = []
    halfway_through1 = []
    halfway_through2 = []
    halfway_through3 = [] 
    real_time = []
    real_time_sum = []
    template1 = 0
   

    for sh in shinseis:

        if template1 == 0:
            template1 = sh.TEMPLATE_NO
        elif template1 != sh.TEMPLATE_NO:
            template2 = sh.TEMPLATE_NO

        if u.CONTRACT_CODE != 2: 
            
            #************************  カウント系統 *******************************
            d = get_last_date(y, m)

 

            dft = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half, tikoku, soutai, kekkin,
                                syuttyou, syuttyou_half, reflesh, s_kyori, FromDay, ToDay)
            dft.other_data()
            
            tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                halfway_through1, halfway_through2, halfway_through3, FromDay, ToDay)
            tm_off.cnt_time_off()
          
  
            
            #************************ 時間計算系統 ********************************   
            d = get_last_date(y, m)
              
                 
            if FromDay <= sh.WORKDAY and ToDay >= sh.WORKDAY:
                dtm = datetime.strptime(sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')
                real_time = dtm
                # 常勤看護師の場合
 
                settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                        sh.CONTRACT_CODE, syukkin_times_0, over_time_0, 
                            real_time, real_time_sum, syukkin_holiday_times_0, sh.HOLIDAY, sh.JOBTYPE_CODE, STAFFID, sh.WORKDAY,
                            sh.HOLIDAY_TIME)

                settime.calc_time()

        ##### データベース貯蔵 #####
        ln_oncall = len(oncall) - len(oncall_holiday)
        ln_oncall_holiday = len(oncall_holiday)
        
        ln_oncall_cnt = 0
        for oc in oncall_cnt:
            if str.isnumeric(oc):
                ln_oncall_cnt += int(oc)
                        
        ln_engel_cnt= 0
        for ac in engel_cnt:
            if str.isnumeric(ac):
                ln_engel_cnt += int(ac)                

        ln_nenkyu = len(nenkyu)
        ln_nenkyu_half = len(nenkyu_half)
        ln_tikoku = len(tikoku)
        ln_soutai = len(soutai)
        ln_kekkin = len(kekkin)
        ln_syuttyou = len(syuttyou)
        ln_syuttyou_half = len(syuttyou_half)
        ln_reflesh = len(reflesh)
        
        ln_s_kyori = 0
        if s_kyori is not None:
            for s in s_kyori:
                ln_s_kyori += float(s)
            ln_s_kyori = math.floor(ln_s_kyori * 10) / 10

        sum_0 = 0
        for n in range(len(syukkin_times_0)):
            sum_0 += syukkin_times_0[n]
        w_h = sum_0 // (60 * 60)
        w_m = (sum_0 - w_h * 60 * 60) // 60
        working_time = w_h + w_m / 100
        working_time_10 = sum_0 / (60 * 60)
        
        sum_over_0 = 0
        for n in range(len(over_time_0)):
            sum_over_0 += over_time_0[n]
        o_h = sum_over_0 // (60 * 60)
        o_m = (sum_over_0 - o_h * 60 * 60) // 60                    
        over = o_h + o_m / 100
        over_10 = sum_over_0 / (60 * 60)

        sum_hol_0 = 0
        for n in range(len(syukkin_holiday_times_0)):
            sum_hol_0 += syukkin_holiday_times_0[n]
        h_h = sum_hol_0 // (60 * 60)
        h_m = (sum_hol_0 - h_h * 60 * 60) // 60   
        holiday_work = h_h + h_m / 100
        holiday_work_10 = sum_hol_0 / (60 * 60)

        workday_count = len(syukkin_times_0)

        syukkin_times = [n//(60*60)+((n-(n//(60*60))*60*60)//60)/100 for n in syukkin_times_0]        

    
        if u.CONTRACT_CODE == 2:
            
            #******************************  カウント系統 *****************************
  
            dft = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half, tikoku, soutai, kekkin,
                                syuttyou, syuttyou_half, reflesh, s_kyori, FromDay, ToDay)
            dft.other_data()

            tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                halfway_through1, halfway_through2, halfway_through3, FromDay, ToDay)
            tm_off.cnt_time_off()

            
            #****************************** 時間計算系統 ******************************
            d = get_last_date(y, m)
            if int(startday) != 1:
                #1日開始以外の場合
                FromDay = date(y, m, int(startday))  - relativedelta(months=1)
                ToDay = date(y, m, 25)
            else:
                #1日開始の場合
                FromDay = date(y, m, int(startday))
                ToDay = date(y, m, d)   
            if FromDay <= sh.WORKDAY and ToDay >= sh.WORKDAY:
                dtm = datetime.strptime(sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')
                real_time = dtm
                # 常勤看護師の場合
 
                settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                        sh.CONTRACT_CODE, syukkin_times_0, over_time_0, 
                            real_time, real_time_sum, syukkin_holiday_times_0, sh.HOLIDAY, sh.JOBTYPE_CODE, STAFFID, sh.WORKDAY,sh.HOLIDAY_TIME)
                settime.calc_time()

            

            ##### データベース貯蔵 #####
            ln_oncall = len(oncall) - len(oncall_holiday)
            ln_oncall_holiday = len(oncall_holiday)

            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                if str.isnumeric(oc):
                    ln_oncall_cnt += int(oc)
                            
            ln_engel_cnt= 0
            for ac in engel_cnt:
                if str.isnumeric(ac):
                    ln_engel_cnt += int(ac)   

            ln_nenkyu = len(nenkyu)
            ln_nenkyu_half = len(nenkyu_half)
            ln_tikoku = len(tikoku)
            ln_soutai = len(soutai)
            ln_kekkin = len(kekkin)
            ln_syuttyou = len(syuttyou)
            ln_syuttyou_half = len(syuttyou_half)
            ln_reflesh = len(reflesh)

            ln_s_kyori = 0
            if s_kyori is not None:
                for s in s_kyori:
                    ln_s_kyori += float(s)
                ln_s_kyori = math.floor(ln_s_kyori * 10) / 10

            sum_0 = 0
            for n in range(len(syukkin_times_0)):
                sum_0 += syukkin_times_0[n]
            w_h = sum_0 // (60 * 60)
            w_m = (sum_0 - w_h * 60 * 60) // 60
            working_time = w_h + w_m / 100
            working_time_10 = sum_0 / (60 * 60)
            
            sum_over_0 = 0
            for n in range(len(over_time_0)):
                sum_over_0 += over_time_0[n]
            o_h = sum_over_0 // (60 * 60)
            o_m = (sum_over_0 - o_h * 60 * 60) // 60                    
            over = o_h + o_m / 100
            over_10 = sum_over_0 / (60 * 60)

            sum_hol_0 = 0
            for n in range(len(syukkin_holiday_times_0)):
                sum_hol_0 += syukkin_holiday_times_0[n]
            h_h = sum_hol_0 // (60 * 60)
            h_m = (sum_hol_0 - h_h * 60 * 60) // 60   
            holiday_work = h_h + h_m / 100
            holiday_work_10 = sum_hol_0 / (60 * 60)

            workday_count = len(syukkin_times_0)
            # 配列に入った出勤時間(秒単位)を時間と分に変換
            syukkin_times = [n//(60*60)+((n-(n//(60*60))*60*60)//60)/100 for n in syukkin_times_0]                 


    return render_template('attendance/jimu_every_dl.html', title='ホーム', cal=cal, shinseis=shinseis, y=y, m=m, form_month=form_month,
                           oc=oc, oc_cnt=oc_cnt, eg=eg, sk=sk, othr=othr, hld=hld, u=u, bk=bk, tbl_clm=tbl_clm, typ=typ, ptn=ptn,
                           specification=specification, wk=wk, td1=td1, td2=td2, td3=td3, td4=td4, td5=td5, td6=td6, td7=td7,
                           td8=td8, td9=td9, td10=td10, td11=td11, td12=td12, td13=td13, td14=td14, td15=td15, td16=td16,
                           workday_data=workday_data, td17=td17, td18=td18, td19=td19, td20=td20, 
                           rp_holiday=rp_holiday, dwl_today=dwl_today, dsp_page=dsp_page, ln_s_kyori=ln_    , workday_count=workday_count,
                           syukkin_times=syukkin_times, working_time=working_time, holiday_work=holiday_work,
                           stf_login=stf_login, startday=startday, FromDay=FromDay, ToDay=ToDay, template1=template1, template2=template2) 

@ app.route('/jimuj_every_select/<STAFFID>/<int:StartDay>', methods=['GET', 'POST'])
@ login_required
def jimu_every_select(STAFFID, StartDay):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()

    STAFFID = STAFFID
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)
            
    ##### タイムカード表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()
    
    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "engel対応件数",
               "開始時間", "終了時間", "走行距離", "届出（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden"]
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    
    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get('workday_name'):
            workday_data_list = request.form.get('workday_name').split('-')
            session["workday_data"] = request.form.get('workday_name') 
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])
            
            
            
            
        return redirect(url_for('jimu_every_dl', STAFFID=STAFFID, startday=StartDay))
            
    return render_template('attendance/jimu_every_dl.html', title='ホーム', u=u, typ=typ, form_month=form_month, form=form,
                           tbl_clm=tbl_clm, specification=specification, session=session, stf_login=stf_login)

    
    
@ app.route('/jimuj_every_select_26/<STAFFID>', methods=['GET', 'POST'])
@ login_required
def jimu_every_select_26(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    STAFFID = STAFFID
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)
            
    ##### タイムカード表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()
    
    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "engel対応件数",
               "開始時間", "終了時間", "走行距離", "届出（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden"]
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    
    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get('workday_name'):
            workday_data_list = request.form.get('workday_name').split('-')
            session["workday_data"] = request.form.get('workday_name') 
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])
            
            
            
            
        return redirect(url_for('jimu_every_dl_26', STAFFID=STAFFID))
            
    return render_template('attendance/jimu_every_dl_26.html', title='ホーム', u=u, typ=typ, form_month=form_month, form=form,
                           tbl_clm=tbl_clm, specification=specification, session=session, stf_login=stf_login)