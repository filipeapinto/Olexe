import jsonpickle
import simplejson
import re 
from jsonpickle import tags

class Subscriber(): 
   def __init__(self): 
      self.firstname = "Neal"
      self.lastname  = "Walters" 
      self.city      = "Rockwall" 
      self.state     = "TX" 
      self.zipcode   = "75087" 

objSubscriber = Subscriber()
objSubscriber.city = "Tulsa"
objSubscriber.state = "OK" 
#print "\nType=" + str(type(objSubscriber))
print "Class=" + objSubscriber.__class__.__name__

pickled = jsonpickle.encode(objSubscriber) 
print pickled 

pattern = '{"py/object": ".*?\.(.*?)",.*'
print "pattern=" + pattern 
result = re.findall(pattern, pickled, re.IGNORECASE)
print "number of results = " + str(len(result)) 
classType = result[0] 
print "RegEx class=" + classType 


objMisc = jsonpickle.decode(pickled)
#print "\nType=" + str(type(objMisc))
print "UnPickled Class=" + objMisc.__class__.__name__


unpickler1 = jsonpickle.Unpickler() 
objMisc2 = unpickler1.restore(pickled) 
print "\n\nUnPickled Class=" + objMisc2.__class__.__name__
print "objMisc2=" + objMisc2

#for key in objMisc2.__dict__: 
#   print key + "=" + objCommonTaskMessage.__dict__[key] 
