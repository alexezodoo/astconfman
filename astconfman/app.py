# -*- coding: utf-8 -*-

import os
from urllib import urlencode
from flask import Flask, send_from_directory, request, Response, session
from flask import g, redirect, url_for
from flask.ext.babelex import Babel, gettext, lazy_gettext
from flask.ext.socketio import SocketIO, emit, join_room
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin, AdminIndexView
from flask.ext.migrate import Migrate
from gevent import monkey
monkey.patch_all()


app = Flask('ConfMan', instance_relative_config=True)
app.config.from_object('config')

# For smooth language switcher 
def append_to_query(s, param, value):
    params = dict(request.args.items())
    params[param] = value
    url = '%s?%s' % (request.path, urlencode(params))
    print url
    return url
app.jinja_env.filters['append_to_query'] = append_to_query


try:
  app.config.from_pyfile('config.py')
except IOError:
  pass

db = SQLAlchemy()
db.init_app(app)

socketio = SocketIO(app)
@socketio.on('join')
def on_join(data):
    join_room(data['room'])


migrate = Migrate(app, db)

from models import Contact, Conference, Participant, ParticipantProfile, ConferenceProfile
from views import ContactAdmin, ConferenceAdmin, ParticipantAdmin, RecordingAdmin
from views import ParticipantProfileAdmin, ConferenceProfileAdmin


babel = Babel(app)
@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')        
    return session.get('lang', app.config.get('LANGUAGE'))


import logging
logging.basicConfig()
# Enable SMTP errors
if not app.debug and app.config['SMTP_LOG_ENABLED']:
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler((app.config['SMTP_HOST'], app.config['SMTP_PORT']),
                               app.config['SMTP_FROM'],
                               [v['email'] for k,v in app.config['ADMINS'].items()],
                               'ConfMain Error')
    mail_handler.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
    '''))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

if app.config['LOG_ENABLED']:
    file_handler = logging.FileHandler(app.config['LOG_FILE'])
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


from views_asterisk import asterisk
app.register_blueprint(asterisk, url_prefix='/asterisk')
