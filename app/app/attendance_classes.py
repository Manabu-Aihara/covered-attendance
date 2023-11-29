"""
**********
勤怠アプリ
2022/04版
**********
"""
from app import routes_attendance_option
from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, SelectMonthForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede, RecordPaidHoliday, CountAttendance, TimeAttendance
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
from app.common_func import GetPullDownList, intCheck, blankCheck


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


class AttendanceAnalysys:
    
    def __init__(self, c, data0, data1, data2, data3, data_4, data5, data6, data7, data8, data9, data10, data11, data12, staffid, InsertFLg):
        self.c = c
        self.data0 = data0
        self.data1 = data1
        self.data2 = data2
        self.data3 = data3
        self.data_4 = data_4
        self.data5 = data5
        self.data6 = data6
        self.data7 = data7
        self.data8 = data8
        self.data9 = data9
        self.data10 = data10
        self.data11 = data11
        self.data12 = data12
        self.staffid = staffid
        self.InsertFlg = InsertFLg
            
    def analysys(self):
        
        def get_day_of_week_jp(dt):
            w_list = ['', '', '', '', '', '1', '1']
            return(w_list[dt.weekday()])

        
        ##### 走行距離小数第1位表示に変換 #####
        if self.data_4 is not None and self.data_4 != '':
            ZEN = "".join(chr(0xff01 + j) for j in range(94))
            HAN = "".join(chr(0x21 + k) for k in range(94))
            ZEN2HAN = str.maketrans(ZEN, HAN)
            data__4 = self.data_4.translate(ZEN2HAN)
            def is_num(s):
                try:
                    float(s)
                except ValueError:
                    return flash("数字以外は入力できません。")
                else:
                    return s
                
            data___4 = is_num(data__4)
            
            data4 = str(Decimal(data___4).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
        else:
            data4 = "0.0"
            
        ##### M_ATTENDANCE登録 #####
        if self.data2 == "":
            self.data2 = "00:00"
        elif self.data3 == "":
            self.data3 = "00:00"

        ##### 届出別条件分岐3                                                                              
        
        if self.data2 == "00:00" and self.data3 != "00:00": #################################                              
            flash(str(self.data1) + "について一時的に保存しました。", "success")

        elif self.data2 != "00:00" and self.data3 == "00:00": #################################                            
            flash(str(self.data1) + "について一時的に保存しました。", "success")
            
        ##### 届出別条件分岐4                            
        elif (int(self.data2.split(':')[0]) == int(self.data3.split(':')[0])) and (int(self.data2.split(':')[1]) > int(self.data3.split(':')[1])) or \
            (int(self.data2.split(':')[0]) > int(self.data3.split(':')[0])) and (int(self.data2.split(':')[0]) != 0 and int(self.data3.split(':')[0] != 0)):
                
                flash(str(self.data1) + "の勤務時間を正しく入力してください。", "warning")
            
        ##### 届出別条件分岐1
        elif self.data7 == "" and self.data11 == "":
            flash("保存しました。", "success")
            
        elif self.data7 == "" and self.data11 != "" and self.data11 != "4" and  self.data11 != "6" and self.data11 != "9" and self.data11 != "16":
            if self.data2 == "00:00" and self.data3 == "00:00":
                flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
    
            elif self.data2 != "00:00" and self.data3 != "00:00":
                flash("保存しました。", "success") 
        
        elif self.data7 == "" and (self.data11 == "4" or self.data11 == "6" or self.data11 == "9" or self.data11 == "16"):
            flash("保存しました。", "success")
        
        elif self.data7 == "1" and self.data11 != "1":
            if self.data2 == "00:00" and self.data3 == "00:00":
                flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")      
                
            elif self.data2 != "00:00" and self.data3 != "00:00":                       
                flash("保存しました。", "success")
        
        elif self.data7 == "2" and (self.data11 == "" or self.data11 == "4" or self.data11 == "6" or self.data11 == "9" or self.data11 == "16"):
            if self.data2 == "00:00" and self.data3 == "00:00":
                flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")

            elif self.data2 != "00:00" and self.data3 != "00:00":                    
                flash("保存しました。", "success")
            
        elif self.data7 == "3" and self.data11 == "":
            flash("保存しました。", "success")
            
        elif (self.data7 == "4" and self.data11 != "4") or (self.data7 == "16" and self.data11 != "16"):
            if self.data11 == "6":
                flash("保存しました。", "success")
                
            elif self.data11 != "6":
                if self.data2 == "00:00" and self.data3 == "00:00" and self.data11 != "":
                    flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                
                elif self.data2 == "00:00" and self.data3 == "00:00" and self.data11 == "":
                    flash("保存しました。", "success")
                    
                elif self.data2 != "00:00" and self.data3 != "00:00":
                    flash("保存しました。", "success")
                
        elif self.data7 == "5" and self.data11 == "":
            flash("保存しました。", "success")
            
        elif self.data7 == "6" and self.data11 != "6":
            if self.data11 == "4" or self.data11 == "16":
                flash("保存しました。", "success")
                        
            elif self.data11 != "4" or self.data11 != "16":
                if self.data2 == "00:00" and self.data3 == "00:00" and self.data11 != "":                
                    flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                
                elif self.data2 == "00:00" and self.data3 == "00:00" and self.data11 == "":                
                    flash("保存しました。", "success")
                                
                elif self.data2 != "00:00" and self.data3 != "00:00":
                    flash("保存しました。", "success")
                
        elif self.data7 == "7" and self.data11 == "":                                                                                
            flash("保存しました。", "success")
        
        elif (self.data7 == "8" or self.data7 == "9" or self.data7 == "17" or self.data7 == "18" or self.data7 == "19" or self.data7 == "20") and self.data11 == "":
            flash("保存しました。", "success")
            
        elif (self.data7 == "10" or self.data7 == "11" or self.data7 == "12" or self.data7 == "13" or \
            self.data7 == "14" or self.data7 == "15") and self.data11 != "1":
            if self.data2 == "00:00" and self.data3 == "00:00":
                flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                
            elif self.data2 != "00:00" and self.data3 != "00:00":
                flash("保存しました。", "success")
            
        ##### 届出別条件分岐2
        elif self.data7 == "1" and self.data11 == "1":                        
            flash(str(self.data1) + "について、同時に同じ届出はできません。", "warning")
        
        elif self.data7 == "2" and (self.data11 !="4" or self.data11 != "6" or self.data11 != "9" or self.data11 != "16"):
            flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
        
        elif self.data7 == "3" and self.data11 != "": 
            flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
            
        elif self.data7 == "4" and self.data11 == "4":
            flash(str(self.data1) + "について、同時に同じ届出はできません。", "warning")
        
        elif self.data7 == "5" and self.data11 != "":
            flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
        
        elif self.data7 == "6" and self.data11 == "6":
            flash(str(self.data1) + "について、同時に同じ届出はできません。", "warning")
    
        elif (self.data7 == "7" or self.data7 == "8" or self.data7 == "17" or self.data7 == "18" or self.data7 == "19" or self.data7 == "20") and self.data11 != "":                                                                                
            flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
        
        elif self.data7 == "9" and self.data11 != "":
            flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
        
        elif (self.data7 == "10" or self.data7 == "11" or self.data7 == "12" or self.data7 == "13" or \
            self.data7 == "14" or self.data7 == "15") and self.data11 == "1":
            flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
        
        holiday = ""
        if jpholiday.is_holiday_name(self.c):
            holiday = "2"
        elif get_day_of_week_jp(self.c) == "1":
            holiday = "1"
        
        

        if self.data6 != "0" and self.data6 is not None and self.data6 != "":
            oncall_cnt = self.data6
        else:
            oncall_cnt = None

        

        if self.data2 != "00:00" or self.data3 != "00:00" or data4 != "0.0" or self.data5 == "on" or self.data7 != '' or \
               self.data12 != '' or oncall_cnt is not None or self.data9 is not None or self.data10 != "":
                self.InsertFlg = 1
      