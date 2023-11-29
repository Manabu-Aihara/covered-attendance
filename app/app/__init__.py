from flask import Flask, request, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_bcrypt import Bcrypt
from jinja2 import Environment
from flask_wtf.csrf import CSRFProtect, CSRFError
from datetime import timedelta
import logging

# loggerを定義
logger = logging.getLogger(__name__)

# loggerのログレベルを設定
logger.setLevel(logging.WARNING)

# loggerのフォーマット、出力先ファイルを定義
formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)s - %(message)s')
file_handler = logging.FileHandler('test.log')
file_handler.setFormatter(formatter)

# loggerのフォーマット、出力先ファイルを設定
logger.addHandler(file_handler)

logger.warning("warning")
logger.error("error")


LOGFILE_NAME = "DEBUG.log"

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=360),
)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
moment = Moment(app)
bcrypt = Bcrypt(app)

jinja_env = Environment(extensions=['jinja2.ext.i18n'])
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

app.logger.setLevel(logging.DEBUG)
log_handler = logging.FileHandler(LOGFILE_NAME)
log_handler.setLevel(logging.DEBUG)
app.logger.addHandler(log_handler)


from app import routes, models, errors



if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/dakoku.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)s]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
