#!/bin/bash -e

cd /home/ubuntu/EasyMap_Shim
sudo iptables-restore < iptables.conf
source ENV/bin/activate
nohup python -u httpredirectserver.py &
nohup python -u server.py &

