#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import signal
from sys import stdout
from time import sleep


from utils import load_config

ini = load_config()
pin_in = int(ini.get('acceptor', 'pin_in'))
pin_out = int(ini.get('acceptor', 'pin_out'))
timeout = ini.get('acceptor', 'timeout')
debug = False

if not debug:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(pin_in, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pin_out, GPIO.OUT)

COIN_VALUE = [
    1,
    2,
    5,
    10,
]


def get_coin():
    coin = 0
    last = 0
    n = 0
    while True:
        if GPIO.input(pin_in) and not last:
            coin += 1
            last = 1
            n = 0
        if not GPIO.input(pin_in):
            last = 0
        if n >= 28 and coin:
          return coin
        n += 1    
        sleep(0.01)


def get_coin_debug():
    n = 0
    while True:
        if n > 5:
            m = int(n)
            n = 0
            return m
        sleep(1)
        n += 1


def main():

    func = get_coin_debug
    if not debug:
        #GPIO.output(pin_out, True)
        func = get_coin

    while True:
        try:
            coin = func()
            if coin:
                print coin
            stdout.flush()
        except IndexError:
            continue
    #if not debug:
    #    GPIO.output(pin_out, False)
    return 0

if __name__ == '__main__':
    main()
