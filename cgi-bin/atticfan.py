#!/usr/bin/python3
import os

from flask import Flask, request, make_response, render_template, redirect
from threading import Thread
from time import sleep
import pigpio

###########################################################################
# Set up global variables for time remaining and a countdown thread object
###########################################################################
time_remaining = 60
pi = pigpio.pi()
highpin = 17
pi.set_mode(highpin, pigpio.OUTPUT)
pi.set_pull_up_down(highpin, pigpio.PUD_DOWN)

def countdown():
    global time_remaining
    global pi

    while time_remaining > 0:
        sleep(1)
        time_remaining -= 1
    print('Done')
    pi.write(highpin, 0)

timer = Thread(target=countdown)

app = Flask(__name__)
app.secret_key = 'any random string'

@app.route('/')
def home():
    return app.root_path


###########################################################################
# start page sets the time remaining value and starts the timer thread
# if it's not running already
###########################################################################
@app.route('/start/')
def set():

    global time_remaining
    global timer
    global pi

    time_remaining = int(request.args.get('time'))
    if not timer.is_alive():
        timer = Thread(target=countdown)
        timer.start()
    pi.write(highpin, 1)

    return make_response(redirect('/read/'))

###########################################################################
# read page reads the time remaining or indicates if the timer thread is
# not running
###########################################################################

@app.route('/read/')
def read():

    global timer
    if timer.is_alive():
        status = 'Is Running'
        time = time_remaining
    else:
        status = 'Is Not Running'
        time = 'N/A'

    return make_response(render_template('fan.html', time=time, status=status))

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    ipaddress = os.getenv('PI_IP_ADD', '127.0.0.1')
    app.run(host=ipaddress, port=8080, debug=True)
# [END gae_python38_app]