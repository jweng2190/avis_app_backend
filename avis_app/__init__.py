from flask import Flask
import logging
import os

from avis_app.json_encoder import CustomJSONEncoder

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'AVIS Team'

app.logger.setLevel(logging.INFO)
app.json_encoder = CustomJSONEncoder

from avis_app.db import AvisDAO

db_username = os.environ['MYSQLDB_USERNAME']
db_password = os.environ['MYSQLDB_PASSWORD']
dao = AvisDAO(db_username, db_password, '72.167.43.203', 'avis_app')
#redis_cli = redis.Redis(host="ec2-13-58-197-138.us-east-2.compute.amazonaws.com", port=6379)

from avis_app import event_controller, auth


