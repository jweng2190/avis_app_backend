import os
from flask_mail import Mail, Message
from flask import render_template

from avis_app import app, dao
#from avis_app.event_controller import dao

mail = Mail(app)


def send_sub_confirm_email_to(username, event_name):
    email = dao.get_email_by_username(username)
    email_text = 'Congratulations! You have subscribed to this event: %s.' % event_name
    msg = Message('Subscription Confirmation', sender="jweng2190@gmail.com", recipients=[email])
    msg.body = email_text
    mail.send(msg)

def send_password_reset_email_to(username, temp_password):
    email = dao.get_email_by_username(username)
    email_text = render_template('passwd_reset_email.html', username=username, tmp=temp_password)
    msg = Message('Password Reset', sender='jweng2190@gmail.com', recipients=[email])
    msg.html = email_text
    mail.send(msg)
    return temp_password   
