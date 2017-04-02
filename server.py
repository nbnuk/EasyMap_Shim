#!/usr/bin/env python
#delete following on refactor
import urllib.request
import io

from loadimage import imageFor
from PIL import Image

from loadbboxes import bboxFor

from loaddatasources import allUidForGuid

from coordtransform import NE_to_EPSG3857, GR_to_EPSG3857, EPSG3857_to_EPSG4326

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.template
import hashlib
import re
import os
import time

def clamp(n, smallest, largest): return max(smallest, min(n, largest))

def hashToCachePath(hash):
   cachepath='cache/'+hash[0:2]+'/'+hash[2:4]+'/'+hash[4:]
   os.makedirs('/'.join(cachepath.split('/')[0:2]),exist_ok=True)
   os.makedirs('/'.join(cachepath.split('/')[0:3]),exist_ok=True)
   return cachepath

class imageRequestHandler(tornado.web.RequestHandler):

   def generateImage(self):
      
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
      if self.get_argument('b0from',default=False) or self.get_argument('b0to',default=False):
         b0from = self.get_argument('b0from',default='0000')
         b0from = re.sub(r'[^0-9]', '', b0from) #sanitise
         if not len(b0from)==4: b0from=False
         b0to = self.get_argument('b0to',default='9999')
         b0to = re.sub(r'[^0-9]', '', b0to) #sanitise
         if not len(b0to)==4: b0to=False
         rangeurl0 = '+AND+year:['+b0from+'+TO+'+b0to+']'
      else:
         rangeurl0 = ''
      b0fill = self.get_argument('b0fill',default='FFFF00').upper()
      b0fill = re.sub(r'[^A-F0-9]', '', b0fill) #sanitise
      if not len(b0fill)==6: b0fill='000000'
      #b0bord =self.get_argument('b0bord',default='000000')

      #Date Band (1 optional layer)
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

      #Date Band (2 optional layer)
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

      #Resolution (10km - use tiles, 2km, 1km, 100m render using static image service circles)
      res = self.get_argument('res',default='').lower()
      if not (res=='10km' or res=='2km' or res=='1km' or res=='100m'): res='10km'
      #Degrees Per Tile (used to control which layer is returned by wms)
      dpt={'10km':400000,'2km':80000,'1km':40000,'100m':4000}[res]
      maxtiles=200

      urlBase="https://layers.nbnatlas.org/geoserver/ALA/wms?layers=ALA:county_coastal_terrestrial_region"
      urlBase="https://layers.nbnatlas.org/geoserver/ALA/wms?layers=ALA:world"
      urlBase="http://129.206.228.72/cached/hillshade?LAYERS=europe_wms:hs_srtm_europa&STYLES="
      url0="https://records-dev-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl0+"&ENV=colourmode:osgrid;color:"+b0fill+";opacity:0.75;gridlabels:false;gridres:singlegrid"
      url1=False if rangeurl1=='' else "https://records-dev-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl1+"&ENV=colourmode:osgrid;color:"+b1fill+";opacity:0.75;gridlabels:false;gridres:singlegrid"
      url2=False if rangeurl2=='' else "https://records-dev-ws.nbnatlas.org/ogc/wms/reflect?q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl2+"&ENV=colourmode:osgrid;color:"+b2fill+";opacity:0.75;gridlabels:false;gridres:singlegrid"

      imgBase = imageFor(urlBase, lon0, lat0, lon1, lat1, w, h, 0, 1)
      #imgBaseGreyThreshold = imgBase.convert('L').point(lambda x: 0 if x<8 else 255, 'L')
      #imgBase = imgBaseGreyThreshold.convert('RGBA')
      imgLayer=imageFor(url0, lon0, lat0, lon1, lat1, w, h, dpt, maxtiles)
      if not imgLayer: #If failed to get an image layer, probably too many tiles requested. Fall back to a 'mapping' url
         print('fallback')
         #At dpi=254, 1 inch=25.4mm (defined), dpmm=dpi/i/mm dpmm=254/1/25.4=10, so 1mm=10pixels for width and height
         radius={'10km':500,'2km':100,'1km':50,'100m':5}[res]*w/(lon1-lon0) #radius (grid /20 [/2 for radius 1mm=10px])*imgwidth(px)/worldwidth(m)
         radius=str(radius) if radius>=0.1 else "0.1" #radius<0.1mm are not drawn by the mapping service
         (lon0,lat0)=EPSG3857_to_EPSG4326((lon0,lat0))
         (lon1,lat1)=EPSG3857_to_EPSG4326((lon1,lat1))
         (w,h)=imgBase.size
         url = "https://records-ws.nbnatlas.org/mapping/wms/image?baselayer=world&format=png&pcolour=3531FF&scale=on&popacity=0.5&q=*:*&fq=species_guid:"+tvk+druidurl+rangeurl0+"&extents="+str(lon0)+","+str(lat0)+","+str(lon1)+","+str(lat1)+"&outline=true&outlineColour=0x000000&pradiusmm=0.1&dpi=254&widthmm="+str(w/10)
         #druid and range currently broken in api, awaiting fix
         url = "https://records-ws.nbnatlas.org/mapping/wms/image?baselayer=world&format=png&pcolour="+b0fill+"&scale=off&popacity=1.0&q=*:*&fq=species_guid:"+tvk+"&extents="+str(lon0)+","+str(lat0)+","+str(lon1)+","+str(lat1)+"&outline=true&outlineColour=0x000000&pradiusmm="+radius+"&dpi=254&widthmm="+str(w/10)
         with urllib.request.urlopen(url) as req:
            f = io.BytesIO(req.read())
         imgLayer = Image.open(f).resize(imgBase.size, Image.NEAREST)
      imgResult=Image.alpha_composite(imgBase,imgLayer)

      if url1:
         imgLayer=imageFor(url1, lon0, lat0, lon1, lat1, w, h, dpt, maxtiles)
         imgResult=Image.alpha_composite(imgResult,imgLayer)
      if url2:
         imgLayer=imageFor(url2, lon0, lat0, lon1, lat1, w, h, dpt, maxtiles)
         imgResult=Image.alpha_composite(imgResult,imgLayer)
      return imgResult
   
   def get(self):
      #Time after which a new image will be generated instead of cache version (0 to force generation)
      cachedays = self.get_argument('cachedays',default='7')
      cachedays = int(re.sub(r'[^0-9]', '', cachedays)) #sanitise
      cachedays = clamp(cachedays, 0, 365)

      #Get path to cached file (remove the additional cachedays parameter, which must be last in the uri)
      uri = self.request.uri.split('&cachedays')[0]
      cachepath = hashToCachePath(hashlib.sha256(uri.encode('utf8')).hexdigest())

      if (not os.path.exists(cachepath)) or (time.time()-os.path.getmtime(cachepath))>cachedays*24*60*60:
         img = self.generateImage()
         img.save(cachepath, 'PNG' )

      self.set_header("Content-type",  "image/png")
      with open(cachepath,'rb') as f:
         data = f.read()
         self.write(data)

class easymapRequestHandler(tornado.web.RequestHandler):
   def initialize(self):
      self.template_loader = tornado.template.Loader("templates")

   def get(self):
      #Adjust uri to return insert image in html
      image_url = re.sub(r'/EasyMap', '/Image', self.request.uri)
      self.write(self.template_loader.load('maponly.html').generate(image_url=image_url))

class singlespeciesRequestHandler(tornado.web.RequestHandler):
   def get(self, tvk):
       #Monkey mapping of a small set of singlespecies params to easymap params
      #https://gis.nbn.org.uk/SingleSpecies/NHMSYS0001387317/map?datasets=GA000157,GA001180&resolution=10km&imagesize=4&band=1600-1987,ffffff,000000&band=1988-1997,0095ff,000000&band=1998-2025,0000ff,000000
      #sizes=[(100,135),(200,270),(300,405),(400,540),(500,675),(600,810),(700,945),(800,1080),(900,1215),(1000,1350),(1100,1485),(1200,1620),(1300,1755),(1400,1890),(1500,2025)]

      def getbandparams(paramstring):
         params=(paramstring.split(',')) #'start_year-stop_year','fill_col' (,'border_col ignored')
         years = re.sub(r'[^0-9\-]','',params[0]).split('-')
         year0 = years[0] if len(years) > 0 and len(years[0])==4 else '0000'
         year1 = years[1] if len(years) > 1 and len(years[1])==4 else '9999'
         fillc = 'ffffff'
         if len(params)>1:
            c = re.sub(r'[^0-9a-f]','',params[1].lower())
            if len(c)==6: fillc = c
         return (year0,year1,fillc)

      #tvk=self.request.uri.split('/')[4]
      datasets=self.get_argument('datasets',default=False)
      w=str(clamp(int(re.sub('[^0-9]','',self.get_argument('imagesize',default='10'))),1,10)*100)
      bands=self.get_arguments('band')
      (b0from,b0to,b0fill) = getbandparams(bands[0]) if len(bands) > 0 else (False, False, False)
      (b1from,b1to,b1fill) = getbandparams(bands[1]) if len(bands) > 1 else (False, False, False)
      (b2from,b2to,b2fill) = getbandparams(bands[2]) if len(bands) > 2 else (False, False, False)
      url = '/Image?tvk='+tvk+'&w='+w
      if datasets: url = url + '&datasets='+datasets
      if b0from:   url = url + '&b0from='+b0from+'&b0to='+b0to+'&b0fill='+b0fill
      if b1from:   url = url + '&b1from='+b1from+'&b1to='+b1to+'&b1fill='+b1fill
      if b2from:   url = url + '&b2from='+b2from+'&b2to='+b2to+'&b2fill='+b2fill
      self.redirect(url) 

application = tornado.web.Application([
   (r'/EasyMap', easymapRequestHandler),
   (r'/Image', imageRequestHandler),
   (r'/SingleSpecies/(.*)/map', singlespeciesRequestHandler),
   (r'/(.*)', tornado.web.StaticFileHandler, {'path': 'static', 'default_filename': 'index.html'})
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

