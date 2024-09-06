#!/usr/bin/python3

#
#  Need to re-write all the fan controls into an app using this example:
#  https://stackoverflow.com/questions/14384739/how-can-i-add-a-background-thread-to-flask
#

import os

from flask import Flask, request, make_response, render_template, redirect, jsonify
from datetime import datetime

###########################################################################
# Set up global variables for start and stop times.  These are manipulated
# by the web calls and used by the fan control thread.
###########################################################################
speeds = ['Off', 'High', 'Low']
status = {'speed': 0, 'start': 0, 'stop': 0}
action = {'action': None}

app = Flask(__name__)
app.secret_key = 'attic app'


###########################################################################
# Main web page determines the fan status and returns a web page using the
# fan.html Flask template
###########################################################################
@app.route('/')
def main_page():

    return make_response(render_template('fan.html', status=fan_status()))


###########################################################################
# Receives a user submitted action from the web page
###########################################################################
@app.route('/action')
def start_fan():

    global action

    action = request.args

    return make_response(redirect('/'))


###########################################################################
# Send actions to and receive status updates from fan control
###########################################################################
@app.route('/control', methods=['GET', 'POST'])
def fan_control():

    global action
    global status

    if request.method == 'GET':
        to_control = action
        action = {'action': None}
        return jsonify(to_control)
    if request.method == 'POST':
        status = request.values
        print(f'Fan Control POST: {fan_status}')
        return ''


###########################################################################
# Web call that returns the status of the fan.  Used by fan.html javascript
###########################################################################
@app.route('/status')
def fan_status():

    global status

    print(f'Fan Status GET: {fan_status}')

    now = datetime.now().timestamp()
    start = datetime.fromtimestamp(status['start'])
    stop = datetime.fromtimestamp(status['stop'])
    speed = speeds[status['speed']]
    if now < status['start']:
        status = f'<b>Delayed Start</b> From {start.hour:02}:{start.minute:02}<br>' \
                 f'to {stop.hour:02}:{stop.minute:02}<br>' \
                 f'at {speed} Speed'
    elif now < status['stop']:
        state = f'<b>Running</b> {speed} Speed<br>Until {stop.hour:02}:{stop.minute:02}'
    else:
        state = '<b>Off</b>'

    return state


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Set PI_IP_ADD environment variable with the server IP address
    ipaddress = os.getenv('PI_IP_ADD', '127.0.0.1')
    app.run(host=ipaddress, port=8080, debug=True)
# [END gae_python38_app]
