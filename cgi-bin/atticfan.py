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


###########################################################################
# Timer function for managing fan run timer and delay timer.  Will be started
# as a thread when web user sets a schedule.
###########################################################################
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
        pi.write(pins[abs(speed-1)], 0)
        sleep(1)
        pi.write(pins[speed], 1)
        time_remaining -= 1
    print('Done')
    time_remaining = 0
    status = '<b>Not Running</b>'
    for pn in pins:
        pi.write(pn, 0)


timer = Thread(target=countdown)
app = Flask(__name__)
app.secret_key = 'any random string'


###########################################################################
# Main web page determines the fan status and returns a web page using the
# fan.html Flask template
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
# Start page sets the delay time, run time and fan speed.  Starts the timer thread
# if it's not running already.  Redirects to main page.
###########################################################################
@app.route('/start/')
def start():

    global time_remaining
    global timer
    global pi
    global delay_remaining
    global speed

    time_value = int(request.args.get('time'))
    delay_value = int(request.args.get('delay'))*3600
    speed = int(request.args.get('speed'))
    if timer.is_alive() & (delay_remaining > 0):
        time_remaining = 0
        delay_remaining = 0
        sleep(3)
        time_remaining = time_value
        delay_remaining = delay_value
    if not timer.is_alive():
        timer = Thread(target=countdown)
        timer.start()

    return make_response(redirect('/'))


###########################################################################
# Stop page clears all timers which will stop the countdown thread and
# also clears all GPIO pins.  Redirects to main page.
###########################################################################
@app.route('/stop/')
def stop():

    global time_remaining
    global delay_remaining
    global pi

    time_remaining = 0
    delay_remaining = 0
    sleep(2)
    for pn in pins:
        pi.write(pn, 0)

    return make_response(redirect('/'))


###########################################################################
# Web call that returns the amount of time on the clock.  Used by fan.html javascript
###########################################################################
@app.route('/clock/')
def fan_clock():

    global time_remaining

    clock = f'{int(time_remaining/3600):2}:{int((time_remaining%3600)/60):02}:{time_remaining%60:02}'
    return clock


###########################################################################
# Web call that returns the status of the fan.  Used by fan.html javascript
###########################################################################
@app.route('/status/')
def fan_status():

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
