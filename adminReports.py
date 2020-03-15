#!/usr/bin/env pythonf
# admin: http://localhost:8080/_ah/admin/datastore 

import os
import cgi
import uuid #GUID 
#import apptools
import datetime
import logging 
import time
import sys
import traceback 
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
from dbModels import RatePlan
from dbModels import PaypalIPN
from dbModels import KeyValuePair 
from dbModels import ServiceRatePlan 
from dbModels import Keywords
from dbModels import Book 
from dbModels import Feedback 
from dbModels import Goal
from dbModels import KnowledgeSource
from dbModels import KnowledgeEvent
from dbModels import Provider
from dbModels import SubscriberProviderCredentials
from dbModels import TaskStatus
from dbModels import TaskStatusHistory 

from commonFunctions import buildLinks 
#from commonFunctions import userLinks
from commonFunctions import adminLinks 
from commonFunctions import loggedin 
from commonFunctions import commonUserCode
from commonFunctions import getSharedTemplateDictionary 

from addressHelpers import orderStates
from addressHelpers import orderFinancialStates
from addressHelpers import countries

from gdataCommon import GetGDocsAuthenticatedClient
from gdataCommon import GetMatchingFileFeed
from gdataCommon import GetGoogleDocHTMLContents
from gdataCommon import GDataXMLDateToPythonDateTime

#template.register_template_library('customTags') 

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


#decided not to use this type of structure:
#languages = {'English':true, 'Spanish',false, 'Portuguese',false, 'Mandarin',true} 

#languages = { 'English': {
#                            'selected': true,
#                            'imageURL': 




#=======================================================
# START of Reports 
#=======================================================


class ReportTasks(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):

     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     #if self.hasValidUser():
     #query = TaskLog.gql("WHERE resultFlag > -2" ORDER BY sequence);  # get all rows
     #processCode = self.request.get('processCode');
     #if processCode < ' ': 
     #   self.response.out.write(
     #     "<h3>Error:URL should contains process code, for example /reportTasks?processCode=xCloud</h3>");
     #   return;
     #query = Tasks.gql("WHERE processCode = :1 order by sequence", processCode);  # get all rows 
     processCode = "N/A"
     query = Tasks.gql("order by processCode, sequence");  # get all rows 
     LIMIT = 1000
     taskList = query.fetch(LIMIT,offset=0);

     templateDictionaryLocal = {"taskList": taskList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportTasks.html', templateDictionaryLocal)

#end of class 


class ReportTaskStatus(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):

     mySession = Session()
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     if 'subscriberkey' in mySession:
        subscriberkey = mySession['subscriberkey']
        subscriber = Subscriber.get(subscriberkey) 
        if not subscriber:
           self.response.out.write("<h3>Subscriber not found with subscriberkey=" + str(subscriberkey) + "</h3>") 
           return 
     #if self.hasValidUser():
     #query = TaskLog.gql("WHERE resultFlag > -2" ORDER BY sequence);  # get all rows
     #processCode = self.request.get('processCode');
     #if processCode < ' ': 
     #   self.response.out.write(
     #     "<h3>Error:URL should contains process code, for example /reportTasks?processCode=xCloud</h3>");
     #   return;
     #query = Tasks.gql("WHERE processCode = :1 order by sequence", processCode);  # get all rows 
     processCode = "N/A"
     #query = TaskStatus.gql("order by processCode, currentTaskCode, currentSeqNum");  # get all rows 
     query = TaskStatus.gql("order by __key__ desc ");  # doesn't work 
     LIMIT = 1000
     taskStatusList = query.fetch(LIMIT,offset=0);
     for taskStatus in taskStatusList:
        #the error takes up too much space on the screen 
        if taskStatus.currentTaskError:
           taskStatus.currentTaskError = "ERROR"
        if taskStatus.acceptedBySubscriber and not taskStatus.dateTimeCurrTaskCompleted: 
           #avoid comparing when None 
           if taskStatus.acceptedBySubscriber.key() == subscriber.key(): 
              taskStatus.isAssignedToCurrentSubscriber = True 
              taskStatus.completedURL = "/completedManualTask?id=" + str(taskStatus.key().id()) + "&key=" + str(taskStatus.key()) + "&subscriberKey=" + str(subscriber.key())
           else: 
              taskStatus.isAssignedToCurrentSubscriber = False 

     templateDictionaryLocal = {"taskStatusList": taskStatusList}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportTaskStatus.html', templateDictionaryLocal)

#end of class 


class ReportTaskStatusHistory(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):

     mySession = Session()
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     if 'subscriberkey' in mySession:
        subscriberkey = mySession['subscriberkey']
        subscriber = Subscriber.get(subscriberkey) 
        if not subscriber:
           self.response.out.write("<h3>Subscriber not found with subscriberkey=" + str(subscriberkey) + "</h3>") 
           return 
     #if self.hasValidUser():
     #query = TaskLog.gql("WHERE resultFlag > -2" ORDER BY sequence);  # get all rows
     #processCode = self.request.get('processCode');
     #if processCode < ' ': 
     #   self.response.out.write(
     #     "<h3>Error:URL should contains process code, for example /reportTasks?processCode=xCloud</h3>");
     #   return;
     #query = Tasks.gql("WHERE processCode = :1 order by sequence", processCode);  # get all rows 
     processCode = "N/A"
     query = TaskStatusHistory.gql("order by dateTimeCurrTaskStarted desc");  # get all rows 
     LIMIT = 1000 
     taskStatusHistoryList = query.fetch(LIMIT,offset=0);

     templateDictionaryLocal = {"taskStatusHistoryList": taskStatusHistoryList}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportTaskStatusHistory.html', templateDictionaryLocal)

#end of class 

class ReportServiceTypes(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     #code below is if we want to have a form to narrow down selection criteria 
     #if self.hasValidUser():
     #query = TaskLog.gql("WHERE resultFlag > -2" ORDER BY sequence);  # get all rows
     #processCode = self.request.get('processCode');
     #if processCode < ' ': 
     #   self.response.out.write(
     #     "<h3>Error:URL should contains process code, for example /reportTasks?processCode=xCloud</h3>");
     #   return;
     #query = ServiceType.gql("WHERE processCode = :1 order by sequence", processCode);  # get all rows 

     query = ServiceType.gql("ORDER BY code");  # get all rows 
     LIMIT = 1000
     serviceTypeList = query.fetch(LIMIT,offset=0);

     templateDictionaryLocal = {"serviceTypes": serviceTypeList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportServiceTypes.html', templateDictionaryLocal)

#end of class 



class ReportIPN(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     sortOrder = self.request.get("sortOrder") 
     orderId   = self.request.get("orderId") 
     txntype   = self.request.get("txntype") 
     status    = self.request.get("status") 
     paytype   = self.request.get("paytype") 
     strStartDate = self.request.get("startDate") 
     strStopDate  = self.request.get("stopDate") 
     strNumRows   = self.request.get("numRows") 
     if txntype <= " ":
        txntype = "ALL" 
     if status <= " ":
        status = "ALL" 
     if paytype <= " ":
        paytype = "ALL" 
     pyStartDate = ""
     pyStopDate = ""
     intNumRows = 50 

     numParms = 0 
     #this allows us to use Post or Get method from form 
     for item in self.request.arguments():
        if item > " ":
	   numParms += 1


     if numParms > 0:   #if parms present 
         logging.debug("button submitted logic") 

         nonAllCounter = 0 
         if txntype != "ALL":
           nonAllCounter += 1
         if status != "ALL":
           nonAllCounter += 1
         if paytype != "ALL":
           nonAllCounter += 1
         if strStartDate > " ": 
           nonAllCounter += 1
         if nonAllCounter > 1: 
           #this reduces for now the number of permutations of queries below 
           self.response.out.write("<h3>Please select only one of these filters: txntype, status, paytype, date-range</h3>") 
           return 
         
	 foundValidationError = False
         
	 try:
            intNumRows  = int(strNumRows) 
         except: 
            self.response.out.write("<BR><span style='color:red'>")
            self.response.out.write("'Number Rows' is not numeric '" + strNumRows + "'")
            foundValidationError = True 

         if strStartDate > " " or strStopDate > " ": 
           try:
              pyStartDate  = datetime.datetime.strptime(strStartDate, "%m/%d/%Y") 
           except: 
              self.response.out.write("<BR><span style='color:red'>")
              self.response.out.write("Invalid date conversion for start date = " + strStartDate)
              foundValidationError = True 

           try:
              pyStopDate   = datetime.datetime.strptime(strStopDate, "%m/%d/%Y")  
           except: 
              self.response.out.write("<BR><span style='color:red'>")
              self.response.out.write("Invalid date conversion for stop date = " + strStopDate )
              foundValidationError = True 

         if foundValidationError: 
            self.response.out.write("<BR>Be sure to include four digit year and date in this format: mm/dd/yyyy") 
            self.response.out.write("<BR><BR>Press browser back key, correct, and re-submit") 
            self.response.out.write("</span>")
            return 

     else:   #when submit button not clicked 
         sortOrder = "dateTimeCreated desc" 

     logging.debug("1) sortOrder=" + sortOrder) 
     if sortOrder < " ": 
        sortOrder = "dateTimeCreated desc"  #this was empty for some reason when selecting paytype 
     if orderId > " ": 
        sortOrder = "order"
        query = PaypalIPN.gql("where invoice = :1 ORDER BY invoice, dateTimeCreated desc", orderId);    #invoice is the Paypay name for order-id 
        logging.debug("ReportIPN query by orderId") 

     elif txntype != "ALL" : 
        query = PaypalIPN.gql("where txn_type = :1 ORDER BY txn_type, " + sortOrder, txntype);    
        logging.debug("ReportIPN query by txntype") 
     elif status != "ALL" : 
        query = PaypalIPN.gql("where payment_status = :1 ORDER BY payment_status, " + sortOrder, status);   
        logging.debug("ReportIPN query by status") 
     elif paytype != "ALL" : 
        query = PaypalIPN.gql("where payment_type = :1 ORDER BY payment_type, " + sortOrder, paytype);    
        logging.debug("ReportIPN query by paytype") 

     elif strStartDate > " ":
        query = PaypalIPN.gql("where dateTimeCreated >= :1 and dateTimeCreated <= :2 ORDER BY dateTimeCreated desc",pyStartDate,pyStopDate);  
        logging.debug("ReportIPN query by date-range") 

     elif sortOrder == "order":
        query = PaypalIPN.gql("ORDER BY invoice, dateTimeCreated desc")  
        logging.debug("ReportIPN - no filters - sort by order") 

     else:
        #default sort 
	sortOrder = "dateTimeCreated"
        query = PaypalIPN.gql("ORDER BY dateTimeCreated desc");  
        logging.debug("ReportIPN - no filters - sort by date/time") 

     logging.debug("2) sortOrder=" + sortOrder) 

     LIMIT = 1000
     PaypalIPNList = query.fetch(LIMIT,offset=0);

     templateDictionaryLocal = {"PaypalIPNList": PaypalIPNList,
                                "sortOrder": sortOrder,
                                "startDate": strStartDate,
                                "stopDate": strStopDate,
				"orderId": orderId,
				"numRows": intNumRows,
				"txntype": txntype,
				"status": status,
				"paytype": paytype 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportIPN.html', templateDictionaryLocal)

#end of class 


class ReportBooks(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     query = Book.gql("ORDER BY name ") 
     LIMIT = 1000
     bookList = query.fetch(LIMIT,offset=0)

     templateDictionaryLocal = {"bookList": bookList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportBooks.html', templateDictionaryLocal)

#end of class 


class ReportGoals(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     mySession = Session() 
     if 'subscriberkey' in mySession:
        subscriberkey = mySession['subscriberkey']
        subscriber = Subscriber.get(subscriberkey) 
        if not subscriber:
           self.response.out.write("<h3>Subscriber not found with subscriberkey=" + str(subscriberkey) + "</h3>") 
           return 

     query = Goal.gql("where subscriber = :1 ORDER BY name ", subscriber) 
     LIMIT = 1000
     goalList = query.fetch(LIMIT,offset=0)

     templateDictionaryLocal = {"goalList": goalList,
                                "showSubscriber": False 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportGoals.html', templateDictionaryLocal)

#end of class 


class ReportKnowledgeSources(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 
     mySession = Session() 
     if 'subscriberkey' in mySession:
        subscriberkey = mySession['subscriberkey']
        subscriber = Subscriber.get(subscriberkey) 
        if not subscriber:
           self.response.out.write("<h3>Subscriber not found with subscriberkey=" + str(subscriberkey) + "</h3>") 
           return 
        #else:
        #   self.response.out.write("<h3>Found Subscriber with subscriberkey=" + str(subscriberkey) + "</h3>") 

     else:
           self.response.out.write("<h3>subscriberkey  not found in mySession</h3>") 
           return 


     goal = None 
     goalKey = self.request.get('goalKey')
     if goalKey > " ":
        goal = Goal.get(goalKey) 
        if not goal:
           self.response.out.write("<h3>Goal not found with goalKey=" + goalKey + "</h3>") 
           return 
        goalList = [] 
        goalList.append(goal) 
     else: 

        #this report shows goals first, then iterates through knowledgeSource under each goal 
        #so that the report will be sorted by goal 
        query = Goal.gql("where subscriber = :1 ORDER BY name ", subscriber) 
        LIMIT = 1000
        #knowledgeSourceList = query.fetch(LIMIT,offset=0)
        goalList = query.fetch(LIMIT,offset=0)

     templateDictionaryLocal = {"showSubscriber": False, 
                                "goalList": goalList, 
                                "selectedGoal": goal 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportKnowledgeSources.html', templateDictionaryLocal)

#end of class 


class ReportKnowledgeEvents(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 
     mySession = Session() 
     if 'subscriberkey' in mySession:
        subscriberkey = mySession['subscriberkey']
        subscriber = Subscriber.get(subscriberkey) 
        if not subscriber:
           self.response.out.write("<h3>Subscriber not found with subscriberkey=" + str(subscriberkey) + "</h3>") 
           return 
        #else:
        #   self.response.out.write("<h3>Found Subscriber with subscriberkey=" + str(subscriberkey) + "</h3>") 

     else:
           self.response.out.write("<h3>subscriberkey  not found in mySession</h3>") 
           return 


     goal = None 
     ksKey = self.request.get('ksKey')
     if ksKey > " ":
        knowledgeSource = KnowledgeSource.get(ksKey) 
        if not knowledgeSource:
           self.response.out.write("<h3>KnowledgeSource not found with ksKey=" + ksKey + "</h3>") 
           return 
        query = KnowledgeEvent.gql("where knowledgeSource = :1 ", knowledgeSource) 
        LIMIT = 1000
        knowledgeEventList = query.fetch(LIMIT,offset=0)
     else:
        self.response.out.write("<h3>ksKey missing</h3>") 
        return 


     templateDictionaryLocal = {"showSubscriber": False, 
                                "knowledgeEventList": knowledgeEventList, 
                                "selectedGoal": goal, 
                                "ksKey": ksKey
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportKnowledgeEvents.html', templateDictionaryLocal)

#end of class 



class ReportFeedback(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     query = Feedback.gql("ORDER BY submittedDateTime desc ") 
     LIMIT = 1000
     feedbackList = query.fetch(LIMIT,offset=0)

     for feedback in feedbackList: 
        if feedback.comments: 
           feedback.lengthComments = len(feedback.comments) 
        else: 
           feedback.lengthComments = "0"
        for item in countries: 
	   if feedback.subscriber: #avoid error if subscriber is "None" 
              if item.value == feedback.subscriber.country:
                 feedback.subscriber.countryDescription = item.description 
		 if feedback.subscriber.countryDescription == "United States": 
		    feedback.subscriber.countryDescription = "USA"  #shorter/abbreviation

     templateDictionaryLocal = {"feedbackList": feedbackList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportFeedback.html', templateDictionaryLocal)

#end of class 


class ReportProviders(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     query = Provider.gql("ORDER BY name ") 
     LIMIT = 1000
     providerList = query.fetch(LIMIT,offset=0)

     templateDictionaryLocal = {"providerList": providerList
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportProviders.html', templateDictionaryLocal)

#end of class 


class ReportCredentials(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     mySession = Session() 
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey)
     if not subscriber:
        self.response.out.write("<h3>Subscriber not found for key=" + str(subscriberkey) + "<h3>" )
        foundValidationError = True  
        return 

     query = SubscriberProviderCredentials.gql("WHERE subscriber = :1", subscriber) 
     LIMIT = 1000
     subscriberProviderCredentialsList = query.fetch(LIMIT,offset=0)


     templateDictionaryLocal = {"subscriberProviderCredentialsList": subscriberProviderCredentialsList,
                                "cmd": self.request.get("cmd") 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportCredentials.html', templateDictionaryLocal)

#end of class 


class ReportRatePlans(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)   #this common routine will redirect to login if not logged-in 

     #code below is if we want to have a form to narrow down selection criteria 
     #if self.hasValidUser():
     #query = TaskLog.gql("WHERE resultFlag > -2" ORDER BY sequence);  # get all rows
     #processCode = self.request.get('processCode');
     #if processCode < ' ': 
     #   self.response.out.write(
     #     "<h3>Error:URL should contains process code, for example /reportTasks?processCode=xCloud</h3>");
     #   return;
     #query = ServiceType.gql("WHERE processCode = :1 order by sequence", processCode);  # get all rows 

     query = RatePlan.gql("ORDER BY code");  # get all rows 
     LIMIT = 1000
     ratePlanList = query.fetch(LIMIT,offset=0);

     templateDictionaryLocal = {"ratePlans": ratePlanList
                               }
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportRatePlans.html', templateDictionaryLocal)

#end of class 



class ReportRatePlanSubscriberXref(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     if self.request.get('key') < ' ': 
        self.response.out.write("<h3>Key not found on URL</h3>") 
        return 

     ratePlan = RatePlan.get(self.request.get('key')) 
     if not ratePlan:
        self.response.out.write("<h3>RatePlan not found with key=" + self.request.get('key') + "</h3>") 
        return 
        
     #Get all serviceRatePlans that have this ratePlan as a "parent" 
     #query = ServiceRatePlan.gql("where ratePlan = :1 order by dateTimeCreated desc", ratePlan) 
     # was getting "badqueryerror parse error expected no additional symbols" on above line
     # so took off the "order by" 
     query = ServiceRatePlan.gql("where ratePlan = :1 ", ratePlan) 
     LIMIT = 1000
     serviceRatePlanList = query.fetch(LIMIT,offset=0);

     if self.request.get("integrityCheck") == "on":   #maybe this later this will be a config parm in KeyValuePair Table 
         countProblems = self.integrityCheck(serviceRatePlanList) 
	 if countProblems > 0: 
	    return                #end before showing Django Template (which will error anyhow) 


     templateDictionaryLocal = {"serviceRatePlanList": serviceRatePlanList,
                                "ratePlan": ratePlan
                               }
     #Note: full url will look like this: http://localhost:8080/reportOrders
     #path will return "/reportOrders"
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportRatePlanSubscriberXref.html', templateDictionaryLocal)

  def IntegrityCheck(self,serviceRatePlanList):
     #temp check integrity - TODO - remove this when we have cascading delete on services 
     countProblems = 0 
     for serviceRatePlan in serviceRatePlanList:
         try:  
            order = Order.get(serviceRatePlan.order.key()) 
            if not order: 
	       self.response.out.write ("<BR> 1) Parent 'order' record does not exist;  serviceRatePlan key=" + str(serviceRatePlan.key()))
	       countProblems += 1 
         except (Exception), e:
	       self.response.out.write("<BR>" + str(e)) 
	       self.response.out.write ("<BR> 2) Parent 'order' record does not exist;  serviceRatePlan key=" + str(serviceRatePlan.key()))
	       countProblems += 1 
     return countProblems 

#end of class 


class ReportServiceTypeSubscriberXref(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     if self.request.get('key') < ' ': 
        self.response.out.write("<h3>Key not found on URL</h3>") 
        return 

     serviceType = ServiceType.get(self.request.get('key')) 
     if not serviceType:
        self.response.out.write("<h3>ServiceType not found with key=" + self.request.get('key') + "</h3>") 
        return 
        
     #Get all serviceRatePlans that have this serviceType as a "parent" 
     query = Service.gql("where serviceType = :1 ", serviceType) 
     LIMIT = 1000
     serviceList = query.fetch(LIMIT,offset=0);

     templateDictionaryLocal = {"serviceList": serviceList,
                                "serviceType": serviceType
                               }
     #Note: full url will look like this: http://localhost:8080/reportOrders
     #path will return "/reportOrders"
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportServiceTypeSubscriberXref.html', templateDictionaryLocal)

#end of class 


class ReportOrders(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  

     domainstartswith  = self.request.get('domainstartswith')
     domainstartswith2 = self.request.get('domainstartswith') + u"\ufffd"  #add the largest unicode character onto the end of prior string 
     orderState        = self.request.get('orderState') 
     financialStatus   = self.request.get('financialStatus') 

     #if user did not select anything from the select/box, it will still have a value of "Select One" 
     if orderState == "Select One": 
        orderState = "" 
     if financialStatus == "Select One": 
        financialStatus = "" 

     import logging
     if domainstartswith > ' ' and orderState > ' ' and financialStatus > ' ': 
         querySelected = "1"
         query = Order.gql("where domain >=  :1 and domain < :2  and orderState = :3 and financialStatus = :4 order by domain", domainstartswith, domainstartswith2, orderState, financialStatus); 
     elif domainstartswith > ' ' and orderState > ' ': 
         querySelected = "2"
         query = Order.gql("where domain >=  :1 and domain < :2 and orderState =:3       order by domain", domainstartswith, domainstartswith2, orderState); 
     elif domainstartswith > ' ' and financialStatus > ' ': 
         querySelected = "3"
         query = Order.gql("where domain >=  :1 and domain < :2 and financialStatus = :3  order by domain", domainstartswith, domainstartswith2, financialStatus); 
     elif financialStatus > ' ' and orderState > ' ': 
         querySelected = "4"
         query = Order.gql("where orderState = :1 and financialStatus = :2 order by domain", orderState, financialStatus); 
     elif financialStatus > ' ': 
         querySelected = "5"
         query = Order.gql("where financialStatus = :1 order by domain", financialStatus); 
     elif orderState > ' ': 
         querySelected = "6"
         query = Order.gql("where orderState = :1 order by domain", orderState); 
     elif domainstartswith > ' ': 
         querySelected = "7"
         query = Order.gql("where domain >=  :1 and domain < :2 order by domain", domainstartswith, domainstartswith2); 
     elif self.request.get('subscriberkey') > ' ':       
         querySelected = "8"
         subscriber = Subscriber.get(self.request.get('subscriberkey')) 
         query = Order.gql("where subscriber =  :1 ", subscriber); 
     else:
         querySelected = "9"
         query = Order.gql("order by orderDate desc");  # get all rows 

     #logging.debug("ReportOrders:query=" + querySelected)
     LIMIT = 1000
     ordersList = query.fetch(LIMIT,offset=0);

     #self.response.out.write("query=" + querySelected) 
     #return

     if self.request.get("integrityCheck") == "on":   #maybe this later this will be a config parm in KeyValuePair Table 
         countProblems = self.integrityCheck(ordersList) 
	 if countProblems > 0: 
	    return                #end before showing Django Template (which will error anyhow) 

     #set up select boxes for form to turn off any previously selected values, to show instead "select one" 
     for item in orderStates:
        if item.value == orderState:
	   item.selected = True
	else:
	   item.selected = False 

     for item in orderFinancialStates:
        if item.value == financialStatus:
	   item.selected = True
	else:
	   item.selected = False 


     templateDictionaryLocal = {"ordersList": ordersList,
                                "showDomainQuery": True, 
                                "domainStartsWith": domainstartswith,
				"orderStates": orderStates,
				"orderFinancialStates": orderFinancialStates 
                               }
     #Note: full url will look like this: http://localhost:8080/reportOrders
     #path will return "/reportOrders"
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportOrders.html', templateDictionaryLocal)


  def integrityCheck(self, ordersList): 
     #temp check integrity - TODO - remove this when we have cascading deletes  
     countProblems = 0 
     for order in ordersList:
         try:  
            service = Service.get(order.service.key()) 
            if not service: 
	       self.response.out.write ("<BR> 1) Parent 'service' record does not exist;  order key=" + str(order.key()))
	       countProblems += 1 
         except (Exception), e:
	       self.response.out.write("<BR>" + str(e)) 
	       self.response.out.write ("<BR> 2) Parent 'service' record does not exist;  order key=" + str(order.key()))
	       countProblems += 1 
         try:  
            subscriber = Subscriber.get(order.subscriber.key()) 
            if not subscriber: 
	       self.response.out.write ("<BR> 3) Parent 'subscriber' record does not exist;  order key=" + str(order.key()))
	       countProblems += 1 
         except (Exception), e:
	       self.response.out.write("<BR>" + str(e)) 
	       self.response.out.write ("<BR> 4) Parent 'subscriber' record does not exist;  order key=" + str(order.key()))
	       countProblems += 1 
     return countProblems

#end of class 


class ReportServices(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  

     objKeyValuePair = KeyValuePair() 
     isServiceDeleteEnabled  = objKeyValuePair.getValueFromKey("isServiceDeleteEnabled") 

     if isServiceDeleteEnabled:
        if isServiceDeleteEnabled == "True":  #convert string to boolean 
	   isServiceDeleteEnabled = True 
	else:
	   isServiceDeleteEnabled = False  
	 
        #isServiceDeleteEnabled = bool(isServiceDeleteEnabled) #this was giving misleading results
        #self.response.out.write ("isServiceDeleteEnabled=" + str(isServiceDeleteEnabled)) 
        #return 

     orderId = self.request.get('orderId')
     domainstartswith = self.request.get('domainstartswith')
     domainstartswith2 = domainstartswith + u"\ufffd"  #add the largest unicode character onto the end of prior string 
     if self.request.get('domainstartswith') > ' ': 
         #currently cannot do this - since domain is not in the service record 
         #would have to do a Python for loop to remove non-related services 
         query = Service.gql("where domain >=  :1 and domain < :2 order by domain", self.request.get('domainstartswith'), domainstartswith2); 
     elif self.request.get('subscriberkey') > ' ':       
         subscriber = Subscriber.get(self.request.get('subscriberkey')) 
         query = Service.gql("where subscriber =  :1 ", subscriber); 
     elif orderId > ' ':       
         order = Order.get_by_id(int(self.request.get('orderId'))) 
         query = Service.gql("where orders =  :1 ", order); 
     else:
         #query = Service.gql("order by orderDate desc");  #cannot sort on fields not in the serivce table! 
         query = Service.gql("order by serviceState");  # get all rows 
     LIMIT = 1000 
     servicesList = query.fetch(LIMIT,offset=0);
     numServices = len(servicesList) 

     if self.request.get('integrityCheck') == "on": 
        exceptions = self.IntegrityCheck(servicesList) 
        if exceptions: 
	    return                #end before showing Django Template (which will error anyhow) 

     templateDictionaryLocal = {"servicesList": servicesList,
                                "domainStartsWith":self.request.get('domainstartswith'),
				"numrows":numServices, 
				"orderId":orderId,
				"isServiceDeleteEnabled":isServiceDeleteEnabled
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)

     #Todo - should only redirect here when the specific error related to referential integrity occurs
     #  need to hit that error again to see what it says... 
     try:
       self.renderPage('templates/reportServices.html', templateDictionaryLocal)
     except (Exception), e:
       if "ReferenceProperty failed to be resolved" in str(e):
          self.redirect("/reportServices?integrityCheck=on") 
       else:
          self.response.out.write(str(e)) 
	  self.response.out.write("<BR><BR><BR>" + traceback.format_exc().replace("\n","<BR>")) 


  def IntegrityCheck(self,servicesList): 
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
                            str(service.key()) + "  &nbsp;&nbsp;&nbsp; ServiceId=" + str(service.key().id()) 
			    ) 
            exceptions = True
     return exceptions 
#end of class 



class BookChapters(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  

     key       = self.request.get('key') 


     if key < ' ': 
        self.response.out.write("<h3>?key=value not found on URL</h3>") 
        return 

     book = Book.get(key) 
     if not book: 
        self.response.out.write("<h3>Book not found with key=" + key + "</h3>") 
        return 

     objKeyValuePair = KeyValuePair() 
     isServiceDeleteEnabled  = objKeyValuePair.getValueFromKey("isServiceDeleteEnabled") 

     if isServiceDeleteEnabled:
        if isServiceDeleteEnabled == "True":  #convert string to boolean 
	   isServiceDeleteEnabled = True 
	else:
	   isServiceDeleteEnabled = False  
	 
        #isServiceDeleteEnabled = bool(isServiceDeleteEnabled) #this was giving misleading results
        #self.response.out.write ("isServiceDeleteEnabled=" + str(isServiceDeleteEnabled)) 
        #return 

     #add colon to end because format will be book01:chapter01 
     bookStartsWith  = book.keywordPrefix + ":"
     bookStartsWith2 = bookStartsWith + u"\ufffd"  #add the largest unicode character onto the end of prior string 
     query = Keywords.gql("where keyword >=  :1 and keyword  < :2 order by keyword", bookStartsWith, bookStartsWith2); 
     LIMIT = 1000 
     keywordList = query.fetch(LIMIT,offset=0);
     numDocs = len(keywordList) 

     counter = 0 
     for keyword in keywordList:
        posFirstColon = keyword.keyword.find(":") + 1 
        counter += 1 
	#self.response.out.write("<BR> counter=" + str(counter) + " posFirstColon=" + str(posFirstColon))
	if posFirstColon > 0:
           keyword.keywordDisplay = keyword.keyword[posFirstColon:]
	   #self.response.out.write("<BR>Revised keyword=" + keyword.keywordDisplay) 

     #some keywords may still existin in DB but not be attached to any documents,
     #we don't want them cluttering our screen (admin should probably delete them) 
     keywordList2 = keywordList 
     for keyword in keywordList:
         if len(keyword.documents) == 0:
	    keywordList.remove(keyword) 


     #this django template is rather overloaded and driven by the variables passed to it,
     #as needed by the HelpKB report, but here, we need only pass the keywordList 
     templateDictionaryLocal = {"feed": None,
                                "numDocs": numDocs,
				"keywordList": keywordList,
				"documentList": None,
				"feed": None,
				"keyword": None,
				"key": None,
				"docContents": None,
				"bookPrefix": book.keywordPrefix,
				"book": book,
				"bookView": True
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportHelpKeywords.html', templateDictionaryLocal)



class ReportKeyValuePairs(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  

     #query = KeyValuePair.gql("where kvIsSecure == :1 order by kvpKey ", False);  # get all non-secure rows
     #decided to show row in report for secured field, but mask the actual values 
     query = KeyValuePair.gql("order by kvpKey ");  # get all rows 

     LIMIT = 1000 
     kvpList = query.fetch(LIMIT,offset=0);
     numrows = len(kvpList) 

     templateDictionaryLocal = {"kvpList": kvpList,
				"numrows":numrows
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportKeyValuePairs.html', templateDictionaryLocal)

#end of class 


class ReportNewsletters(webapp.RequestHandler):
  """
    Find/list gdocs starting with name=3WC.Marketing.Newsletters 
  """

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     #mySession = Session()
     #currentUser = mySession['username'] 

     client = GetGDocsAuthenticatedClient() 
     prefix = "3WC.Marketing.Newsletters"
     contains = ""  #limits search to files containing this string in the title
     # GetMatchingFileFeed massages the fileFeed and sends us back a list 
     # of or our own Document records 
     googleFiles = GetMatchingFileFeed(client,prefix,contains) 
     numDocs = len(googleFiles) 
     
     templateDictionaryLocal = {"googleFiles": googleFiles,
                                 "numDocs": numDocs 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportNewsletters.html', templateDictionaryLocal)

    

class DetailNewsletter(webapp.RequestHandler):
  """
    Find/list gdocs starting with name=3WC.Marketing.Newsletters 
  """

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     #mySession = Session()
     #currentUser = mySession['username'] 

     docId = self.request.get('docId')
     docName = self.request.get('docName')

     if docId < ' ': 
        self.response.out.write("<h3>?docId=value not found on URL</h3>") 
        return 


     client = GetGDocsAuthenticatedClient() 
     htmlFileContents = GetGoogleDocHTMLContents(client,docId) 

     
     templateDictionaryLocal = {"htmlFileContents": htmlFileContents,
                                 "docId": docId,
                                 "docName": docName 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/detailNewsletter.html', templateDictionaryLocal)

    

class ReportCustomerOrders(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     domainstartswith2 = self.request.get('domainstartswith') + u"\ufffd"  #add the largest unicode character onto the end of prior string 
     if self.request.get('domainstartswith') > ' ': 
         query = CustomerOrders.gql("where domain >=  :1 and domain < :2 order by domain", self.request.get('domainstartswith'), domainstartswith2); 
     else:
         query = CustomerOrders.gql("order by orderDateTime desc");  # get all rows 
     LIMIT = 1000
     CustomerOrdersList = query.fetch(LIMIT,offset=0);

     params = {}
     params = commonUserCode(params,self.request.url)
     self.renderPage('templates/reportCustomerOrders.html', 
                     {"CustomerOrdersList": CustomerOrdersList,
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "currentUser": params['user'],
                      "debugText": debugText,
                      "domainstartswith":self.request.get('domainstartswith'),
                      "now": datetime.datetime.now()
                      }
                     ) 

#end of class 


class ReportSubscribers(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     lastnameStartsWith = self.request.get('lastnamestartswith').capitalize() 
     lastnamestartswith2 = lastnameStartsWith + u"\ufffd"  #add the largest unicode character onto the end of prior string 
     emailStartsWith = self.request.get('emailstartswith').lower() 
     emailStartsWith2 = emailStartsWith + u"\ufffd"  #add the largest unicode character onto the end of prior string 
     sortOrder = self.request.get('sortOrder') 

     #default sortOrder to lastname/firstname (if user didn't click any of the radio buttons) 
     if lastnameStartsWith > ' ': 
           #must sort by same thing as filter - limit of BigTable 
           query = Subscriber.gql("where lastname >=  :1 and lastname < :2 order by lastname, firstname ", lastnameStartsWith, lastnamestartswith2); 
	   sortOrder = "name" 
     elif emailStartsWith > ' ': 
           #must sort by same thing as filter - limit of BigTable 
           query = Subscriber.gql("where userEmail >=  :1 and userEmail < :2 order by userEmail ", emailStartsWith, emailStartsWith2); 
	   sortOrder = "email" 
     else:
         if sortOrder == "dateTimeCreated":
            query = Subscriber.gql("order by dateTimeCreated desc "); 
         elif sortOrder == "email":
            query = Subscriber.gql("order by userEmail "); 
         else:
            query = Subscriber.gql("order by lastname, firstname "); 

     LIMIT = 1000
     subscriberList = query.fetch(LIMIT,offset=0);

     #subscriberList2[]
     #subscriberList2.append(subscriberList)  #make copy of list 
     for subscriber in subscriberList:
        for country in countries:
	   if country.value == subscriber.country:
	      if country.description == "United States": 
	         subscriber.countryName = "US"  #further abbreviate since most customers are US
              else:
	         subscriber.countryName = country.description 
        
	   
     templateDictionaryLocal = {"subscriberList": subscriberList,
                                "lastnameStartsWith":lastnameStartsWith,
				"sortOrder": sortOrder,
				"emailStartsWith": emailStartsWith
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportSubscribers.html', templateDictionaryLocal)
#end of class 


class ReportWorkers(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     lastnameStartsWith = self.request.get('lastnamestartswith')
     lastnamestartswith2 = lastnameStartsWith + u"\ufffd"  #add the largest unicode character onto the end of prior string 

     if self.request.get('type') == 'admin': 
         query = Subscriber.gql("where isAdmin =:1 order by lastname, firstname ", True); 
     elif self.request.get('type') == 'worker': 
         query = Subscriber.gql("where isWorker =:1 order by lastname, firstname ", True); 
     else:
         self.response.out.write("<h3>Invalid type, should be value=admin or value=worker</h3>") 
         return 

     LIMIT = 1000
     subscriberList = query.fetch(LIMIT,offset=0);


     templateDictionaryLocal = {"subscriberList": subscriberList,
                                "type": self.request.get('type')
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportWorkers.html', templateDictionaryLocal)
#end of class 



class ReportSessions(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     if self.request.get('filter') == 'Submitted': 
         query = CumulusSession.gql("where submitted = :1 order by dateTimeModified desc", True)
     elif self.request.get('filter') == 'Not-Submitted': 
         query = CumulusSession.gql("where submitted = :1 order by dateTimeModified desc", False)
     else:
         query = CumulusSession.gql("order by dateTimeModified desc"); 
       
     LIMIT = 1000
     sessionList = query.fetch(LIMIT,offset=0);


     templateDictionaryLocal = {"sessionList": sessionList,
                                "lastnameStartsWith":self.request.get('lastnameStartsWith'),
                                "filter":self.request.get("filter")
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportSessions.html', templateDictionaryLocal)

#end of class 

class DetailSubscriber(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()
     user = loggedin(self)

     #subscriber = Subscriber()
     if self.request.get('key') < ' ': 
        self.response.out.write("<h3>Key not found on URL</h3>") 
        return 

     subscriber = Subscriber.get(self.request.get('key')) 

     import addressHelpers
     #country = addressHelpers.Countries.countryCodeLookUp(addressHelpers.countries,subscriber.country)
     country = "Temp-Value"
     for item in countries: 
        if item.value == subscriber.country:
	   country = item.description 

     templateDictionaryLocal = {"subscriber": subscriber,
                                "country": country,
                                "isAdmin": subscriber.isAdmin,
                                "isStaff": subscriber.isWorker
                               }
                               
     serviceCode = "" 
     page = 1 
     nullForms = []

     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, nullForms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/detailSubscriber.html', templateDictionaryLocal)

class DetailTaskStatus(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()
     user = loggedin(self)

     #subscriber = Subscriber()
     if self.request.get('key') < ' ': 
        self.response.out.write("<h3>Key not found on URL</h3>") 
        return 

     taskStatus = TaskStatus.get(self.request.get('key')) 

     if taskStatus.currentTaskError:
       #convert new-line to html-break so error message appears better on web form 
       taskStatus.currentTaskError = taskStatus.currentTaskError.replace("\n","<br/>")
       taskStatus.currentTaskError = taskStatus.currentTaskError.replace("\r"," ")

     if taskStatus.jsonPickledCommonTaskMsg:
       #format JSON dictionary/object so that it appears better on web form 
       taskStatus.jsonPickledCommonTaskMsg = taskStatus.jsonPickledCommonTaskMsg.replace(",",",<br/>")

     templateDictionaryLocal = {"taskStatus": taskStatus  }
                               
     serviceCode = "" 
     page = 1 
     nullForms = []

     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, nullForms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/detailTaskStatus.html', templateDictionaryLocal)


class DetailLog(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()
     user = loggedin(self)

     #subscriber = Subscriber()
     if self.request.get('key') < ' ': 
        self.response.out.write("<h3>Key not found on URL</h3>") 
        return 

     log = CumulusLog.get(self.request.get('key')) 


     templateDictionaryLocal = {"log": log
                               }
                               
     serviceCode = "" 
     page = 1 
     nullForms = []
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, nullForms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/detailLog.html', templateDictionaryLocal)



class ReportLog(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     log = CumulusLog()    
     log.category = "ReportLog:Get" 
     log.ipaddress = self.request.remote_addr 

     user = loggedin(self)
     #user = "temp"
     if not user:
        return;     #stop user if not logged in  

     log.username = user

     strStartDate = "" 
     strStopDate = "" 
     strNumRows = "50" 
     intNumRows = int(strNumRows) 
     strcategoryStartsWith    = self.request.get("categoryStartsWith")
     stripaddressStartsWith   = self.request.get("ipaddressStartsWith")


     #TODO 1: allow filter by time as well 
     #TODO 2: paging currently won't go forward from the time filter
     #TODO 3: check that stop date > start date (if user enters dates backwards, he might get confused/frustrated) 
     
     if self.request.get('startDate') > '':   #if submit button was clicked 
      
         #strDate = "06/15/2009"   #sample... 
         #pyDate = datetime.datetime.strptime(strDate, "%m/%d/%Y")  # "%Y-%m-%d %H:%M:%S")

         strStartDate = self.request.get("startDate")
         strStopDate  = self.request.get("stopDate")
         strNumRows   = self.request.get("numRows")
         strcategoryStartsWith    = self.request.get("categoryStartsWith")
         stripaddressStartsWith   = self.request.get("ipaddressStartsWith")


         pyStartDate = datetime.datetime.now()  #avoids "local variable ... referenced before assignment 
         pyStopDate = datetime.datetime.now()
         foundValidationError = False 

         try:
            intNumRows  = int(strNumRows) 
         except: 
            self.response.out.write("<BR><span style='color:red'>")
            self.response.out.write("'Number Rows' is not numeric '" + strNumRows + "'")
            foundValidationError = True 

         try:
            pyStartDate  = datetime.datetime.strptime(strStartDate, "%m/%d/%Y") 
         except: 
            self.response.out.write("<BR><span style='color:red'>")
            self.response.out.write("Invalid date conversion for start date = " + strStartDate)
            foundValidationError = True 

         try:
            pyStopDate   = datetime.datetime.strptime(strStopDate, "%m/%d/%Y")  
         except: 
            self.response.out.write("<BR><span style='color:red'>")
            self.response.out.write("Invalid date conversion for stop date = " + strStopDate )
            foundValidationError = True 

         if foundValidationError: 
            self.response.out.write("<BR>Be sure to include four digit year and date in this format: mm/dd/yyyy") 
            self.response.out.write("<BR><BR>Press browser back key, correct, and re-submit") 
            self.response.out.write("</span>")
            return 

         query = CumulusLog.gql("where dateTime >= :1 and dateTime <= :2 order by dateTime desc", pyStartDate, pyStopDate)
         log.message = "Queried by date range from: " + strStartDate + " to: " + strStopDate 
     else:
         query = CumulusLog.gql("order by dateTime desc"); 
         log.message = "No Filter" 

     log.put() 

     debugText = "Start Debug" 

     #there could be 1000s of these log records, so we need to provide paging    
     userOffsetText = self.request.get('offset')
     if not userOffsetText:
        userOffset = 0 
     else: 
        userOffset = int(userOffsetText) 

     ipaddressStartsWith = self.request.get("ipaddressStartsWith")
     categoryStartsWith  = self.request.get("categoryStartsWith")

     debugText += "<BR>CategoryStartsWithFilter = " + categoryStartsWith 
     debugText += "<BR>IpAddressStartsWithFilter = " + ipaddressStartsWith 

     userLimit = intNumRows   #this is the number of rows to display per page 

     if ipaddressStartsWith > " " or categoryStartsWith > " ":
        overrideLimit = 1000 
     else:
        overrideLimit = userLimit 
     
     logList = query.fetch(overrideLimit,offset=userOffset);

     debugText += "<BR>Len of logList = " + str(len(logList))


     if ipaddressStartsWith > " ": 
        log = CumulusLog()    
        log.category = "ReportLog:Get" 
        log.ipaddress = self.request.remote_addr 
        log.message = "Additional Filter on ipaddressStartsWith: '" + ipaddressStartsWith   + "'"
        log.username = user
        log.put() 

     if categoryStartsWith > " ": 
        log = CumulusLog()    
        log.category = "ReportLog:Get" 
        log.ipaddress = self.request.remote_addr 
        log.message = "Additional Filter on categoryStartsWith: '" + categoryStartsWith  + "'"
        log.username = user
        log.put() 

     #Notes, it possible to get 1000 rows, but somewhat unlikely, 
     #then reject all of them based on the search critiera below. 

     counter = 0 
     matchCounter = 0 
     logList2 = []

     for log in logList:
        removeFlag = False 
        counter += 1 
        if ipaddressStartsWith > " ": 
           #Todo - might also want to filter out the NoneTypes? 
           if log.ipaddress:  # not NoneType
              if not log.ipaddress.startswith(ipaddressStartsWith):
                 removeFlag = True 
        if categoryStartsWith > " ": 
	   #debugText += "<BR>---" + str(counter) + " categoryStartsWithFilter" 
           if log.category:  # not NoneType
	      #debugText += "<BR>" + str(counter) + " Category is not NoneType "
              if not log.category.startswith(categoryStartsWith):
	         #debugText += "<BR>" + str(counter) + " Set RemoveFlag/True "
                 removeFlag = True 
        #only return numRows to the screen 
        if matchCounter > userLimit:
           removeFlag = True 
        if removeFlag:
           #debugText += "<BR>" + str(counter) + " Removing... "
	   #bug arises if we try to remove inside our loop, 
	   #i.e. not some items get skipped, so instead 
	   #add the items to keep to another list in the else clause 
	   #logList.remove(log) 
	   pass 
        else: 
           matchCounter += 1 
	   logList2.append(log)  

     debugText += "<BR>Revised Len of logList2 = " + str(len(logList2))

     offsetNext = userOffset + userLimit
     if userOffset > userLimit: 
        offsetBack = userOffset - userLimit 
     else: 
        offsetBack = 0 



     templateDictionaryLocal = {"logList": logList2,
                                "lastnameStartsWith":self.request.get('lastnameStartsWith'),
                                "filter":self.request.get("filter"),
                                "offsetNext": offsetNext,
                                "offsetBack": offsetBack,
                                "startDate": strStartDate,
                                "stopDate": strStopDate,
                                "categoryStartsWith": categoryStartsWith,
                                "ipaddressStartsWith": ipaddressStartsWith,
                                "numRows": strNumRows,
				"debugText": debugText
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportLog.html', templateDictionaryLocal)

#end of class 



class ReportBundle(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def post(self):
     ReportTaskLogs.get(self);

  def showChildren(self, service, depth): 
     outText = ""
     stChildren = db.get(service.children)

     subCounter = 0 
     for child in stChildren: 
         subCounter += 1 
         if subCounter == 1:
            outText += ( "  <OL>\n")   #don't print unless we have at least one child
         outText += ( "<LI>" + child.code +  "</LI>\n") 
         depth += 1 
         self.showChildren(child, depth)

     if subCounter > 0:
         outText += ( "  </OL>\n")  #don't print unless we have at least one child

     return outText 


  def get(self):
     debugText = ""
     outText = ""

     #look for ?parm=ALL on the URL 
     if self.request.get('parm') == 'ALL': 
        query = ServiceType.gql("")  #no where clause needed
        genericReportTitle = "<h3>All ServiceTypes - and related Bundles</h3>"
        #outText +=  genericReportTitle + "\n"
     else: 
        query = ServiceType.gql("where isSellable = :1", True)  #no where clause needed
        genericReportTitle = "<h3>Sellable ServiceTypes - and related Bundles</h3>"
        #outText += ( "<h3>Sellable ServiceTypes - and related Bundles</h3>\n")

     LIMIT = 1000
     serviceList = query.fetch(LIMIT,offset=0)

     counter = 0 
     outText += ( "<OL>\n")

     for service in serviceList:
         counter += 1 
         outText += ( "<LI>" + service.code + "&nbsp;&nbsp; name='" + service.name + "' infrastructureName=" + service.infrastructureName) 
         countParents = 0
         for x in service.parents:
             countParents += 1
         if countParents > 0: 
            outText += ( "<BR> &nbsp&nbsp&nbsp;&nbsp;Parent(s): ") 
            loopcounter = 0 
            for parent in service.parents:
               loopcounter += 1 
               if loopcounter > 1:
                 outText += ( ", ") 
               outText += ( parent.code) 
         depth = 1
         outText += ( "</LI>\n")
         outText += self.showChildren(service, depth)
     outText += ( "</OL>\n") 
      

     if self.request.get('parm') == 'ALL': 
        # Report Above showed "ALL" (if parm was set, 
        # so now, just give a list of only the sellable products (without the bundles/expansion) 
        query = ServiceType.gql("where isSellable = :1", True)  #no where clause needed
        LIMIT = 1000
        serviceList = query.fetch(LIMIT,offset=0)

        outText += ( "<h3>All Sellable ServiceTypes</h3>\n")
        counter = 0 
        outText += ( "<OL>\n")

        for service in serviceList:
           outText += ( "<LI>" + service.code + "&nbsp;&nbsp; name='" + service.name + "'" ) 
        outText += ( "</OL>\n")

     templateDictionaryLocal = {"genericText": outText,
                                "genericReportTitle": genericReportTitle
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/reportGenericText.html', templateDictionaryLocal)


#end of class 



#=======================================================
#END of Reports 
#=======================================================



class DumpSessionData(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))


  def get(self):

      mySession = Session()
      outText = "" 

      if mySession:        #recommended: http://groups.google.com/group/google-appengine-python/browse_thread/thread/3f4fbfd45afa7abd#
      #if mySession != None:   # do not do this  
      #if not isinstance(mySession,NoneType):  #might work, but needs: from types import NoneType
         #self.response.out.write("<h4>Session Variables</h4>\n") 
         counter = 0 
         for item in mySession:
            counter += 1 
            outText += "&nbsp;" + str(counter) + " " 
            outText += str(item) 
            # only show values for simple types enumerated here 
            if item in ['username','subscriberkey','sessionkey', 'userDomain', 'isAdmin', 'submitButtonText', 'redirectPageAfterLogin']: 
               outText += " Value=" + str(mySession[item]) 
            else: 
               outText += " (Value not displayed) " 
            outText += "<BR>\n"
      else: 
         outText += "Session = None" 

      #if not 'forms' in mySession:
      #   self.response.out.write("<BR><BR><font color='red'>No forms in session variables</form>") 
      #  return

      #forms = mySession['forms']

      #self.response.out.write("<h4>Forms</h4>\n") 
      #subscript = 0 
      #self.response.out.write("Size of forms = " + str(len(forms)) + "<BR>\n")
      #for form in forms: 
      #   self.response.out.write(str(subscript) + ":" + 
#                                " seq=" + str(form.seq) + 
#                                " pageSubmitted=" + str(form.pageSubmitted) + 
#                                "<BR>\n"
#                                )
#          subscript += 1 
#     return 

      if 'sessionkey' in mySession:
         sessionkey = mySession['sessionkey']
         session = CumulusSession.get(sessionkey)   #retrieve session record from BigTable Database 
         outText += "<h2>CumulusSession Data (from Database)</h2>" 
         outText += "Number of pagesSubmitted variables = " + str(len(session.pagesSubmitted)) 
         outText += "<br/><br/>Each page submitted variable listed below:"

         counter = 0 
         for page in session.pagesSubmitted:
            outText += "<br/>" + str(counter) + " " + str(page) 
            counter += 1 
         outText += "<br/><br/>" 

         #any value that might be None must have str() around it for concatenation to work 
         outText += "<br/>Domain=" + str(session.domain)
         outText += "<br/>Firstname=" + str(session.firstname)
         outText += "<br/>Lastname=" + str(session.lastname)
         outText += "<br/>Bio=" + str(session.bio) 

         for var in CumulusSession.__dict__:
            value = getattr(session,var)
            outText += ("<br/>" + var + "=" + str(value))

      genericReportTitle = "Dump Session Variables" 
      templateDictionaryLocal = {"genericText": outText,
                                "genericReportTitle": genericReportTitle
                               }

                                
      templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
      templateDictionaryLocal.update(templateDictionaryGeneral)
      self.renderPage('templates/reportGenericText.html', templateDictionaryLocal)




class DetailSession(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))


  def get(self):

      outText = "" 

      if self.request.get('key') > ' ': 
        session = CumulusSession.get(self.request.get('key')) 
        if not session:
           self.response.out.write("<h3>Session not found with key=" + str(self.request.get('key')) + "</h3>") 
           return 

        counter = 0 
        for item in session.__dict__:
            counter += 1 
            outText += "&nbsp;" + str(counter) + " " 
            item2 = item
            outText += str(item2) 
            # only show values for simple types enumerated here 
            if item not in ['_photo','_resume','_entity']: 
               try: 
                 value = str(getattr(session, item)) 
                 outText += " Value=" + str(value) 
               except (Exception), e:
                 outText += " " + str(e) 
            else: 
               outText += " (Value not displayed) " 
            outText += "<BR>\n"
      else: 
         outText += "Session = None" 


      genericReportTitle = "Dump Session Variables" 
      templateDictionaryLocal = {"genericText": outText,
                                "genericReportTitle": genericReportTitle
                               }

                                
      templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
      templateDictionaryLocal.update(templateDictionaryGeneral)
      self.renderPage('templates/reportGenericText.html', templateDictionaryLocal)


class DetailIPN(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))


  def get(self):

      outText = "" 

      if self.request.get('key') > ' ': 
        objPaypalIPNTest = PaypalIPNTest.get(self.request.get('key')) 
        if not objPaypalIPNTest:
           self.response.out.write("<h3>PaypalIPNTest not found with key=" + str(self.request.get('key')) + "</h3>") 
           return 

        outText += "<BR>ID=" + str(objPaypalIPNTest.key().id()) + "<BR><BR>" 
        outText += "<BR>DateTimeCreated=" + str(objPaypalIPNTest.dateTimeCreated) + "<BR><BR>" 
        outText += "<table border=1>" 
        counter = 0 
        for item in objPaypalIPNTest.item:
            counter += 1 
            outText += "<TR><TD>" + str(counter) + "</TD><TD>" + item + "</TD><TD>" + objPaypalIPNTest.itemValue[counter-1] + "</TD></TR>" 
      else: 
        self.response.out.write("<h3>No Key= found on URL</h3>") 
        return 

        outText += "</table>" 

      genericReportTitle = "IPNTest Data " 
      templateDictionaryLocal = {"genericText": outText,
                                "genericReportTitle": genericReportTitle
                               }

                                
      templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, [], '',0) 
      templateDictionaryLocal.update(templateDictionaryGeneral)
      self.renderPage('templates/reportGenericText.html', templateDictionaryLocal)


