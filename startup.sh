#!/bin/sh -e

cd /home/ubuntu/EasyMap_Shim
sudo iptables-restore < iptables.conf
source ENV/bin/activate
nohup python server.py &

