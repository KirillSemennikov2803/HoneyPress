#!/usr/bin/env python3
import os
import hashlib
import json
import re
import requests
import time
import uuid
from flask import Flask, render_template, redirect, url_for, request
from werkzeug.wsgi import LimitedStream
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from haikunator import Haikunator

application = Flask(__name__)
application.secret_key = ''
haikunator = Haikunator()

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
	global honeyDB
	if os.getenv('MONGO_HOST') is not None:
		MONGO_HOST = os.getenv('MONGO_HOST')
		MONGO_PORT = int(os.getenv('MONGO_PORT'))
		MONGO_USER = os.getenv('MONGO_USER')
		MONGO_PASS = os.getenv('MONGO_PASS')
		mongo = MongoClient(MONGO_HOST)
		honeyDB = mongo.honey
		honeyDB.authenticate(MONGO_USER, MONGO_PASS, source='admin')
	else:
		mongo = MongoClient('mongo', MONGO_PORT)
		honeyDB = mongo.honey

def analyze_uri(uri):
	if 'wp-content/themes/' in uri:
		target_type = 'theme'
	elif 'wp-content/plugins/' in uri:
		target_type = 'plugin'
	elif 'wp-admin' or 'wp-login.php' in uri:
		target_type = 'wp-login'
	else:
		target_type = 'unknown'
	if 'wp-content' not in uri:
		target_name = 'unknown'
	else:
		target_name = uri.split('/')[5]
	target_metadata = {'target_name': target_name, 'target_type': target_type}
	return target_metadata

## Logging functions
def logPOST(ip,useragent,isTor,triggered_url,payload):
	ConnectMongo()
	request_id = str(uuid.uuid1())
	if honeyDB.payloads.find({'ip': '{}'.format(ip)}).count() == 0:
		honeyDB.payloads.insert({'ip': '{}'.format(ip),
		'codename': '{}'.format(haikunator.haikunate(token_length=0)),
		'Tor': isTor,
		'requests': {request_id: {'user-agent': '{}'.format(useragent), 'attack_meta':analyze_uri(triggered_url), 'triggered_url': '{}'.format(triggered_url), 'time': '{}'.format(int(time.time())), 'data': payload}}}, check_keys=False)
	else:
		honeyDB.payloads.update_one({'ip': ip}, {'$push': {'requests.{}'.format(request_id): {'user-agent': '{}'.format(useragent), 'attack_meta':analyze_uri(triggered_url), 'triggered_url': '{}'.format(triggered_url), 'time': '{}'.format(int(time.time())), 'data': payload}}}, True)
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
		logPOST(request.remote_addr, request.headers.get('User-Agent'), checkTor(request.remote_addr), request.url, request.form)
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
    application.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
