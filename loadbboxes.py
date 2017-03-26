import urllib.request
import json
import re
from pyproj import Proj

def bboxFor(url):
   gpstoproj=Proj(init='epsg:3857')
   def splitOnSpace(x):
      return x.split(' ')
   bboxes={}
   rsp=urllib.request.urlopen(url).readall().decode('utf-8')
   obj=json.loads(rsp)
   for rec in obj:
      bbox=re.sub(r'[^\-0-9., ]', '', rec['bbox'])
      lid=rec['id'].lower()
      (lons,lats)=zip(*map(splitOnSpace,bbox.split(',')))
      lon0=min(float(i) for i in lons)
      lat0=min(float(i) for i in lats)
      (lon0,lat0)=gpstoproj(lon0,lat0)
      lon1=max(float(i) for i in lons)
      lat1=max(float(i) for i in lats)
      (lon1,lat1)=gpstoproj(lon1,lat1)
      bboxes[lid]=(lon0, lat0, lon1, lat1)
   return bboxes

