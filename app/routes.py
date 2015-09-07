#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

logging.basicConfig(level=logging.WARN, format='%(levelname)-8s %(message)s')
logger = logging.getLogger('garagesec')

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

import gpio
import json
import time
import datetime
from jabber import Jabber
from camera import Camera
from HIH6130 import Temperature
from config import configuration
from bottle import Bottle, HTTPResponse, static_file, get, put, request, response, template

instance_name = configuration.get('instance_name')

camera = Camera()
temperature = Temperature()

jabber_service = Jabber(configuration.get('xmpp_username'), configuration.get('xmpp_password'), camera, temperature)

application = Bottle()
application.install(temperature)
application.install(jabber_service)

@application.route('/favicon.ico')
def send_favicon():
	return static_file('favicon.ico', root='views/images')

@application.route('/installed/<filename:path>')
def send_bower(filename):
	return static_file(filename, root='views/bower_components')

@application.route('/js/<filename:path>')
def send_js(filename):
	return static_file(filename, root='views/js')

@application.route('/css/<filename:path>')
def send_css(filename):
	return static_file(filename, root='views/css')

@application.get('/')
def dashboard():
	return template('index', webcam_url=configuration.get('webcam_url'))

@application.get('/status')
def show_status():
	archive_dir = configuration.get('webcam_archive')
	archive_dir = configuration.get('webcam_archive')
	time_struct = max(map(lambda x: os.path.getmtime("%s/%s" % (archive_dir, x)), os.listdir(archive_dir)))
	return '{ "last_area_detected": "%s" }' % time.strftime("%c", time.localtime(time_struct))

@application.get('/environment')
def get_environment(temperature):
	humidity, celsius, status = temperature.get_conditions()
	fahrenheit_val = ((celsius * 9) / 5) + 32 if celsius else "null"
	celsius_val = celsius if celsius else "null"
	humidity_val = humidity if humidity else "null"
	status_val = status if status else "null"
	return '{ "relative_humidity": %s, "celsius": %s, "fahrenheit": %s, "status": %s }' % (humidity_val, celsius_val, fahrenheit_val, status_val)

@application.get('/snapshot')
def show_snapshot():
	response.headers['Content-Type'] = 'image/jpeg'
	return camera.get_image()

@application.put('/picture_save')
def picture_save(jabber):
	motion_event = request.json
	image_file_path = motion_event['file']

	jabber.send_alert_image(image_file_path)

	return request.body.getvalue()

@application.put('/movie_start')
def movie_start():
	return request.body.getvalue()

@application.put('/movie_end')
def movie_end():
	return request.body.getvalue()

@application.put('/motion_detected')
def motion_detected():
	return request.body.getvalue()

@application.put('/area_detected')
def area_detected(jabber):
	motion_event = request.json
	date_time = time.localtime(motion_event['event_time'])
	time_string = time.strftime('%a, %d %b %Y %H:%M:%S', date_time)

	jabber.send_alert_msg('Motion in %s Detected at %s' % (instance_name, time_string))

	return request.body.getvalue()

@application.put('/remote/<button:int>')
def push_remote_button(button):
	if gpio.push_button(button):
		return '{ "pressed": %d }' % button
	else:
		raise HTTPResponse('{ "error": %d }' % button, 500)

@application.get('/lastevent')
def get_lastevent(jabber):
	archive_dir = configuration.get('webcam_archive')
	time_struct = max(map(lambda x: os.path.getmtime("%s/%s" % (archive_dir, x)), os.listdir(archive_dir)))
	return '{ "datetime": "%s" }' % time.strftime("%c", time.localtime(time_struct))

@application.get('/alerts')
def get_silence(jabber):
	return '{ "silence": %s }' % ("true" if jabber.silent else "false")

@application.put('/alerts')
def set_silence(jabber):
	silence_request = request.json
	jabber.set_silence(silence_request['silence'])
	return get_silence(jabber)
