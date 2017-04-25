import json
import urllib.request
import os.path
from simpleflock import SimpleFlock

#Create and cache a lookup table for the old style data source ids
def createUidForGuidCache(filename):
   guid_to_uid={}
   req = 'http://records-ws.nbnatlas.org/occurrences/search?q=*:*&facets=data_resource_uid&flimit=-1&pageSize=0'
   rsp=urllib.request.urlopen(req).readall().decode('utf-8')
   obj1=json.loads(rsp)
   for i in obj1['facetResults'][0]['fieldResult']:
      druid = i['fq'].split(':')[1].strip('\"')
      req = 'https://registry.nbnatlas.org/ws/dataResource/'+druid
      try:
         rsp=urllib.request.urlopen(req).readall().decode('utf-8')
         obj2 = json.loads(rsp)
         guid_to_uid[obj2['guid']]=obj2['uid']
      except:
         pass
   with SimpleFlock(filename+'.lock', 10):
      with open(filename,'w') as f:
         json.dump(guid_to_uid,f)

#Load (cached) data source table. If old datasource cannot be found, assume it's a new druid
_druid=None
_druid_mtime=-1
def druidForDs(ds):
   global _druid, _druid_mtime
   cachefilename='guid-to-uid.json'
   if(os.path.getmtime(cachefilename)!=_druid_mtime):
      _druid_mtime=os.path.getmtime(cachefilename)
      with SimpleFlock(cachefilename+'.lock', 10):
         with open(cachefilename,'r') as f:
            _druid=json.load(f)
   try:
      result=_druid[ds]
   except:
      result=ds
   return result

def sciNameForTVK(tvk):
   req = 'https://species-ws.nbnatlas.org/species/'+tvk
   rsp=urllib.request.urlopen(req).readall().decode('utf-8')
   obj=json.loads(rsp)
   try:
      nameString=obj['taxonConcept']['nameString']
   except:
      nameString='No taxonConcept/nameString for tvk:'+tvk
   return nameString

def comNameForTVK(tvk):
   req = 'https://species-ws.nbnatlas.org/species/'+tvk
   rsp=urllib.request.urlopen(req).readall().decode('utf-8')
   obj=json.loads(rsp)
   try:
      nameString=obj['commonNames'][0]['nameString']
   except:
      nameString=sciNameForTVK(tvk)+' (no common names)'
   return nameString

def datasourceListForDRUIDSandTVK(druids,tvk):
   req = 'http://records-ws.nbnatlas.org/occurrences/search?q=*:*&fq=lsid:'+tvk+'&facets=data_resource_uid&flimit=-1&pageSize=0'
   rsp=urllib.request.urlopen(req).readall().decode('utf-8')
   obj=json.loads(rsp)
   result=[]
   for i in obj['facetResults'][0]['fieldResult']:
      druid = i['fq'].split(':')[1].strip('\"')
      count = int(i['count'])
      if (len(druids)==0 or druid in druids) and count>0:
         result.append(i['label'])
   return result

acceptedTVKs={}
def acceptedTVKforTVK(tvk):
   try:
      result=acceptedTVKs[tvk]
   except:
      req = 'https://species-ws.nbnatlas.org/species/'+tvk
      rsp=urllib.request.urlopen(req).readall().decode('utf-8')
      obj=json.loads(rsp)
      try:
         result=obj['taxonConcept']['acceptedConceptID']
      except:
         result=tvk
   acceptedTVKs[tvk]=result
   return result
