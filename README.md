## 功能描述：  
	1、获取甲醛传感数据，通讯方式UART方式，实现了主动上传和问答式回传，传感数据异常报警机制。  
	2、传感数据上传EMQ平台，使用MQTT协议将传感数据周期上传EMQ平台，网络自检机制，发现断网后，主动重连。  
	3、状态指示，上电联网成功与否指示灯，传感数据采集状态指示灯，传感数据正常周期闪烁，错误指示灯熄灭。  
  
## 设备引脚对应关系图：  
	电源指示灯：PIN4(5V)  PIN6(GND)  
	Online指示灯：PIN12(BCM18) PIN14(GND)  
	数据采集指示灯：PIN11(BCM17) PIN9(GND)  
	开关机按钮：PIN5(BCM3) PIN9(GND)  

## 系统配置：  
	1、首先安装vim工具，执行：  
	```  
	sudo apt-get install vim命令
	```
	2、更换国内源，中科大的源：  
	```
	Raspbian http://mirrors.ustc.edu.cn/raspbian/raspbian/
    	sudo nano /etc/apt/sources.list
   	sudo nano /etc/apt/sources.list.d/raspi.list
	```
	3、安装pip3包：  
	```
  	curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  	sudo apt-get install python3-distutils
  	sudo python3 get-pip.py
	pip3 --version
	```

## 系统配置清单：  
	1、SSH和VNC远程登录：使用hostname登录系统，hostname为craftsman，系统登录名：密码为pi:raspberry。  
	2、必须要的安装包：  
	paho-mqtt、vim、pyserial、sudo apt-get install python3-rpi.gpio  
	3、设置树莓派不休眠：  
	```
    	cd /etc/profile.d
   	sudo vim screen.sh
    	xset dpms 0 0 0
   	xset s off
	```
	4、设置树莓派硬件UART：  
	修改cmdline.txt文件，将所有有关console的全部内容删掉并关闭板载蓝牙  
	```
   	sudo systemctl disable hciuart
	```
	编辑config.txt文件增加：  
	```  
    	dtoverlay=pi3-disable-bt
    	sudo shutdown -r now
  	sudo raspberry-config
  	sudo shutdown -r now
	```
	5、设置脚本自启动：将脚本放置在/boot目录下，配置文件config.json文件放在/boot目录下，方便系统烧录前做相关配置。  
	```  
   	sudo chmod -R 777 /boot/craftsman
    	sudo vim /etc/rc.local
    	su pi -c "exec /boot/craftsman/onreboot.sh"
	```
