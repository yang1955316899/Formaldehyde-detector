# -*- coding:utf-8 -*-
"""
日期: 2020.11.15
概要: 数据通过MQTT上传至EMQ平台 测试脚本
功能：1、获取甲醛传感数据，通讯方式UART方式，实现了主动上传和问答式回传，传感数据异常报警机制
	2、传感数据上传EMQ平台，使用MQTT协议将传感数据周期上传EMQ平台，网络自检机制，发现断网后，主动重连
	3、状态指示，上电联网成功与否指示灯，传感数据采集状态指示灯，传感数据正常周期闪烁，错误指示灯熄灭
参考：EMQ，官网：https://github.com/eclipse/paho.mqtt.python
"""
import threading
import logging
import time
from paho.mqtt.client import Client
import paho.mqtt.client as mqtt
import json
import re
import random
from craftsman.utils.plugins_led import *
from craftsman.utils.conf import Conf
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger()

flagThread = True
flagUploadData = False
count = 1

def pub_ReadCH2O_data(client, ds_id):
    def message_json(data):
        message = {
            "datastreams": [
                {
                    "id": ds_id,
                    "datapoints": [
                        {
                            "value": {data[0]:data[1],}
                        }
                    ]
                }
            ]
        }
        message = json.dumps(message)
        mess_len = len(message)
        array = bytearray(mess_len + 3)
        array[0] = 1
        array[1] = int(mess_len/256)
        array[2] = mess_len % 256
        message = message.encode(encoding='ASCII')
        for i in range(mess_len):
            array[i+3] = message[i]
        return array

    while True:
        if flagUploadData == True:
            time.sleep(9)
            cmd = 'FF 01 86 00 00 00 00 00 79'
            serialPort_write(cmd)
            time.sleep(1)
            data = serialPort_read()
            if len(data) == 9:
                value = (int(data[2], 16) * 256 + int(data[3], 16)) / 1000
            elif len(data) == 5:
                value = 255
            else:
                value = 255
            logger.info('当前网络正常，正常上传数据')

            data = ['ch2o', value]
            array = message_json(data)
            client.publish(topic='$dp', payload=array, qos=0)
        else:
            time.sleep(2)
            logger.info('当前网络异常，停止上传数据')

class MyMQTTClass(Client):
    def __init__(self, client_id):
        super(MyMQTTClass, self).__init__(client_id=client_id,protocol=mqtt.MQTTv311, clean_session=False)
    def on_connect(self, client, obj, flags, rc):
        global flagUploadData
        flagUploadData = True
        led_on(18)
        logger.info('连接成功-----on_connect')
        global flagThread
        logger.info("on connect, rc: %s, flags: %s" % (rc, flags))
        client.subscribe(topic="gpio", qos=0) 
        logger.info("start ReadCH2O-Data service-----") 
        if flagThread == True:
            t1 = threading.Thread(target=pub_ReadCH2O_data, args=(client, 'data'))
            t1.start()
            self.worker1 = t1
            flagThread = False
        
    def on_message(self, client, obj, msg):
        logger.debug("on message, topic: %s, qos: %s, data: %s" %(msg.topic, msg.qos, msg.payload))
        if msg.topic == "test01":
            logger.info("deal test01, data: %s" % msg.payload)
        else:
            logger.info("other topic %s, data: %s" %(msg.topic, msg.payload))

    def on_publish(self, client, obj, mid):
        global count
        logger.debug("publish -> ,mid: %s" % mid) 
        logger.info("发送-----OK！%d", count)
        count = count + 1
        led_toggle(17, count)

    def on_subscribe(self, client, obj, mid, granted_qos):
        logger.debug("subscribed <- ,mid: %s, qos: %s" %(mid, granted_qos))  

    def on_log(self, mqttc, obj, level, string):
        logger.debug("mqtt debug: %s, %s" %(level, string)) 

    def on_disconnect(self, client, userdata, rc): 
        global flagUploadData
        flagUploadData = False
        led_off(18)  
        led_off(17)  
        logger.info('连接失败-----on_disconnect')
		
        while rc == 1:
            try:
                client.reconnect()
                rc = 0
                logger.info('连接成功-----on_disconnect_内')
            except Exception as e:  
                logger.info('连接失败---%s--on_disconnect_内，3S后重新连接----' % e)
                time.sleep(3)  
    def run(self, host, port, keepalive, namespace, auif):
        flag = 1 
        while flag == 1:
            try:
                self.username_pw_set(namespace, auif)
                self.connect(host, port, keepalive)
                flag = 0
                logger.info('连接成功-----run')  

            except Exception as e:
                led_off(18)  
                led_off(17)  
                logger.info('连接失败-----run')
                time.sleep(3) 
				
        while True:
            rc = self.loop()  
            if rc != 0:
                logger.info("重新连接网络成功-------run")
                time.sleep(1)  # 休息1秒
                rc = self.loop()  # 循环执行
                logger.info("recovery from error loop, %s" %rc)  
                        
def main():
    conf = Conf("/boot/config.json")
    gpio_setup()
    host = conf["host"]  
    port = conf["port"]     
    namespace = conf["namespace"] 
    keepalive = conf["keepalive"]  
    client_id = conf["client_id"]
    auif = conf["auif"]   

    client = MyMQTTClass(client_id)
    client.run(host, port, keepalive, namespace, auif)

if __name__ == "__main__":
    main()
