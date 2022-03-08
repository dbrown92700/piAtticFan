#!/usr/bin/python3
import os

from flask import Flask, request, make_response, render_template, redirect
from threading import Thread
from time import sleep

###########################################################################
# Set up global variables for time remaining and a countdown thread object
###########################################################################
time_remaining = 60

def countdown():
    global time_remaining
    while time_remaining > 0:
        sleep(1)
        time_remaining -= 1
    print('Done')

timer = Thread(target=countdown)

app = Flask(__name__)
app.secret_key = 'any random string'

###########################################################################
# start page sets the time remaining value and starts the timer thread
# if it's not running already
###########################################################################
@app.route('/start/')
def set():

    global time_remaining
    global timer
    time_remaining = int(request.args.get('time'))
    if not timer.is_alive():
        timer = Thread(target=countdown)
        timer.start()

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