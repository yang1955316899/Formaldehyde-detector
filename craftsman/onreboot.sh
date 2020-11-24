#########################################################################
# File Name: onreboot.sh
# Author: NanGe
# Created Time: 2020.05.16
#########################################################################
#!/bin/bash

chmod 777 /boot/craftsman
chmod 777 /boot/config.json
cd /boot/craftsman
/usr/bin/python3 mqtt2OneNET.py
