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

      #TaxonVersionKey (required)
      tvk = self.get_argument('tvk')
      tvk = re.sub(r'[^a-zA-Z0-9]', '', tvk) #sanitise

      #Vice County
      vc = self.get_argument('vc',default='')
      vc = re.sub(r'[^0-9]', '', vc) #sanitise
      zoom = self.get_argument('zoom',default='UK')
      zoom = re.sub(r'[^a-zA-Z\-]', '', zoom).lower() #sanitise
      if vc=='': vc=zoom
      (lon0,lat0,lon1,lat1)=bboxes[vc]

      #OSGrid Reference
      bl = self.get_argument('bl',default=False) 
      tr = self.get_argument('tr',default=False)
      if bl and tr:
         bl = re.sub(r'[^a-zA-Z0-9]', '', bl) #sanitise
         tr = re.sub(r'[^a-zA-Z0-9]', '', tr) #sanitise
         (lon0,lat0)=GR_to_EPSG3857(bl)
         (lon1,lat1)=GR_to_EPSG3857(tr)

      #Northing,Easting
      blCoord = self.get_argument('blCoord',default=False)
      trCoord = self.get_argument('trCoord',default=False)
      if blCoord and trCoord:
         blCoord = re.sub(r'[^0-9,]', '', blCoord).split(',') #sanitise
         trCoord = re.sub(r'[^0-9,]', '', trCoord).split(',') #sanitise
         if len(blCoord)==2 and len(trCoord)==2:
            (lon0,lat0)=NE_to_EPSG3857(blCoord)
            (lon1,lat1)=NE_to_EPSG3857(trCoord)

      #Retrict the range of lat,lon and correct the order
      lon0 = clamp(lon0,bboxes['uk'][0],bboxes['uk'][2])
      lat0 = clamp(lat0,bboxes['uk'][1],bboxes['uk'][3])
      lon1 = clamp(lon1,bboxes['uk'][0],bboxes['uk'][2])
      lat1 = clamp(lat1,bboxes['uk'][1],bboxes['uk'][3])
      if lon0>lon1: lon0,lon1 = lon1,lon0
      if lat0>lat1: lat0,lat1 = lat1,lat0

      #Datasource
      ds = self.get_argument('ds',default='')
      ds = re.sub(r'[^a-zA-Z0-9,]', '', ds) #sanitise
      druidurl=''
      if not ds=='':
         for dsk in ds.split(','):
            if druidurl=='':
               druidurl='+AND+(data_resource_uid:'+druid[dsk]
            else:
               druidurl=druidurl+'+OR+data_resource_uid:'+druid[dsk]
         druidurl=druidurl+')'

      #Image Width
      w = self.get_argument('w',default='')
      w = re.sub(r'[^0-9]', '', w) #sanitise
      w = -1 if w=='' else clamp(int(w),80,800)

      #Image Height
      h = self.get_argument('h',default='')
      h = re.sub(r'[^0-9]', '', h) #sanitise
      h = -1 if h=='' else clamp(int(h),80,800)

      #Date Band (0)
      b0from = self.get_argument('b0from',default='0000')
      b0from = re.sub(r'[^0-9]', '', b0from) #sanitise
      if not len(b0from)==4: b0from=False
      b0to = self.get_argument('b0to',default='9999')
      b0to = re.sub(r'[^0-9]', '', b0to) #sanitise
      if not len(b0to)==4: b0to=False
      b0fill = self.get_argument('b0fill',default='FFFF00').upper()
      b0fill = re.sub(r'[^A-F0-9]', '', b0fill) #sanitise
      if not len(b0fill)==6: b0fill='000000'
      #b0bord =self.get_argument('b0bord',default='000000')
      rangeurl0 = '' if not (b0from and b0to) else '+AND+year:['+b0from+'+TO+'+b0to+']'

      #Date Band (1 optional)
      if self.get_argument('b1from',default=False) or self.get_argument('b1to',default=False):
         b1from = self.get_argument('b1from',default='0000')
         b1from = re.sub(r'[^0-9]', '', b1from) #sanitise
         if not len(b1from)==4: b1from=False
         b1to = self.get_argument('b1to',default='9999')
         b1to = re.sub(r'[^0-9]', '', b1to) #sanitise
         if not len(b1to)==4: b1to=False
         b1fill = self.get_argument('b1fill',default='FF00FF').upper()
         b1fill = re.sub(r'[^A-F0-9]', '', b1fill) #sanitise
         if not len(b1fill)==6: b1fill='000000'
         #b1bord =self.get_argument('b1bord',default='000000')
         rangeurl1 = '+AND+year:['+b1from+'+TO+'+b1to+']'
      else:
         rangeurl1 = ''

      #Date Band (2 optional)
      if self.get_argument('b2from',default=False) or self.get_argument('b2to',default=False):
         b2from = self.get_argument('b2from',default='0000')
         b2from = re.sub(r'[^0-9]', '', b2from) #sanitise
         if not len(b2from)==4: b2from=False
         b2to = self.get_argument('b2to',default='9999')
         b2to = re.sub(r'[^0-9]', '', b2to) #sanitise
         if not len(b2to)==4: b2to=False
         b2fill = self.get_argument('b2fill',default='00FFFF').upper()
         b2fill = re.sub(r'[^A-F0-9]', '', b2fill) #sanitise
         if not len(b2fill)==6: b2fill='000000'
         #b2bord =self.get_argument('b2bord',default='000000')
         rangeurl2 = '+AND+year:['+b2from+'+TO+'+b2to+']'
      else:
         rangeurl2 = ''

      dpt=400000

      urlBase="https://layers.nbnatlas.org/geoserver/ALA/wms?layers=ALA:county_coastal_terrestrial_region"
      url0="https://records-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl0+"&ENV=colourmode:osgrid;color:"+b0fill+";opacity:0.75;gridlabels:false;gridres:singlegrid"
      url1=False if rangeurl1=='' else "https://records-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl1+"&ENV=colourmode:osgrid;color:"+b1fill+";opacity:0.75;gridlabels:false;gridres:singlegrid"
      url2=False if rangeurl2=='' else "https://records-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl2+"&ENV=colourmode:osgrid;color:"+b2fill+";opacity:0.75;gridlabels:false;gridres:singlegrid"

      #Supersampling 
      #img1=imageFor(url1, lon0, lat0, lon1, lat1, w*2, h*2, dpt)
      #img1.thumbnail((img1.size[0]/2,img1.size[1]/2), Image.LINEAR)
      #img2=imageFor(url2, lon0, lat0, lon1, lat1, w*2, h*2, dpt)
      #img2.thumbnail((img2.size[0]/2,img2.size[1]/2), Image.LINEAR)
      imgBase = imageFor(urlBase, lon0, lat0, lon1, lat1, w, h, dpt)
      imgBaseGreyThreshold = imgBase.convert('L').point(lambda x: 0 if x<8 else 255, 'L')
      imgBase = imgBaseGreyThreshold.convert('RGBA')
      imgLayer=imageFor(url0, lon0, lat0, lon1, lat1, w, h, dpt)
      imgResult=Image.alpha_composite(imgBase,imgLayer)
      if url1:
         imgLayer=imageFor(url1, lon0, lat0, lon1, lat1, w, h, dpt)
         imgResult=Image.alpha_composite(imgResult,imgLayer)
      if url2:
         imgLayer=imageFor(url2, lon0, lat0, lon1, lat1, w, h, dpt)
         imgResult=Image.alpha_composite(imgResult,imgLayer)
      imgResult.save( 'tmp.png', 'PNG' )

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

