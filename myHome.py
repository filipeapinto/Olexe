#!/usr/bin/env pythonf
# admin: http://localhost:8080/_ah/admin/datastore 

import os
import cgi
import uuid #GUID 
#import apptools
import datetime
import traceback 
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
from google.appengine.ext.webapp.util import run_wsgi_app
from django import shortcuts
#from google.appengine.ext import users
#from userpreferences import UserPreferences

from dbModels import ServiceType
from dbModels import CumulusSession
from dbModels import Subscriber
from dbModels import Order
from dbModels import Service
from dbModels import TaskLog
from dbModels import Tasks
from dbModels import Workers
from dbModels import CustomerOrders
from dbModels import CumulusLog 
from dbModels import Document
from dbModels import Keywords
from dbModels import Book
from dbModels import Goal
from dbModels import KnowledgeSource
from dbModels import KnowledgeEvent
from dbModels import Provider
from dbModels import SubscriberProviderCredentials


from commonFunctions import buildLinks 
#from commonFunctions import userLinks
from commonFunctions import adminLinks 
from commonFunctions import loggedin 
from commonFunctions import commonUserCode
from commonFunctions import getSharedTemplateDictionary 
from commonFunctions import validateDateTimeFlex

from commonFunctions import MenuLinks
from gdataCommon import GetGDocsAuthenticatedClient
from gdataCommon import GetFeedByKeyword
from gdataCommon import GetGoogleDocHTMLContents
from gdataCommon import CreateGoogleDoc
from gdataCommon import GetGDocsAuthenticatedClientForCurrentUser


from addressHelpers import goalTypeChoices
from addressHelpers import knowledgeTypeChoices
from addressHelpers import eventTypeChoices
from addressHelpers import payloadTypeChoices

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



class MyOrders(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     mySession = Session()  
     if not 'subscriberkey' in mySession:
        self.redirect("/login")    
        return 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey)
     if not subscriber:
        self.response.out.write("<h3>Subscribernot found for key=" + str(subscriberkey) + "<h3>" )
     query = Order.gql("where subscriber =  :1 ", subscriber); 
     LIMIT = 1000
     ordersList = query.fetch(LIMIT,offset=0);

     ordersList2 = ordersList;
     for order in ordersList2:
       if not order.financialStatus in ["PayPal.paid","PayPal.pending","Complementary"]:
          order.showPaymentLink = True
          if len(order.services) > 0: 
             order.URL = "/formHandler?serviceCode=" + order.services[0].serviceType.code + "&page=5&resubmitOrderKey=" + str(order.key())
          else:
             order.URL = "No Services?"  # this should not happen 
       else:
          order.showPaymentLink = False  
          order.URL = "N.A."  #Not applicable 

     templateDictionaryLocal = {"ordersList": ordersList2,
                                "showDomainQuery": False,  
                                "domainStartsWith":self.request.get('domainstartswith')
                               }
     #Note: full url will look like this: http://localhost:8080/reportOrders
     #path will return "/reportOrders"
     forms = []
     serviceCode = ""
     page = 0 
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportOrders.html', templateDictionaryLocal)

#end of class 



class MyHome(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     user = loggedin(self)   #will redirect to login if not logged in 

     mySession = Session()
     params = {} 
     params = commonUserCode(params,self.request.url)

     log = CumulusLog()    #log invalid signins  
     log.category = "MyHome:Get" 
     if not mySession:
        log.message = "ERROR: NO-SESSION DATA" 
     else:
        if not user: 
           log.message = "ERROR: SESSION DATA BUT NO-USER!"
        else:
           log.message = "" 
     log.username = user
     log.ipaddress = self.request.remote_addr 
     if log.message > "": 
        log.put() 

     returnURL = "" 
     dynamicHTML = "" 

     #This message could have been set anywhere, but is held until user is redirected back to /myHome page. 
     if 'myHomeMessage' in mySession:
        dynamicHTML = "<center>" + mySession['myHomeMessage'] + "</center><BR><BR>"
        mySession.delete_item('myHomeMessage') #no need to show this message more than once, so delete it from Session variables 

     ##########################################################
     # show any sessions (order started but never submitted)
     ##########################################################

     query = db.GqlQuery("SELECT * FROM CumulusSession WHERE userEmail = :1 and submitted = :2", params['user'], False ) 
     LIMIT = 10
     sessionList = query.fetch(LIMIT,offset=0)

     if len(sessionList) > 0:
         dynamicHTML += "<h3>You have incomplete orders that you may continue:</h3>\n"
         dynamicHTML += "<table border=1>"
         dynamicHTML += "<tr>"
         dynamicHTML += "<th>Click Below<BR>To Continue</th>"
         dynamicHTML += "<th>Click Below<BR>To Delete</th>"
         dynamicHTML += "<th>Product<BR>or<BR>Service</th>"
         dynamicHTML += "<th>Date Last Updated</th>"
         dynamicHTML += "<th>Domain</th>"
         dynamicHTML += "</tr>\n"

     for session in sessionList:
         #must wrap all strings with str() because they might have value of None
         dynamicHTML += "<tr>\n"
         URL = "temp" 
         #for form in forms:
         #   if form.seq == 1 and form.serviceCode == session.serviceCode:
         #      URL1 = "formHandler?serviceCode=" + session.serviceCode + "&page=1"

         URL1 = "/resumeCustomerOrder?sessionkey=" + str(session.key())
         URL2 = "/deleteCustomerOrder?sessionkey=" + str(session.key())
         dynamicHTML += "<td><a href='" + URL1 + "'>Continue</a></td>\n" 
         dynamicHTML += "<td><a href='" + URL2 + "'>Delete</a></td>\n" 

         #"join" to serviceType to get full serviceName (instead of printing code) 
         query = db.GqlQuery("SELECT * FROM ServiceType where code = :1", session.serviceCode) 
         LIMIT = 1000
         serviceTypeList = query.fetch(LIMIT,offset=0)
         serviceType = ServiceType() 
         serviceType.name = "temp"  #in case the query didn't return anything 
         if len(serviceTypeList) > 0: 
            serviceType = serviceTypeList[0] 

         #dynamicHTML += "<td>" + str(session.serviceCode) + "</td>\n"
         dynamicHTML += "<td>" + str(serviceType.name) + "</td>\n"
         if session.dateTimeModified:
            dynamicHTML += "<td>" + session.dateTimeModified.strftime("%m/%d/%y %H:%M:%S")  + "</td>\n"
         else:
            dynamicHTML += "<td>&nbsp;</td>" 
         dynamicHTML += "<td>" + str(session.domain) + "&nbsp;</td>\n"
         dynamicHTML += "</tr>\n"

     if len(sessionList) > 0:
         dynamicHTML += "</table>\n"


     boolFoundActiveICloud = False 
     userDomain = "" 
     if 'subscriberkey' in mySession:

	#get the current Subscriber record (based on key that /Login saved to session variables) 
        subscriber = Subscriber.get(mySession['subscriberkey']) 
        if subscriber: 
           query = db.GqlQuery("SELECT * FROM Service WHERE subscriber = :1 and serviceState = :2", subscriber, "Active" ) 
           LIMIT = 100 
           serviceList = query.fetch(LIMIT,offset=0)
           #self.response.out.write("Len serviceList=" + str(len(serviceList)) )
           #return 
           for service in serviceList:
              if service.serviceType.code == "1CloudI":  #TODO - how to check for any iCloud? 
                 userDomain = service.domain 
                 boolFoundActiveICloud = True 

           ##################################################
           # now show any unpaid orders for this subscriber
           ##################################################
           query = db.GqlQuery("SELECT * FROM Order WHERE subscriber = :1 ", subscriber ) 
           LIMIT = 1000
	   orderList = query.fetch(LIMIT,offset=0)

	   hasUnpaidOrders = False 
	   for order in orderList:
	       if order.financialStatus != "PayPal.paid": 
 	          hasUnpaidOrders = True 
           if hasUnpaidOrders: 
              dynamicHTML += "<h3>You have the following started but unpaid orders:</h3>\n"
              dynamicHTML += "<table border=1>"
              dynamicHTML += "<tr>"
              dynamicHTML += "<th>Service Name</th>"
              dynamicHTML += "<th>Order<BR>ID</th>"
              dynamicHTML += "<th>Order Date</th>"
              dynamicHTML += "<th>Domain</th>"
              dynamicHTML += "<th>Payment<BR>Status</th>"
              dynamicHTML += "<th>Payment<BR>Options</th>"
              dynamicHTML += "</tr>\n"
	      for order in orderList:
	        if order.financialStatus != "PayPal.paid":
                  dynamicHTML += "<tr>\n"
		  serviceListForThisOrder = order.services
		  #there should always be one service tied to this order, but check just to be sure 
		  #to avoid home page bombing for any reason 
                  if serviceListForThisOrder:  #handle value of NONE 
 		     if len(serviceListForThisOrder) > 0:
                        dynamicHTML += "<td>" + serviceListForThisOrder[0].serviceType.name + "</td>\n" 
                     else:
                        dynamicHTML += "<td>N.A.</td>\n" 
                  else:
                     dynamicHTML += "<td>N.A.</td>\n" 
                  dynamicHTML += "<td>" + str(order.key().id())  + "</td>\n"
                  dynamicHTML += "<td>" + order.orderDate.strftime("%m/%d/%y %H:%M:%S")  + "</td>\n"
                  dynamicHTML += "<td>" + str(order.domain) + "</td>\n" 
                  dynamicHTML += "<td>" + str(order.financialStatus) + "</td>\n" 
                  if serviceListForThisOrder:  #handle value of NONE 
                      dynamicHTML += "<td> <a href='/formHandler?serviceCode=" + serviceListForThisOrder[0].serviceType.code + "&page=5&resubmitOrderKey=" + str(order.key()) + "'>Resubmit Paypal</a></td>\n" 
		  else: 
                     dynamicHTML += "<td>N.A.</td>\n" 
                  dynamicHTML += "</tr>\n"
              dynamicHTML += "</table>\n"
	         

     dynamicHTML += "<br><br><br>\n"
     templateDictionaryLocal = {"dynamicHTML": dynamicHTML } 

     mySession['userDomain'] = userDomain  #save time of lookup each time page loaded      
                                           #(this is used to display email.domain.com, www.domain.com,docs.domain.com, etc...) 
                               
     forms = []
     serviceCode = ""
     page = 0 
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/customer/home.html', templateDictionaryLocal)

#end of class 



class ResumeCustomerOrder(webapp.RequestHandler):

  def get(self):
     #this allows us to reset the session key (in order to resume the order the user chose). 
     #  likely - he will just have one stopped order, but could potentially have more than one. 
     mySession = Session()
     user = loggedin(self)   #will redirect to login if not logged in 
     sessionkey = self.request.get('sessionkey') 
     mySession['sessionkey'] = sessionkey
     # retrieve existing user/session row from database table  

     try:
        session = CumulusSession.get(sessionkey) 
        if session == None:
           #TODO better error handling here 
           self.response.out.write("<h3>Session key not found</h3>")
           return 

        #send user to the first page of the formhandler for the specified product 
        URL = "/formHandler?serviceCode=" + str(session.serviceCode) + "&page=1"
        self.redirect(URL)
     except Exception, e:
        #self.response.out.write("Key=" + sessionkey) 
        self.response.out.write("Invalid key - make sure URL is not changed, please use back key to select again<BR>") 
        self.response.out.write(str(e))
        return




class DeleteCustomerOrder(webapp.RequestHandler):

  def get(self):
     #this allows us to reset the session key (in order to resume the order the user chose). 
     #  likely - he will just have one stopped order, but could potentially have more than one. 
     mySession = Session()
     user = loggedin(self)   #will redirect to login if not logged in 
     sessionkey = self.request.get('sessionkey') 
     mySession['sessionkey'] = sessionkey
     # retrieve existing user/session row from database table  

     try:
        session = CumulusSession.get(sessionkey) 
        if not session:
           #TODO better error handling here 
           self.response.out.write("<h3>Session key not found</h3>")
           return 

        #send user to the first page of the formhandler for the specified product 
        session.delete()
        if 'sessionkey' in mySession:
                mySession.delete_item('sessionkey')
        self.redirect("/myHome")
        #self.response.out.write("Deleted - Please go back to <a href='/menu'>Menu</a>")
        #return
     except Exception, e:
        #self.response.out.write("Key=" + sessionkey) 
        self.response.out.write("Invalid key - make sure URL is not changed, please use back key to select again<BR>") 
        self.response.out.write(str(e))
        return

#end of class 




class MyHelpBooks(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     #TODO - in the future - we can limit which books a user has access to 
     #       but initial goal is to get this up and running (08/04/2009) 
     #       Each book can currently be tied to a serviceType - so we could 
     #       only show books related to services subscribed by current user 

     query = Book.gql("ORDER BY name ") 
     LIMIT = 1000   #TODO potentially add paging here, but it will be a while before we have enough books to worry about that. 
     bookList = query.fetch(LIMIT,offset=0) 

     templateDictionaryLocal = {"bookList": bookList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/myHelpBooks.html', templateDictionaryLocal)

#end of class 




class MyHelpKeywords(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     #mySession = Session()  
     #if not 'subscriberkey' in mySession:
     #   #self.response.out.write("<h3>Session data - please login</h3>") 
     #   self.redirect("/login")    
     #   return 

     book = Book()
     #subscriberkey = mySession['subscriberkey']
     #subscriber = Subscriber.get(subscriberkey) 

     key = self.request.get("key")
     keyId = self.request.get("keyId")
     keywordSearch = self.request.get("keywordSearch")
     docId = self.request.get("docId")
     keyword = self.request.get("keyword")

     numDocs = 0 

     docContents = None
     if docId > " ": 
     # just show a list of potential keywords  
     # TODO: only show 20? per page 
        client = GetGDocsAuthenticatedClient() 
        docContents = GetGoogleDocHTMLContents(client,docId) 

     keywordList = None
     if key < " " and keywordSearch < " " and docId < " ": 
     # if no parms on URL, then default is to 
     # just show a list of potential keywords  
     # TODO: only show 20? per page 
        query = Keywords.gql("order by keyword "); 
        LIMIT = 1000 
        keywordList = query.fetch(LIMIT,offset=0);

     #if key given on URL (it is key to Keywords table on o
     #our BigTable Keyword Database - retrieve all related documents 
     documentList = None  
     if key > " " and docId <= " ":
        #TODO = future ideas on how to sort and rank more efficiently 
        #  keywords is a list of db.keys 
	keywords = Keywords.get(key)
        #query = Document.gql("where keywords = :1 order by docName ", keywords);  
        #LIMIT = 1000 
	# the Keywords
        documentList = keywords.documents
        numDocs = len(documentList) 
	#self.response.out.write("b) numDocs = " + str(numDocs)) 
	#return 
	keyword = self.request.get("keyword") 

     if keyId > " " and docId <= " ":
        #TODO = future ideas on how to sort and rank more efficiently 
        #  keywords is a list of db.keys 
	keywords = Keywords.get_by_id(keyId)
        #query = Document.gql("where keywords = :1 order by docName ", keywords);  
        #LIMIT = 1000 
	# the Keywords
        documentList = keywords.documents
        numDocs = len(documentList) 
	#self.response.out.write("b) numDocs = " + str(numDocs)) 
	#return 
	keyword = self.request.get("keyword") 

     #if keywordSearch given on URL, then do Google Search through 3WC.KB. documents 
     feed = None 
     if keywordSearch > " " and docId <= " ": 
        client = GetGDocsAuthenticatedClient() 
        feed = GetFeedByKeyword(client, keywordSearch) 
        if not feed: 
           self.response.out.write("Feed = None") 
	   return 
        numDocs = len(feed.entry) 
	keyword = keywordSearch 

     #this form shows either keywords or documents, depending on the variables passed: 
     templateDictionaryLocal = {"feed": feed,
                                "numDocs": numDocs,
				"keywordList": keywordList,
				"documentList": documentList,
				"feed": feed,
				"keyword": keyword,
				"key": key,
				"docContents": docContents,
				"book": book,
				"bookPrefix":self.request.get("bookPrefix")  
                               }
                               
     forms = []
     serviceCode = ""
     page = 0 
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportHelpKeywords.html', templateDictionaryLocal)

#end of class 



class MyServices(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     mySession = Session()  
     user = loggedin(self)   #will redirect to login if not logged in 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey) 
     query = Service.gql("where subscriber =  :1 ", subscriber); 
     LIMIT = 1000 
     servicesList = query.fetch(LIMIT,offset=0);
     numServices = len(servicesList) 

     #check for error here - easier to debug than in template 
     #this error will only happen when someone deletes a records out of sync in the DataViewer 
     exceptions = False 
     for service in servicesList: 
         try:
            test = service.order
            try:
               test = service.order.subscriber 
            except: 
               self.response.out.write("Problem with xref from service to order to subscriber service.key=" + 
                            str(service.key()) + " order.key=" + str(service.order.key())) 
               exceptions = True
         except: 
            self.response.out.write("Problem with xref from service to order<BR> service.key=" + 
                            str(service.key()) + "   Id=" + str(service.key().id())) 
            exceptions = True


     if exceptions: 
        return 

     templateDictionaryLocal = {"servicesList": servicesList,
                                "domainStartsWith":self.request.get('domainstartswith'),
                               }
                               
     forms = []
     serviceCode = ""
     page = 0 
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportServices.html', templateDictionaryLocal)

#end of class 



class UpdateGoal(webapp.RequestHandler):

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

    goal = Goal()
    #initialize values instead of showing "None" 
    goal.name = ""  
    goal.startDate = datetime.datetime.now() 
    goal.plannedCompletionDate = goal.startDate 

    if key > " ":
        goal = Goal.get(self.request.get('key')) 
        if not goal:
           self.response.out.write("<h3>Goal not found with key=" + key + "</h3>") 




    for item in goalTypeChoices:
       if item.value == goal.goalType: 
          item.selected = True 
       else: 
          item.selected = False 
        
    templateDictionaryLocal = {"goal":goal,
                               "goalTypeChoices":goalTypeChoices,
                               "command":command 

                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateGoal.html', templateDictionaryLocal)

  def post(self):
     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey)
     if not subscriber:
        self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )

     key = self.request.get('key')

     goal = Goal()   #create new object (in case we are doing an ADD instead of Modify) 
     #goal.dateTimeCreated = datetime.datetime.now() 
     #goal.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        goal = Goal.get(key) 
        if not goal:
           self.response.out.write("<h3>Goal not found with key=" + key + "</h3>") 


     foundValidationError = False 

     strStartDate = self.request.get('startDate') 
     strPlannedCompletionDate = self.request.get('plannedCompletionDate') 

     try:
        pyStartDate  = datetime.datetime.strptime(strStartDate, "%m/%d/%Y") 
     except: 
        self.response.out.write("<BR><span style='color:red'>")
        self.response.out.write("Invalid date conversion for StartDate = " + strStartDate)
        foundValidationError = True 

     try:
        pyPlannedCompletionDate  = datetime.datetime.strptime(strPlannedCompletionDate, "%m/%d/%Y") 
     except: 
        self.response.out.write("<BR><span style='color:red'>")
        self.response.out.write("Invalid date conversion for PlannedCompletionDate = " + strStartDate)
        foundValidationError = True 

     if foundValidationError: 
            self.response.out.write("<BR>Be sure to include four digit year and date in this format: mm/dd/yyyy") 
            self.response.out.write("<BR><BR>Press browser back key, correct, and re-submit") 
            self.response.out.write("</span>")
            return 

     goal.name = self.request.get('name') 
     goal.goalType = self.request.get('goalType') 
     goal.shareWithFriends = eval(self.request.get('shareWithFriends')) #use eval() not bool()  
     goal.startDate = pyStartDate
     goal.plannedCompletionDate = pyPlannedCompletionDate 

     if key <= " ":    #only when adding new record   
        goal.dateTimeCreated = datetime.datetime.now()
        goal.subscriber = subscriber  

     goal.dateTimeModified = datetime.datetime.now()
 
     goal.put()      
     self.redirect("/reportGoals")    



#end of class 


class UpdateKnowledgeSource(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    user = loggedin(self)   #will redirect to login if not logged in 
    command = self.request.get("cmd") 

    key = self.request.get('key')
    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    knowledgeSource = KnowledgeSource() 
    #avoid showing "None" for some values 
    knowledgeSource.name = ""
    knowledgeSource.shortName = ""

    if 'subscriberkey' not in mySession:
       self.response.out.write("No 'subscriberkey' found in Session variables") 
       self.response.out.write("CurrentUser=" + user) 
       return 
    subscriberkey = mySession['subscriberkey']
    subscriber = Subscriber.get(subscriberkey)
    if not subscriber:
       self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )

    query = Goal.gql("where subscriber = :1 ORDER BY name ", subscriber) 
    LIMIT = 1000
    goalList = query.fetch(LIMIT,offset=0)

    #self.response.out.write("# of goals = " + str(len(goalList))) 
    #return 

    if key > " ":
        knowledgeSource = KnowledgeSource.get(key) 
        if not knowledgeSource:
           self.response.out.write("<h3>KnowledgeSource not found with key=" + key + "</h3>") 
           retirm 

    goal = None 
    goalKey = self.request.get('goalKey')
    if goalKey > " ":
        goal = Goal.get(goalKey) 
        if not goal:
           self.response.out.write("<h3>Goal not found with goalKey=" + goalKey + "</h3>") 
           return 

    if not goal:   
       if knowledgeSource:
          goal = knowledgeSource.goal 

    for item in knowledgeTypeChoices:
       if item.value == knowledgeSource.knowledgeType: 
          item.selected = True 
       else: 
          item.selected = False 

    strPages = knowledgeSource.pages 
    strMinutes = knowledgeSource.minutes 
    strMeetingStartDateTime = knowledgeSource.meetingStartDateTime
    strMeetingStopDateTime  = knowledgeSource.meetingStopDateTime

    #if goal: 
    #   self.response.out.write("TempDebug: Have goal") 
    #   return 
    #else: 
    #   self.response.out.write("TempDebug: No goal") 
    #   return 

      
    templateDictionaryLocal = {"knowledgeSource":knowledgeSource,
                               "command": command, 
                               "knowledgeTypeChoices":knowledgeTypeChoices,
                               "goal": goal,
                               "goalList": goalList,
                               "strPages":strPages,
                               "strMinutes":strMinutes,
                               "strMeetingStartDateTime":strMeetingStartDateTime,
                               "strMeetingStopDateTime":strMeetingStopDateTime
                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateKnowledgeSource.html', templateDictionaryLocal)

  def post(self):
     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     validationErrors = ""
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     key     = self.request.get('key')
     command = self.request.get('command') 
     foundValidationError = False 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey)
     if not subscriber:
        self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )
        foundValidationError = True  


     knowledgeSource = KnowledgeSource()   #create new object (in case we are doing an ADD instead of Modify) 

     if command != "ADD" and key > ' ': 
        knowledgeSource = KnowledgeSource.get(key) 
        if not knowledgeSource:
           self.response.out.write("<h3>KnowledgeSource not found with key=" + key + "</h3>") 
           foundValidationError = True 

     if self.request.get('knowledgeType') <= " " :
           self.response.out.write("<h3>KnowledgeType is a required field, please select a value.</h3>") 
           foundValidationError = True 
        

     goal = None 
     #in some cases, user might pick goal from form (depends on how he got to the form) 
     #(when adding new knowledgeSource) 

     goalKey = self.request.get('goalKey')
     if goalKey > " ":
        goal = Goal.get(goalKey) 
        if not goal:
           self.response.out.write("<h3>Goal not found with goalKey=" + goalKey + "</h3>") 
           return 

     knowledgeSource.goal = goal 

     strISBN                  = self.request.get('isbn') 
     strAuthorName            = self.request.get('authorName') 
     strPages                 = self.request.get('pages') 
     strMinutes               = self.request.get('minutes') 
     strMeetingLocation       = self.request.get('meetingLocation') 
     strMeetingStartDateTime  = self.request.get('meetingStartDateTime') 
     strMeetingStopDateTime   = self.request.get('meetingStopDateTime') 

    
     knowledgeSource.knowledgeType = self.request.get('knowledgeType') 

     knowledgeSource.name      = self.request.get('name') 
     knowledgeSource.shortName = self.request.get('shortName') 

     #only change a field if it is non-blank and != None 
     #because fields might really be null/None, not all fields apply to all knowledgeTypes 

     if strISBN > " " and strISBN != "None":
        knowledgeSource.isbn = strISBN

     if strAuthorName > " " and strAuthorName != "None":
         knowledgeSource.authorName = strAuthorName

     if strPages > " " and strPages != "None":
        try:
           intPages = int(strPages)
           knowledgeSource.pages = intPages 
        except: 
           validationErrors += "Pages = '" + strMinutes + "' is not an integer value."  + "<BR>" 
           foundValidationError = True 

     if strMinutes > " " and strMinutes != "None":
        try:
           intMinutes = int(strMinutes)
           knowledgeSource.minutes = intMinutes
        except: 
           validationErrors += "Minutes = '" + strMinutes + "' is not an integer value."  + "<BR>" 
           foundValidationError = True 

     if strMeetingLocation > " " and strMeetingLocation != "None":
         knowledgeSource.meetingLocation = strMeetingLocation

     if strMeetingStartDateTime > " " and strMeetingStartDateTime != "None":
        try:
           pyDateTime  = validateDateTimeFlex(strMeetingStartDateTime) 
           knowledgeSource.meetingStartDateTime = pyDateTime
        except: 
           validationErrors += "Invalid date conversion for MeetingStartDateTime = " + strMeetingStartDateTime + "(Format is mm/dd/yyyy with optional hh:mm:ss) <BR>" 
           foundValidationError = True 

     if strMeetingStopDateTime > " " and strMeetingStopDateTime != "None":
        try:
           pyDateTime  = validateDateTimeFlex(strMeetingStartDateTime) 
           knowledgeSource.meetingStopDateTime = pyDateTime
        except: 
           validationErrors += "Invalid date conversion for MeetingStopDateTime = " + strMeetingStopDateTime + "(Format is mm/dd/yyyy with optional hh:mm:ss) <BR>" 
           foundValidationError = True 


     knowledgeSource.dateTimeModified = datetime.datetime.now()
 
     if key <= " ":     #only when adding new record 
        knowledgeSource.dateTimeCreated = datetime.datetime.now()
        knowledgeSource.subscriber = subscriber  

     if foundValidationError: 
            templateDictionaryLocal = {"knowledgeSource":knowledgeSource,
                               "command": command, 
                               "knowledgeTypeChoices":knowledgeTypeChoices,
                               "goal": goal,
                               "strPages":strPages,
                               "strMinutes":strMinutes,
                               "strMeetingStartDateTime":strMeetingStartDateTime,
                               "strMeetingStopDateTime":strMeetingStopDateTime,
                               "validationErrors": validationErrors 
                               }
            templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
            templateDictionaryLocal.update(templateDictionaryGeneral)
            self.renderPage('templates/updateKnowledgeSource.html', templateDictionaryLocal)
            return 

     knowledgeSource.put()    

     #now create new google doc for this user 

     try: 
        docTitle = "oneCloud." + str(knowledgeSource.key().id()) + "." + knowledgeSource.shortName 
        fmtDateTime = datetime.datetime.now().strftime("%m/%d/%Y %H:%M") 
        client = GetGDocsAuthenticatedClientForCurrentUser() 
        #TODO - docContents could be a template that the user could modify 
        #TODO - docContents assumes book, not meeting... 
        docContents = ("<h1>" + knowledgeSource.knowledgeType.capitalize() + ":" + knowledgeSource.name + "</h1>" +
                      "<br/>Book Author: " + knowledgeSource.authorName + 
                      "<br/>Number of Pages: " + strPages + 
                      "<br/>" + 
                      "<br/>Docucment Name: " + docTitle  + 
                      "<br/>Document Created: " + fmtDateTime + 
                      "<br/>Document Author: " +  subscriber.firstname + " " + subscriber.lastname + 
                      "<br/><br/>"   )
        CreateGoogleDoc(client, docTitle, docContents)
     except (Exception), e:
        self.response.out.write("Database updated, but document not created.<BR>") 
        self.response.out.write("Error: " + str(e) + "<BR>") 
        self.response.out.write("<BR><BR><BR>" + traceback.format_exc().replace("\n","<BR>")) 
        return 
     
     
     if goalKey > " ":
        self.redirect("/reportKnowledgeSources?goalKey=" + goalKey)    
     else: 
        self.redirect("/reportGoals")    



class UpdateCredentials(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    user = loggedin(self)   #will redirect to login if not logged in 
    command = self.request.get("cmd") 

    subscriberkey = mySession['subscriberkey']
    subscriber = Subscriber.get(subscriberkey)
    if not subscriber:
       self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )
       foundValidationError = True  

    key = self.request.get('key')
    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    query = Provider.all()
    LIMIT = 1000
    providerList = query.fetch(LIMIT,offset=0);

    #
    query = SubscriberProviderCredentials.gql("WHERE subscriber = :1", subscriber) 
    LIMIT = 1000
    subscriberProviderCredentialsList = query.fetch(LIMIT,offset=0)

    #TODO - don't allow two different credentials for the same provider 
    #  one way todo this would be to better prompt the select list with only providers that
    #  the subscriber hasn't used yet. 
    #  This code removes items from the list of available providers 
    #  those providers where the user has alread provided credentials. 

    for item in subscriberProviderCredentialsList: 
        for provider in providerList:
            if provider.name == item.provider.name:
               providerList.remove(provider) 
                            

    subscriberProviderCredentials = SubscriberProviderCredentials() 
    subscriberProviderCredentials.userid = ""
    subscriberProviderCredentials.password = "" 


    if key > ' ': 
        subscriberProviderCredentials = SubscriberProviderCredentials.get(key) 
        if not subscriberProviderCredentials:
           self.response.out.write("<h3>SubscriberProviderCredentials not found with key=" + key + "</h3>") 
           return 
    else:
        subscriberProviderCredentials.dateTimeCreated = datetime.datetime.now() 


    templateDictionaryLocal = {"subscriberProviderCredentials":subscriberProviderCredentials,
                               "providerList": providerList,
                               "command": command, 
                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateCredentials.html', templateDictionaryLocal)


  def post(self):
     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     if 'username' in mySession:
        currentUser = mySession['username'] 

     foundValidationError = False 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey)
     if not subscriber:
        self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )
        foundValidationError = True  
        return 

     key = self.request.get('key')

     subscriberProviderCredentials = SubscriberProviderCredentials()   #create new object (in case we are doing an ADD instead of Modify) 
     #subscriberProviderCredentials.dateTimeCreated = datetime.datetime.now() 
     #subscriberProviderCredentials.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        subscriberProviderCredentials = SubscriberProviderCredentials.get(key) 
        if not subscriberProviderCredentials:
           self.response.out.write("<h3>SubscriberProviderCredentials not found with key=" + key + "</h3>") 
           return 
     else:
        subscriberProviderCredentials.dateTimeCreated = datetime.datetime.now() 

     if self.request.get('cmd') == "DELETE":
        #TODO - add a confirm delete here 
        if self.request.get("deleteCode") == "DELETEME":
           if subscriberProviderCredentials.subscriber.key() == subscriber.key():   #don't allow someone to sneakily try to delete someone elses... 
              subscriberProviderCredentials.delete() 
              self.redirect("/reportCredentials")    
           else: 
              self.response.out.write("<h3>Tried to delete credential of another subscriber</h3>") 
              #self.response.out.write("<BR>Credentials.subscriber = " + str(subscriberProviderCredentials.subscriber.key()))
              #self.response.out.write("<BR>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; subscriber = " + str(subscriber.key()))
              return 
        else: 
           self.response.out.write("<h3>The delete code you typed in was not correct.  This protects you from accidentally deleting your data.  Please use the browser's back-key and try entering the correct code.</h3>") 
           return 

     #TODO - in the future we can call webservice to validate that this user/pass is valid 

     providerKey = self.request.get('provider')
     if providerKey < " ":
        validationErrors = "Please select a provider" 
        foundValidationError = True  
     else:
        provider = Provider.get(providerKey)
        if not provider:
           self.response.out.write("<h3>Provider not found for key=" + str(providerKey) + "<h3>" )
           foundValidationError = True  
           return 
     
     subscriberProviderCredentials.userid     = self.request.get('userid') 
     subscriberProviderCredentials.password   = self.request.get('password') 

     if foundValidationError:
            query = Provider.all()
            LIMIT = 1000
            providerList = query.fetch(LIMIT,offset=0);
            command = self.request.get("command") 
            templateDictionaryLocal = {"subscriberProviderCredentials":subscriberProviderCredentials,
                                       "providerList": providerList,
                                       "command": command, 
                                       "validationErrors": validationErrors
                                      }
                                       
            templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
            templateDictionaryLocal.update(templateDictionaryGeneral)
            self.renderPage('templates/updateCredentials.html', templateDictionaryLocal)
     else: 
        subscriberProviderCredentials.subscriber = subscriber 
        subscriberProviderCredentials.provider   = provider 
        subscriberProviderCredentials.dateTimeModified = datetime.datetime.now() 
        subscriberProviderCredentials.put()      
        self.redirect("/reportCredentials")    


#end of class 



class UpdateKnowledgeEvent(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    #is it possible that we have username but not subscriberkey? 
    if 'subscriberkey' not in mySession and 'username' in mySession:
       self.response.out.write("Have username but not subscriber id") 
       return 
    user = loggedin(self)   #will redirect to login if not logged in 
    command = self.request.get("cmd") 
    if not 'subscriberkey' in mySession: 
        self.response.out.write("Logged-in as user=" + str(user) + " but subscriberkey not found in mySession")
        return 
    subscriberkey = mySession['subscriberkey']
    subscriber = Subscriber.get(subscriberkey)
    if not subscriber:
        self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )
        return 


    key   = self.request.get('key')
    ksKey = self.request.get('ksKey')

    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    knowledgeEvent = KnowledgeEvent() 
    knowledgeEvent.microBlog = ""

    if key > " ":
        knowledgeEvent = KnowledgeEvent.get(key) 
        if not knowledgeEvent:
           self.response.out.write("<h3>KnowledgeEvent not found with key=" + key + "</h3>") 
           return 

    for item in eventTypeChoices:
       if item.value == knowledgeEvent.eventType: 
          item.selected = True 
       else: 
          item.selected = False 
        

    for item in payloadTypeChoices:
       if item.value == knowledgeEvent.payloadType: 
          item.selected = True 
       else: 
          item.selected = False 

    #show all the providers on the form for the MicroBlog "Post To" based 
    #on the providers the users has designated by giving us his credentials for that provider 
    # and show the other providers without a checkbox - so the user knows that we support them
    # but he has not yet registered them to his account via credentials 
    query = Provider.all()
    LIMIT = 1000
    providerList = query.fetch(LIMIT)
    for provider in providerList:
        query2 = SubscriberProviderCredentials.gql("where provider = :1 and subscriber =:2", provider, subscriber) 
        credentialList = query2.fetch(LIMIT)
        #the attribute available is not part of dbModels, but used just on form 
        if len(credentialList) == 0:
           provider.available = False 
        else:
           provider.available = True
        
    templateDictionaryLocal = {"knowledgeEvent":knowledgeEvent,
                               "command": command, 
                               "providerList": providerList,
                               "eventTypeChoices":eventTypeChoices,
                               "payloadTypeChoices":payloadTypeChoices,
                               "ksKey": ksKey
                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/updateKnowledgeEvent.html', templateDictionaryLocal)



  def post(self):

     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     key   = self.request.get('key')
     ksKey = self.request.get('ksKey')

     knowledgeEvent = KnowledgeEvent()   #create new object (in case we are doing an ADD instead of Modify) 
     #knowledgeEvent.dateTimeCreated = datetime.datetime.now() 
     #knowledgeEvent.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        knowledgeEvent = KnowledgeEvent.get(key) 
        if not knowledgeEvent:
           self.response.out.write("<h3>KnowledgeEvent not found with key=" + key + "</h3>") 
           return 
     else: 
        knowledgeEvent.dateTimeCreated  = datetime.datetime.now() 

     if not key:  #only need ksKey for doing Adds 
       if ksKey > " ":   
          knowledgeSource = KnowledgeSource.get(ksKey)
          if not knowledgeEvent:
             self.response.out.write("<h3>KnowledgeEvent not found with key=" + ksKey + "</h3>") 
             return 
          knowledgeEvent.knowledgeSource = knowledgeSource 
          knowledgeEvent.subscriber      = knowledgeSource.subscriber
       else:
          self.response.out.write("<h3>KnowledgeSource key (ksKey) is missing</h3>") 
          return 

     knowledgeEvent.eventType        = self.request.get('eventType') 
     knowledgeEvent.payloadType      = self.request.get('payloadType') 
     knowledgeEvent.microBlog        = self.request.get('microBlog') 

     knowledgeEvent.dateTimeModified = datetime.datetime.now() 

     knowledgeEvent.put()      
     self.redirect("/reportKnowledgeEvents?ksKey=" + ksKey)    

     objKeyValuePair = KeyValuePair() 
     userid    = objKeyValuePair.getValueFromKey("KB_Document_Userid") 


#end of class 
  