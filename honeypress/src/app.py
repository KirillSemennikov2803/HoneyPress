#!/usr/bin/env python3
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
	headers = {'user-agent': 'honeypress/(https://github.com/dustyfresh/HoneyPress)'}
	try:
		exit_nodes = requests.get('https://check.torproject.org/exit-addresses', headers=headers)
		exit_nodes = exit_nodes.text
		if re.search(ip, exit_nodes):
			return True
		else:
			return False
	except Exception as err:
		return "err"

def ConnectMongo():
    global mongo
    mongo = MongoClient('mongo', 27017)
    global honeyDB
    honeyDB = mongo.honey

application = Flask(__name__)
application.secret_key = ''

## Logging functions
def loginattempt(ip,user,passwd,useragent):
    with open("/opt/honeypress/logs/auth.log", "a") as log:
        log.write('[{}] - {} - user: {} pass: {} - {}\n\n\n'.format(str(datetime.now()),ip,user,passwd, useragent))

def logPOST(ip,useragent,isTor,triggered_url,payload):
    ConnectMongo()
    honeyDB.payloads.insert({'ip': '{}'.format(ip),
    'time': '{}'.format(int(time.time())),
    'user-agent': '{}'.format(useragent),
    'Tor': isTor,
    'triggered_url': '{}'.format(triggered_url),
    'payload': {'data': payload}}, check_keys=False)
    mongo.close()

## Start of routes
@application.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
	return render_template('index.php'), 200

@application.route('/searchreplacedb2.php', methods=['GET', 'POST'])
def searchreplacedb2():
	if request.method == 'POST':
		logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
	return render_template('searchreplacedb2.php'), 200

@application.route('/wp-content/debug.log')
def debuglog():
    return 'aaa', 200

@application.route('/wp-admin/admin-ajax.php', methods=['GET', 'POST'])
def adminajaxphp():
	if request.method == 'POST':
		logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
	return '0', 200

@application.route('/xmlrpc.php', methods=['GET', 'POST'])
def xmlrpc():
	if request.method == 'GET':
		return 'XML-RPC server accepts POST requests only.', 405
	elif request.method == 'POST':
		logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
	return '', 200

@application.route('/readme.html')
def readme():
    return render_template('readme.html'), 200

@application.route('/wp-config.php', methods=['GET', 'POST'])
def wpconfig():
	if request.method == 'POST':
		logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
	return '', 200

@application.route('/wp-admin')
def wpadmin():
    return redirect("/wp-login.php", code=302)

@application.route('/wp-admin/')
def wpadminslash():
    return redirect("/wp-login.php", code=302)

@application.route('/wp-login.php', methods=['GET', 'POST'])
def wplogin():
    if request.method == 'POST':
        username = request.form['log']
        password = request.form['pwd']
        loginattempt(request.remote_addr,username,password,request.headers.get('User-Agent'))
    return render_template('wp-login.php'), 200

# If it's a 404 log the POST data to a file then return 200 status code
@application.errorhandler(404)
def not_found(e):
    if request.method == 'POST':
        logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
    return '', 200

@application.errorhandler(400)
def bad_req(e):
    print("ERROR: {}".format(e))
    return '', 200

@application.after_request
def apply_headers(response):
    response.headers["Server"] = "nginx"
    response.headers["Content-Type"] = "text/html; charset=UTF-8"
    response.headers["Connection"] = "keep-alive"
    response.headers["Keep-Alive"] = "timeout=20"
    response.headers["Link"] = '<http://wordpress.com/wp-json/>; rel="https://api.w.org/"'
    response.headers["Set-Cookie"] = 'wordpress_test_cookie=WP+Cookie+check; path=/'
    return response

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
