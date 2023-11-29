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


class MakeCalender:
    def __init__(self, cal, hld, y, m):
        self.cal = cal
        self.hld = hld
        self.y = y
        self.m = m
        
    def mkcal(self):
        
        ##### カレンダー設計 #####
        if self.m == 1:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 1, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 1, d)))

        elif self.m == 3:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 3, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 3, d)))

        elif self.m == 5:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 5, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 5, d)))

        elif self.m == 7:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 7, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 7, d)))

        elif self.m == 8:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 8, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 8, d)))

        elif self.m == 10:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 10, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 10, d)))

        elif self.m == 12:
            ds = 31
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 12, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 12, d)))

        elif self.m == 4:
            ds = 30
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 4, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 4, d)))

        elif self.m == 6:
            ds = 30
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 6, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 6, d)))

        elif self.m == 9:
            ds = 30
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 9, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 9, d)))

        elif self.m == 11:
            ds = 30
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 11, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 11, d)))

        elif self.y % 4 != 0 and self.m == 2:
            ds = 28
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 2, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 2, d)))

        elif self.y % 4 == 0 and self.m == 2:
            ds = 29
            for d in range(1, ds + 1):
                self.cal.append(datetime(self.y, 2, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 2, d)))        



class MakeCalender26:
    def __init__(self, cal, hld, y, m):
        self.cal = cal
        self.hld = hld
        self.y = y
        self.m = m
        
    def mkcal(self):
        
        ##### カレンダー設計 #####
        if self.m == 1:
            for d in range(26, 32):
                self.cal.append(datetime(self.y-1, 12, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y-1, 12, d)))
                            
            for d in range(1, 26):
                self.cal.append(datetime(self.y, 1, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 1, d)))

        elif (self.y-1) % 4 != 0 and self.m == 3:
            for d in range(26, 29):
                self.cal.append(datetime(self.y, 2, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 2, d)))            
            
            for d in range(1, 26):
                self.cal.append(datetime(self.y, 3, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 3, d)))

        elif (self.y-1) % 4 == 0 and self.m == 3:
            for d in range(26, 30):
                self.cal.append(datetime(self.y, 2, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 2, d)))            
            
            for d in range(1, 26):
                self.cal.append(datetime(self.y, 3, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 3, d)))

        elif self.m == 5:
            for d in range(26, 31):
                self.cal.append(datetime(self.y, 4, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 5, d)))            
            
            for d in range(1, 26):
                self.cal.append(datetime(self.y, 5, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 5, d)))

        elif self.m == 7:
            for d in range(26, 31):
                self.cal.append(datetime(self.y, 6, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 6, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 7, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 7, d)))

        elif self.m == 8:
            for d in range(26, 32):
                self.cal.append(datetime(self.y, 7, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 7, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 8, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 8, d)))

        elif self.m == 10:
            for d in range(26, 31):
                self.cal.append(datetime(self.y, 9, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 9, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 10, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 10, d)))

        elif self.m == 12:
            for d in range(26, 31):
                self.cal.append(datetime(self.y, 11, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 11, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 12, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 12, d)))

        elif self.m == 4:
            for d in range(26, 32):
                self.cal.append(datetime(self.y, 3, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 3, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 4, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 4, d)))

        elif self.m == 6:
            for d in range(26, 32):
                self.cal.append(datetime(self.y, 5, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 5, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 6, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 6, d)))

        elif self.m == 9:
            for d in range(26, 32):
                self.cal.append(datetime(self.y, 8, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 8, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 9, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 9, d)))

        elif self.m == 11:
            for d in range(26, 32):
                self.cal.append(datetime(self.y, 10, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 10, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 11, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 11, d)))

        elif self.m == 2:
            for d in range(26, 32):
                self.cal.append(datetime(self.y, 1, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 1, d)))

            for d in range(1, 26):
                self.cal.append(datetime(self.y, 2, d))
                self.hld.append(jpholiday.is_holiday_name(
                    datetime(self.y, 2, d)))
       
