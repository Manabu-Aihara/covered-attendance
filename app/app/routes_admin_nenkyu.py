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
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, AddDataUserForm
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
import json
import numpy as np


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 管理者か判断 *****"""

def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view


@app.route('/admin/users_nenkyu', methods=['GET', 'POST'])
@login_required
@admin_login_required
def users_nenkyu():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    disp = ["全職員", "本社", "WADEWADE訪問介護ステーション宇都宮", "WADEWADE訪問介護ステーション下野",
            "WADEWADE訪問介護ステーション鹿沼", "KODOMOTOナースステーションうつのみや",
            "わでわで在宅支援センターうつのみや", "わでわで子どもそうだんしえん", "WADEWADE訪問看護ステーションつくば"]
    serch = ["条件なし", "４月更新", "１０月更新", "使用年休５日以下"]
    val = ["", "1", "2", "3", "4", "5", "6", "7", "8"]
    specification = ["readonly", "checked", "selected", "hidden", "disabled"]

    datatocsv = datetime.today().strftime("%Y-%m-%d")
    dwl_today = datetime.today()
    
    users = None
    rp_hols = None
    
    if request.method == 'POST':
        
        session['lname'] = request.form.get('lname')
        session['fname'] = request.form.get('fname')        
        session['team'] = request.form.get('team')
        session['terms'] = request.form.get('terms')
        session['sort'] = request.form.get('sort')
        
        team = session['team']
        term = session['terms']
        
        users = User.query.all()
                    
        for user in users: ##############################################
            n = user.STAFFID
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).all()
            cnt_attendance = CountAttendance.query.get(n)           
                                   
            if shinseis == None:
                pass
            else:               
                if User.query.get(n) == None:
                    pass
                else:
                    usr = User.query.get(n)
                    rp_holiday = RecordPaidHoliday.query.get(n)                    
        
                    inday = User.query.get(n).INDAY
                    team_code = User.query.get(n).TEAM_CODE
                    lname = User.query.get(n).LNAME
                    fname = User.query.get(n).FNAME
                    lkana = User.query.get(n).LKANA
                    fkana = User.query.get(n).FKANA
                    contract_code = User.query.get(n).CONTRACT_CODE

                    def nenkyu_days():  
                        nenkyu_all_days = set()
                        nenkyu_half_days = set()                  
                        
                        if rp_holiday.LAST_DATEGRANT is None:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                        
                        else:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                    
                                    
                        a = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 # 年休使用日数
                            
                        return a                   
                                        
                    
                    if inday is not None:
                        ##### 基準月に変換 #####
                        if inday.month >= 4 and inday.month < 10:
                            change_day = inday.replace(month=10, day=1) # 基準月
                            giveday = change_day # 初回付与日
                        elif inday.month >= 10 and inday.month <= 12:
                            change_day = inday.replace(month=4, day=1)  # 基準月
                            giveday = change_day + relativedelta(months=12) # 初回付与日
                        elif inday.month < 4:
                            change_day = inday.replace(month=4, day=1) # 基準月
                            giveday = change_day # 初回付与日

                        ##### 基準付与日設定 #####
                        if datetime.today() < giveday and monthmod(datetime.today(), giveday)[0].months < 6: # 新入職員
                            last_giveday = inday # 今回付与
                            next_giveday = giveday # 次回付与                                
                        elif datetime.today() > giveday and monthmod(giveday, datetime.today())[0].months < 6: # 新入職員
                            last_giveday = giveday # 今回付与
                            next_giveday = giveday + relativedelta(months=12) # 次回付与                         
                        elif giveday < datetime.today():
                            while giveday < datetime.today():                           
                                giveday = giveday + relativedelta(months=12)
                                                                
                            last_giveday = giveday - relativedelta(months=12) # 今回付与
                            next_giveday = giveday # 次回付与
                        
                        ##### 基準付与日のSQLへの登録 #####
                        if rp_holiday.LAST_DATEGRANT is None and rp_holiday.NEXT_DATEGRANT is None: # 新規登録職員＝今回付与、次回付与のない状態
                            if last_giveday == inday: # 新入職員＝今回付与がない場合
                                rp_holiday.STAFFID = n
                                rp_holiday.INDAY = inday
                                rp_holiday.LAST_DATEGRANT = inday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                rp_holiday.TEAM_CODE = team_code
                                rp_holiday.LNAME = lname
                                rp_holiday.FNAME=fname
                                rp_holiday.LKANA=lkana
                                rp_holiday.FKANA=fkana
                                rp_holiday.CONTRACT_CODE=contract_code
                                db.session.commit()

                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()

                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                                                  

                            else: # 新データ設定時、新規入職者
                                rp_holiday.LAST_DATEGRANT = last_giveday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                db.session.commit()                               
                                
                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()
                                    
                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                          

                        else: # 既登録職員のSQLへの登録
                            rp_holiday.STAFFID = n
                            rp_holiday.INDAY = inday
                            rp_holiday.LAST_DATEGRANT = last_giveday
                            rp_holiday.NEXT_DATEGRANT = next_giveday
                            db.session.commit()                       
                            
                            if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                rp_holiday.LAST_CARRIEDOVER = 0
                                db.session.commit()
                                
                            if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                rp_holiday.USED_PAIDHOLIDAY = 0
                                db.session.commit()

                            if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                db.session.commit()

                            ##### 今回付与日数 #####
                            inday = rp_holiday.INDAY
                            ddm = monthmod(inday, datetime.today())[0].months
                            dm = monthmod(inday, last_giveday)[0].months
                            
                            """ 常勤 """
                            if rp_holiday.CONTRACT_CODE != 2:
                                if inday.month == 4 or inday.month == 10:
                                    if ddm < 6:
                                        aquisition_days = 2
                                    elif ddm < 12:
                                        aquisition_days = 10
                                    elif dm < 24:
                                        aquisition_days = 11
                                    elif dm < 36:
                                        aquisition_days = 12
                                    elif dm < 48:
                                        aquisition_days = 14
                                    elif dm < 60:
                                        aquisition_days = 16
                                    elif dm < 72:
                                        aquisition_days = 18
                                    elif dm >= 72:
                                        aquisition_days = 20
                                elif inday.month == 5 or inday.month == 11:
                                    if ddm < 5:
                                        aquisition_days = 2
                                    elif ddm < 11:
                                        aquisition_days = 10 
                                    elif dm < 23:
                                        aquisition_days = 11
                                    elif dm < 35:
                                        aquisition_days = 12
                                    elif dm < 47:
                                        aquisition_days = 14
                                    elif dm < 59:
                                        aquisition_days = 16
                                    elif dm < 71:
                                        aquisition_days = 18
                                    elif dm >= 71:
                                        aquisition_days = 20                
                                elif inday.month == 6 or inday.month == 12:
                                    if ddm < 4:
                                        aquisition_days = 1
                                    elif ddm < 10:
                                        aquisition_days = 10 
                                    elif dm < 22:
                                        aquisition_days = 11
                                    elif dm < 34:
                                        aquisition_days = 12
                                    elif dm < 46:
                                        aquisition_days = 14
                                    elif dm < 58:
                                        aquisition_days = 16
                                    elif dm < 70:
                                        aquisition_days = 18
                                    elif dm >= 70:
                                        aquisition_days = 20            
                                elif inday.month == 7 or inday.month == 1:
                                    if ddm < 3:
                                        aquisition_days = 1
                                    elif ddm < 9:
                                        aquisition_days = 10 
                                    elif dm < 21:
                                        aquisition_days = 11
                                    elif dm < 33:
                                        aquisition_days = 12
                                    elif dm < 45:
                                        aquisition_days = 14
                                    elif dm < 57:
                                        aquisition_days = 16
                                    elif dm < 69:
                                        aquisition_days = 18
                                    elif dm >= 69:
                                        aquisition_days = 20             
                                elif inday.month == 8 or inday.month == 2:
                                    if ddm < 2:
                                        aquisition_days = 0
                                    elif ddm < 8:
                                        aquisition_days = 10 
                                    elif dm < 20:
                                        aquisition_days = 11
                                    elif dm < 32:
                                        aquisition_days = 12
                                    elif dm < 44:
                                        aquisition_days = 14
                                    elif dm < 56:
                                        aquisition_days = 16
                                    elif dm < 68:
                                        aquisition_days = 18
                                    elif dm >= 68:
                                        aquisition_days = 20                                     
                                elif inday.month == 9 or inday.month == 3:
                                    if ddm < 1:
                                        aquisition_days = 0
                                    elif ddm < 7:
                                        aquisition_days = 10 
                                    elif dm < 19:
                                        aquisition_days = 11
                                    elif dm < 31:
                                        aquisition_days = 12
                                    elif dm < 43:
                                        aquisition_days = 14
                                    elif dm < 55:
                                        aquisition_days = 16
                                    elif dm < 67:
                                        aquisition_days = 18
                                    elif dm >= 67:
                                        aquisition_days = 20                                     

                                ##### 繰越残日数２年消滅設定 #####
                                if monthmod(inday, datetime.today())[0].months == 24 and rp_holiday.REMAIN_PAIDHOLIDAY >= 12:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
                                elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
                                elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
                                elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
                                elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
                                elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
                                elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
                                elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20 
                                
                                db.session.commit()
                                enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER # 使用可能日数

                                ##### 取得日　取得日数　年休種類 #####
                                                                
                                a = nenkyu_days()                                                                                              
                                

                                if rp_holiday.USED_PAIDHOLIDAY == "":
                                    rp_holiday(USED_PAIDHOLIDAY=a)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = a
                                    db.session.commit()

                                b = rp_holiday.LAST_CARRIEDOVER + aquisition_days - a # 年休残日数
                                if b < 0:
                                    b = 0
                                                
                                rp_holiday.REMAIN_PAIDHOLIDAY = b
                                db.session.commit()
                                

                                """ パート """                            
                            elif rp_holiday.CONTRACT_CODE == 2:

                                aquisition_days = 0 # 簡易的に記載
                                enable_days = 0 # 簡易的に記載
                                
                                ##### 取得日　取得日数　年休種類 #####

                                a = nenkyu_days()
                                            

                                if rp_holiday.USED_PAIDHOLIDAY is None:                                   
                                    rp_holiday(USED_PAIDHOLIDAY=a)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = a
                                    db.session.commit()
                                    
                                if rp_holiday.LAST_CARRIEDOVER: # 繰越年休データが編集ページで入力されていた場合
                                    if rp_holiday.USED_PAIDHOLIDAY == "":
                                        rp_holiday(USED_PAIDHOLIDAY=a)
                                        db.session.add(rp_holiday)
                                        db.session.commit()
                                    else:
                                        rp_holiday.USED_PAIDHOLIDAY = a
                                        db.session.commit()
                                        
                                b = rp_holiday.LAST_CARRIEDOVER + aquisition_days - a # 年休残日数
                                if b < 0:
                                    b = 0
 
                                rp_holiday.REMAIN_PAIDHOLIDAY = b
                                db.session.commit()
                                    
                    warn_for_holiday_style = "font-weight:bold; color: #ff0000;"      
        
                       
        ##### 条件検索設定 #####
        if session['lname'] != "" and session['fname'] != "" and session['team'] != "":
                
            if session['terms'] == "3":
                users = User.query.filter(User.LNAME==session['lname']).filter(User.FNAME==session['fname']).filter(User.TEAM_CODE==session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                            
        elif session['lname'] != "" and session['team'] != "" and session['fname'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).filter_by(TEAM_CODE=session['team']).all()            
                            
        elif session['lname'] != "" and session['fname'] != "" and session['team'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).all()
                
        elif session['lname'] == "" and session['fname'] != "" and session['team'] != "":
              
            if session['terms'] == "3":
                users = User.query.filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()           
                                         
        elif session['lname'] != "" and session['fname'] == "" and session['team'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(LNAME=session['lname']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).all()         
                            
        elif session['lname'] == "" and session['fname'] != "" and session['team'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                    
            elif session['terms'] == "":
                users = User.query.filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(FNAME=session['fname']).all()
                            
        elif session['lname'] == "" and session['fname'] == "" and session['team'] != "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(TEAM_CODE=session['team']).all()           
                            
        else:
               
            if session['terms'] == "3":
                users = User.query.all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.all()
                rp_hols = RecordPaidHoliday.query.all()
                
    else:
        session['lname'] = ""
        session['fname'] = ""        
        session['team'] = ""
        session['terms'] = ""
        session['sort'] = ""
        
        team = ""
        term = ""
        
        users = User.query.all()                           
                    
        for user in users: ###############
            n = user.STAFFID
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).all()
            cnt_attendance = CountAttendance.query.get(n)           
                                   
            if shinseis == None:
                pass
            else:               
                if User.query.get(n) == None:
                    pass
                else:
                    usr = User.query.get(n)
                    rp_holiday = RecordPaidHoliday.query.get(n)                    
        
                    inday = User.query.get(n).INDAY
                    team_code = User.query.get(n).TEAM_CODE
                    lname = User.query.get(n).LNAME
                    fname = User.query.get(n).FNAME
                    lkana = User.query.get(n).LKANA
                    fkana = User.query.get(n).FKANA
                    contract_code = User.query.get(n).CONTRACT_CODE
                    
                    def nenkyu_days():  
                        nenkyu_all_days = set()
                        nenkyu_half_days = set()                  
                        
                        if rp_holiday.LAST_DATEGRANT is None:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                        
                        else:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                    
                                    
                        a = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 # 年休使用日数
                            
                        return a                    
                    
                    
                    if inday is not None:
                        ##### 基準月に変換 #####
                        if inday.month >= 4 and inday.month < 10:
                            change_day = inday.replace(month=10, day=1) # 基準月
                            giveday = change_day # 初回付与日
                        elif inday.month >= 10 and inday.month <= 12:
                            change_day = inday.replace(month=4, day=1)  # 基準月
                            giveday = change_day + relativedelta(months=12) # 初回付与日
                        elif inday.month < 4:
                            change_day = inday.replace(month=4, day=1) # 基準月
                            giveday = change_day # 初回付与日

                        ##### 基準付与日設定 #####
                        if datetime.today() < giveday and monthmod(datetime.today(), giveday)[0].months < 6: # 新入職員
                            last_giveday = inday # 今回付与
                            next_giveday = giveday # 次回付与                                
                        elif datetime.today() > giveday and monthmod(giveday, datetime.today())[0].months < 6: # 新入職員
                            last_giveday = giveday # 今回付与
                            next_giveday = giveday + relativedelta(months=12) # 次回付与                         
                        elif giveday < datetime.today():
                            while giveday < datetime.today():                           
                                giveday = giveday + relativedelta(months=12)
                                                                
                            last_giveday = giveday - relativedelta(months=12) # 今回付与
                            next_giveday = giveday # 次回付与
                        
                        ##### 基準付与日のSQLへの登録 #####
                        if rp_holiday.LAST_DATEGRANT is None and rp_holiday.NEXT_DATEGRANT is None: # 新規登録職員＝今回付与、次回付与のない状態
                            if last_giveday == inday: # 新入職員＝今回付与がない場合
                                rp_holiday.STAFFID = n
                                rp_holiday.INDAY = inday
                                rp_holiday.LAST_DATEGRANT = inday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                rp_holiday.TEAM_CODE = team_code
                                rp_holiday.LNAME = lname
                                rp_holiday.FNAME=fname
                                rp_holiday.LKANA=lkana
                                rp_holiday.FKANA=fkana
                                rp_holiday.CONTRACT_CODE=contract_code
                                db.session.commit()

                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()

                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                                                  

                            else: # 新データ設定時、新規入職者
                                rp_holiday.LAST_DATEGRANT = last_giveday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                db.session.commit()                               
                                
                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()
                                    
                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                          

                        else: # 既登録職員のSQLへの登録
                            rp_holiday.STAFFID = n
                            rp_holiday.INDAY = inday
                            rp_holiday.LAST_DATEGRANT = last_giveday
                            rp_holiday.NEXT_DATEGRANT = next_giveday
                            db.session.commit()                       
                            
                            if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                rp_holiday.LAST_CARRIEDOVER = 0
                                db.session.commit()
                                
                            if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                rp_holiday.USED_PAIDHOLIDAY = 0
                                db.session.commit()

                            if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                db.session.commit()

                            ##### 今回付与日数 #####
                            inday = rp_holiday.INDAY
                            ddm = monthmod(inday, datetime.today())[0].months
                            dm = monthmod(inday, last_giveday)[0].months
                            
                            """ 常勤 """
                            if rp_holiday.CONTRACT_CODE != 2:
                                if inday.month == 4 or inday.month == 10:
                                    if ddm < 6:
                                        aquisition_days = 2
                                    elif ddm < 12:
                                        aquisition_days = 10
                                    elif dm < 24:
                                        aquisition_days = 11
                                    elif dm < 36:
                                        aquisition_days = 12
                                    elif dm < 48:
                                        aquisition_days = 14
                                    elif dm < 60:
                                        aquisition_days = 16
                                    elif dm < 72:
                                        aquisition_days = 18
                                    elif dm >= 72:
                                        aquisition_days = 20
                                elif inday.month == 5 or inday.month == 11:
                                    if ddm < 5:
                                        aquisition_days = 2
                                    elif ddm < 11:
                                        aquisition_days = 10 
                                    elif dm < 23:
                                        aquisition_days = 11
                                    elif dm < 35:
                                        aquisition_days = 12
                                    elif dm < 47:
                                        aquisition_days = 14
                                    elif dm < 59:
                                        aquisition_days = 16
                                    elif dm < 71:
                                        aquisition_days = 18
                                    elif dm >= 71:
                                        aquisition_days = 20                
                                elif inday.month == 6 or inday.month == 12:
                                    if ddm < 4:
                                        aquisition_days = 1
                                    elif ddm < 10:
                                        aquisition_days = 10 
                                    elif dm < 22:
                                        aquisition_days = 11
                                    elif dm < 34:
                                        aquisition_days = 12
                                    elif dm < 46:
                                        aquisition_days = 14
                                    elif dm < 58:
                                        aquisition_days = 16
                                    elif dm < 70:
                                        aquisition_days = 18
                                    elif dm >= 70:
                                        aquisition_days = 20            
                                elif inday.month == 7 or inday.month == 1:
                                    if ddm < 3:
                                        aquisition_days = 1
                                    elif ddm < 9:
                                        aquisition_days = 10 
                                    elif dm < 21:
                                        aquisition_days = 11
                                    elif dm < 33:
                                        aquisition_days = 12
                                    elif dm < 45:
                                        aquisition_days = 14
                                    elif dm < 57:
                                        aquisition_days = 16
                                    elif dm < 69:
                                        aquisition_days = 18
                                    elif dm >= 69:
                                        aquisition_days = 20             
                                elif inday.month == 8 or inday.month == 2:
                                    if ddm < 2:
                                        aquisition_days = 0
                                    elif ddm < 8:
                                        aquisition_days = 10 
                                    elif dm < 20:
                                        aquisition_days = 11
                                    elif dm < 32:
                                        aquisition_days = 12
                                    elif dm < 44:
                                        aquisition_days = 14
                                    elif dm < 56:
                                        aquisition_days = 16
                                    elif dm < 68:
                                        aquisition_days = 18
                                    elif dm >= 68:
                                        aquisition_days = 20                                     
                                elif inday.month == 9 or inday.month == 3:
                                    if ddm < 1:
                                        aquisition_days = 0
                                    elif ddm < 7:
                                        aquisition_days = 10 
                                    elif dm < 19:
                                        aquisition_days = 11
                                    elif dm < 31:
                                        aquisition_days = 12
                                    elif dm < 43:
                                        aquisition_days = 14
                                    elif dm < 55:
                                        aquisition_days = 16
                                    elif dm < 67:
                                        aquisition_days = 18
                                    elif dm >= 67:
                                        aquisition_days = 20

                                ##### 繰越残日数２年消滅設定 #####
                                if monthmod(inday, datetime.today())[0].months == 24 and rp_holiday.REMAIN_PAIDHOLIDAY >= 12:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
                                elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
                                elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
                                elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
                                elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
                                elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
                                elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
                                elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20 
                                
                                db.session.commit()
                                enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER # 使用可能日数

                                ##### 取得日　取得日数　年休種類 #####

                                a = nenkyu_days()
                            

                                if rp_holiday.USED_PAIDHOLIDAY == "":
                                    rp_holiday(USED_PAIDHOLIDAY=a)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = a
                                    db.session.commit()
                                    
                                if rp_holiday.USED_PAIDHOLIDAY == "":
                                    rp_holiday(USED_PAIDHOLIDAY=a)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = a
                                    db.session.commit()
                                    
                                b = rp_holiday.LAST_CARRIEDOVER + aquisition_days - a # 年休残日数
                                if b < 0:
                                    b = 0
                                

                                """ パート """                            
                            elif rp_holiday.CONTRACT_CODE == 2:

                                aquisition_days = 0 # 簡易的に記載
                                enable_days = 0 # 簡易的に記載
                                
                                ##### 取得日　取得日数　年休種類 #####

                                a = nenkyu_days()


                                if rp_holiday.USED_PAIDHOLIDAY is None:                                   
                                    rp_holiday(USED_PAIDHOLIDAY=a)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = a
                                    db.session.commit()
                                    
                                if rp_holiday.LAST_CARRIEDOVER: # 繰越年休データが編集ページで入力されていた場合
                                    if rp_holiday.USED_PAIDHOLIDAY == "":
                                        rp_holiday(USED_PAIDHOLIDAY=a)
                                        db.session.add(rp_holiday)
                                        db.session.commit()
                                    else:
                                        rp_holiday.USED_PAIDHOLIDAY = a
                                        db.session.commit()
                                        
                                b = rp_holiday.LAST_CARRIEDOVER + aquisition_days - a # 年休残日数
                                if b < 0:
                                    b = 0
                                    
                    warn_for_holiday_style = "font-weight:bold; color: #ff0000;"      
        
                       
        ##### 条件検索設定 #####
        if session['lname'] != "" and session['fname'] != "" and session['team'] != "":
              
            if session['terms'] == "3":
                users = User.query.filter(User.LNAME==session['lname']).filter(User.FNAME==session['fname']).filter(User.TEAM_CODE==session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                            
        elif session['lname'] != "" and session['team'] != "" and session['fname'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).filter_by(TEAM_CODE=session['team']).all()            
                            
        elif session['lname'] != "" and session['fname'] != "" and session['team'] == "":
              
            if session['terms'] == "3":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).filter_by(FNAME=session['fname']).all()
                
        elif session['lname'] == "" and session['fname'] != "" and session['team'] != "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(FNAME=session['fname']).filter_by(TEAM_CODE=session['team']).all()           
                                         
        elif session['lname'] != "" and session['fname'] == "" and session['team'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(LNAME=session['lname']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LNAME==session['lname']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(LNAME=session['lname']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(LNAME=session['lname']).all()         
                            
        elif session['lname'] == "" and session['fname'] != "" and session['team'] == "":
               
            if session['terms'] == "3":
                users = User.query.filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.FNAME==session['fname']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                    
            elif session['terms'] == "":
                users = User.query.filter_by(FNAME=session['fname']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(FNAME=session['fname']).all()
                            
        elif session['lname'] == "" and session['fname'] == "" and session['team'] != "":
             
            if session['terms'] == "3":
                users = User.query.filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.TEAM_CODE==session['team']).filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.filter_by(TEAM_CODE=session['team']).all()
                rp_hols = RecordPaidHoliday.query.filter_by(TEAM_CODE=session['team']).all()           
                            
        else:
             
            if session['terms'] == "3":
                users = User.query.all()
                rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.USED_PAIDHOLIDAY<=5.0).all()
                
            elif session['terms'] == "":
                users = User.query.all()
                rp_hols = RecordPaidHoliday.query.all()

    
        return render_template('admin/users_nenkyu.html', users=users, rp_hols=rp_hols, disp=disp, serch=serch, val=val,
                               datatocsv=datatocsv, warn_for_holiday_style=warn_for_holiday_style, dwl_today=dwl_today, 
                               specification=specification, team=team, term=term, stf_login=stf_login)   
            
    return render_template('admin/users_nenkyu.html', users=users, rp_hols=rp_hols, disp=disp, serch=serch, val=val,
                           datatocsv=datatocsv, dwl_today=dwl_today, specification=specification, team=team, term=term,
                           stf_login=stf_login)


@app.route('/admin/users_kana', methods=['GET', 'POST'])
@login_required
@admin_login_required
def users_kana():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    disp = ["全職員", "本社", "WADEWADE訪問介護ステーション宇都宮", "WADEWADE訪問介護ステーション下野",
            "WADEWADE訪問介護ステーション鹿沼", "KODOMOTOナースステーションうつのみや",
            "わでわで在宅支援センターうつのみや", "わでわで子どもそうだんしえん", "WADEWADE訪問看護ステーションつくば"]
    serch = ["条件なし", "４月更新", "１０月更新", "使用年休５日以下"]
    val = ["", "1", "2", "3", "4", "5", "6", "7"]
    specification = ["readonly", "checked", "selected", "hidden", "disabled"]
        
    datatocsv = datetime.today().strftime("%Y-%m-%d")
    dwl_today = datetime.today()
    
    usrs = User.query.all()
    
    if request.method == 'POST':
        
        session['kana'] = request.form.get('kana')
        users = User.query.filter(User.LKANA.startswith(session['kana'])).all()     
        rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LKANA.startswith(session['kana'])).all()
                
        for usr in usrs: ################################################
            n = usr.STAFFID
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).all() 
            rp_holiday = RecordPaidHoliday.query.get(n)          
            cnt_attendance = CountAttendance.query.get(n) 
                          
                       
            if shinseis == None:
                pass
            else:               
                if User.query.get(n) == None:
                    pass
                else:
                    usr = User.query.get(n)
                            
                    inday = usr.INDAY
                    team_code = usr.TEAM_CODE
                    lname = usr.LNAME
                    fname = usr.FNAME
                    lkana = usr.LKANA
                    fkana = usr.FKANA
                    contract_code = usr.CONTRACT_CODE
                    
            
                    def nenkyu_days():  
                        nenkyu_all_days = set()
                        nenkyu_half_days = set()                  
                        
                        if rp_holiday.LAST_DATEGRANT is None:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                        
                        else:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                    
                                    
                        a = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 # 年休使用日数
                            
                        return a                  
                    
                    
                    if inday is not None:
                        """ 基準月に変換 """
                        if inday.month >= 4 and inday.month < 10:
                            change_day = inday.replace(month=10, day=1) # 基準月
                            giveday = change_day # 初回付与日
                        elif inday.month >= 10 and inday.month <= 12:
                            change_day = inday.replace(month=4, day=1)  # 基準月
                            giveday = change_day + relativedelta(months=12) # 初回付与日
                        elif inday.month < 4:
                            change_day = inday.replace(month=4, day=1) # 基準月
                            giveday = change_day # 初回付与日

                        """ 基準付与日設定 """
                        if datetime.today() < giveday and monthmod(datetime.today(), giveday)[0].months < 6: # 新入職員
                            last_giveday = inday # 今回付与
                            next_giveday = giveday # 次回付与                                
                        elif datetime.today() > giveday and monthmod(giveday, datetime.today())[0].months < 6: # 新入職員
                            last_giveday = giveday # 今回付与
                            next_giveday = giveday + relativedelta(months=12) # 次回付与                         
                        elif giveday < datetime.today():
                            while giveday < datetime.today():                           
                                giveday = giveday + relativedelta(months=12)
                                                                
                            last_giveday = giveday - relativedelta(months=12) # 今回付与
                            next_giveday = giveday # 次回付与
                        
                        """ 基準付与日のSQLへの登録 """
                        if rp_holiday.LAST_DATEGRANT is None and rp_holiday.NEXT_DATEGRANT is None: # 新規登録職員＝今回付与、次回付与のない状態
                            if last_giveday == inday: # 新入職員＝今回付与がない場合
                                rp_holiday.STAFFID = n
                                rp_holiday.INDAY = inday
                                rp_holiday.LAST_DATEGRANT = inday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                rp_holiday.TEAM_CODE = team_code
                                rp_holiday.LNAME = lname
                                rp_holiday.FNAME=fname
                                rp_holiday.LKANA=lkana
                                rp_holiday.FKANA=fkana
                                rp_holiday.CONTRACT_CODE=contract_code
                                db.session.commit()

                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()

                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                                                  

                            else: # 新データ設定時、新規入職者
                                rp_holiday.LAST_DATEGRANT = last_giveday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                db.session.commit()                               
                                
                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()
                                    
                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                          
                                
                        else: # 既登録職員のSQLへの登録
                            rp_holiday.STAFFID = n
                            rp_holiday.INDAY = inday
                            rp_holiday.LAST_DATEGRANT = last_giveday
                            rp_holiday.NEXT_DATEGRANT = next_giveday
                            db.session.commit()                            
                            
                            if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                rp_holiday.LAST_CARRIEDOVER = 0
                                db.session.commit()
                                
                            if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                rp_holiday.USED_PAIDHOLIDAY = 0
                                db.session.commit()

                            if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                db.session.commit()
                                
                            ##### 今回付与日数 #####
                            inday = rp_holiday.INDAY
                            ddm = monthmod(inday, datetime.today())[0].months                        
                            dm = monthmod(inday, last_giveday)[0].months
                            
                            """ 常勤 """
                            if rp_holiday.CONTRACT_CODE != 2:
                                if inday.month == 4 or inday.month == 10:
                                    if ddm < 6:
                                        aquisition_days = 2
                                    elif ddm < 12:
                                        aquisition_days = 10
                                    elif dm < 24:
                                        aquisition_days = 11
                                    elif dm < 36:
                                        aquisition_days = 12
                                    elif dm < 48:
                                        aquisition_days = 14
                                    elif dm < 60:
                                        aquisition_days = 16
                                    elif dm < 72:
                                        aquisition_days = 18
                                    elif dm >= 72:
                                        aquisition_days = 20
                                elif inday.month == 5 or inday.month == 11:
                                    if ddm < 5:
                                        aquisition_days = 2
                                    elif ddm < 11:
                                        aquisition_days = 10 
                                    elif dm < 23:
                                        aquisition_days = 11
                                    elif dm < 35:
                                        aquisition_days = 12
                                    elif dm < 47:
                                        aquisition_days = 14
                                    elif dm < 59:
                                        aquisition_days = 16
                                    elif dm < 71:
                                        aquisition_days = 18
                                    elif dm >= 71:
                                        aquisition_days = 20                
                                elif inday.month == 6 or inday.month == 12:
                                    if ddm < 4:
                                        aquisition_days = 1
                                    elif ddm < 10:
                                        aquisition_days = 10 
                                    elif dm < 22:
                                        aquisition_days = 11
                                    elif dm < 34:
                                        aquisition_days = 12
                                    elif dm < 46:
                                        aquisition_days = 14
                                    elif dm < 58:
                                        aquisition_days = 16
                                    elif dm < 70:
                                        aquisition_days = 18
                                    elif dm >= 70:
                                        aquisition_days = 20            
                                elif inday.month == 7 or inday.month == 1:
                                    if ddm < 3:
                                        aquisition_days = 1
                                    elif ddm < 9:
                                        aquisition_days = 10 
                                    elif dm < 21:
                                        aquisition_days = 11
                                    elif dm < 33:
                                        aquisition_days = 12
                                    elif dm < 45:
                                        aquisition_days = 14
                                    elif dm < 57:
                                        aquisition_days = 16
                                    elif dm < 69:
                                        aquisition_days = 18
                                    elif dm >= 69:
                                        aquisition_days = 20             
                                elif inday.month == 8 or inday.month == 2:
                                    if ddm < 2:
                                        aquisition_days = 0
                                    elif ddm < 8:
                                        aquisition_days = 10 
                                    elif dm < 20:
                                        aquisition_days = 11
                                    elif dm < 32:
                                        aquisition_days = 12
                                    elif dm < 44:
                                        aquisition_days = 14
                                    elif dm < 56:
                                        aquisition_days = 16
                                    elif dm < 68:
                                        aquisition_days = 18
                                    elif dm >= 68:
                                        aquisition_days = 20                                     
                                elif inday.month == 9 or inday.month == 3:
                                    if ddm < 1:
                                        aquisition_days = 0
                                    elif ddm < 7:
                                        aquisition_days = 10 
                                    elif dm < 19:
                                        aquisition_days = 11
                                    elif dm < 31:
                                        aquisition_days = 12
                                    elif dm < 43:
                                        aquisition_days = 14
                                    elif dm < 55:
                                        aquisition_days = 16
                                    elif dm < 67:
                                        aquisition_days = 18
                                    elif dm >= 67:
                                        aquisition_days = 20
                                        
                                ##### 繰越残日数２年消滅設定 #####
                                if monthmod(inday, datetime.today())[0].months == 24 and rp_holiday.REMAIN_PAIDHOLIDAY >= 12:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
                                elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
                                elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
                                elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
                                elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
                                elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
                                elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
                                elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20 
                                
                                db.session.commit()
                                enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER # 使用可能日数

                                ##### 取得日　取得日数　年休種類 #####

                                x = nenkyu_days()


                                if rp_holiday.USED_PAIDHOLIDAY is None:
                                    rp_holiday(USED_PAIDHOLIDAY=x)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = x
                                    db.session.commit()

                                y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
                                if y < 0:
                                    y = 0                        
                                

                                """ パート """                            
                            elif rp_holiday.CONTRACT_CODE == 2:

                                aquisition_days = 0 # 簡易的に記載
                                enable_days = 0 # 簡易的に記載
                                
                                ##### 取得日　取得日数　年休種類 #####

                                x = nenkyu_days()


                                if rp_holiday.LAST_CARRIEDOVER is None:
                                    rp_holiday(USED_PAIDHOLIDAY=x)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.LAST_CARRIEDOVER = x
                                    db.session.commit()
                                    
                                y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
                                if y < 0:
                                    y = 0        
                                    
                warn_for_holiday_style = "font-weight:bold; color: #ff0000;"

    else:
        
        session['kana'] = ""
        users = User.query.filter(User.LKANA.startswith(session['kana'])).all()     
        rp_hols = RecordPaidHoliday.query.filter(RecordPaidHoliday.LKANA.startswith(session['kana'])).all()

        usrs = User.query.all()
        
        for usr in usrs: #################################################
            n = usr.STAFFID
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).all() 
            rp_holiday = RecordPaidHoliday.query.get(n)          
            cnt_attendance = CountAttendance.query.get(n)        
                          
            if shinseis == None:
                pass
            else:               
                if User.query.get(n) == None:
                    pass
                else:
                    usr = User.query.get(n)
                            
                    inday = usr.INDAY
                    team_code = usr.TEAM_CODE
                    lname = usr.LNAME
                    fname = usr.FNAME
                    lkana = usr.LKANA
                    fkana = usr.FKANA
                    contract_code = usr.CONTRACT_CODE
                    
                    def nenkyu_days():  
                        nenkyu_all_days = set()
                        nenkyu_half_days = set()                  
                        
                        if rp_holiday.LAST_DATEGRANT is None:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                        
                        else:
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="3").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_all_days.add(shs.WORKDAY)
                                    
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="4").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                            
                            shinseis = Shinsei.query.filter(Shinsei.STAFFID==n).filter(Shinsei.NOTIFICATION2=="16").all()
                            set_shinseis = set(shinseis)
                            for shs in set_shinseis:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    nenkyu_half_days.add(shs.WORKDAY)
                                    
                                    
                        a = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 # 年休使用日数
                            
                        return a

                    
                    if inday is not None:
                        """ 基準月に変換 """
                        if inday.month >= 4 and inday.month < 10:
                            change_day = inday.replace(month=10, day=1) # 基準月
                            giveday = change_day # 初回付与日
                        elif inday.month >= 10 and inday.month <= 12:
                            change_day = inday.replace(month=4, day=1)  # 基準月
                            giveday = change_day + relativedelta(months=12) # 初回付与日
                        elif inday.month < 4:
                            change_day = inday.replace(month=4, day=1) # 基準月
                            giveday = change_day # 初回付与日

                        """ 基準付与日設定 """
                        if datetime.today() < giveday and monthmod(datetime.today(), giveday)[0].months < 6: # 新入職員
                            last_giveday = inday # 今回付与
                            next_giveday = giveday # 次回付与                                
                        elif datetime.today() > giveday and monthmod(giveday, datetime.today())[0].months < 6: # 新入職員
                            last_giveday = giveday # 今回付与
                            next_giveday = giveday + relativedelta(months=12) # 次回付与                         
                        elif giveday < datetime.today():
                            while giveday < datetime.today():                           
                                giveday = giveday + relativedelta(months=12)
                                                                
                            last_giveday = giveday - relativedelta(months=12) # 今回付与
                            next_giveday = giveday # 次回付与
                        
                        """ 基準付与日のSQLへの登録 """
                        if rp_holiday.LAST_DATEGRANT is None and rp_holiday.NEXT_DATEGRANT is None: # 新規登録職員＝今回付与、次回付与のない状態
                            if last_giveday == inday: # 新入職員＝今回付与がない場合
                                rp_holiday.STAFFID = n
                                rp_holiday.INDAY = inday
                                rp_holiday.LAST_DATEGRANT = inday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                rp_holiday.TEAM_CODE = team_code
                                rp_holiday.LNAME = lname
                                rp_holiday.FNAME=fname
                                rp_holiday.LKANA=lkana
                                rp_holiday.FKANA=fkana
                                rp_holiday.CONTRACT_CODE=contract_code
                                db.session.commit()

                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()

                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                                                  

                            else: # 新データ設定時、新規入職者
                                rp_holiday.LAST_DATEGRANT = last_giveday
                                rp_holiday.NEXT_DATEGRANT = next_giveday
                                db.session.commit()                               
                                
                                if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                    rp_holiday.LAST_CARRIEDOVER = 0
                                    db.session.commit()
                                    
                                if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                    rp_holiday.USED_PAIDHOLIDAY = 0
                                    db.session.commit()

                                if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                    rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                    db.session.commit()                          
                                
                        else: # 既登録職員のSQLへの登録
                            rp_holiday.STAFFID = n
                            rp_holiday.INDAY = inday
                            rp_holiday.LAST_DATEGRANT = last_giveday
                            rp_holiday.NEXT_DATEGRANT = next_giveday
                            db.session.commit()                            
                            
                            if rp_holiday.LAST_CARRIEDOVER == None: # 前回繰越データ自体がない場合
                                rp_holiday.LAST_CARRIEDOVER = 0
                                db.session.commit()
                                
                            if rp_holiday.USED_PAIDHOLIDAY == None: # 使用日数データ自体がない場合
                                rp_holiday.USED_PAIDHOLIDAY = 0
                                db.session.commit()

                            if rp_holiday.REMAIN_PAIDHOLIDAY == None: # 年休残データ自体がない場合
                                rp_holiday.REMAIN_PAIDHOLIDAY = 0
                                db.session.commit()
                                
                            ##### 今回付与日数 #####
                            inday = rp_holiday.INDAY
                            ddm = monthmod(inday, datetime.today())[0].months                        
                            dm = monthmod(inday, last_giveday)[0].months
                            
                            """ 常勤 """
                            if rp_holiday.CONTRACT_CODE != 2:
                                if inday.month == 4 or inday.month == 10:
                                    if ddm < 6:
                                        aquisition_days = 2
                                    elif ddm < 12:
                                        aquisition_days = 10
                                    elif dm < 24:
                                        aquisition_days = 11
                                    elif dm < 36:
                                        aquisition_days = 12
                                    elif dm < 48:
                                        aquisition_days = 14
                                    elif dm < 60:
                                        aquisition_days = 16
                                    elif dm < 72:
                                        aquisition_days = 18
                                    elif dm >= 72:
                                        aquisition_days = 20
                                elif inday.month == 5 or inday.month == 11:
                                    if ddm < 5:
                                        aquisition_days = 2
                                    elif ddm < 11:
                                        aquisition_days = 10 
                                    elif dm < 23:
                                        aquisition_days = 11
                                    elif dm < 35:
                                        aquisition_days = 12
                                    elif dm < 47:
                                        aquisition_days = 14
                                    elif dm < 59:
                                        aquisition_days = 16
                                    elif dm < 71:
                                        aquisition_days = 18
                                    elif dm >= 71:
                                        aquisition_days = 20                
                                elif inday.month == 6 or inday.month == 12:
                                    if ddm < 4:
                                        aquisition_days = 1
                                    elif ddm < 10:
                                        aquisition_days = 10 
                                    elif dm < 22:
                                        aquisition_days = 11
                                    elif dm < 34:
                                        aquisition_days = 12
                                    elif dm < 46:
                                        aquisition_days = 14
                                    elif dm < 58:
                                        aquisition_days = 16
                                    elif dm < 70:
                                        aquisition_days = 18
                                    elif dm >= 70:
                                        aquisition_days = 20            
                                elif inday.month == 7 or inday.month == 1:
                                    if ddm < 3:
                                        aquisition_days = 1
                                    elif ddm < 9:
                                        aquisition_days = 10 
                                    elif dm < 21:
                                        aquisition_days = 11
                                    elif dm < 33:
                                        aquisition_days = 12
                                    elif dm < 45:
                                        aquisition_days = 14
                                    elif dm < 57:
                                        aquisition_days = 16
                                    elif dm < 69:
                                        aquisition_days = 18
                                    elif dm >= 69:
                                        aquisition_days = 20             
                                elif inday.month == 8 or inday.month == 2:
                                    if ddm < 2:
                                        aquisition_days = 0
                                    elif ddm < 8:
                                        aquisition_days = 10 
                                    elif dm < 20:
                                        aquisition_days = 11
                                    elif dm < 32:
                                        aquisition_days = 12
                                    elif dm < 44:
                                        aquisition_days = 14
                                    elif dm < 56:
                                        aquisition_days = 16
                                    elif dm < 68:
                                        aquisition_days = 18
                                    elif dm >= 68:
                                        aquisition_days = 20                                     
                                elif inday.month == 9 or inday.month == 3:
                                    if ddm < 1:
                                        aquisition_days = 0
                                    elif ddm < 7:
                                        aquisition_days = 10 
                                    elif dm < 19:
                                        aquisition_days = 11
                                    elif dm < 31:
                                        aquisition_days = 12
                                    elif dm < 43:
                                        aquisition_days = 14
                                    elif dm < 55:
                                        aquisition_days = 16
                                    elif dm < 67:
                                        aquisition_days = 18
                                    elif dm >= 67:
                                        aquisition_days = 20

                                ##### 繰越残日数２年消滅設定 #####
                                if monthmod(inday, datetime.today())[0].months == 24 and rp_holiday.REMAIN_PAIDHOLIDAY >= 12:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
                                elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
                                elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
                                elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
                                elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
                                elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
                                elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
                                elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
                                    rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20 
                                
                                db.session.commit()
                                enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER # 使用可能日数

                                ##### 取得日　取得日数　年休種類 #####

                                x = nenkyu_days()


                                if rp_holiday.USED_PAIDHOLIDAY is None:
                                    rp_holiday(USED_PAIDHOLIDAY=x)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.USED_PAIDHOLIDAY = x
                                    db.session.commit()

                                y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
                                if y < 0:
                                    y = 0                                 
                                

                                """ パート """                            
                            elif rp_holiday.CONTRACT_CODE == 2:

                                aquisition_days = 0 # 簡易的に記載
                                enable_days = 0 # 簡易的に記載
                                
                                ##### 取得日　取得日数　年休種類 #####

                                x = nenkyu_days()


                                if rp_holiday.LAST_CARRIEDOVER is None:
                                    rp_holiday(USED_PAIDHOLIDAY=x)
                                    db.session.add(rp_holiday)
                                    db.session.commit()
                                else:
                                    rp_holiday.LAST_CARRIEDOVER = x
                                    db.session.commit()
                                    
                                y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
                                if y < 0:
                                    y = 0        
                                    
                warn_for_holiday_style = "font-weight:bold; color: #ff0000;"
                                     

        return render_template('admin/users_nenkyu.html', users=users, rp_hols=rp_hols, disp=disp, serch=serch, cnt_attendance=cnt_attendance,
                               val=val, datatocsv=datatocsv, warn_for_holiday_style=warn_for_holiday_style, dwl_today=dwl_today, 
                               specification=specification, stf_login=stf_login,)

    return render_template('admin/users_nenkyu.html', users=users, rp_hols=rp_hols, val=val, disp=disp, serch=serch,
                            datatocsv=datatocsv, dwl_today=dwl_today, specification=specification, stf_login=stf_login)


@app.route('/admin/nenkyu_detail/<STAFFID>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def nenkyu_detail(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = STAFFID
    user = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).all()
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)

    next_datagrant = rp_holiday.NEXT_DATEGRANT - timedelta(days=1)

                
    ##### 今回付与日数 #####
    inday = rp_holiday.INDAY
    
            
    def nenkyu_days(a, h, s):                                  
        
        if rp_holiday.LAST_DATEGRANT is None:
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="3").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_all_days.add(shs.WORKDAY)
                    
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
                
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
        
        else:
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="3").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_all_days.add(shs.WORKDAY)
                    
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
                
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
                                       
                    
        return nenkyu_all_days, nenkyu_half_days, seiri_days
    
    
    if inday.month == 4 and inday.month == 5:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 6 and inday.month == 7:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 8 and inday.month == 9:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 10 and inday.month == 11:
        first_day = inday.replace(month=4, day=1)
    elif inday.month == 12 and inday.month == 1:
        first_day = inday.replace(month=4, day=1)
    elif inday.month == 2 and inday.month == 3:
        first_day = inday.replace(month=4, day=1)
        
    ddm = monthmod(inday, datetime.today())[0].months    
    dm = monthmod(inday, rp_holiday.LAST_DATEGRANT)[0].months
    
    """ 常勤 """
    if rp_holiday.CONTRACT_CODE != 2:

        ##### 年休付与日数設定 #####
        if inday.month == 4 or inday.month == 10:
            if ddm < 6:
                aquisition_days = 2
            elif ddm < 12:
                aquisition_days = 10
            elif dm < 24:
                aquisition_days = 11
            elif dm < 36:
                aquisition_days = 12
            elif dm < 48:
                aquisition_days = 14
            elif dm < 60:
                aquisition_days = 16
            elif dm < 76:
                aquisition_days = 18
            elif dm >= 76:
                aquisition_days = 20
        elif inday.month == 5 or inday.month == 11:
            if ddm < 5:
                aquisition_days = 2
            elif ddm < 11:
                aquisition_days = 10 
            elif dm < 23:
                aquisition_days = 11
            elif dm < 35:
                aquisition_days = 12
            elif dm < 47:
                aquisition_days = 14
            elif dm < 59:
                aquisition_days = 16
            elif dm < 71:
                aquisition_days = 18
            elif dm >= 71:
                aquisition_days = 20                
        elif inday.month == 6 or inday.month == 12:
            if ddm < 4:
                aquisition_days = 1
            elif ddm < 10:
                aquisition_days = 10 
            elif dm < 22:
                aquisition_days = 11
            elif dm < 34:
                aquisition_days = 12
            elif dm < 46:
                aquisition_days = 14
            elif dm < 58:
                aquisition_days = 16
            elif dm < 70:
                aquisition_days = 18
            elif dm >= 70:
                aquisition_days = 20            
        elif inday.month == 7 or inday.month == 1:
            if ddm < 3:
                aquisition_days = 1
            elif ddm < 9:
                aquisition_days = 10 
            elif dm < 21:
                aquisition_days = 11
            elif dm < 33:
                aquisition_days = 12
            elif dm < 45:
                aquisition_days = 14
            elif dm < 57:
                aquisition_days = 16
            elif dm < 69:
                aquisition_days = 18
            elif dm >= 69:
                aquisition_days = 20             
        elif inday.month == 8 or inday.month == 2:
            if ddm < 2:
                aquisition_days = 0
            elif ddm < 8:
                aquisition_days = 10 
            elif dm < 20:
                aquisition_days = 11
            elif dm < 32:
                aquisition_days = 12
            elif dm < 44:
                aquisition_days = 14
            elif dm < 56:
                aquisition_days = 16
            elif dm < 68:
                aquisition_days = 18
            elif dm >= 68:
                aquisition_days = 20                                     
        elif inday.month == 9 or inday.month == 3:
            if ddm < 1:
                aquisition_days = 0
            elif ddm < 7:
                aquisition_days = 10 
            elif dm < 19:
                aquisition_days = 11
            elif dm < 31:
                aquisition_days = 12
            elif dm < 43:
                aquisition_days = 14
            elif dm < 55:
                aquisition_days = 16
            elif dm < 67:
                aquisition_days = 18
            elif dm >= 67:
                aquisition_days = 20                                     

        ##### 繰越残日数２年消滅設定 #####
        if monthmod(inday, datetime.today())[0].months == 24 and rp_holiday.REMAIN_PAIDHOLIDAY >= 12:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
        elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
        elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
        elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
        elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
        elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
        elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
        elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20 
        
        db.session.commit()
        enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER # 使用可能日数
        
        ##### 取得日　取得日数　年休種類 #####
        nenkyu_all_days = set()
        nenkyu_half_days = set()
        seiri_days = set()

        nenkyu_days(nenkyu_all_days, nenkyu_half_days, seiri_days)
                        
        x = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 + len(seiri_days) * 0.5 # 年休使用日数 

        if rp_holiday.USED_PAIDHOLIDAY is None:
            rp_holiday(USED_PAIDHOLIDAY=x)
            db.session.add(rp_holiday)
            db.session.commit()
        else:
            rp_holiday.USED_PAIDHOLIDAY = x
            db.session.commit()

        y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
        if y < 0:
            y = 0                                                 
      

        """ パート """                            
    elif rp_holiday.CONTRACT_CODE == 2:

        aquisition_days = 0 # 簡易的に記載
        enable_days = 0 # 簡易的に記載
        
        ##### 取得日　取得日数　年休種類 #####
        nenkyu_all_days = set()
        nenkyu_half_days = set()
        seiri_days = set()

        nenkyu_days(nenkyu_all_days, nenkyu_half_days, seiri_days)

        x = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 + len(seiri_days) * 0.5 # 年休使用日数                         

        if rp_holiday.USED_PAIDHOLIDAY is None:
            rp_holiday(USED_PAIDHOLIDAY=x)
            db.session.add(rp_holiday)
            db.session.commit()
        else:
            rp_holiday.USED_PAIDHOLIDAY = x
            db.session.commit()
            
        y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
        if y < 0:
            y = 0        
            
            
    return render_template('admin/nenkyu_detail.html', user=user, rp_holiday=rp_holiday, aquisition_days=aquisition_days,
                           next_datagrant=next_datagrant, nenkyu_all_days=nenkyu_all_days, nenkyu_half_days=nenkyu_half_days,
                           enable_days=enable_days, cnt_attendance=cnt_attendance, tm_attendance=tm_attendance, 
                           seiri_days=seiri_days, stf_login=stf_login)