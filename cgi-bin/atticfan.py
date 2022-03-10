#!/usr/bin/python3
import os

from flask import Flask, request, make_response, render_template, redirect
from threading import Thread
from time import sleep
import pigpio
from datetime import datetime, timedelta

###########################################################################
# Set up global variables for time remaining and a countdown thread object
###########################################################################
time_remaining = 0
delay_remaining = 0
status = 'Is Not Running'

# Initialize GPIO for Attic Fan
pi = pigpio.pi()
highpin = 17
lowpin = 22
pins = [highpin, lowpin]
speeds = ['High', 'Low']
speed = 0

for pin in pins:
    pi.set_mode(pin, pigpio.OUTPUT)
    pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
    pi.write(pin, 0)


def countdown():
    global time_remaining
    global pi
    global status
    global delay_remaining
    global speed

    while delay_remaining > 0:
        sleep(1)
        delay_remaining -= 1
    while time_remaining > 0:
        pi.write(pins[speed], 1)
        sleep(1)
        time_remaining -= 1
    print('Done')
    time_remaining = 0
    status = '<b>Not Running</b>'
    for pin in pins:
        pi.write(pin, 0)


timer = Thread(target=countdown)
app = Flask(__name__)
app.secret_key = 'any random string'

###########################################################################
# read page reads the time remaining or indicates if the timer thread is
# not running
###########################################################################


@app.route('/')
def controller():

    global timer
    global status
    global pi
    global speed

    if timer.is_alive():
        if delay_remaining > 0:
            st = datetime.now() + timedelta(seconds=delay_remaining)
            status = f'''Scheduled start time: <b>{st.hour}:{st.minute:02}</b><br>
                    Fan speed: <b>{speeds[speed]}</b>'''
        else:
            status = f'<b>Running<br>{speeds[speed]} Speed</b>'
        time = f'{int(time_remaining/3600):2}:{int((time_remaining%3600)/60):02}:{time_remaining%60:02}'
    else:
        status = '<b>Not Running</b>'
        time = '0:00:00'

    return make_response(render_template('fan.html', time=time, status=status))


###########################################################################
# start page sets the time remaining value and starts the timer thread
# if it's not running already
###########################################################################


@app.route('/start/')
def start():

    global time_remaining
    global timer
    global pi
    global delay_remaining
    global speed

    time_remaining = int(request.args.get('time'))
    delay_remaining = int(request.args.get('delay'))*3600
    speed = int(request.args.get('speed'))
    if not timer.is_alive():
        timer = Thread(target=countdown)
        timer.start()

    return make_response(redirect('/'))

###########################################################################
# start page sets the time remaining value and starts the timer thread
# if it's not running already
###########################################################################


@app.route('/stop/')
def stop():

    global time_remaining
    global delay_remaining
    global pi

    time_remaining = 0
    delay_remaining = 0
    for pin in pins:
        pi.write(pin, 0)

    return make_response(redirect('/'))

###########################################################################
# Web call that returns the amount of time on the clock
###########################################################################


@app.route('/clock/')
def fan_clock():

    global time_remaining

    clock = f'{int(time_remaining/3600):2}:{int((time_remaining%3600)/60):02}:{time_remaining%60:02}'
    return clock


@app.route('/status/')
def fanstat():

    global status

    return status


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Set PI_IP_ADD environment variable with the server IP address
    ipaddress = os.getenv('PI_IP_ADD', '127.0.0.1')
    app.run(host=ipaddress, port=8080, debug=True)
# [END gae_python38_app]
