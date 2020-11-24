# -*- coding:utf-8 -*-
"""
日期: 2020.11.15
概要: 数据通过MQTT上传至EMQ平台 测试脚本
功能：1、获取甲醛传感数据，通讯方式UART方式，实现了主动上传和问答式回传，传感数据异常报警机制
	2、传感数据上传EMQ平台，使用MQTT协议将传感数据周期上传EMQ平台，网络自检机制，发现断网后，主动重连
	3、状态指示，上电联网成功与否指示灯，传感数据采集状态指示灯，传感数据正常周期闪烁，错误指示灯熄灭
参考：EMQ，官网：https://github.com/eclipse/paho.mqtt.python
"""

# 导入软件包
import threading
import logging
import time
from paho.mqtt.client import Client
# 引入MQTT模块
import paho.mqtt.client as mqtt
import json
import re
import random
# 导入初始化LED和调用LED使用库
from craftsman.utils.plugins_led import *
# 导入配置文件
from craftsman.utils.conf import Conf
# 设置log信息显示 formater用户格式化输出日志的信息
# 格式为：时间-行数-错误等级-错误内容
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# logger是提供我们记录日志的方法
# formater用户格式化输出日志的信息 format = 输出格式 level=logging.INFO 输出等级 INFO 权重20 等级排名：3
logging.basicConfig(format=FORMAT, level=logging.INFO)
# 获取log
logger = logging.getLogger()

# 设置一个标志位 默认设备上电只开启一个线程 设备断网重连后不开启新的线程
flagThread = True
# 设置一个标志位 判断是否断网 决定是否上传数据
flagUploadData = False#默认断网
# 数据上传状态指示计数
count = 1

""" 
    获取CH2O传感数据信息上传EMQ平台接口函数
        client:MQTT客户端类
        ds_id：话题
"""
def pub_ReadCH2O_data(client, ds_id):
    # 待发送的数据  JSON格式组织
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
        array = bytearray(mess_len + 3)#创建一个新数组大小比Massige大三位
        array[0] = 1
        array[1] = int(mess_len/256)
        array[2] = mess_len % 256
        message = message.encode(encoding='ASCII')
        # 将message中信息存入array[3]到array[n]中(每个字节对应一个字符)
        for i in range(mess_len):
            array[i+3] = message[i]
        # print(array)
        return array

    while True:
        # 周期数据采集，检查上传变量是否为真，真就上传
        if flagUploadData == True:

            # 设置周期采集数据  9S每次
            time.sleep(9)
            # 获取传感器的数据  实现两种方式：主动上传和问答
            # 下发指令
            cmd = 'FF 01 86 00 00 00 00 00 79'
            serialPort_write(cmd)#写入cmd
            # 获取传感器返回的数据  预留1s的时间缓存数据
            time.sleep(1)
            #从串口读取数据
            data = serialPort_read()
            # 根据返回的数据格式  计算CH2O浓度
            if len(data) == 9:
                value = (int(data[2], 16) * 256 + int(data[3], 16)) / 1000#从data[2]读取，转换为10进制 同理在与data[3]读取相加后/1000
            # 甲醛数据传感采集错误  默认发送255
            elif len(data) == 5:
                value = 255
                # print(value)
            else:
                value = 255
                # print(value)
            logger.info('当前网络正常，正常上传数据')

            data = ['ch2o', value]
            # 以EMQ平台数据格式  组织数据
            array = message_json(data)
            # 发布主题（此处用了0）
            # "至多一次"，消息发布完全依赖底层TCP/IP网络。会发生消息丢失或重复。
            # 环境传感器数据，丢失一次读记录无所谓，因为不久后还会有第二次发送。
            # 这一种方式主要普通APP的推送，倘若你的智能设备在消息推送时未联网，推送过去没收到，再次联网也就收不到了。
            client.publish(topic='$dp', payload=array, qos=0)#调用函数，topic 客户端将订阅的主题字符串 发送出去
        else:
            time.sleep(2)
            logger.info('当前网络异常，停止上传数据')
  

class MyMQTTClass(Client):
    """
        mqtt client for deal data
    """

    def __init__(self, client_id):
        # 设置设备在EMQ平台上注册的ID号 并定义MQTT协议版本为EMQ支持的版本
        # protocol=mqtt.MQTTv311 使用的协议 client_id = "596968197"  连接到代理时使用的唯一客户端ID字符串 客户端是持久性客户端，设置成False则在客户端断开连接时将保留订阅信息和排队消息
        super(MyMQTTClass, self).__init__(client_id=client_id,protocol=mqtt.MQTTv311, clean_session=False)#确认收到信息回复

    # 连接成功回调函数
    '''
    client --- 此回调的客户端实例
    flags --- 经纪人发送的响应标志
    RC --- 连接结果
    mid是订阅请求的消息ID。中间值可用于通过检查on_subscribe（）回调中的mid参数来跟踪订阅请求（如果已定义）。
    '''

    def on_connect(self, client, obj, flags, rc):
        global flagUploadData
        flagUploadData = True
        # 只需要在此处加 连接成功的指示灯18引脚即可 常亮
        led_on(18)
        logger.info('连接成功-----on_connect')
        # 设置一个标志位 默认设备上电只开启一个线程 设备断网重连后不开启新的线程
        global flagThread
        # 连接成功/失败标志，并记录下flags即clean_session=False
        logger.info("on connect, rc: %s, flags: %s" % (rc, flags))
        # 订阅感兴趣的主题   支持多线程同时订阅多个主题
        # 引用百度：其中结果是 MQTT_ERR_SUCCESS表示成功，或者（MQTT_ERR_NO_CONN，None）如果客户端当前未连接。
        client.subscribe(topic="gpio", qos=0)  # 订阅主题并接收消息，qos = 0
        logger.info("start ReadCH2O-Data service-----")  # 记录
        if flagThread == True:#检查线程
            t1 = threading.Thread(target=pub_ReadCH2O_data, args=(client, 'data'))#创建线程
            t1.start()#启动线程
            self.worker1 = t1
            flagThread = False
        
    # 消息推送回调函数
    def on_message(self, client, obj, msg):
        logger.debug("on message, topic: %s, qos: %s, data: %s" %(msg.topic, msg.qos, msg.payload))
        # 对订阅的主题进行逻辑处理
        if msg.topic == "test01":
            logger.info("deal test01, data: %s" % msg.payload)#判断订阅主题
        else:
            logger.info("other topic %s, data: %s" %(msg.topic, msg.payload))

    def on_publish(self, client, obj, mid):
        global count#全局变量的引用
        logger.debug("publish -> ,mid: %s" % mid)  # 记录发送消息的mid值，
        logger.info("发送-----OK！%d", count)
        count = count + 1
        # 此处添加设备数据收发指示灯 闪烁count次
        led_toggle(17, count)
    # 当代理响应订阅请求时调用。该中期变量从相应返回的中期可变匹配订阅（）调用。该granted_qos变量是给QoS级别的经纪人已经授予每个不同的订阅请求的整数列表

    def on_subscribe(self, client, obj, mid, granted_qos):
        logger.debug("subscribed <- ,mid: %s, qos: %s" %(mid, granted_qos))  # 记录当前消息产生的mid值和qos等级

    # Bug记录者
    def on_log(self, mqttc, obj, level, string):
        logger.debug("mqtt debug: %s, %s" %(level, string))  # 记录bug，格式为：等级 + 事件

    def on_disconnect(self, client, userdata, rc):  # 掉线处理
        global flagUploadData
        flagUploadData = False#设备离线标志变量
        # 只需要在此处加 连接失败的指示灯即可 常灭
        led_off(18)  # 引脚18闭灯
        led_off(17)  # 引脚17闭灯
        # print('连接失败-----on_disconnect')
        logger.info('连接失败-----on_disconnect')
        #logger.info("disconnect: %s" % rc)

        # 如果rc == 1协议版本错误，则重新连接
        while rc == 1:
            # 重新连接直到re == 0 跳出循环
            try:
                # 调用重新连接函数
                client.reconnect()
                #logger.info("reconnect success")
                rc = 0
                logger.info('连接成功-----on_disconnect_内')
            except Exception as e:  # e在Python中可以用e.vaule实现，可以查看错误
                #logger.error("reconnect error, %s retry after 3s" % e)
                logger.info('连接失败---%s--on_disconnect_内，3S后重新连接----' % e)
                time.sleep(3)  # 休息3秒，爷累了

    def run(self, host, port, keepalive, namespace, auif):
        # 上电后程序入口
        # 设置产品ID和密码 上电自检 检测设备是否联到网络  若开机未连接到网络  3s重连
        flag = 1  # 设置标指旗帜
        while flag == 1:
            # try子句先执行，接下来执行时是否出现异常
            try:
                # 为代理认证设置一个用户名和一个可选的密码
                # auif = "craftsman0012"   # 设备鉴权信息 namespace = "344248"     # 产品ID
                self.username_pw_set(namespace, auif)
                # 使用connect（）连接到代理
                # host：远程代理的主机名或IP地址
                # port：要连接的服务器主机的网络端口。默认为1883
                # keepalive：与代理通信之间允许的最长时间（以秒为单位）。如果没有交换其他消息，则控制客户端将ping消息发送给代理的速率
                self.connect(host, port, keepalive)
                flag = 0  # 标志旗倒下，跳出循环
                # 此处可以添加系统运行正常指示灯
                logger.info('连接成功-----run')  # 记录日志

            # 出错时
            except Exception as e:
                #logger.info("reconnect error, retry after 3s")
                # 只需要在此处加 连接失败的指示灯即可 常灭
                led_off(18)  # 引脚18闭灯
                led_off(17)  # 引脚17闭灯
                logger.info('连接失败-----run')
                time.sleep(3)  # 等待3秒重试

        # rc ReConnect的缩写，检查设备连接状况
        '''
        0	连接成功
        1	协议版本错误
        2	无效的客户端标识
        3	服务器无法使用
        4	错误的用户名或密码
        5	未经授权
        '''
        while True:
            rc = self.loop()  # 保持与Broker网络连接
            #logger.info("打印当前的rc值是 %s" % rc)
            if rc != 0:
                logger.info("重新连接网络成功-------run")
                time.sleep(1)  # 休息1秒
                rc = self.loop()  # 循环执行
                logger.info("recovery from error loop, %s" %rc)  # 记录连接问题方便以后调试
                        
def main():
    # 加载配置文件，这里并不将账户名
    conf = Conf("/boot/config.json")
    # 初始化所有GPIO为输出状态，且输出低电平
    gpio_setup()
    
    # host = "183.230.40.39"  # EMQ平台IP地址(mqtt协议)
    # port = 6002            # 端口
    # namespace = "345719"     # 产品ID
    # keepalive = 10   # 跟EMQ平台保活时间 单位s
    # client_id = "598256294" # 设备ID
    # auif = "nange123456"   # 设备鉴权信息
    
    # EMQ平台IP地址(mqtt协议)
    host = conf["host"]  
    # EMQ平台IP地址(mqtt协议)端口
    port = conf["port"]     
    # 产品ID    
    namespace = conf["namespace"] 
    # 跟EMQ平台保活时间 单位s    
    keepalive = conf["keepalive"]  
    # 设备ID
    client_id = conf["client_id"]
    # 设备鉴权信息
    auif = conf["auif"]   

    client = MyMQTTClass(client_id)
    client.run(host, port, keepalive, namespace, auif)

# 即文件作为脚本直接执行，才会被执行
if __name__ == "__main__":
    main()