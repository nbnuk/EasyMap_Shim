#!/usr/bin/env python3
#Daily cronjob to remove 'stale' files from the cache

from glob import glob
from time import time
from os.path import getmtime
from os import remove

old = 31*24*60*60
now = time()
cachefiles=glob("./cache/*/*/*")
for filepath in cachefiles:
   remove(filepath)      

