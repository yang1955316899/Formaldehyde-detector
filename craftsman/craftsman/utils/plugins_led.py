#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
Date:   2019.10.22 11:56
brief:  led控制驱动逻辑
"""

import RPi.GPIO as GPIO


# BCM GPIO编号
pins = [17,18,27,22,23,24,25,4]

# GPIO引脚初始化设置
def gpio_setup():
    # 采用BCM编号
    GPIO.setmode(GPIO.BCM)
    # 设置所有GPIO为输出状态，且输出低电平
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        
# 设置所有GPIO复位    
def gpio_destroy():
    for pin in pins:
        GPIO.output(pin, GPIO.LOW)
        GPIO.setup(pin, GPIO.IN)

# 清楚所有GPIO    
def gpio_cleanup():
    GPIO.cleanup()
      
# 开灯
def led_on(pin_num):
    GPIO.output(pin_num, GPIO.HIGH)

# 关灯
def led_off(pin_num):
    GPIO.output(pin_num, GPIO.LOW)
    
    
def led_toggle(pin_num, count):
    
    if count % 2 == 0:
        led_on(pin_num)
    else:
        led_off(pin_num)
    
    
    
    
    