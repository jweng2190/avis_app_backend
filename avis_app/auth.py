import base64

from flask import url_for, render_template, request, redirect, Response, jsonify
from flask_login import UserMixin, login_user, logout_user, LoginManager

from avis_app import app, dao

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    pass

# db = SQLAlchemy(app)
#
# roles_users = db.Table('roles_users', db.Column('user_id', db.Integer(), db.ForeignKey('user_account.id')),
#         db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))
#
#
# class User(db.Model, UserMixin):
#     __tablename__ = 'user_account'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(35), unique=True)
#     password = db.Column(db.String(64))
#     salt = db.Column(db.String(20))
#     real_name = db.Column(db.String(60))
#     email = db.Column(db.String(60))
#     roles = db.relationship('Role', secondary='roles_users', backref=db.backref('user_account', lazy='dynamic'))
#
#
# class Role(db.Model):
#     __tablename__ = 'role'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(20))
#     description = db.Column(db.String(255))


# class UserRoles(db.Model):
#     __tablename__ = 'roles_users'
#     user_id = db.Column(db.Integer, db.ForeignKey('user_account.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
#     role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


# user_datastore = SQLAlchemyUserDatastore(db, User, Role)
# security = Security(app, user_datastore)


@login_manager.user_loader
def load_user(username):
    if dao.check_username(username) is False:
        return None
    user = User()
    user.id = username
    return user


@login_manager.request_loader
def load_user_from_request(req):
    api_key = req.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key)
        except TypeError:
            pass
        username = api_key.decode('utf-8').split(':')[0].lower()
        password = api_key.decode('utf-8').split(':')[1]
        app.logger.info('username: %s' % username)
        app.logger.info('password: %s' % password)
        if dao.validate_user(username, password) is True:
            user = User()
            user.id = username
            return user
        else:
            return None


@app.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form.
    For POSTS, login the current user by processing the form.

    """
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username'].lower()
        password = request.form['password']
        app.logger.info('username: %s' % username)
        app.logger.info('password: %s' % password)

        if dao.validate_user(username, password) is True:
            user = User()
            user.id = username
            login_user(user)
            next_url = request.args.get('next')
            app.logger.info('Successful login!')
            app.logger.info('next_url: %s' % next_url)
            # if next_url is not None:
            #     return redirect(next_url)
            # else:
            #     return redirect(url_for('index'))
            user_status = dao.get_user_status(username)
            user_id = dao.get_id_by_username(username)
            if user_status == 'active':
                return jsonify({'success': True, 'reset_flag': False, 'user_id': user_id})
            elif user_status == 'reset':
                return jsonify({'success': True, 'reset_flag': True, 'user_id': user_id})
        else:
            #return render_template('login.html', msg='Incorrect username/password!')
            return jsonify({'success': False, 'user_id': None})

    # Show the login form with message (if any)
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_manager.unauthorized_handler
def unauthorized_callback():
    api_key = request.headers.get('Authorization')
    if api_key is None or api_key == '':
        return redirect('/login?next=' + request.path)
    else:
        return Response(response='Unauthorized login', status=401)


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

