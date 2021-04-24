import hashlib
import string
import random
import threading
import mysql.connector

from avis_app import app

class AvisDAO:
    def __init__(self, user, password, host, database):
        dbconfig = {
            "user": user,
            "password": password,
            "host": host,
            "database": database,
        }
        self.conn = mysql.connector.connect(pool_name='avis_pool', pool_size=5, **dbconfig)
        #self.conn = mysql.connector.connect(**dbconfig)
        # def pin_db():
        #     try:
        #         cursor = self.conn.cursor()
        #         cursor.execute('SELECT 1 FROM event_info')
        #     except mysql.connector.Error as e:
        #         self.conn = mysql.connector.connect(pool_name='avis_pool', pool_size=5, **dbconfig)
        # threading.Timer(21600, pin_db).start()



    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def get_event_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM event_info WHERE DATE(date_time)=%s', (date,))
        col_names = cursor.column_names
        result_set = cursor.fetchall()

        event_info = []
        for item in result_set:
            event_info.append(item)

        return event_info, col_names

    def get_events_by_date_range(self, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * from event_info WHERE DATE(date_time) BETWEEN STR_TO_DATE(%s, "%Y-%m-%d") AND STR_TO_DATE(%s, "%Y-%m-%d") OR date_time="1000-01-01 00:00:00"',
         (start_date, end_date))
        #self.conn.commit()
        col_names = cursor.column_names
        result_set = cursor.fetchall()

        event_info = []
        for item in result_set:
            event_info.append(item)

        return event_info, col_names

    def add_user(self, username, password, real_name, email, role='user'):
        salt = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=16))
        password_salted = password + salt
        password_hashed = hashlib.sha256(password_salted.encode()).hexdigest()
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO user_account (username, password, salt, real_name, email) VALUES (%s, %s, %s, '
                           '%s,%s)', (username, password_hashed, salt, real_name, email))
            cursor.execute(
                'SELECT id FROM user_account WHERE username=%s', (username,))
            user_id = cursor.fetchone()[0]
            cursor.execute(
                'INSERT INTO roles_users SELECT %s, id FROM role WHERE name=%s', (user_id, role))
            self.conn.commit()
            return True
        except mysql.connector.Error as e:
            print('There was an error: %s' % e)
            return False

    def subscribe_user_to_event(self, username, event_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'SELECT id FROM user_account WHERE username=%s', (username,))
            result_set = cursor.fetchone()
            user_id = result_set[0]
            cursor.execute(
                'INSERT INTO user_event VALUES (%s, %s)', (user_id, event_id))
            self.conn.commit()
            return True
        except mysql.connector.Error as err:
            return False

    def unsubscribe_user_to_event(self, username, event_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'SELECT id FROM user_account WHERE username=%s', (username,))
            result_set = cursor.fetchone()
            user_id = result_set[0]
            cursor.execute('DELETE FROM user_event WHERE user_id=%s AND event_id=%s', (user_id, event_id))
            self.conn.commit()
            return True
        except:
            return False

    def get_events_by_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT e.* FROM event_info AS e INNER JOIN user_event AS u ON e.event_id=u.event_id WHERE '
                       'u.user_id=%s', (user_id,))
        #self.conn.commit()
        col_names = cursor.column_names
        result_set = cursor.fetchall()

        event_info = []
        for item in result_set:
            event_info.append(item)

        return col_names, event_info

    def replace_event_by_user_id(self, new_event_id, old_event_id, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM user_event WHERE event_id=%s AND user_id=%s', (new_event_id, user_id))
        if len(cursor.fetchall()) == 0:
            cursor.execute('UPDATE user_event SET event_id=%s WHERE event_id=%s AND user_id=%s',
                           (new_event_id, old_event_id, user_id))
        else:
            cursor.execute(
                'DELETE FROM user_event WHERE user_id=%s AND event_id=%s', (user_id, old_event_id))
        self.conn.commit()

    def get_users_by_event(self, event_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT ua.username, ua.real_name FROM user_account AS ua INNER JOIN user_event AS ue ON '
                       'ua.id=ue.user_id WHERE event_id=%s', (event_id,))
        col_names = cursor.column_names
        result_set = cursor.fetchall()

        user_info = []
        for item in result_set:
            user_info.append(item)

        return col_names, user_info

    def validate_user(self, username, password):
        cursor = self.conn.cursor()
        #cursor.execute(
        #    'SELECT salt FROM user_account WHERE username=%s', (username,))
        #salt = cursor.fetchone()[0]
        #password_salted = password + salt
        #password_hashed = hashlib.sha256(password_salted.encode()).hexdigest()
        cursor.execute(
            'SELECT * FROM user_account WHERE username=%s AND password=SHA2(CONCAT(%s, salt), 256)', (username, password))

        result_set = cursor.fetchall()
        self.conn.commit()
        cursor.close()
        if not result_set:
            return False
        else:
            return True

    def check_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT username FROM user_account WHERE username=%s', (username,))
        result_set = cursor.fetchall()
        if not result_set:
            return False
        else:
            return True

    def delete_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute(
            'DELETE FROM user_account WHERE username=%s', (username,))
        self.conn.commit()

    def get_user_roles(self, username):
        cursor = self.conn.cursor()
        cursor.execute('SELECT r.name FROM role AS r INNER JOIN roles_users AS ru ON r.id=ru.role_id INNER JOIN '
                       'user_account AS u ON ru.user_id=u.id WHERE u.username=%s', (username,))
        result_set = cursor.fetchall()
        roles = [x[0] for x in result_set]
        return roles

    def get_username_by_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT username FROM user_account WHERE id=%s', [user_id])
        result_set = cursor.fetchone()
        if result_set is not None:
            username = result_set[0]
        else:
            username = None
        return username

    def get_id_by_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id FROM user_account WHERE username=%s', [username])
        result_set = cursor.fetchone()
        user_id = result_set[0]
        return user_id

    def get_email_by_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT email FROM user_account WHERE username=%s', [username])
        result_set = cursor.fetchone()
        email = result_set[0]
        return email

    def get_event_desc_by_event_id(self, event_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT event_description FROM event_info WHERE event_id=%s', [event_id])
        result_set = cursor.fetchone()
        desc = result_set[0]
        return desc

    def search_event_by_keyword(self, keyword):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM event_info WHERE event_description LIKE %s', ["%" + keyword + "%"])
        col_names = cursor.column_names
        result_set = cursor.fetchall()
        event_related = []
        for item in result_set:
            event_related.append(item)
        return col_names, event_related

    def get_all_events(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM event_info')
        col_names = cursor.column_names
        result_set = cursor.fetchall()
        self.conn.commit()

        event_info = []
        for item in result_set:
            event_info.append(item)

        return col_names, event_info

    
    def update_user_status(self, username, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE user_account SET status=%s WHERE username=%s', (status, username))

    
    def change_user_password(self, username, new_password):
        new_salt = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=16))
        new_password_salted = new_password + new_salt
        new_password_hashed = hashlib.sha256(new_password_salted.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute('UPDATE user_account SET password=%s, salt=%s WHERE username=%s', \
                (new_password_hashed, new_salt, username))

    def change_user_password_and_update_status(self, username, new_password, status):
        cursor = self.conn.cursor()
        new_salt = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=16))
        new_password_salted = new_password + new_salt
        new_password_hashed = hashlib.sha256(new_password_salted.encode()).hexdigest()
        try:
            cursor.execute('UPDATE user_account SET password=%s, salt=%s, status=%s WHERE username=%s', \
                    (new_password_hashed, new_salt, status, username))
            #cursor.execute('UPDATE user_account SET status=%s WHERE username=%s', (status, username))
            self.conn.commit()
            cursor.close()
        except mysql.connector.Error as err:
            app.logger.error(err.msg)
            self.conn.rollback()

    
    def get_user_status(self, username):
        cursor = self.conn.cursor()
        cursor.execute('SELECT status FROM user_account WHERE username=%s', (username,))
        result_set = cursor.fetchone()
        status = result_set[0]
        return status
