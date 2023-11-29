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


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


class AttendanceAdminAnalysys:
    
    def __init__(self, c, STAFFID, data0, data1, data2, data3, data_4, data5, data6, data7, data8, data9, data10, data11):
        self.c = c
        self.STAFFID = STAFFID
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
            
    def analysys(self):
        
        STAFFID = self.STAFFID
        shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
        
        shin = Shinsei.query.filter_by(STAFFID=STAFFID)
        u = User.query.get(STAFFID)
        rp_holiday = RecordPaidHoliday.query.get(STAFFID)
        cnt_attemdance = CountAttendance.query.get(STAFFID)
        tm_attendance = TimeAttendance.query.get(STAFFID)

        sh = Shinsei.query.get(self.data0)        

        def get_day_of_week_jp(dt):
            w_list = ['', '', '', '', '', '1', '1']
            return(w_list[dt.weekday()])

        
        ##### 走行距離小数第1位表示に変換 #####
        if self.data_4 is not None:
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
            

        ##### リフレッシュ休暇付与予備設定 ######
        inday = rp_holiday.INDAY
        session.permanent = True

        ##### M_ATTENDANCE登録 #####
        if self.c.strftime('%Y-%m-%d') == self.data1 and sh:   # 登録上書き
            hiduke = self.data1
            user_s_id = STAFFID
            bikou = self.data10

            if self.data2 == "":
                self.data2 = "00:00"
            elif self.data3 == "":
                self.data3 = "00:00"

            ##### 届出別条件分岐3                                                                              
            
            if self.data2 == "00:00" and self.data3 != "00:00": #################################                              
                flash(str(self.data1) + "について一時的に保存しました。", "success")
                start_time = self.data2
                fin_time = self.data3
                                
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0

                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                        
                todokede_PM = self.data11 
                hiduke = self.data1
                
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            elif self.data2 != "00:00" and self.data3 == "00:00": #################################                            
                flash(str(self.data1) + "について一時的に保存しました。", "success")
                start_time = self.data2
                fin_time = self.data3
                                
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0

                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                        
                todokede_PM = self.data11 
                hiduke = self.data1
              
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            ##### 届出別条件分岐4                            
            elif (int(self.data2.split(':')[0]) == int(self.data3.split(':')[0])) and (int(self.data2.split(':')[1]) > int(self.data3.split(':')[1])) or \
                (int(self.data2.split(':')[0]) > int(self.data3.split(':')[0])) and (int(self.data2.split(':')[0]) != 0 and int(self.data3.split(':')[0] != 0)):
                    
                    flash(str(self.data1) + "の勤務時間を正しく入力してください。", "warning")
                    
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0

                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()
                
            ##### 届出別条件分岐1
            elif self.data7 == "" and self.data11 == "":
                flash("保存しました。", "success")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
                
            elif self.data7 == "" and self.data11 != "" and self.data11 != "4" and  self.data11 != "6" and self.data11 != "9" and self.data11 != "16":
                if self.data2 == "00:00" and self.data3 == "00:00":
                    flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()
                
                elif self.data2 != "00:00" and self.data3 != "00:00":
                    flash("保存しました。", "success")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()                                        
            
            elif self.data7 == "" and (self.data11 == "4" or self.data11 == "6" or self.data11 == "9" or self.data11 == "16"):
                flash("保存しました。", "success")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()                
                        
            
            elif self.data7 == "1" and self.data11 != "1":
                if self.data2 == "00:00" and self.data3 == "00:00":
                    flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()                    
                    
                elif self.data2 != "00:00" and self.data3 != "00:00":                       
                    flash("保存しました。", "success")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit() 

            
            elif self.data7 == "2" and (self.data11 == "" or self.data11 == "4" or self.data11 == "6" or self.data11 == "9" or self.data11 == "16"):
                if self.data2 == "00:00" and self.data3 == "00:00":
                    flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()                    

                elif self.data2 != "00:00" and self.data3 != "00:00":                    
                    flash("保存しました。", "success")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()
                
                
            elif self.data7 == "3" and self.data11 == "":
                flash("保存しました。", "success")
                start_time = "00:00"
                fin_time = "00:00"                  
                skyori = "0.0"
                oncall = 0
                oncall_cnt = "0"
                
                todokede = self.data7                                          

                zangyou = 0
                engel = "0"
                    
                todokede_PM = ""
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
                
            elif (self.data7 == "4" and self.data11 != "4") or (self.data7 == "16" and self.data11 != "16"):
                if self.data11 == "6":
                    flash("保存しました。", "success")
                    start_time = "00:00"
                    fin_time = "00:00"
                    skyori = data4
                    oncall = 0
                    oncall_cnt = "0"
                    
                    todokede = self.data7
                    zangyou = 0
                    engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()
                
                elif self.data11 != "6":
                    if self.data2 == "00:00" and self.data3 == "00:00" and self.data11 != "":
                        flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                        start_time = self.data2
                        fin_time = self.data3                  
                        skyori = data4
                        
                        if self.data5 == "on":
                            oncall = 1
                        else:
                            oncall = 0

                        if self.data6 != "0":
                            oncall_cnt = self.data6
                        elif self.data6 == "" or self.data6 == "0":
                            oncall_cnt = "0"
                        
                        todokede = self.data7                                          

                        if self.data8 == "on":
                            zangyou = 1
                        else:
                            zangyou = 0
                            
                        if self.data9 != "0":
                            engel = self.data9
                        elif self.data9 == "" or self.data9 == "0":
                            engel = "0"
                            
                        todokede_PM = self.data11
                    
                        sh.WORKDAY = hiduke
                        sh.STARTTIME = start_time
                        sh.ENDTIME = fin_time
                        sh.MILEAGE = skyori
                        sh.STAFFID = user_s_id
                        sh.ONCALL = oncall
                        sh.ONCALL_COUNT = oncall_cnt
                        sh.NOTIFICATION = todokede
                        sh.OVERTIME = zangyou
                        sh.ENGEL_COUNT = engel
                        sh.REMARK = bikou
                        sh.NOTIFICATION2 = todokede_PM
                        db.session.commit()

                    elif self.data2 == "00:00" and self.data3 == "00:00" and self.data11 == "":
                        flash("保存しました。", "success")
                        start_time = self.data2
                        fin_time = self.data3                  
                        skyori = data4
                        
                        if self.data5 == "on":
                            oncall = 1
                        else:
                            oncall = 0

                        if self.data6 != "0":
                            oncall_cnt = self.data6
                        elif self.data6 == "" or self.data6 == "0":
                            oncall_cnt = "0"
                        
                        todokede = self.data7                                          

                        if self.data8 == "on":
                            zangyou = 1
                        else:
                            zangyou = 0
                            
                        if self.data9 != "0":
                            engel = self.data9
                        elif self.data9 == "" or self.data9 == "0":
                            engel = "0"
                            
                        todokede_PM = self.data11
                    
                        sh.WORKDAY = hiduke
                        sh.STARTTIME = start_time
                        sh.ENDTIME = fin_time
                        sh.MILEAGE = skyori
                        sh.STAFFID = user_s_id
                        sh.ONCALL = oncall
                        sh.ONCALL_COUNT = oncall_cnt
                        sh.NOTIFICATION = todokede
                        sh.OVERTIME = zangyou
                        sh.ENGEL_COUNT = engel
                        sh.REMARK = bikou
                        sh.NOTIFICATION2 = todokede_PM
                        db.session.commit()
                        
                    elif self.data2 != "00:00" and self.data3 != "00:00":
                        flash("保存しました。", "success")
                        start_time = self.data2
                        fin_time = self.data3                  
                        skyori = data4
                        
                        if self.data5 == "on":
                            oncall = 1
                        else:
                            oncall = 0

                        if self.data6 != "0":
                            oncall_cnt = self.data6
                        elif self.data6 == "" or self.data6 == "0":
                            oncall_cnt = "0"
                        
                        todokede = self.data7                                          

                        if self.data8 == "on":
                            zangyou = 1
                        else:
                            zangyou = 0
                            
                        if self.data9 != "0":
                            engel = self.data9
                        elif self.data9 == "" or self.data9 == "0":
                            engel = "0"
                            
                        todokede_PM = self.data11
                    
                        sh.WORKDAY = hiduke
                        sh.STARTTIME = start_time
                        sh.ENDTIME = fin_time
                        sh.MILEAGE = skyori
                        sh.STAFFID = user_s_id
                        sh.ONCALL = oncall
                        sh.ONCALL_COUNT = oncall_cnt
                        sh.NOTIFICATION = todokede
                        sh.OVERTIME = zangyou
                        sh.ENGEL_COUNT = engel
                        sh.REMARK = bikou
                        sh.NOTIFICATION2 = todokede_PM
                        db.session.commit()
                
            
            elif self.data7 == "5" and self.data11 == "":
                flash("保存しました。", "success")
                start_time = "00:00"
                fin_time = "00:00"                  
                skyori = data4
                oncall = 0
                oncall_cnt = "0"
                
                todokede = self.data7                                          

                zangyou = 0
                engel = "0"
                    
                todokede_PM = ""
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            
            elif self.data7 == "6" and self.data11 != "6":
                if self.data11 == "4" or self.data11 == "16":
                    flash("保存しました。", "success")
                    start_time = "00:00"
                    fin_time = "00:00"                  
                    skyori = "0.0"
                    oncall = 0
                    oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    zangyou = 0
                    engel = "0"
                        
                    todokede_PM = ""
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()                    
                elif self.data11 != "4" or self.data11 != "16":
                    if self.data2 == "00:00" and self.data3 == "00:00" and self.data11 != "":                
                        flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                        start_time = self.data2
                        fin_time = self.data3                  
                        skyori = data4
                        
                        if self.data5 == "on":
                            oncall = 1
                        else:
                            oncall = 0

                        if self.data6 != "0":
                            oncall_cnt = self.data6
                        elif self.data6 == "" or self.data6 == "0":
                            oncall_cnt = "0"
                        
                        todokede = self.data7                                          

                        if self.data8 == "on":
                            zangyou = 1
                        else:
                            zangyou = 0
                            
                        if self.data9 != "0":
                            engel = self.data9
                        elif self.data9 == "" or self.data9 == "0":
                            engel = "0"
                            
                        todokede_PM = self.data11
                    
                        sh.WORKDAY = hiduke
                        sh.STARTTIME = start_time
                        sh.ENDTIME = fin_time
                        sh.MILEAGE = skyori
                        sh.STAFFID = user_s_id
                        sh.ONCALL = oncall
                        sh.ONCALL_COUNT = oncall_cnt
                        sh.NOTIFICATION = todokede
                        sh.OVERTIME = zangyou
                        sh.ENGEL_COUNT = engel
                        sh.REMARK = bikou
                        sh.NOTIFICATION2 = todokede_PM
                        db.session.commit()
                        
                    elif self.data2 == "00:00" and self.data3 == "00:00" and self.data11 == "":                
                        flash("保存しました。", "success")
                        start_time = self.data2
                        fin_time = self.data3                  
                        skyori = data4
                        
                        if self.data5 == "on":
                            oncall = 1
                        else:
                            oncall = 0

                        if self.data6 != "0":
                            oncall_cnt = self.data6
                        elif self.data6 == "" or self.data6 == "0":
                            oncall_cnt = "0"
                        
                        todokede = self.data7                                          

                        if self.data8 == "on":
                            zangyou = 1
                        else:
                            zangyou = 0
                            
                        if self.data9 != "0":
                            engel = self.data9
                        elif self.data9 == "" or self.data9 == "0":
                            engel = "0"
                            
                        todokede_PM = self.data11
                    
                        sh.WORKDAY = hiduke
                        sh.STARTTIME = start_time
                        sh.ENDTIME = fin_time
                        sh.MILEAGE = skyori
                        sh.STAFFID = user_s_id
                        sh.ONCALL = oncall
                        sh.ONCALL_COUNT = oncall_cnt
                        sh.NOTIFICATION = todokede
                        sh.OVERTIME = zangyou
                        sh.ENGEL_COUNT = engel
                        sh.REMARK = bikou
                        sh.NOTIFICATION2 = todokede_PM
                        db.session.commit()                        
                        
                        
                    elif self.data2 != "00:00" and self.data3 != "00:00":
                        flash("保存しました。", "success")
                        start_time = self.data2
                        fin_time = self.data3                  
                        skyori = data4
                        
                        if self.data5 == "on":
                            oncall = 1
                        else:
                            oncall = 0

                        if self.data6 != "0":
                            oncall_cnt = self.data6
                        elif self.data6 == "" or self.data6 == "0":
                            oncall_cnt = "0"
                        
                        todokede = self.data7                                          

                        if self.data8 == "on":
                            zangyou = 1
                        else:
                            zangyou = 0
                            
                        if self.data9 != "0":
                            engel = self.data9
                        elif self.data9 == "" or self.data9 == "0":
                            engel = "0"
                            
                        todokede_PM = self.data11
                    
                        sh.WORKDAY = hiduke
                        sh.STARTTIME = start_time
                        sh.ENDTIME = fin_time
                        sh.MILEAGE = skyori
                        sh.STAFFID = user_s_id
                        sh.ONCALL = oncall
                        sh.ONCALL_COUNT = oncall_cnt
                        sh.NOTIFICATION = todokede
                        sh.OVERTIME = zangyou
                        sh.ENGEL_COUNT = engel
                        sh.REMARK = bikou
                        sh.NOTIFICATION2 = todokede_PM
                        db.session.commit()
                
            
            elif self.data7 == "7" and self.data11 == "":                                                                                
                flash("保存しました。", "success")
                start_time = "00:00"
                fin_time = "00:00"                  
                skyori = "0.0"
                oncall = 0
                oncall_cnt = "0"
                
                todokede = self.data7                                          

                zangyou = 0
                engel = "0"
                    
                todokede_PM = ""
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()

            
            elif (self.data7 == "8" or self.data7 == "9" or self.data7 == "17" or self.data7 == "18" or self.data7 == "19" or self.data7 == "20") and self.data11 == "":
                flash("保存しました。", "success")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
                
            elif (self.data7 == "10" or self.data7 == "11" or self.data7 == "12" or self.data7 == "13" or \
                self.data7 == "14" or self.data7 == "15") and self.data11 != "1":
                if self.data2 == "00:00" and self.data3 == "00:00":
                    flash(str(self.data1) + "について、正しい勤務時間を入力してください。", "warning")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()
                elif self.data2 != "00:00" and self.data3 != "00:00":
                    flash("保存しました。", "success")
                    start_time = self.data2
                    fin_time = self.data3                  
                    skyori = data4
                    
                    if self.data5 == "on":
                        oncall = 1
                    else:
                        oncall = 0

                    if self.data6 != "0":
                        oncall_cnt = self.data6
                    elif self.data6 == "" or self.data6 == "0":
                        oncall_cnt = "0"
                    
                    todokede = self.data7                                          

                    if self.data8 == "on":
                        zangyou = 1
                    else:
                        zangyou = 0
                        
                    if self.data9 != "0":
                        engel = self.data9
                    elif self.data9 == "" or self.data9 == "0":
                        engel = "0"
                        
                    todokede_PM = self.data11
                
                    sh.WORKDAY = hiduke
                    sh.STARTTIME = start_time
                    sh.ENDTIME = fin_time
                    sh.MILEAGE = skyori
                    sh.STAFFID = user_s_id
                    sh.ONCALL = oncall
                    sh.ONCALL_COUNT = oncall_cnt
                    sh.NOTIFICATION = todokede
                    sh.OVERTIME = zangyou
                    sh.ENGEL_COUNT = engel
                    sh.REMARK = bikou
                    sh.NOTIFICATION2 = todokede_PM
                    db.session.commit()


            ##### 届出別条件分岐2
            elif self.data7 == "1" and self.data11 == "1":                        
                flash(str(self.data1) + "について、同時に同じ届出はできません。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit() 

            
            elif self.data7 == "2" and (self.data11 !="4" or self.data11 != "6" or self.data11 != "9" or self.data11 != "16"):
                flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
                
            elif self.data7 == "3" and self.data11 != "": 
                flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
                
            elif self.data7 == "4" and self.data11 == "4":
                flash(str(self.data1) + "について、同時に同じ届出はできません。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            
            elif self.data7 == "5" and self.data11 != "":
                flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            
            elif self.data7 == "6" and self.data11 == "6":
                flash(str(self.data1) + "について、同時に同じ届出はできません。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            
            elif (self.data7 == "7" or self.data7 == "8" or self.data7 == "17" or self.data7 == "18" or self.data7 == "19" or self.data7 == "20") and self.data11 != "":                                                                                
                flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
            
            elif self.data7 == "9" and self.data11 != "":
                flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()
                
                
            elif (self.data7 == "10" or self.data7 == "11" or self.data7 == "12" or self.data7 == "13" or \
                self.data7 == "14" or self.data7 == "15") and self.data11 == "1":
                flash(str(self.data1) + "について、届出を入力しなおしてください。", "warning")
                start_time = self.data2
                fin_time = self.data3                  
                skyori = data4
                
                if self.data5 == "on":
                    oncall = 1
                else:
                    oncall = 0

                if self.data6 != "0":
                    oncall_cnt = self.data6
                elif self.data6 == "" or self.data6 == "0":
                    oncall_cnt = "0"
                
                todokede = self.data7                                          

                if self.data8 == "on":
                    zangyou = 1
                else:
                    zangyou = 0
                    
                if self.data9 != "0":
                    engel = self.data9
                elif self.data9 == "" or self.data9 == "0":
                    engel = "0"
                    
                todokede_PM = self.data11
            
                sh.WORKDAY = hiduke
                sh.STARTTIME = start_time
                sh.ENDTIME = fin_time
                sh.MILEAGE = skyori
                sh.STAFFID = user_s_id
                sh.ONCALL = oncall
                sh.ONCALL_COUNT = oncall_cnt
                sh.NOTIFICATION = todokede
                sh.OVERTIME = zangyou
                sh.ENGEL_COUNT = engel
                sh.REMARK = bikou
                sh.NOTIFICATION2 = todokede_PM
                db.session.commit()

            
            ##### 休日チェック #####
            if ((self.data7 != "7" or self.data7 != "8" or self.data7 != "17" or self.data7 != "18" or self.data7 != "19" or self.data7 != "20") and \
                ((self.data7 != "" or self.data11 != "") or (self.data2 != "00:00" and self.data3 != "00:00") or self.data5)) and \
                    jpholiday.is_holiday_name(self.c):
                        holiday = "2"
                        sh.HOLIDAY = holiday
                        db.session.commit()
            elif ((self.data7 != "7" or self.data7 != "8" or self.data7 != "17" or self.data7 != "18" or self.data7 != "19" or self.data7 != "20") and \
                ((self.data7 != "" or self.data11 != "") or (self.data2 != "00:00" and self.data3 != "00:00") or self.data5)) and \
                    get_day_of_week_jp(self.c) == "1":
                        holiday = "1"
                        sh.HOLIDAY = holiday
                        db.session.commit()
            else:
                holiday = ""
                sh.HOLIDAY = holiday
                db.session.commit()

            ##### リフレッシュ休暇取得制限設定 #####
            if self.data7 == "7":
                d_input = datetime.strptime(hiduke, '%Y-%m-%d')
                dm = monthmod(inday.replace(month=4, day=1),
                                d_input.replace(month=4, day=1))[0].months

                if inday.month >= 4 and inday.month <= 7:
                    if d_input >= inday and d_input < inday.replace(month=4, day=1) + relativedelta(months=12):
                        # reflesh = 3

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday and d < inday.replace(month=4, day=1) + relativedelta(months=12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        elif n == 2:
                            sh.NOTIFICATION = "7"

                        elif n == 3:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                    elif d_input >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d_input < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                        # reflesh = 3

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        elif n == 2:
                            sh.NOTIFICATION = "7"

                        elif n == 3:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                elif inday.month >= 8 and inday.month <= 11:
                    if d_input >= inday and d_input < inday.replace(month=4, day=1) + relativedelta(months=12):
                        # reflesh = 2

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday and d < inday.replace(month=4, day=1) + relativedelta(months=12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        elif n == 2:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                    elif d_input >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d_input < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                        # reflesh = 3

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        elif n == 2:
                            sh.NOTIFICATION = "7"

                        elif n == 3:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                elif inday.month == 12:
                    if d_input >= inday and d_input < inday.replace(month=4, day=1) + relativedelta(months=12):
                        # reflesh = 1

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday and d < inday.replace(month=4, day=1) + relativedelta(months=12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                    elif d_input >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d_input < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                        # reflesh = 3

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        elif n == 2:
                            sh.NOTIFICATION = "7"

                        elif n == 3:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                elif inday.month <= 3:
                    if d_input >= inday and d_input < inday.replace(month=4, day=1):
                        # reflesh = 1

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday and d < inday.replace(month=4, day=1):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

                    elif d_input >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d_input < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                        # reflesh = 3

                        n = 1
                        for shs in shinseis:
                            dd = shs.WORKDAY
                            d = datetime.strptime(dd, "%Y-%m-%d")
                            if d >= inday.replace(month=4, day=1) + relativedelta(months=dm) and d < inday.replace(month=4, day=1) + relativedelta(months=dm+12):
                                if shs.NOTIFICATION == "7":
                                    n = n + 1

                        if n == 1:
                            sh.NOTIFICATION = "7"

                        elif n == 2:
                            sh.NOTIFICATION = "7"

                        elif n == 3:
                            sh.NOTIFICATION = "7"

                        else:
                            flash("取得可能なリフレッシュ休暇数を超えています。", "warning")

            else:
                sh.NOTIFICATION = self.data7  # その他の届出
                db.session.commit()
            
            
            """if (jpholiday.is_holiday_name(self.c) or get_day_of_week_jp(self.c) == "1") and (sh.NOTIFICATION == "1" or sh.NOTIFICATION == "2" or sh.NOTIFICATION == "3" \
                or sh.NOTIFICATION == "4" or sh.NOTIFICATION == "7" or sh.NOTIFICATION == "8" or sh.NOTIFICATION == "9" \
                    or sh.NOTIFICATION2 == "1" or sh.NOTIFICATION2 == "2" or sh.NOTIFICATION2 == "8" or sh.NOTIFICATION2 == "9"):
                sh.NOTIFICATION = ""
                sh.NOTIFICATION2 = ""
                db.session.commit()"""                      
      