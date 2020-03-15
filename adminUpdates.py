#!/usr/bin/env pythonf
# admin: http://localhost:8080/_ah/admin/datastore 

import os
import cgi
import logging
import traceback
import uuid #GUID 
import jsonpickle
import simplejson 
#import apptools
from datetime import datetime as datetime2
import datetime
import time 
import sys
import atom.url
import settings   #this moodule is created from source here: http://code.google.com/appengine/articles/gdata.html
from appengine_utilities.sessions import Session 
#import gdata.alt.appengine
#import gdata.docs
#import gdata.docs.service
#help(gdata.MediaSource)
#import StringIO
import wsgiref.handlers
from xml.sax import make_parser 
from xml.sax import parseString 
from xml.sax import SAXParseException
from xml.sax import ContentHandler
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.api import images
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp.util import run_wsgi_app
from django import shortcuts
#from google.appengine.ext import users
#from userpreferences import UserPreferences
#from xml.utils.iso8601 import parse  #for xml date/time conversion 
#from time import strftime 

from dbModels import ServiceType
from dbModels import Session
from dbModels import Subscriber
from dbModels import Order
from dbModels import Service
from dbModels import ServiceRatePlan
from dbModels import PaypalIPN
from dbModels import TaskLog
from dbModels import Tasks
from dbModels import TaskStatus
from dbModels import Workers
from dbModels import CustomerOrders
from dbModels import CumulusLog 
from dbModels import RatePlan
from dbModels import KeyValuePair 
from dbModels import Document 
from dbModels import Keywords 
from dbModels import Book 
from dbModels import Feedback
from dbModels import Provider
from dbModels import SubscriberProviderCredentials

from commonFunctions import buildLinks 
#from commonFunctions import userLinks
from commonFunctions import adminLinks 
from commonFunctions import loggedin 
from commonFunctions import commonUserCode
from commonFunctions import getSharedTemplateDictionary 

from commonTaskHandler import CommonTaskHandler 

from addressHelpers import orderStates
from addressHelpers import orderFinancialStates
from addressHelpers import mediaTypeChoices
from addressHelpers import appliesToChoices
from addressHelpers import adminStatusChoices
from addressHelpers import departmentChoices
from addressHelpers import feedbackTypeChoices
from addressHelpers import goalTypeChoices

from gdataCommon import GetGDocsAuthenticatedClient
from gdataCommon import GetMatchingFileFeed
from gdataCommon import GetGoogleDocHTMLContents
from gdataCommon import GDataXMLDateToPythonDateTime


#large chunks of code moved to separate python files 
from storeInitialProductBundle import StoreBundle



import jsonpickle
from jsonpickle import tags

port = os.environ['SERVER_PORT']
if port and port != '80':
  HOST_NAME = '%s:%s' % (os.environ['SERVER_NAME'], port)
else:
  HOST_NAME = os.environ['SERVER_NAME']

# *** Symbolic Constants ***
BASE = ord('0')
CACHE_SECONDS = 60 * 60;  # 60 minutes * 60 seconds/minute 
debugText = "";  # allow variable to be global? 
XMLRESULTS = ""; # global variable 
XMLVALUES = ""; 
XMLFIELD = ""; 
XMLFIELDTYPE = ""; 
OBJ = ""; 
SUBMIT = False; 

def getTrueFalseForCheckbox(fieldname,webapp): 
     if webapp.request.get(fieldname) == "on": 
        return True 
     else:
        return False    


# need this to show currently selected ratePlan on form  
class RatePlanForm(db.Model): 
  code                    = db.StringProperty()     # short code/name - 10 charactes - unique! 
  name                    = db.StringProperty()     # upto about 25-32 characters (often similar to or same as serviceTypeName)
  description             = db.StringProperty()     # lengthy description 
  isSelected              = db.BooleanProperty(default=False) 
  dbkey                   = db.StringProperty()     

#=======================================================
#Start Updates 
#=======================================================
  
class UpdateService(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']

     if self.request.get('key') < " " and self.request.get('orderId') < " ": 
        self.response.out.write("<h3>URL requires one of the following parameter keys:</h3>") 
        self.response.out.write("?key=<BR>") 
        self.response.out.write("?orderId=<BR>") 
        self.response.out.write("?serviceId=<BR>") 
        return 

     if self.request.get('key') > ' ': 
        service = Service.get(self.request.get('key')) 
        if not service:
           self.response.out.write("<h3>Service not found with key='" + str(self.request.get('key')) + "'</h3>") 
           return 

     if self.request.get('serviceId') > ' ': 
        serviceId = int(self.request.get('serviceId'))
        service = Service.get_by_id(serviceId) 
        if not service:
           self.response.out.write("<h3>Service not found with serviceId='" + str(self.request.get('serviceId')) + "'</h3>") 
           return 

     if self.request.get('orderId') > ' ': 
        #TODO - need to think about this logic, as one order could have multiple services 
        #     - why should we show only the first one? 
        orderId = int(self.request.get('orderId'))
        order = Order.get_by_id(orderId)
        if not order:
           self.response.out.write("<h3>Order not found with orderId='" + str(orderId) + "'</h3>") 
           return 
        serviceListForThisOrder = order.services 
        #there should always be one service tied to this order, but check just to be sure 
        #to avoid home page bombing for any reason 
        if not serviceListForThisOrder:  #handle value of NONE 
           self.response.out.write ("<h3>Order id=" + str(orderId) + " found, but no related services (None) </h3>") 
           return 
        if len(serviceListForThisOrder) == 0:
           self.response.out.write ("<h3>Order id=" + str(orderId) + " found, but no related services (Zero-Count)</h3>") 
           return 
        # for now, just show the first service related to this order  #TODO - consider what to do when one to many? 
        service = serviceListForThisOrder[0]

     #socialDict = {} 
     #counter = 0 
     #for social in service.socialSites:
     #   socialDict.update( {social: service.socialURLs[counter] } ) 
     #  counter += 1 

     counter = 0 
     socialHTML = ""
     for social in service.socialSites:
        socialHTML += "<tr><td>" + social + "</td><td>" + service.socialURLs[counter] + "</td></tr>"
        counter += 1 

     orderList = service.getOrders

     #first time debug of many-to-many 
     #for order in orderList:
     #    self.response.out.write("<BR> order key=" + str(order.key())) 
     #return 

     templateDictionaryLocal = {"service": service,
                                "socialHTML": socialHTML,
                                "orderList": orderList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateService.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     if 'username' in mySession: 
        currentUser = mySession['username'] 
     else: 
        currentUser = "nwalters@sprynet.com"  #for test system speed 

     if self.request.get('key') > ' ': 
        service = Service.get(self.request.get('key')) 
        if not service:
           self.response.out.write("<h3>Service not found with key=" + str(self.request.get('key')) + "</h3>") 


     #now set fields 
     service.serviceState = self.request.get('serviceState') 
     service.put() 

     debugText = debugText + "&nbsp;&nbsp; Put()" 
     self.redirect("/reportServices")    


class UpdateOrder(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']

     if self.request.get('key') < " " and self.request.get('orderId') < " ": 
        self.response.out.write("<h3>URL requires one of the following parameter keys:</h3>") 
        self.response.out.write("?key=<BR>") 
        self.response.out.write("?orderId=<BR>") 
        return 

     if self.request.get('key') > ' ': 
        order = Order.get(self.request.get('key')) 
        if not order:
           self.response.out.write("<h3>Order not found with key='" + str(self.request.get('key')) + "'</h3>") 
           return 


     if self.request.get('orderId') > ' ': 
        orderId = int(self.request.get('orderId'))
        order = Order.get_by_id(orderId)
        if not order:
           self.response.out.write("<h3>Order not found with orderId='" + str(orderId) + "'</h3>") 
           return 

     #special logic hidden to normal users 
     if self.request.get('delete') == 'True': 
        query = ServiceRatePlan.gql('WHERE order = :1 ', order.key())
        LIMIT = 1000
        serviceRatePlanList = query.fetch(LIMIT,offset=0) 
        for serviceRatePlan in serviceRatePlanList: 
	    serviceRatePlan.delete() 

        query = PaypalIPN.gql('WHERE invoice = :1 ', str(order.key().id()))
        LIMIT = 1000
        PaypalIPNList = query.fetch(LIMIT,offset=0) 
        for objPaypalIPNList in PaypalIPNList: 
	    objPaypalIPNList.delete() 

        order.delete() 

	self.response.out.write("<h3>Completed Deletion</h3>") 
        return 
        


     #set up select boxes for form to show selected values 
     for item in orderStates:
        if item.value == order.orderState:
           item.selected = True
        else:
           item.selected = False 

     for item in orderFinancialStates:
        if item.value == order.financialStatus:
           item.selected = True
        else:
           item.selected = False 


     templateDictionaryLocal = {"order": order,
                                "orderStates": orderStates,
                                "orderFinancialStates": orderFinancialStates 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateOrder.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     if 'username' in mySession: 
        currentUser = mySession['username'] 
     else: 
        currentUser = "nwalters@sprynet.com"  #for test system speed 

     if self.request.get('key') > ' ': 
        order = Order.get(self.request.get('key')) 
        if not order:
           self.response.out.write("<h3>Order not found with key=" + str(self.request.get('key')) + "</h3>") 


     #now set fields 
     order.orderState      = self.request.get('orderState') 
     order.financialStatus = self.request.get('financialStatus') 
     order.put() 

     self.redirect("/reportOrders")    


class DeleteServices(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    self.response.out.write("This form requires a post from /ReportServices") 
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     if 'username' in mySession: 
        currentUser = mySession['username'] 
     else: 
        currentUser = "nwalters@sprynet.com"  #for test system speed 


     numrows = int(self.request.get('numrows'))
     self.response.out.write("<BR>numrows=" + str(numrows) + "<BR>")

     for rownum in range(1,numrows+1):
        deleteBoxValue = self.request.get("deleteBox" + str(rownum))
        self.response.out.write("<BR>rownum=" + str(rownum) ) 
        #self.response.out.write(" deleteBox=" + str(deleteBoxValue) ) 
        key = self.request.get("key" + str(rownum))
        if deleteBoxValue == "on":
           self.response.out.write(" Deleting key=" + key)
           service = Service.get(key) 
           service.delete() 
        else: 
           self.response.out.write(" Skip   key=" + key)


     url = "/reportServices"
     self.response.out.write("<BR><BR>Deletes Have Completed, return to: <a href='" + url + "'>" + url + "</a>")
     #self.redirect("/reportServices")    




class UpdateFeedback(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    command = self.request.get("cmd") 

    key = self.request.get('key')
    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    feedback = Feedback() 
    if key > " ":
        feedback = Feedback.get(self.request.get('key')) 
        if not feedback:
           self.response.out.write("<h3>Feedback not found with key=" + key + "</h3>") 


    for item in feedbackTypeChoices:
       if item.value == feedback.feedbackType: 
          item.selected = True 
       else: 
          item.selected = False 
        

    for item in departmentChoices:
       if item.value == feedback.department: 
          item.selected = True 
       else: 
          item.selected = False 
        

    for item in adminStatusChoices:
       if item.value == feedback.adminStatus: 
          item.selected = True 
       else: 
          item.selected = False 
        
    templateDictionaryLocal = {"feedback":feedback,
                               "feedbackTypeChoices":feedbackTypeChoices,
                               "departmentChoices":departmentChoices,
                               "adminStatusChoices":adminStatusChoices,

                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateFeedback.html', templateDictionaryLocal)

  def post(self):
     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     key = self.request.get('key')

     adminPriority = self.request.get('adminPriority')
     if adminPriority != "None":  #the literal as stored on the form  
       try:
         adminPriorityNum = int(adminPriority.strip().split()[0])
       except (ValueError, IndexError):
         self.response.out.write("<h3>adminPriority is not numeric, value='" + adminPriority + "' </h3>") 
         self.response.out.write("<h3>Press the browser's 'Back' key, correct the value, and submit again.</h3>") 
         return 

       if adminPriorityNum < 0 or adminPriorityNum > 10: 
         self.response.out.write("<h3>adminPriority is not between legal values of 0 to 10, value='" + adminPriority + "' </h3>") 
         self.response.out.write("<h3>Press the browser's 'Back' key, correct the value, and submit again.</h3>") 
         return 
     




     #self.response.out.write ("Priority='" + self.request.get('adminPriority') + "'") 
     #return 

     feedback = Feedback()   #create new object (in case we are doing an ADD instead of Modify) 
     #feedback.dateTimeCreated = datetime.datetime.now() 
     #feedback.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        feedback = Feedback.get(key) 
        if not feedback:
           self.response.out.write("<h3>Feedback not found with key=" + key + "</h3>") 
           return 

     #These fields should be permanent data entry of user administrator should not be able to change. 
     #feedback.submittedDateTime = self.request.get('submittedDateTime') 
     #feedback.subscriber = self.request.get('subscriber') 
     #feedback.rating = self.request.get('rating') 
     #feedback.comments = self.request.get('comments') 
     #feedback.relatedURL = self.request.get('relatedURL') 

     feedback.feedbackType = self.request.get('feedbackType') 
     feedback.department = self.request.get('department') 
     feedback.isDefect = eval(self.request.get('isDefect')) #use eval() not bool()  
     feedback.isCumbersome = eval(self.request.get('isCumbersome')) #use eval() not bool()  
     feedback.isUgly = eval(self.request.get('isUgly')) #use eval() not bool()  
     feedback.isImStuck = eval(self.request.get('isImStuck')) #use eval() not bool() 
     

     if self.request.get('adminStatus') > " ": 
        feedback.adminStatus = self.request.get('adminStatus') 

     #need to change code-builder/parser to wrap integerProperties with int() 
     if self.request.get('adminPriority') > " " and self.request.get('adminPriority') != "None":
        feedback.adminPriority = int(self.request.get('adminPriority'))
 
     feedback.put()      
     self.redirect("/reportFeedback")    




class SubmitFeedback(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    self.response.out.write("<h3>SubmitFeedback - Only supports 'Post' method from form</h3>") 
    self.response.out.write("<a href='/home'>Home</a>") 
      

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea

     feedback = Feedback() 

     #get subscriber 
     if 'subscriberkey' in mySession:
        subscriberkey = mySession['subscriberkey']
        subscriber = Subscriber.get(subscriberkey) 
        if subscriber: 
           feedback.subscriber = subscriber 

     feedback.submittedDateTime = datetime.datetime.now() 

     feedback.rating = int(self.request.get("feedbackRating")) 
     feedback.comments = self.request.get("feedbackComments") 
     feedback.relatedURL = self.request.get('relatedURL') 


     feedback.isDefect = getTrueFalseForCheckbox("isDefect",self) 
     feedback.isCumbersome = getTrueFalseForCheckbox("isCumbersome",self) 
     feedback.isUgly = getTrueFalseForCheckbox("isUgly",self) 
     feedback.isImStuck = getTrueFalseForCheckbox("isImStuck",self) 

     feedback.put() 

     mySession['myHomeMessage'] = """
     Thank you for submitting your feedback.  
     We carefully look at each and every feedback we receive in order to improve our system.
     """

     self.redirect("/home")    



class UpdateKeyValuePair(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']

     cmd="MOD"    #default unless "ADD" is passed on URL 
     cmd = self.request.get("cmd") 

     kvp = KeyValuePair()
     if self.request.get('key') > ' ': 
        kvp = KeyValuePair.get(self.request.get('key')) 
        if not kvp:
           self.response.out.write("<h3>KeyValuePair not found with key=" + str(self.request.get('key')) + "</h3>") 
           return 
        templateDictionaryLocal = {"kvp": kvp,
                                   "cmd":cmd}
     else:
        templateDictionaryLocal = {"cmd":cmd}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateKeyValuePair.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     if 'username' in mySession:
        currentUser = mySession['username'] 
     else:
        self.redirect("/login") 
        return 

     kvp = KeyValuePair() 

     command = self.request.get("command") 

     if self.request.get('key') > ' ': 
        kvp = KeyValuePair.get(self.request.get('key')) 
        if not kvp:
           self.response.out.write("<h3>KeyValuePair not found with key=" + str(self.request.get('key')) + "</h3>") 

     strKvpIsSecure = self.request.get('kvpIsSecure') 
     if strKvpIsSecure == "True": 
        kvpIsSecure = True 
     else:
        kvpIsSecure = False 


     #now set fields for ADD/UPDATE  
     kvp.kvpValue    = self.request.get('kvpValue') 
     kvp.kvpIsSecure = kvpIsSecure 
     kvp.kvpDoc      = self.request.get('kvpDoc')
     kvp.userEmailLastModified = currentUser 

     if command == 'ADD':
        kvp.kvpKey           = self.request.get('kvpKey') 
        kvp.dateTimeCreated  = datetime.datetime.now()
        kvp.userEmailCreated = currentUser 

     kvp.put() 

     debugText = debugText + "&nbsp;&nbsp; Put()" 
     self.redirect("/reportKeyValuePairs")    



class UpdateRatePlan(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']
     ratePlan = RatePlan() 
     ratePlan.billingPeriod = "M" 

     if self.request.get('key') > ' ': 
        ratePlan = RatePlan.get(self.request.get('key')) 
        if not ratePlan:
           self.response.out.write("<h3>RatePlan not found with key=" + str(self.request.get('key')) + "</h3>") 
     
     
     if self.request.get('cmd') > 'ADD': 
        pass
        #we have already instantiated empty rateplan above, just default some fields 

     templateDictionaryLocal = {"ratePlan": ratePlan,
                                "command": self.request.get('cmd'), 
                                "debug": True
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateRatePlan.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     ratePlan = RatePlan()   #create new object (in case we are doing an ADD instead of Modify) 
     ratePlan.dateTimeCreated = datetime.datetime.now() 
     ratePlan.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if self.request.get('key') > ' ': 
        ratePlan = RatePlan.get(self.request.get('key')) 
        if not ratePlan:
           self.response.out.write("<h3>RatePlan not found with key=" + str(self.request.get('key')) + "</h3>") 


     #self.response.out.write("recurringAmount=" + str(self.request.get('recurringAmount')))
     #return 

     #now set fields from the form  
     ratePlan.code             = self.request.get('code') 
     ratePlan.name             = self.request.get('name') 
     ratePlan.description      = self.request.get('description') 

     log = CumulusLog()    
     log.category = "UpdateRatePlan:Post1" 
     log.ipaddress = self.request.remote_addr 
     log.message = "recurringAmount=" + self.request.get('recurringAmount') 
     log.put() 

     log = CumulusLog()    
     log.category = "UpdateRatePlan:Post2" 
     log.ipaddress = self.request.remote_addr 
     log.message = "onetimeAmount=" + self.request.get('onetimeAmount') 
     log.put() 
     
     # User entering 25 instead of 25.0 will cause 
     # BadValueError: Property recurringAmount must be a float
     # User might enter 12.789 and we will round to 12.79 

     ratePlan.setRecurringAmount(self.request.get('recurringAmount'))
     ratePlan.setOnetimeAmount  (self.request.get('onetimeAmount'))

     ratePlan.billingPeriod    = self.request.get('billingPeriod') 
     ratePlan.billingInterval  = int(self.request.get('billingInterval'))
     ratePlan.numberOfPayments = int(self.request.get('numberOfPayments'))
     ratePlan.dateTimeModified = datetime.datetime.now() 
     ratePlan.userModified     = currentUser 
     ratePlan.put() 


     debugText = debugText + "&nbsp;&nbsp; Put()" 
     self.redirect("/reportRatePlans")    



class UpdateServiceType(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     currentUser = params['user']
     serviceType = ServiceType() 
     # initialize any field here 
     #serviceType.xxxx = 0 

     query = RatePlan.gql('');  
     LIMIT = 1000
     ratePlanList = query.fetch(LIMIT,offset=0);

     ratePlanFormList = []
     for ratePlan in ratePlanList: 
        ratePlanFormList.append(RatePlanForm(code=ratePlan.code, description=ratePlan.description, dbkey=str(ratePlan.key()) ))


     if self.request.get('key') > ' ': 
        serviceType = ServiceType.get(self.request.get('key')) 
        if not serviceType:
           self.response.out.write("<h3>ServiceType not found with key=" + str(self.request.get('key')) + "</h3>") 

     if self.request.get('cmd') > 'ADD': 
        pass
        #we have already instantiated empty serviceType above, just default some fields 

     #loop through and set the selected=True attribute so current item will show on update screen as being selected 
     for ratePlanForm in ratePlanFormList:
        #self.response.out.write("<BR><BR> serviceType.code=" + serviceType.code + 
        #                              " st.rateplan=" + str(serviceType.ratePlan.key()) + 
        #                              " ratePlanForm.dbkey=" + ratePlanForm.dbkey) 
        if serviceType.ratePlan:               #cannot do call key() method if ratePlan is none 
           if str(serviceType.ratePlan.key()) == ratePlanForm.dbkey: 
              ratePlanForm.isSelected = True 
              #self.response.out.write("<BR>Set this item isSelect to True") 

     templateDictionaryLocal = {"serviceType": serviceType,
                                "ratePlanList": ratePlanFormList,
                                "command": self.request.get('cmd') 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateServiceType.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     serviceType = ServiceType()   #create new object (in case we are doing an ADD instead of Modify) 
     serviceType.dateTimeCreated = datetime.datetime.now() 
     serviceType.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if self.request.get('key') > ' ': 
        serviceType = ServiceType.get(self.request.get('key')) 
        if not serviceType:
           self.response.out.write("<h3>serviceType not found with key=" + str(self.request.get('key')) + "</h3>") 

     #self.response.out.write("recurringAmount=" + str(self.request.get('recurringAmount')))
     #return 

     #now set fields from the form  
     serviceType.code               = self.request.get('code') 
     serviceType.name               = self.request.get('name') 
     serviceType.infrastructureName = self.request.get('infrastructureName') 
     serviceType.description        = self.request.get('description') 

     serviceType.salesWhatIsIt            = self.request.get('salesWhatIsIt') 
     serviceType.salesWhyYouNeedIt        = self.request.get('salesWhyYouNeedIt') 
     serviceType.salesWhatsInItForYou     = self.request.get('salesWhatsInItForYou')
     serviceType.salesHowDoesItWork       = self.request.get('salesHowDoesItWork') 
     serviceType.salesSpecialInstructions = self.request.get('salesSpecialInstructions') 

     if self.request.get('isSellable') == "on": 
        serviceType.isSellable = True
     else:
        serviceType.isSellable = False 

     #ratePlan (select list) value contains the key of RatePlan 
     if self.request.get('ratePlan') != "Select one":
        ratePlan = RatePlan.get(self.request.get('ratePlan')) 
        serviceType.ratePlan = ratePlan

     serviceType.dateTimeModified = datetime.datetime.now() 
     serviceType.userModified     = currentUser 
     serviceType.put() 


     debugText = debugText + "&nbsp;&nbsp; Put()" 
     self.redirect("/reportServiceTypes")    


class UpdateBook(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     currentUser = params['user']
     serviceType = ServiceType() 
     # initialize any field here 
     #serviceType.xxxx = 0 

     book = Book()   #temp book in case we are doing ADD logic 

     query = ServiceType.gql('');  
     LIMIT = 1000
     serviceTypeList = query.fetch(LIMIT,offset=0);

     cmd = self.request.get("cmd") 
     if cmd != "ADD": 
       key = self.request.get('key')
       if key > ' ': 
          book = Book.get(key)
          if not book:
             self.response.out.write("<h3>Book not found with key=" + str(key) + "</h3>") 

     #set-up select/list for mediaType 
     for item in appliesToChoices:
        if item.value == book.appliesTo: 
           item.selected = True 
        else: 
           item.selected = False 



     templateDictionaryLocal = {"serviceTypeList": serviceTypeList,
                                "book": book,
                                "appliesToChoices": appliesToChoices,
                                "command": cmd 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateBook.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     book = Book()   #create new object (in case we are doing an ADD instead of Modify) 
     #book.dateTimeCreated = datetime.datetime.now() 
     #book.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     command = self.request.get('command') 

     if command != "ADD": 
       key = self.request.get('key')
       if key > ' ': 
          book = Book.get(key) 
          if not book:
             self.response.out.write("<h3>book not found with key=" + str(key) + "</h3>") 

     #self.response.out.write("appliesTo=" + str(self.request.get('appliesTo') ))
     #return 

     #now set fields from the form  
     book.name = self.request.get('name') 
     #prefix must be lower case because keywords are lowercase (for sorting purposes) 
     book.keywordPrefix = self.request.get('keywordPrefix').lower() 
     book.appliesTo = self.request.get('appliesTo') 
     if self.request.get('serviceType') > " ":  #user might not have moved off the "Select One" option 
        serviceType = ServiceType.get(self.request.get('serviceType')) 
        if not serviceType:
           self.response.out.write("<h3>Error serviceType not found with key=" + self.request.get('serviceType') + "</h3>") 
        book.serviceType = serviceType
     book.put()

     self.redirect("/reportBooks")    



class UpdateSession(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']

     if self.request.get('key') > ' ': 
        service = Service.get(self.request.get('key')) 
        if not service:
           self.response.out.write("<h3>Service not found with key=" + str(self.request.get('key')) + "</h3>") 

     mySession = Session() 
     sendEmailsTo = None 
     if 'sendEmailsTo' in mySession:
        sendEmailsTo = mySession['sendEmailsTo'] 

     message = ""
     templateDictionaryLocal = {"sendEmailsTo": sendEmailsTo,
                                "message": message}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateSession.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     #currentUser = mySession['username'] 

     sendEmailsTo = self.request.get('sendEmailsTo')

     #now set fields in the session variables 
     mySession = Session() 

    
     if 'sendEmailsTo' in mySession:
        if sendEmailsTo == "": 
            mySession.delete_item('sendEmailsTo')
        else: 
            mySession['sendEmailsTo'] = sendEmailsTo



     message = "<h2>Update Completed</h2>" 
     templateDictionaryLocal = {"sendEmailsTo": sendEmailsTo,
                                "message": message}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("/reportWorkers",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateSession.html', templateDictionaryLocal)



class UpdateDocument(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     #mySession = Session()

     #params = {} 
     #params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     #currentUser = params['user']

     command = self.request.get("cmd") 

     if self.request.get('key') < ' ' and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

     htmlFileContents = None 
     if self.request.get('key') > ' ': 
        document = Document.get(self.request.get('key')) 
        if not document:
           self.response.out.write("<h3>Document not found with key=" + str(self.request.get('key')) + "</h3>") 
           return 
        if document.docId:   #external links will not have google docs 
           client = GetGDocsAuthenticatedClient() 
           htmlFileContents = GetGoogleDocHTMLContents(client,document.docId) 
  
        numKeywords1 = len(document.keywords)   #save original number of keywords as variable 
        keywords = document.keywords 
     else:  
        document = Document()
        #set default values to make data-entry easier 
        document.dateTimePublished = datetime.datetime.now() 
        document.dateTimeCreated   = datetime.datetime.now() 
        document.language = "English" 
        document.mediaType = "blog" 
        numKeywords1 = 0 
        keywords = None

     #set-up select/list for mediaType 
     for item in mediaTypeChoices:
        if item.value == document.mediaType: 
           item.selected = True 
        else: 
           item.selected = False 

     message = ""
     templateDictionaryLocal = {"document": document,
                                "keywords": keywords,
                                "numKeywords1": numKeywords1,
                                "htmlFileContents": htmlFileContents,
                                "mediaTypeChoices": mediaTypeChoices,
                                "command": command, 
                                "message": message}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateDocument.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     currentUser = mySession['username'] 

     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     #params = {}
     #params = commonUserCode(params,self.request.url)
 
     #document = Document()
     if self.request.get('key') < ' ' and self.request.get('command') != "ADD": 
          self.response.out.write("<h3>Missing key= parameters</h3>") 
          return 

     if self.request.get('key') > ' ': 
       document = Document.get(self.request.get('key')) 
       if not document:
          self.response.out.write("<h3>Document not found with key=" + str(self.request.get('key')) + "</h3>") 
          return 
       self.response.out.write("<h3>Existing Document Retrieved</h3>") 
     else:
       document = Document()   

    
     counter = 0 
#    document.docId = self.request.get('docId') 
     document.docName = self.request.get('docName') 
#    document.keywords = self.request.get('keywords') 

     document.title = self.request.get('title')
     
     if self.request.get('subtitle') <> "None":
        document.subtitle = self.request.get('subtitle') 
     if self.request.get('summary') <> "None":
        document.summary = self.request.get('summary') 
     if self.request.get('authorName') <> "None":
        document.authorName = self.request.get('authorName') 
     if self.request.get('authorEmail') <> "None":
        document.authorEmail = self.request.get('authorEmail') 

     if self.request.get('mediaType') != "None":
        document.mediaType = self.request.get('mediaType') 

     document.isGDoc         = eval(self.request.get('isGDoc'))  #don't use "bool()" 
     document.isExternalLink = eval(self.request.get('isExternalLink'))


     if self.request.get('externalLink') != "None":
        document.externalLink = self.request.get('externalLink')
     
     if self.request.get('language') != "None":
        document.language = self.request.get('language') 

     document.dateTimePublished = datetime2.strptime(self.request.get('dateTimePublished'), "%m/%d/%y %H:%M:%S")

     if self.request.get('command') == "ADD": 
        document.dateTimeCreated = datetime.datetime.now()
        document.userEmailCreated = currentUser

     document.dateTimeLastModified = datetime.datetime.now()
     document.userEmailLastModified = currentUser

     document.put()     
     self.redirect("/updDocuments") 


class UpdateDocumentKeywords(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()
     currentUser = mySession['username'] 

     if self.request.get('key') < ' ': 
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

     document = Document.get(self.request.get('key')) 
     if not document:
        self.response.out.write("<h3>Document not found with key=" + str(self.request.get('key')) + "</h3>") 
        return 

     numKeywords1 = len(document.keywords)   #save original number of keywords as variable 
     keywords = Keywords.get(document.keywords) 

     #add 5 blank keywords onto the end of the list 
     #  so user can add up to 5 new keywords on the form 
     for j in range (0,5):   
        newKeywords = Keywords() 
        newKeywords.keyword = ""
        keywords.append(newKeywords)

     htmlFileContents = None 
     if document.docId: 
        client = GetGDocsAuthenticatedClient() 
        htmlFileContents = GetGoogleDocHTMLContents(client,document.docId) 
        
     message = ""
     templateDictionaryLocal = {"document": document,
                                "keywords": keywords,
                                "numKeywords1": numKeywords1,
                                "numKeywords2": len(keywords),
                                "htmlFileContents": htmlFileContents,
                                "message": message}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateDocumentKeywords.html', templateDictionaryLocal)
                     

  def post(self):
     mySession = Session()
     currentUser = mySession['username'] 

     debugText = "" 
 
     #document = Document()
     if self.request.get('key') < ' ': 
          self.response.out.write("<h3>Missing key= parameters</h3>") 
          return 

     document = Document.get(self.request.get('key')) 
     if not document:
        self.response.out.write("<h3>Document not found with key=" + str(self.request.get('key')) + "</h3>") 
        return 

    
     counter = 0 
     keywordsArray = [] 
     numKeywords = int(self.request.get('numKeywords'))
     self.response.out.write ("<BR>numKeywords=" + str(numKeywords)) 
     for j in range(1,numKeywords):
   
        fieldname = 'delCheckbox' + str(j) 
        checkbox  = self.request.get(fieldname)
        #self.response.out.write ("<BR>" + fieldname + "=" + checkbox) 
        if checkbox != "on": 
          keywordFieldname = "keyword" + str(j) 
          keywordValue = self.request.get(keywordFieldname)
          #self.response.out.write("<BR> keywordFieldname = " + keywordFieldname + " KeywordValue=" + keywordValue) 
          if keywordValue > " " and keywordValue != "None": 
             keywords = self.KeywordsConstructor(keywordValue) 
             keywordsArray.append(keywords.key()) 
        #note, in the case of a delete, the keyword is not added to array
        #      and thus essentially removed from this document. 
        #      However, it is not deleted from the Keyword database.
        #      TODO - maybe build a cron job to childless Keywords later. 
        #note2, on delete keyword, we also do not lower the referenceCounter.
        #      The referenceCounter just gives us an approximate idea of how 
        #      popular keywords are. 

     document.keywords = keywordsArray
     document.put()
     #self.response.out.write("<h3> updated document keywords</h3>") 
     self.redirect("/updDocuments") 

  def KeywordsConstructor(self, keywordValue):
     """
     Return either an object of the current keyword, or create a new row 
     with that keyword, then return that object 
     NOTE: I thought about putting this in constructor or in the Keywords class
     but was boggled a little on how to do it. 
     """
     query = db.GqlQuery("SELECT * FROM Keywords WHERE keyword = :1", keywordValue) 
     LIMIT = 1 
     keywordList = query.fetch(LIMIT,offset=0) 
     if len(keywordList) > 0: 
        keywords = keywordList[0] 
        keywords.referenceCounter += 1 
        keywords.put()  #update the reference counter 
        return keywords

     else:
        keywords = Keywords()
        keywords.keyword = keywordValue.lower() 
        keywords.referenceCounter = 1 
        keywords.put()
        return keywords 
    

class UpdateDocuments(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     #mySession = Session()

     #params = {} 
     #params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     #currentUser = params['user']

     LIMIT = 1000 
     documentList = Document.all().fetch(LIMIT)

     client = GetGDocsAuthenticatedClient() 
     prefix = "3WC.KB"
     contains = ""  #limits search to files containing this string in the title
     # GetMatchingFileFeed massages the fileFeed and sends us back a list 
     # of or our own Document records 
     googleFiles = GetMatchingFileFeed(client,prefix,contains) 
     
     #counter = 0
     #for item in googleFiles:
     #   if counter == 0:
     #      for itemName in item.__dict__:
     #         self.response.out.write("<BR> itemName=" + itemName) 
     #   counter += 1 
     #   self.response.out.write("<BR><span style='color:red'> title=" + str(item.title)) 
     #   self.response.out.write(" docname=" + str(item.docName)) 
     #   self.response.out.write(" dateTimePublished=" + str(item.dateTimePublished)) 
     #   self.response.out.write(" authorName=" + str(item.authorName)) 
     #   self.response.out.write(" dateTimeCreated=" + str(item.dateTimeCreated)) 
     #   self.response.out.write(" authorEmail=" + str(item.authorEmail))
     #   self.response.out.write(" keywords=" + str(item.keywords))
     #   self.response.out.write("</span>") 
     #return 

     
     showGoogleFiles = [] 
     #set flag for match logic 
     for dbItem in documentList: 
        dbItem.foundMatch = False 

     for item in googleFiles: 
         item.foundMatch = False 
         for dbItem in documentList:
            if dbItem.docId == item.docId: 
               item.foundMatch = True 
               dbItem.foundMatch = True
               item.key = dbItem.key()
               item.dateTimePublished = dbItem.dateTimePublished 
               break 
         if not item.foundMatch:
            item.key = None   #avoid "NotSavedError" in Django template 
            
         showGoogleFiles.append(item) 

     #now add all items from Documents that did not match to the googleFiles 
     #to be displayed on Form 
     for dbItem in documentList: 
        if not dbItem.foundMatch:
            dbItem.foundMatch = True  #avoid checkbox from showing now 
            showGoogleFiles.append(dbItem) 
           

     message = ""
     templateDictionaryLocal = {"documentList": documentList,
                                "googleFiles": showGoogleFiles,
                                "numDocs": len(showGoogleFiles),
                                "message": message}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '',0)  
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateDocuments.html', templateDictionaryLocal)
                     

  def post(self):
     mySession = Session()
     if 'username' in mySession: 
        currentUser = mySession['username'] 
     else: 
        currentUser = "nwalters@sprynet.com"  #for test system speed 

     debugText = "" 
 
     counter = 0 
     numDocs = int(self.request.get('numDocs'))
     #self.response.out.write ("<BR>numDocs=" + str(numDocs)) 
     if self.request.get("DeleteCode") != "DELETE": 
      for j in range(1,numDocs+1):
   
        fieldname = 'checkbox' + str(j) 
        checkbox  = self.request.get(fieldname)
        self.response.out.write ("<BR>" + fieldname + "=" + checkbox) 
        if checkbox == "on": 
          docId     = self.request.get('docId'+ str(j))
          docName   = self.request.get('docName' + str(j))
          pubDate   = self.request.get('publishedDate' + str(j))

          document = Document() 
          document.docName               = docName 
          document.docId                 = docId 

           
          try: 
             document.dateTimePublished     = GDataXMLDateToPythonDateTime(pubDate)
          except (Exception), e:
             document.dateTimePublished     = datetime.datetime.now()
             
             #self.response.out.write("<BR>pubDate=" + pubDate) 
             #self.response.out.write("<BR>Error: " + str(e)) 
             #self.response.out.write("<BR><BR><BR>" + traceback.format_exc().replace("\n","<BR>")) 
             #return 

          # filename should be 3WC.KB.xxxxxxx 
          # so strip off the first 7 letters and use the remainder as the title 
          document.title = docName[7:]
          document.userEmailCreated      = currentUser 
          document.userEmailLastModified = currentUser 
          document.dateTimeCreated       = datetime.datetime.now() 
          document.isGDoc                = True 
          document.language              = "English"
          


          #don't allow duplicate docName 
          query = db.GqlQuery("SELECT * FROM Document WHERE docName = :1", document.docName) 
          LIMIT = 1 
          docList = query.fetch(LIMIT,offset=0) 
          self.response.out.write("&nbsp;&nbsp; Len=" + str(len(docList))) 

          #if document.isUnique:
          if len(docList) == 0:  
             self.response.out.write (" Put() for docName=" + document.docName) 
             document.put() 
             counter += 1 

     if self.request.get("DeleteCode") == "DELETE": 
        for j in range(1,numDocs+1):
           fieldname = 'checkbox' + str(j) 
           checkbox  = self.request.get(fieldname)
           self.response.out.write ("<BR>" + fieldname + "=" + checkbox) 
           if checkbox == "on": 
             key       = self.request.get('key'+ str(j))
             document = Document.get(key) 
             if document: 
                document.delete() 
              

     #self.response.out.write("<h3> updated " + str(counter) + " rows<h3>") 
     self.redirect("/updDocuments") 



class UpdateProvider(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    command = self.request.get("cmd") 

    key = self.request.get('key')
    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    provider = Provider() 
    #default values (instead of "None") 
    provider.name           = ""
    provider.description    = ""
    provider.sampleServices = ""

    if key > " ":
        provider = Provider.get(self.request.get('key')) 
        if not provider:
           self.response.out.write("<h3>Provider not found with key=" + key + "</h3>") 

    templateDictionaryLocal = {"provider":provider,
                               "command": command, 
                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateProvider.html', templateDictionaryLocal)

  def post(self):
     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     key = self.request.get('key')

     provider = Provider()   #create new object (in case we are doing an ADD instead of Modify) 
     #provider.dateTimeCreated = datetime.datetime.now() 
     #provider.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        provider = Provider.get(key) 
        if not provider:
           self.response.out.write("<h3>Provider not found with key=" + key + "</h3>") 

     if self.request.get("cmd") == "DELETE":
        if self.request.get("deleteCode") == "DELETEME":
           try: 
              provider.delete()  #might throw error if children exist for this provider 
           except (Exception), e:
              self.response.out.write("<h3>" + str(e) + "</h3>")
              return 
        else:
           self.response.out.write("<h3>Delete Code was not the proper value to do a delete.</h3>")
           return 
     else: 
        provider.name           = self.request.get('name') 
        provider.description    = self.request.get('description') 
        provider.sampleServices = self.request.get('sampleServices') 
        provider.put()      
 
     self.redirect("/reportProviders")    



class UpdateTask(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    command = self.request.get("cmd") 

    key = self.request.get('key')
    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    tasks = Tasks() 
    if key > " ":
        tasks = Tasks.get(self.request.get('key')) 
        if not tasks:
           self.response.out.write("<h3>Tasks not found with key=" + key + "</h3>") 



    templateDictionaryLocal = {"tasks":tasks,
                               "command": command
                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateTask.html', templateDictionaryLocal)

  def post(self):
     debugText = "" 
     foundValidationError = False 
     validationErrors = ""
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     key = self.request.get('key')

     task = Tasks()   #create new object (in case we are doing an ADD instead of Modify) 
     #tasks.dateTimeCreated = datetime.datetime.now() 
     #tasks.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        task = Tasks.get(key) 
        if not task:
           self.response.out.write("<h3>Tasks not found with key=" + key + "</h3>") 
     else: 
        task.dateTimeCreated = datetime.datetime.now()
        task.userEmailCreated = currentUser

     strSequence = self.request.get('sequence')   
     #this is a required field, cannot be blank or None 
     try:
           intSequence     = int(strSequence)
           task.sequence   = intSequence 
     except: 
           validationErrors += "Sequence = '" + strSequence + "' is not an integer value."  + "<BR>" 
           foundValidationError = True 

     if foundValidationError: 
            #send validation messages back to same page 
            templateDictionaryLocal = {"tasks":task,
                                       "validationErrors": validationErrors 
                                      }
            templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
            templateDictionaryLocal.update(templateDictionaryGeneral)
            self.renderPage('templates/updateTask.html', templateDictionaryLocal)
            return 

     task.taskCode              = self.request.get('taskCode') 
     task.taskDescription       = self.request.get('taskDescription') 
     task.processCode           = self.request.get('processCode') 
     task.isManual              = eval(self.request.get('isManual'))   #use eval() not bool()   
     task.dateTimeLastModified  = self.request.get('dateTimeLastModified') 
     task.userEmailLastModified = currentUser
 
     task.put()      
     self.redirect("/reportTasks")    


class AcceptManualTask(webapp.RequestHandler):
  """
  When a manual task arises on the business process task queue (TaskStatus), 
  the TaskHandler sends an email to all the potential workers. 
  The first worker to accept the task (by clicking the link in the email) 
  locks it for himself, to prevent more than one person from accepting it.  
  Manual Tasks, for example, include setting up a Google Management Account, 
  which requires entering a CAPTCHA code. 
  """

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    id  = self.request.get('id') 
    key = self.request.get('key') 
    subscriberKey = self.request.get('subscriberKey') 

    if id < " ": 
       self.response.out.write("<h3>Missing id= on URL</h3>") 
       return
    if key < " ": 
       self.response.out.write("<h3>Missing key= on URL</h3>") 
       return
    if subscriberKey < " ": 
       self.response.out.write("<h3>Missing subscriberKey= on URL</h3>") 
       return

    taskStatus = TaskStatus.get(key) 
    if not taskStatus: 
       self.response.out.write("<h3>TaskStatus record not found with key=" + key + "</h3>") 
       return

    if str(taskStatus.key().id()) != id: 
       #we might not need to ask the worker to logon if we include the key in the URL, 
       #because the key is similar to a GUID, very hard for anyone to guess or spoof. 
       self.response.out.write("<h3>TaskStatus id does not id on URL</h3>") 
       #don't want to reveal too much info to the worker - only use next line when admin/testing 
       self.response.out.write("<h3>TaskStatus id=" + str(taskStatus.key().id()) + " <> URL/id=" + id + "</h3>") 
       return

    if taskStatus.isManualAccepted:
       #then someone else already accepted this task, cannot give it to more than one person 
       self.response.out.write("<h3 style='color:red'>Task already accepted by another worker: " + taskStatus.acceptedBySubscriber.firstname + " " + taskStatus.acceptedBySubscriber.lastname + "</h3>") 
       return


    subscriber = Subscriber.get(subscriberKey) 
    if not subscriber: 
       self.response.out.write("<h3>Subscriber/Worker record not found with key=" + subscriberKey + "</h3>") 
       return 

    taskStatus.isManualAccepted     = True 
    taskStatus.acceptedBySubscriber = subscriber   #set reference/key 
    taskStatus.dateTimeManualAccepted = datetime.datetime.now() 
    taskStatus.put() 

    if taskStatus.jsonPickledCommonTaskMsg:
       #format JSON dictionary/object so that it appears better on web form 
       #(Change for web page only, not to be stored in database like this) 
       taskStatus.jsonPickledCommonTaskMsg = taskStatus.jsonPickledCommonTaskMsg.replace(",",",<br/>")



    msg = "<h3>" + taskStatus.acceptedBySubscriber.firstname + ", the task has been reserved for you.</h3>" 
    templateDictionaryLocal = {"taskStatus": taskStatus,
                               "msg": msg
                              }
                               
    serviceCode = "" 
    page = 1 
    nullForms = []

    templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, nullForms, serviceCode, page)
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/detailTaskStatus.html', templateDictionaryLocal)


class CompletedManualTask(webapp.RequestHandler):
  """
  When a manual task arises on the business process task queue (TaskStatus), 
  the TaskHandler sends an email to all the potential workers. 
  The first worker to accept the task (by clicking the link in the email) 
  locks it for himself, to prevent more than one person from accepting it.  
  Manual Tasks, for example, include setting up a Google Management Account, 
  which requires entering a CAPTCHA code. 
  When the workers has finished the task, he needs to mark it as completed, 
  so the business process can continue to the next task. 
  """

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    id  = self.request.get('id') 
    key = self.request.get('key') 
    subscriberKey = self.request.get('subscriberKey') 

    if id < " ": 
       self.response.out.write("<h3>Missing id= on URL</h3>") 
       return
    if key < " ": 
       self.response.out.write("<h3>Missing key= on URL</h3>") 
       return
    if subscriberKey < " ": 
       self.response.out.write("<h3>Missing subscriberKey= on URL</h3>") 
       return

    taskStatus = TaskStatus.get(key) 
    if not taskStatus: 
       self.response.out.write("<h3>TaskStatus record not found with key=" + key + "</h3>") 
       return

    if str(taskStatus.key().id()) != id: 
       #we might not need to ask the worker to logon if we include the key in the URL, 
       #because the key is similar to a GUID, very hard for anyone to guess or spoof. 
       self.response.out.write("<h3>TaskStatus id does not id on URL</h3>") 
       #don't want to reveal too much info to the worker - only use next line when admin/testing 
       self.response.out.write("<h3>TaskStatus id=" + str(taskStatus.key().id()) + " <> URL/id=" + id + "</h3>") 
       return


    if str(taskStatus.acceptedBySubscriber.key()) != subscriberKey: 
       self.response.out.write("<h3>TaskStatus.Subscriber doesn't match subscriberKey (from URL)=" + subscriberKey + "</h3>") 
       return 

    #temporarily avoid so we can restest 
    taskStatus.dateTimeCurrTaskCompleted = datetime.datetime.now() 
    taskStatusHistoryKey = taskStatus.createHistory() 

    #put JSON back into object so we can pass it as parm to method 
    objCommonTaskMessage = jsonpickle.decode(taskStatus.jsonPickledCommonTaskMsg) 
    #the getAndPostNextTask uses the seqnum from the objCommonTaskMessage rather than the db row 
    #in order to find the next larger seq num 
    objCommonTaskMessage.currentSeqNum = taskStatus.currentSeqNum 
    objCommonTaskMessage.taskCode      = taskStatus.currentTaskCode 


    #not 100% this update needs to be done 
    #taskStatus.objCommonTaskMessage = jsonpickle.encode(objCommonTaskMessage) 
    #taskStatus.put() 

    #find the next task and post it back to the task queue - 
    #using code we already wrote in CommonTaskHandler 
    objCommonTaskHandler = CommonTaskHandler() 
    objCommonTaskHandler.getAndPostNextTask  (objCommonTaskMessage, taskStatusHistoryKey) 


    self.redirect("/reportTaskStatus") 

#=======================================================
# End Updates 
#=======================================================
 