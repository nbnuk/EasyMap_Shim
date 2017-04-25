#!/bin/bash -e

cd /home/ubuntu/EasyMap_Shim
sudo iptables-restore < iptables.conf
source ENV/bin/activate
nohup python -u httpredirectserver.py </dev/null >/dev/null 2>&1 &
nohup python -u server.py </dev/null >/dev/null 2>&1 &
