#!/usr/bin/env python

from loadimage import imageFor
from PIL import Image

from loadbboxes import bboxFor

from loaddatasources import allUidForGuid

from coordtransform import NE_to_EPSG3857, GR_to_EPSG3857

import tornado.httpserver
import tornado.ioloop
import tornado.web
import re

class requestHandler(tornado.web.RequestHandler):
   def get(self):

      def clamp(n, smallest, largest): return max(smallest, min(n, largest))

      tvk = self.get_argument('tvk')
      tvk = re.sub(r'[^a-zA-Z0-9]', '', tvk) #sanitise

      vc = self.get_argument('vc',default='')
      vc = re.sub(r'[^0-9]', '', vc) #sanitise
      zoom = self.get_argument('zoom',default='UK')
      zoom = re.sub(r'[^a-zA-Z\-]', '', zoom).lower() #sanitise
      if vc=='': vc=zoom
      (lon0,lat0,lon1,lat1)=bboxes[vc]

      bl = self.get_argument('bl',default=False) 
      tr = self.get_argument('tr',default=False)
      if bl and tr:
         bl = re.sub(r'[^a-zA-Z0-9]', '', bl) #sanitise
         tr = re.sub(r'[^a-zA-Z0-9]', '', tr) #sanitise
         (lon0,lat0)=GR_to_EPSG3857(bl)
         (lon1,lat1)=GR_to_EPSG3857(tr)

      blCoord = self.get_argument('blCoord',default=False)
      trCoord = self.get_argument('trCoord',default=False)
      if blCoord and trCoord:
         blCoord = re.sub(r'[^0-9,]', '', blCoord).split(',') #sanitise
         trCoord = re.sub(r'[^0-9,]', '', trCoord).split(',') #sanitise
         if len(blCoord)==2 and len(trCoord)==2:
            (lon0,lat0)=NE_to_EPSG3857(blCoord)
            (lon1,lat1)=NE_to_EPSG3857(trCoord)

      ds = self.get_argument('ds','')
      ds = re.sub(r'[^a-zA-Z0-9,]', '', ds) #sanitise
      druidurl=''
      if not ds=='':
         for dsk in ds.split(','):
            if druidurl=='':
               druidurl='+AND+(data_resource_uid:'+druid[dsk]
            else:
               druidurl=druidurl+'+OR+data_resource_uid:'+druid[dsk]
         druidurl=druidurl+')'

      w = self.get_argument('w','')
      w = re.sub(r'[^0-9]', '', w) #sanitise
      w = -1 if w=='' else clamp(int(w),80,800)

      h = self.get_argument('h','')
      h = re.sub(r'[^0-9]', '', h) #sanitise
      h = -1 if h=='' else clamp(int(h),80,800)

      dpt=400000

      url1="https://layers.nbnatlas.org/geoserver/ALA/wms?layers=ALA:county_coastal_terrestrial_region"
      url2="https://records-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+"&ENV=colourmode:osgrid;color:ffff00;opacity:0.75;gridlabels:false;gridres:singlegrid"
      #Supersampling 
      #img1=imageFor(url1, lon0, lat0, lon1, lat1, w*2, h*2, dpt)
      #img1.thumbnail((img1.size[0]/2,img1.size[1]/2), Image.LINEAR)
      #img2=imageFor(url2, lon0, lat0, lon1, lat1, w*2, h*2, dpt)
      #img2.thumbnail((img2.size[0]/2,img2.size[1]/2), Image.LINEAR)
      img1=imageFor(url1, lon0, lat0, lon1, lat1, w, h, dpt)
      gray = img1.convert('L')
      img1 = gray.point(lambda x: 0 if x<8 else 255, 'L')
      img1 = img1.convert('RGBA')
      img2=imageFor(url2, lon0, lat0, lon1, lat1, w, h, dpt)
      img3=Image.alpha_composite(img1,img2)
      img3.save( 'tmp.png', 'PNG' )

      self.set_header("Content-type",  "image/png")
      with open('tmp.png','rb') as f: 
         data = f.read()
         self.write(data)
#      os.remove('tmp.png')

application = tornado.web.Application([
   (r'/EasyMap', requestHandler),
])

#Load vc/zoom tables
bboxes={}
bboxes.update(bboxFor('https://layers.nbnatlas.org/ws/objects/cl2'))  #UK Countries
bboxes.update(bboxFor('https://layers.nbnatlas.org/ws/objects/cl14')) #UK Vice Counties
#and some more I looked up by hand on google earth (gps->epsg:3857)
bboxes.update({'highland':(-775130.5274544959, 7630301.682472427, -308177.99150700646, 8134127.260152808)})
bboxes.update({'sco-mainland':(-734225.0673675996, 7278475.738469875, -176279.97964568838, 8118784.824617484)})
bboxes.update({'outer-heb':(-964621.4589895669, 7687560.282221712, -675534.4261951343, 8092442.674175756)})
bboxes.update({'uk':(-1208316.543132066, 6415818.406144551, 225030.61127155885, 8284550.873660544)})

#Load (cached) data source table
druid=allUidForGuid()

if __name__ == "__main__":
   http_server = tornado.httpserver.HTTPServer(application)
   http_server.listen(8200)
   loop=tornado.ioloop.IOLoop.instance()
loop.start()

