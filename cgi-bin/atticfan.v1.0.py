#!/usr/bin/python3

#
#  Need to re-write all the fan controls into an app using this example:
#  https://stackoverflow.com/questions/14384739/how-can-i-add-a-background-thread-to-flask
#

import os

from flask import Flask, request, make_response, render_template, redirect
from threading import Thread
from time import sleep
import pigpio
from datetime import datetime, timedelta

###########################################################################
# Set up global variables for start and stop times.  These are manipulated
# by the web calls and used by the fan control thread.
###########################################################################
start_time = datetime.now()
stop_time = start_time - timedelta(seconds=1)
status = 'Initializing'
pi = pigpio.pi()
speeds = ['High', 'Low']
speed = 0
button = 26
highpin = 17
lowpin = 22
pins = [highpin, lowpin]


def app_with_background_proc():

    # This pulls the background processes into a single app with Flask which
    # will be called by the WSGI

    app = Flask(__name__)
    app.secret_key = 'any random string'

    ###########################################################################
    # Initialize GPIO for Attic Fan.  Set High Speed and Low Speed pins to off.
    ###########################################################################
    def init_gpio():
        global pi
        global speed

        for pin in pins:
            pi.set_mode(pin, pigpio.OUTPUT)
            pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
            pi.write(pin, 0)

        pi.set_mode(button, pigpio.INPUT)
        pi.set_pull_up_down(button, pigpio.PUD_DOWN)

    ###########################################################################
    # Control function for managing fan power and start and stop times.
    # Started as a thread on load.
    ###########################################################################
    def fan_controller():
        global start_time
        global stop_time
        global pi
        global status
        global speed

        while True:
            now = datetime.now()
            if (now < start_time) or (now > end_time):
                for pn in pins:
                    pi.write(pn, 0)
                if now < start_time:
                    starting = f'{start_time.hour}:{start_time.minute:02}:{start_time.second:02}'
                    seconds_remaining = (end_time - start_time).seconds
                    time_remaining = f'{int(seconds_remaining / 3600):2}:{int((seconds_remaining % 3600) / 60):02}:' \
                                     f'{seconds_remaining % 60:02}'
                    status = f'<b>Delayed Start</b> at {starting}<br>Will run for {time_remaining}<br>' \
                             f'at {speeds[speed]} Speed'
                else:
                    status = "<b>OFF</b>"
            else:
                pi.write(pins[abs(speed-1)], 0)
                pi.write(pins[speed], 1)
                seconds_remaining = (end_time - now).seconds
                time_remaining = f'{int(seconds_remaining / 3600):2}:{int((seconds_remaining % 3600) / 60):02}:' \
                                 f'{seconds_remaining % 60:02}'
                status = f'<b>Running</b> {speeds[speed]} Speed<br>Time Remaining: {time_remaining}'
            sleep(1)

    ###########################################################################
    # Thread function for reading the button.  Pressing the button cycles the
    # fan through Low, High, Off.  If the fan is off, it sets the timer to
    # 2 hours.
    ###########################################################################
    def button_function():
        global start_time
        global stop_time
        global speed
        global pi

        while True:
            button_status = pi.read(button)
            if button_status:
                print('Attic Fan App: Button pressed: Set to ', end=' ')
                now = datetime.now()
                if now < end_time:
                    if speeds[speed] == 'High':
                        start_time = end_time = now
                        print('OFF')
                    else:
                        speed = 0
                        print('HIGH')
                else:
                    start_time = now
                    end_time = now + timedelta(hours=2)
                    speed = 1
                    print('LOW')
                while pi.read(button):
                    sleep(0.5)
            sleep(0.1)

    init_gpio()
    fan_control = Thread(target=fan_controller)
    fan_control.start()
    button_control = Thread(target=button_function)
    button_control.start()

    return app


app = app_with_background_proc()


###########################################################################
# Main web page determines the fan status and returns a web page using the
# fan.html Flask template
###########################################################################
@app.route('/')
def main_page():

    global status

    return make_response(render_template('fan.html', status=status))


###########################################################################
# Start page sets the delay time, run time and fan speed.  Starts the timer thread
# if it's not running already.  Redirects to main page.
###########################################################################
@app.route('/start/')
def start_fan():

    global start_time
    global stop_time
    global speed

    time_value = int(request.args.get('time'))
    delay_value = float(request.args.get('delay'))
    speed = int(request.args.get('speed'))

    start_time = datetime.now() + timedelta(minutes=delay_value)
    end_time = start_time + timedelta(seconds=time_value)

    print(f'Attic Fan App: Web call to start: Time-{time_value} Delay-{delay_value} Speed-{speeds[speed]}')
    return make_response(redirect('/'))


###########################################################################
# Stop page clears all timers which will stop the countdown thread and
# also clears all GPIO pins.  Redirects to main page.
###########################################################################
@app.route('/stop/')
def stop_fan():

    global start_time
    global stop_time

    start_time = end_time = datetime.now() - timedelta(seconds=1)
    print(f'Attic Fan App: Web call to stop')
    return make_response(redirect('/'))


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
