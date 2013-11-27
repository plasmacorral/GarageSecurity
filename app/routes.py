#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

logging.basicConfig(level=logging.WARN, format='%(levelname)-8s %(message)s')

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

import gpio
import json
from jabber import Jabber
from config import configuration
from bottle import Bottle, HTTPResponse, static_file, get, put, request, template

application = Bottle()
application.install(Jabber())

@application.route('/favicon.ico')
def send_favicon():
	return static_file('favicon.ico', root='views/images')

@application.route('/js/<filename:path>')
def send_js(filename):
	return static_file(filename, root='views/js')

@application.route('/css/<filename:path>')
def send_css(filename):
	return static_file(filename, root='views/css')

@application.get('/')
def show_status(jabber):
	jabber.send_recipients('GarageSec motion is working from index')
	return template('index')

@application.put('/picture_save')
def picture_save():
	return HTTPResponse(request.body.getvalue(), 200)

@application.put('/movie_start')
def movie_start():
	return HTTPResponse(request.body.getvalue(), 200)

@application.put('/movie_end')
def movie_end():
	return HTTPResponse(request.body.getvalue(), 200)

@application.put('/motion_detected')
def motion_detected():
	return HTTPResponse(request.body.getvalue(), 200)

@application.put('/area_detected')
def area_detected():
	motion_event = request.json
	return HTTPResponse(request.body.getvalue(), 200)

@application.put('/remote/<button:int>')
def push_remote_button(button):
	if gpio.push_button(button):
		raise HTTPResponse('{ "pressed": %d }' % button, 200)
	else:
		raise HTTPResponse('{ "error": %d }' % button, 500)
