#flaskapp.wsgi
import sys
import os
sys.path.insert(0, '/var/www/html/flaskapp')

def application(environ, start_response):
    os.environ['MYSQLDB_USERNAME'] = environ.get('MYSQLDB_USERNAME', '')
    os.environ['MYSQLDB_PASSWORD'] = environ.get('MYSQLDB_PASSWORD', '')
    os.environ['MAIL_USERNAME'] = environ.get('MAIL_USERNAME', '')
    os.environ['MAIL_PASSWORD'] = environ.get('MAIL_PASSWORD', '')
    from avis_app import app as _application

    return _application(environ, start_response)