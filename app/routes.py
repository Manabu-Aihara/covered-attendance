"""
**********
勤怠システム
2022/04版
**********
"""

from app import routes_attendance
from app import kinmu_index
from app import routes_approvals
from app import routes_admin
from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede
from flask_login import logout_user
from flask import abort
from functools import wraps
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import jpholiday
import os




"""***** ログイン後最初のページ *****"""


@app.route('/')
@app.route('/select_links', methods=['GET', 'POST'])
@login_required
def select_links():
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    STAFFID = current_user.STAFFID
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    u = User.query.get(STAFFID)

    team = u.TEAM_CODE  # この職員のチームコード
    jobtype = u.JOBTYPE_CODE # この職員の職種

    return render_template('select_links.html', title='Select link', STAFFID=STAFFID, shinseis=shinseis, u=u, team=team,
                           jobtype=jobtype, stf_login=stf_login, typ=typ)


"""***** ログイン・ログアウト処理 *****"""
@ app.route('/logout_mes', methods=['GET', 'POST'])
def logout_mes():
    return render_template('logout_mes.html') 



@ app.route('/login', methods=['GET', 'POST'])
def login():  
    if current_user.is_authenticated:
        return redirect(url_for('select_links'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = StaffLoggin.query.filter_by(STAFFID=form.STAFFID.data).first()
        if user is None or not user.check_password(form.PASSWORD.data):
            flash('ユーザ名かパスワードが違います')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('select_links')
        return redirect(next_page)
    return render_template('login.html', title='yoboiryo株式会社 System', form=form)


@ app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('logout_mes'))


"""***** WebブラウザのCSSキャッシュ対策 *****"""


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
