#!/usr/bin/env python3
#Remove all 'small' files from the cache

from glob import glob
from os import remove
from os.path import getsize

cachefiles=glob("/home/ubuntu/EasyMap_Shim/cache/*/*/*")
for filepath in cachefiles:
   if getsize(filepath)<10000:
      remove(filepath)      

