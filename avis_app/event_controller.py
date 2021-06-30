import json
import random
import string
from datetime import date, datetime, timedelta

import flask_login
import mysql.connector
from flask import Response, jsonify, render_template, request
from flask_login import login_required

from avis_app import app, dao, redis_client
from avis_app.event_service import *
from avis_app.mail_service import *
from avis_app.request_decorators import current_user_only, roles_required
from avis_app.json_encoder import CustomJSONEncoder


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/create', methods=['POST'])
def create_user():
    username = request.json.get('username').lower()
    password = request.json.get('password')
    realname = request.json.get('realname')
    email = request.json.get('email')
    success = dao.add_user(username, password, realname, email)
    if success is True:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


@app.route('/passwd_reset', methods=['POST'])
def reset_passwd():
    '''
    Password is reset automatically and a temporary password is generated.
    '''
    username = request.form.get('username').lower()
    user_existed = dao.check_username(username)
    if user_existed is False:
        return Response('username doesn\'t exist')
    temp_password = ''.join(random.choices('abcdefghijkmnpqrstuvwxyz' + 'ABCDEFGHJKLMNPQRSTUVWXYZ' + \
        string.digits + '!#$', k=8))
    dao.change_user_password_and_update_status(username, temp_password, 'reset')
    send_password_reset_email_to(username, temp_password)

    return Response('reset done')


@app.route('/passwd_change', methods=['POST'])
@login_required
def change_passwd():
    '''
    Password is manually changed by a user.
    A new password will be entered by a user.
    '''
    username = flask_login.current_user.id
    new_password = request.form.get('password')
    connection = dao.conn
    try:
        dao.change_user_password(username, new_password)
        dao.update_user_status(username, 'active')
        connection.commit()
        response = 'change done'
        status_code = 200
    except mysql.connector.Error as err:
        app.logger.error(err.msg)
        connection.rollback()
        response = 'change failed'
        status_code = 500

    return Response(response, status=status_code)



@app.route('/events/<date>')
@login_required
def get_events_by_date(date):
    events, col_names = dao.get_event_by_date(date)
    print(col_names)
    event_info_list = []
    event_key_list = col_names
    for item in events:
        event_info = dict(zip(event_key_list, item))
        event_info_list.append(event_info)
    return jsonify(event_info_list)


@app.route('/events/dates')
@login_required
def get_events_by_date_range():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    app.logger.info('Start date is %s' % start_date)
    app.logger.info('End date is %s' % end_date)
    events, col_names = dao.get_events_by_date_range(start_date, end_date)
    event_info_list = []
    for item in events:
        event_info = dict(zip(col_names, item))
        event_info_list.append(event_info)
    return jsonify(event_info_list)


@app.route('/subscribe/user/event', methods=['POST'])
@login_required
@current_user_only
def sub_user_to_event():
    username = request.json.get('username')
    event_id = request.json.get('event_id')
    success = dao.subscribe_user_to_event(username, event_id)
    if success is True:
        event_desc = dao.get_event_desc_by_event_id(event_id)
        #send_sub_confirm_email_to(username, event_desc)
        response = jsonify({"success": True}), 201
    else:
        response = jsonify({"success": False}), 400
    return response

@app.route('/unsubscribe/user/event', methods=['POST'])
@login_required
@current_user_only
def unsub_user_to_event():
    username = request.json.get('username')
    event_id = request.json.get('event_id')
    success = dao.unsubscribe_user_to_event(username, event_id)
    if success is True:
        response = jsonify({"sucess": True}), 200
    else:
        response = jsonify({"success": False}), 400
    return response


@app.route('/events/user/<user_id>')
@login_required
@current_user_only
def get_events_by_user(user_id):
    user_id = int(user_id)
    col_names, events = dao.get_events_by_user(user_id)
    print(col_names)
    event_info_list = []
    event_key_list = col_names
    for item in events:
        event_info = dict(zip(event_key_list, item))
        event_info_list.append(event_info)
    return jsonify(event_info_list)


@app.route('/upcoming_events/user/<user_id>')
@login_required
@current_user_only
def get_upcoming_events_by_user(user_id):
    user_id = int(user_id)
    col_names, upcoming_events = get_my_upcoming_events(user_id)
    event_info_list = []
    event_key_list = col_names
    for item in upcoming_events:
        event_info = dict(zip(event_key_list, item))
        event_info_list.append(event_info)
    event_info_list.sort(key = lambda x: x['date_time'])
    return jsonify(event_info_list)

        
@app.route('/other_events/user/<user_id>')
@login_required
@current_user_only
def get_other_events_by_user(user_id):
    user_id = int(user_id)
    col_names, other_events = get_other_upcoming_events(user_id)
    event_info_list = []
    event_key_list = col_names
    for item in other_events:
        event_info = dict(zip(event_key_list, item))
        event_info_list.append(event_info)
    event_info_list.sort(key=lambda x: x['date_time'])
    return jsonify(event_info_list)


@app.route('/past_events/user/<user_id>')
@login_required
@current_user_only
def get_past_events_by_user(user_id):
    user_id = int(user_id)
    col_names, past_events = get_past_events()
    event_info_list = []
    event_key_list = col_names
    for item in past_events:
        event_info = dict(zip(event_key_list, item))
        event_info_list.append(event_info)
    event_info_list.sort(key=lambda x: x['date_time'], reverse=True)
    return jsonify(event_info_list)


@app.route('/replace/event', methods=['PUT'])
@login_required
@current_user_only
def replace_event_by_user_id():
    old_event_id = request.json.get('old_event_id')
    username = request.json.get('username')
    new_event_id = request.json.get('new_event_id')
    try:
        user_id = dao.get_id_by_username(username)
        dao.replace_event_by_user_id(new_event_id, old_event_id, user_id)
        response = Response(response="Success!", status=201)
    except mysql.connector.Error as e:
        response = Response(status=400)
    return response


@app.route('/users/events/<event_id>')
@login_required
def get_users_by_event(event_id):
    col_names, users = dao.get_users_by_event(event_id)
    print(col_names)
    user_info_list = []
    user_key_list = col_names
    for item in users:
        user_info = dict(zip(user_key_list, item))
        user_info_list.append(user_info)
    return jsonify(user_info_list)


@app.route('/user/delete/<username>', methods=['DELETE'])
@login_required
@roles_required('admin')
def delete_user(username):
    try:
        dao.delete_user(username)
        return Response(status=200)
    except mysql.connector.Error as err:
        print('There was an error: %s' % err)
        return Response(status=500)


@app.route('/events')
@login_required
def search_event():
    event_keyword = request.args.get('q').lower()
    col_names, event_related_list = dao.search_event_by_keyword(event_keyword)
    if len(event_related_list) == 0:
        column_names, suggestion_list = suggest_possible_events(event_keyword)
        if len(suggestion_list) == 0:
            return jsonify({'result_found': False})
        else:
            event_related_list = suggestion_list

    user_id = dao.get_id_by_username(flask_login.current_user.id)
    col_names, my_upcoming_events = get_my_upcoming_events(user_id)
    _, other_upcoming_events = get_other_upcoming_events(user_id)
    _, past_events = get_past_events()

    my_upcoming_containing_search = set(event_related_list).intersection(set(my_upcoming_events))
    other_upcoming_containing_search = set(event_related_list).intersection(set(other_upcoming_events))
    past_containing_search = set(event_related_list).intersection(set(past_events))
    all_search_result = dict()
    if my_upcoming_containing_search:
        my_upcoming_search_list = []
        for item in my_upcoming_containing_search:
            my_upcoming_search_list.append(dict(zip(col_names, item)))
        all_search_result['my_upcoming'] = my_upcoming_search_list

    if other_upcoming_containing_search:
        other_upcoming_search_list = []
        for item in other_upcoming_containing_search:
            other_upcoming_search_list.append(dict(zip(col_names, item)))
        all_search_result['other_upcoming'] = other_upcoming_search_list

    if past_containing_search:
        past_search_list = []
        for item in past_containing_search:
            past_search_list.append(dict(zip(col_names, item)))
        all_search_result['past'] = past_search_list

    return jsonify(all_search_result)


@app.route('/events/upcoming')
def get_events_upcoming():
    """ Upcoming events

    This is the default event list for visitor's view without user login.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    app.logger.info('Today is %s' % today)
    # future date from today
    future_date = today + timedelta(days=180)
    app.logger.info('Future is %s' % future_date)
    events, col_names = dao.get_events_by_date_range(tomorrow.strftime('%Y-%m-%d'), future_date.strftime('%Y-%m-%d'))
    event_info_list = []
    for item in events:
        event_info = dict(zip(col_names, item))
        event_info_list.append(event_info)
    return jsonify(event_info_list)


@app.route('/events/all')
def get_events_all():
    col_names, events = dao.get_all_events()
    upcoming_events_list = []
    past_events_list = []
    now = datetime.now()
    datetime_tbd = datetime.strptime('1000-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
    for item in events:
        event_info = dict(zip(col_names, item))
        event_datetime = event_info['date_time']
        if event_datetime > now or event_datetime == datetime_tbd:
            upcoming_events_list.append(event_info)
        else:
            past_events_list.append(event_info)
    event_info_list = {}
    if upcoming_events_list:
        event_info_list['upcoming'] = upcoming_events_list
    if past_events_list:
        event_info_list['past'] = past_events_list
    jsonEncoder = CustomJSONEncoder()
    redis_client.put_all_events(jsonEncoder.encode(event_info_list))    
    return jsonify(event_info_list)
