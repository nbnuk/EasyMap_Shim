import urllib.request
from PIL import Image
import io
import concurrent.futures

def imageFor(base_url, bbox_lon0, bbox_lat0, bbox_lon1, bbox_lat1, img_width, img_height, degrees_per_tile):
   #Linearly map a->b
   def mapcoord(a0,a1,b0,b1,b2):
      da=a1-a0
      db=b1-b0
      l=(b2-b0)/db
      return a0+l*da

   #Calculate the image size and size fo each tile to get the required degrees/tile
   def setup(bbox_lon0, bbox_lat0, bbox_lon1, bbox_lat1, img_width, img_height, degrees_per_tile):

      dlon=bbox_lon1-bbox_lon0
      dlat=bbox_lat1-bbox_lat0

      if img_width==-1 and img_height==-1:
         img_width=350
         img_height=350

      degrees_per_pixel_lon=dlon/img_width
      degrees_per_pixel_lat=dlat/img_height
      
      if img_width==-1:
         degrees_per_pixel=degrees_per_pixel_lat
         img_width=int(dlon/degrees_per_pixel)
      elif img_height==-1:
         degrees_per_pixel=degrees_per_pixel_lon
         img_height=int(dlat/degrees_per_pixel)
      else:
         degrees_per_pixel=max(degrees_per_pixel_lon,degrees_per_pixel_lat)

      tilesize=int(degrees_per_tile/degrees_per_pixel)

      return (img_width, img_height, tilesize)

   #Parallelisable routine to load tile and save its position in the image
   def loadtile(tilespec, timeout):
      with urllib.request.urlopen(tilespec['url']) as req:
         f = io.BytesIO(req.read())
      tileimg = Image.open(f)
      return {'tileimg':tileimg,'pos':tilespec['pos']}

   #Setup configuration
   (Width,Height,TileSize)=setup(bbox_lon0, bbox_lat0, bbox_lon1, bbox_lat1, img_width, img_height, degrees_per_tile)

   #Iterate over all tiles and create url requests
   tilespecs=[] #url and x,y position in final image
   for x in range(0,Width,TileSize):
      for y in range(0,Height,TileSize):
          bblon0=mapcoord(bbox_lon0,bbox_lon1,0,Width,x)
          bblon1=mapcoord(bbox_lon0,bbox_lon1,0,Width,x+TileSize)
          bblat0=mapcoord(bbox_lat0,bbox_lat1,0,Height,y)
          bblat1=mapcoord(bbox_lat0,bbox_lat1,0,Height,y+TileSize)
          bbox=str(bblon0)+","+str(bblat0)+","+str(bblon1)+","+str(bblat1)
          url=base_url+"&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&BBOX="+bbox+"&SRS=EPSG:3857&WIDTH="+str(TileSize)+"&HEIGHT="+str(TileSize)+"&format=image%2Fpng"
          tilespecs.append({'url':url,'pos':(x, Height-TileSize-1-y)})

   #Create workers to load each tile
   tileobjs=[]
   with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
      future_to_url = {executor.submit(loadtile, tilespec, 60): tilespec['url'] for tilespec in tilespecs}
      for future in concurrent.futures.as_completed(future_to_url):
         try:
            tileobj = future.result()
         except Exception as exc:
            print('%r generated an exception: %s' % (future_to_url[future], exc))
         else:
            tileobjs.append(tileobj)

   #Combine the tiles into the final image
   img=Image.new("RGBA",(Width,Height))
   for tileobj in tileobjs:
      img.paste(tileobj['tileimg'],tileobj['pos'])
   return img


