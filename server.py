#!/usr/bin/env python

from loadimage import imageFor
from PIL import Image, ImageEnhance

from loadbboxes import bboxFor

from loaddatasources import allUidForGuid

import tornado.httpserver
import tornado.ioloop
import tornado.web
import re

class requestHandler(tornado.web.RequestHandler):
   def get(self):
      tvk = self.get_argument('tvk')
      tvk = re.sub(r'[^a-zA-Z0-9]', '', tvk) #sanitise

      vc = self.get_argument('vc',default='')
      vc = re.sub(r'[^0-9]', '', vc) #sanitise
      zoom = self.get_argument('zoom',default='England')
      zoom = re.sub(r'[^a-zA-Z]', '', zoom).lower() #sanitise
      if vc=='':
         vc=zoom
      (lon0,lat0,lon1,lat1)=bboxes[vc]

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

      dpt=800000

      url1="https://layers.nbnatlas.org/geoserver/ALA/wms?layers=ALA:county_coastal_terrestrial_region"
      url2="https://records-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+"&ENV=colourmode:osgrid;color:ffff00;name:circle;size:4;opacity:0.5;gridlabels:false;gridres:singlegrid"
      img1=imageFor(url1, lon0, lat0, lon1, lat1, 1024, -1, dpt)
      img1.thumbnail((img1.size[0]/4,img1.size[1]/4), Image.LINEAR)
      img2=imageFor(url2, lon0, lat0, lon1, lat1, 1024, -1, dpt)
      img2.thumbnail((img2.size[0]/4,img2.size[1]/4), Image.LINEAR)
      img3 = Image.blend(img1, img2, alpha=0.65)
      img4 = ImageEnhance.Contrast(img3).enhance(2)
      img4.save( 'tmp.png', 'PNG' )

      self.set_header("Content-type",  "image/png")
      with open('tmp.png','rb') as f: 
         data = f.read()
         self.write(data)
#      os.remove('tmp.png')

application = tornado.web.Application([
   (r'/', requestHandler),
])

#Load tables
bboxes={}
bboxes.update(bboxFor('https://layers.nbnatlas.org/ws/objects/cl2'))  #UK Countries
bboxes.update(bboxFor('https://layers.nbnatlas.org/ws/objects/cl14')) #UK Vice Counties
druid=allUidForGuid()

if __name__ == "__main__":
   http_server = tornado.httpserver.HTTPServer(application)
   http_server.listen(8100)
   loop=tornado.ioloop.IOLoop.instance()
loop.start()

