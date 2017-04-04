#!/bin/sh -e

cd /home/ubuntu/EasyMap_Shim
sudo iptables-load < iptables.conf
nohup python server.py &

