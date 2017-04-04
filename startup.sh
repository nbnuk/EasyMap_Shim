#!/bin/sh -e

cd /home/ubuntu/EasyMap_Shim
sudo iptables-restore < iptables.conf
nohup python server.py &

