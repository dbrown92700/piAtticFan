#!/usr/bin/python3
import json
from time import sleep
import pigpio
from datetime import datetime, timedelta
from threading import Thread
import requests
import logging


###########################################################################
# Set up global variables for start and stop times.  These are manipulated
# by the web calls and used by the fan control thread.
###########################################################################

start_time = stop_time = datetime.now()
speed = 0
speeds = ['High', 'Low']
fan_host = '192.168.1.66'

pi = pigpio.pi()
button = 26
highpin = 17
lowpin = 22
pins = [highpin, lowpin]


###########################################################################
# Initialize GPIO for Attic Fan.  Set High Speed and Low Speed pins to off.
###########################################################################
def init_gpio():
    global pi

    for pin in pins:
        pi.set_mode(pin, pigpio.OUTPUT)
        pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        pi.write(pin, 0)

    pi.set_mode(button, pigpio.INPUT)
    pi.set_pull_up_down(button, pigpio.PUD_DOWN)
    logger.info('************** Starting fan_control. Init GPIO')


###########################################################################
# Control function for managing fan power and start and stop times.
# Started as a thread on load.
###########################################################################
def fan_controller():
    global start_time
    global stop_time
    global pi
    global speed

    while True:
        now = datetime.now()
        if (now > start_time) and (now < stop_time):
            pi.write(pins[abs(speed - 1)], 0)
            pi.write(pins[speed], 1)
        else:
            for pn in pins:
                pi.write(pn, 0)
        sleep(1)


###########################################################################
# Thread function for reading the button.  Pressing the button cycles the
# fan through Low, High, Off.  If the fan is off, it sets the timer to
# 2 hours.
###########################################################################

def event_function():
    global start_time
    global stop_time
    global speed
    global pi

    while True:
        post = False
        now = datetime.now()

        #####
        # Check to see if the button is pressed
        #####
        button_status = pi.read(button)
        if button_status:
            if now < stop_time:
                if speed == 0:
                    start_time = stop_time = now
                else:
                    speed = 0
            else:
                start_time = now
                stop_time = now + timedelta(hours=2)
                speed = 1
            while pi.read(button):
                sleep(0.5)
            post = True
            logger.info(f'Button Push: Speed {speed} Start: {start_time} Stop: {stop_time}')

        #####
        # Check for a user action from the webserver
        #####
        try:
            web_action = requests.get(f'http://{fan_host}/control').json()
        except requests.exceptions.ConnectionError:
            logger.error('Web GET Connection Error')
            web_action = {'action': None}
        if web_action['action']:
            post = True
            if web_action['action'] == 'stop':
                start_time = stop_time = now
                logger.info(f'Web Stop')
            else:
                speed = int(web_action['speed'])
                start_time = datetime.fromtimestamp(now.timestamp() + int(web_action['delay'])*60)
                stop_time = datetime.fromtimestamp(start_time.timestamp() + int(web_action['time']))
                logger.info(f'Web Push: Speed {speed} Start: {start_time} Stop: {stop_time}')

        #####
        # If the settings have changed, post the update to the webserver
        # Re-post data every 10 minutes to fix issue with atticfan variables getting cleared over time
        #####
        if post or (now.minute % 10 == 0 and now.second % 60 == 0):
            payload = {
                'speed': speed,
                'start': datetime.timestamp(start_time),
                'stop': datetime.timestamp(stop_time)
            }
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            try:
                requests.post(f'http://{fan_host}/control', data=json.dumps(payload), headers=headers)
            except requests.exceptions.ConnectionError:
                logger.error('POST Connection Error')

        sleep(1)


if __name__ == "__main__":
    t = datetime.now()
    logging.basicConfig(
        filename=f"fan_control_{t.year}.{t.month:02}.log",
        filemode="a",
        format="'%(asctime)s %(levelname)-10s:%(message)s",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    logger.info('created logger')
    init_gpio()
    fan_control = Thread(target=fan_controller)
    fan_control.start()
    event_control = Thread(target=event_function)
    event_control.start()
