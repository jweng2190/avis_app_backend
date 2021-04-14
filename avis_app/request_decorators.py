from functools import wraps

import flask_login
from flask import Response, request

from avis_app.event_controller import dao


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = flask_login.current_user.id
            user_roles = dao.get_user_roles(username)
            for role in roles:
                if role not in user_roles:
                    return Response(response='Denied for access', status=403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def current_user_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_username = flask_login.current_user.id
        if len(args) == 0 and len(kwargs) == 0:
            if request.json is not None:
                username = request.json.get('username')
            elif len(request.form) != 0:
                username = request.form.get('username')
            elif len(request.args) != 0:
                username = request.args.get('username')
            else:
                return Response(response='No username entered', status=400)
        else:
            user_id = kwargs['user_id']
            username = dao.get_username_by_id(user_id)
        if current_username != username:
            return Response(response='Access denied', status=403)
        return f(*args, **kwargs)
    return decorated_function

