from pyproj import Proj, transform 

EPSG4326=Proj(init='epsg:4326')
#EPSG3857=Proj(init='epsg:3857')
EPSG27700=Proj(init='epsg:27700')

def EPSG27700_to_EPSG4326(LL):
   return transform(EPSG27700, EPSG4326, LL[0], LL[1])

def GR_to_EPSG27700(GR):
   NE=GR_to_NE(GR)
   return NE

#def EPSG3857_to_EPSG4326(LL):
#   return transform(EPSG3857, EPSG4326, LL[0], LL[1])

#def NE_to_EPSG3857(NE):
#   return transform(EPSG27700, EPSG3857, NE[0], NE[1])

#def GR_to_EPSG3857(GR):
#   NE=GR_to_NE(GR)
#   return NE_to_EPSG3857(NE)

#GR_to_NE is not verbatim as the version on the os website has a bug (as below). Also, integer division fixed for python3.
#https://www.ordnancesurvey.co.uk/business-and-government/help-and-support/web-services/os-openspace/tutorials/bill-chadwick-eastings-and-northings-from-grid-reference.html
def GR_to_NE( gr ):   
   gr = gr.strip().replace( ' ', '' )
   if len(gr) == 0 or len(gr) % 2 == 1 or len(gr) > 12:
      return None, None
    
   gr = gr.upper()  
   if gr[0] not in 'STNOH' or gr[1] == 'I' :
      return None, None
      
   e = n = 0
   c = gr[0]
   
   if c == 'T' :
      e = 500000
   elif c == 'N' :
      n = 500000
   elif c == 'O' :
      e = 500000
      n = 500000
   elif c == 'H':
      n = 1000000 #Incorrect on os website as n = 10000000
   
   c = ord(gr[1]) - 66
   if c < 8: # J
      c += 1;
      
   e += (c % 5) * 100000;
   n += (4 - int(c/5)) * 100000;
   
   c = gr[2:]
   try :
      s = c[:int(len(c)/2)]
      while len(s) < 5 :
         s += '0'
         
      e += int( s ) 
      
      s = c[-int(len(c)/2):]
      while len(s) < 5 :
         s += '0';
      
      n += int( s )
      
   except Exception:
      return None,None;
   
   return e,n
