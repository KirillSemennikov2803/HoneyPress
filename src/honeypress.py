#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, request
from werkzeug.wsgi import LimitedStream
from datetime import datetime
from pymongo import MongoClient
import hashlib
import json
import re
import requests
import time

def checkTor(ip):
	headers = {'user-agent': 'honeypress/1.3.3.7 (https://github.com/dustyfresh/HoneyPress)'}
	exit_nodes = requests.get('https://check.torproject.org/exit-addresses', headers=headers)
	exit_nodes = exit_nodes.text
	if re.search(ip, exit_nodes):
		return True
	else:
		return False

def ConnectMongo():
    global mongo
    mongo = MongoClient()
    global honeyDB
    honeyDB = mongo.honey

app = Flask(__name__)
app.secret_key = ''

# connection reset fix
# see: http://flask.pocoo.org/snippets/47/
class StreamConsumingMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        stream = LimitedStream(environ['wsgi.input'],
                               int(environ['CONTENT_LENGTH'] or 0))
        environ['wsgi.input'] = stream
        app_iter = self.app(environ, start_response)
        try:
            stream.exhaust()
            for event in app_iter:
                yield event
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()
app.wsgi_app = StreamConsumingMiddleware(app.wsgi_app)

## Logging functions
def loginattempt(ip,user,passwd,useragent):
    with open("/opt/honeypress/logs/auth.log", "a") as log:
        log.write('[{}] - {} - user: {} pass: {} - {}\n\n\n'.format(str(datetime.now()),ip,user,passwd, useragent))

def logPOST(ip,useragent,isTor,triggered_url,payload,payload_hash):
    ConnectMongo()
    honeyDB.payloads.insert({'ip': '{}'.format(ip),
    'time': '{}'.format(int(time.time())),
    'user-agent': '{}'.format(useragent),
    'Tor': isTor,
    'triggered_url': '{}'.format(triggered_url),
    'payload': {'hash': '{}'.format(payload_hash), 'data': payload}}, check_keys=False)
    mongo.close()

## Start of routes
@app.route('/')
def index():
    return render_template('index.php'), 200

@app.route('/searchreplacedb2.php', methods=['GET', 'POST'])
def searchreplacedb2():
    return render_template('searchreplacedb2.php'), 200

# Detecting dirlisting for uploads
@app.route('/wp-content/uploads/')
def uploadsdirlisting():
    return 'index of /', 200

@app.route('/wp-content/debug.log')
def debuglog():
    return 'aaa', 200

@app.route('/wp-admin/admin-ajax.php')
def adminajaxphp():
    return '0', 200

@app.route('/xmlrpc.php', methods=['GET', 'POST'])
def xmlrpc():
    if request.method == 'GET':
        return 'XML-RPC server accepts POST requests only.', 405
    elif request.method == 'POST':
        return '', 403

@app.route('/readme.html')
def readme():
    return render_template('readme.html'), 200

@app.route('/wp-config.php')
def wpconfig():
    return '', 200

@app.route('/wp-content')
def wpcontent():
    return '', 200

@app.route('/wp-content/themes')
def wpcontentthemes():
    return '', 200

@app.route('/wp-content/plugins')
def wpcontentplugins():
    return '', 200

@app.route('/wp-content/uploads')
def uploads():
    return '', 200

@app.route('/wp-admin')
def wpadmin():
    return redirect("/wp-login.php", code=302)

@app.route('/wp-admin/')
def wpadminslash():
    return redirect("/wp-login.php", code=302)

@app.route('/wp-login.php', methods=['GET', 'POST'])
def wplogin():
    if request.method == 'POST':
        username = request.form['log']
        password = request.form['pwd']
        loginattempt(request.remote_addr,username,password,request.headers.get('User-Agent'))
        if username == 'admin' and password == 'admin':
            return 'username and password are both admin. Likely a bot trying to use default login details or brute force.', 200
        elif username == 'admin' and password == 'password':
            return 'username and password are admin:password. Likely a bot trying to use default login details or brute force.', 200
        return render_template('wp-login.php'), 200
    return render_template('wp-login.php'), 200

@app.route('/robots.txt')
def robots():
    return '', 200

# If it's a 404 log the POST data to a file then return 200 status code
@app.errorhandler(404)
def not_found(e):
    if request.method == 'POST':
        logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form, hashlib.sha256(u'{}'.format(request.form)).hexdigest())
    return '', 200

@app.errorhandler(400)
def bad_req(e):
    print("ERROR: {}".format(e))
    return '', 200

@app.after_request
def apply_headers(response):
    response.headers["Server"] = "nginx"
    response.headers["Content-Type"] = "text/html; charset=UTF-8"
    response.headers["Connection"] = "keep-alive"
    response.headers["Keep-Alive"] = "timeout=20"
    response.headers["Link"] = '<http://wordpress.com/wp-json/>; rel="https://api.w.org/"'
    response.headers["Set-Cookie"] = 'wordpress_test_cookie=WP+Cookie+check; path=/'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
