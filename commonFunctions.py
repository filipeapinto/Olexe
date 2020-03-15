#!/usr/bin/env pythonf
# admin: http://localhost:8080/_ah/admin/datastore 

import os
import cgi
import uuid #GUID 
import datetime
import time
import sys
import atom.url
import settings   #this moodule is created from source here: http://code.google.com/appengine/articles/gdata.html
from appengine_utilities.sessions import Session 
import wsgiref.handlers
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

from dbModels import CumulusLog 
from storeInitialProductBundle import StoreBundle

def validateDateTimeFlex(textIn):
   """
      accepts a date/time in string format, and converts to python date/time type if possible. 
      allows for a variety of different less precise date/times (with or without time, hour, minute, second 
   """

   textIn = textIn.strip(' ')  #remove any leading/trailing blanks user may have left in the field 
   validationStrings = ["%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M","%m/%d/%Y %H","%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H", "%Y-%m-%d"]

   validationError = False 
   countValid = 0 
   countInvalid = 0 
   
   for validationString in validationStrings:
       try:
          #print "validating against format: " + validationString
          #be sure to import datetime or this might run but not work properly 
          pyDateTime  = datetime.datetime.strptime(textIn, validationString) 
          countValid += 1 
       except: 
          countInvalid += 1 

   #print "CountValid=" + str(countValid) + " countInvalid=" + str(countInvalid) 

   if countValid > 0:
      return pyDateTime 
   else:
      raise Exception("DateTime=" + textIn + " is not a valid date/time")
      #return "DateTime=" + textIn + " is not a valid date/time" 

class CommonEmail():

  def sendMailFromTemplate(self, toEmail, firstname, title, templateFilename):

     message = mail.EmailMessage()
     message.sender = "3WCloud<googleadmin@3wcloud.com>"
     message.subject = title 
     message.to = toEmail

     templateDictionary = {
                      "firstname": firstname, 
                      "email": toEmail 
                      }

     path = os.path.join(os.path.dirname(__file__),templateFilename)

     try:
       renderedMessage = template.render(path, templateDictionary)
       message.html = renderedMessage 
       message.send()
     except (Exception), e:
       #if webapp: 
       #   webapp.response.out.write(str(e))
       #   webapp.response.out.write("<BR><BR>") 
       #   webapp.response.out.write(dir(template)) 
       #else:
          raise(e) 

class DojoLinks(db.Model): #this is never stored in database 
     label = db.StringProperty()  
     URL  = db.StringProperty(default="")  
     icon = db.StringProperty()  


class MenuLinks(db.Model): #this is never stored in database 
     description = db.StringProperty()  
     URL  = db.StringProperty(default="")  
     selected  = db.BooleanProperty(default=False) 
     level = db.IntegerProperty() 
     newWindow = db.BooleanProperty(default=False)  

oneCloudLinks = []   #global variable 

adminLinks = []
adminLinks.append(MenuLinks(level=1,description="---------") )
adminLinks.append(MenuLinks(level=1,description="Reports") )
adminLinks.append(MenuLinks(level=2,description="ServiceTypes",  URL="/reportServiceTypes") )
adminLinks.append(MenuLinks(level=2,description="Bundles",       URL="/reportBundle") )
adminLinks.append(MenuLinks(level=2,description="Subscribers",   URL="/reportSubscribers") )
adminLinks.append(MenuLinks(level=2,description="Orders",        URL="/reportOrders") )
adminLinks.append(MenuLinks(level=2,description="Services",      URL="/reportServices")) 
adminLinks.append(MenuLinks(level=2,description="Transactions",  URL="/reportIPN")) 
#adminLinks.append(MenuLinks(level=2,description="Workers",      URL="/reportWorkers?type=admin")) 
adminLinks.append(MenuLinks(level=2,description="Sessions",      URL="/reportSessions")) 
adminLinks.append(MenuLinks(level=2,description="RatePlans",     URL="/reportRatePlans")) 
adminLinks.append(MenuLinks(level=2,description="KeyValuePairs", URL="/reportKeyValuePairs")) 
adminLinks.append(MenuLinks(level=2,description="Log",           URL="/reportLog")) 
adminLinks.append(MenuLinks(level=2,description="SessionData",   URL="/dumpSessionData")) 
adminLinks.append(MenuLinks(level=2,description="Newsletters",   URL="/reportNewsletters")) 
adminLinks.append(MenuLinks(level=2,description="KB-Books",      URL="/reportBooks")) 
adminLinks.append(MenuLinks(level=2,description="KB-Documents",  URL="/updDocuments")) 
adminLinks.append(MenuLinks(level=2,description="Feedback",      URL="/reportFeedback")) 
adminLinks.append(MenuLinks(level=2,description="Providers",     URL="/reportProviders")) 
adminLinks.append(MenuLinks(level=2,description="Tasks",         URL="/reportTasks")) 
adminLinks.append(MenuLinks(level=2,description="RunningTasks",  URL="/reportTaskStatus")) 
adminLinks.append(MenuLinks(level=2,description="TaskHistory",   URL="/reportTaskStatusHistory")) 






def buildLinks(isAdmin, userLinks, currentPage):
    global oneCloudLinks 
    showLinks = userLinks
    if isAdmin: 
        showLinks = userLinks + oneCloudLinks + adminLinks   # userLinks.append(adminLinks) 
    else: 
        showLinks = userLinks + oneCloudLinks 
    for link in showLinks:                          #highlight the current link 
        if link.URL == currentPage: 
           link.selected = True 
        else:
           link.selected = False      #not sure why needed this, but old values didn't seem to be clearing between web pages 
    return showLinks
    

def getSharedTemplateDictionary(currentPage, URL, forms, serviceCode, currentPageNum): 
     params = {}
     params = commonUserCode(params,URL)

     dojoLinks = []
     userLinks = []
     userLinks.append(MenuLinks(level=1,description="You"))
     userLinks.append(MenuLinks(level=2,description="Home",      URL="/myHome") )
     userLinks.append(MenuLinks(level=2,description="Help-KB",   URL="/myHelpBooks") )
     userLinks.append(MenuLinks(level=2,description="Profile",   URL="/myProfile") )
     userLinks.append(MenuLinks(level=2,description="Orders",    URL="/myOrders") )
     userLinks.append(MenuLinks(level=2,description="Services",  URL="/myServices") )
     userLinks.append(MenuLinks(level=2,description="Goals",     URL="/reportGoals") )
     userLinks.append(MenuLinks(level=2,description="Knowledge", URL="/reportKnowledgeSources") )
     userLinks.append(MenuLinks(level=2,description="Credentials", URL="/reportCredentials") )

     userDomain = params['userDomain']
     oneCloudStatus = params['OneCloudStatus'] 

     #new orders will have status=Inactive, so don't show links until activated 
     #if userDomain and oneCloudStatus == "Active": 
     # on 07/23/09 Neal changed login/query to only get "Active" services 
     #             and to return the domain of the first Active OneCloud Service 
     if userDomain: 
        userLinks.append(MenuLinks(level=1,description="OneCloud",  URL="")) 
        userLinks.append(MenuLinks(level=2,description="Email",     URL="http://mail." + userDomain, newWindow=True)) 
        userLinks.append(MenuLinks(level=2,description="Docs",      URL="http://docs." + userDomain, newWindow=True)) 
        userLinks.append(MenuLinks(level=2,description="Sites",     URL="http://sites." + userDomain, newWindow=True)) 
        userLinks.append(MenuLinks(level=2,description="Calendar",  URL="http://calendar." + userDomain, newWindow=True)) 
        userLinks.append(MenuLinks(level=2,description="OneCloud",  URL="http://www."  + userDomain, newWindow=True)) 

        dojoLinks.append(DojoLinks(icon="/images/icon_email.png",      description="Email",     URL="http://mail." + userDomain)) 
        dojoLinks.append(DojoLinks(icon="/images/icon_texteditor.png", description="Docs",      URL="http://docs." + userDomain)) 
        dojoLinks.append(DojoLinks(icon="/images/icon_browser.png",    description="Sites",     URL="http://sites." + userDomain)) 
        dojoLinks.append(DojoLinks(icon="/images/icon_calendar.png",   description="Calendar",  URL="http://calendar." + userDomain)) 
        dojoLinks.append(DojoLinks(icon="/images/icon_update.png",     description="OneCloud",  URL="http://www."  + userDomain)) 

     #userLinks.append(MenuLinks(level=1,description="Billing") )
     #userLinks.append(MenuLinks(level=2,description="Future1") )
     #userLinks.append(MenuLinks(level=2,description="Future2") )
     #userLinks.append(MenuLinks(level=1,description="Invoices") )
     #userLinks.append(MenuLinks(level=2,description="Future1") )
     #userLinks.append(MenuLinks(level=2,description="Future2") )
     userLinks.append(MenuLinks(level=1,description="Logout",  URL="/logout") )


     #build the tabs to be displayed at the top of the form 
     tabs=[]
     for form in forms:
        if form.serviceCode == serviceCode: 
	   #form[currentPage) = True   # TODO how to set page 
	   tabs.append(form) 

     showLinks = buildLinks(params['is_admin'], userLinks, currentPage) 
     debugText = "" 
     if serviceCode == "register":
        orderType = "registration"
     else:
        orderType = "order"

     posSlash = URL.rfind("/") 
     URLPath = URL[posSlash:]

     templateDictionaryGeneral = {
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "currentUser": params['user'],
                      "serviceCode": serviceCode,
                      "orderType": orderType,
                      "userLinks":showLinks,
                      "tabs":tabs,
                      "URL":URLPath,
                      "dojoLinks":dojoLinks,
		      "currentPageNum":currentPageNum, 
                      "now": datetime.datetime.now()
                      }
     return templateDictionaryGeneral 


def commonUserCode(params, url):
       #user = users.get_current_user()  #for Google  user 
  
       mySession = Session()  #our own user is stored in Session variable

       if 'username' in mySession:
           user = mySession['username']
       else: 
           user = ""


       if 'userDomain' in mySession:
           userDomain = mySession['userDomain']
       else: 
           userDomain = ""

       if 'OneCloudStatus' in mySession:
           OneCloudStatus = mySession['OneCloudStatus']
       else: 
           OneCloudStatus = ""


       isAdmin = False 
       if 'isAdmin' in mySession:
           isAdmin = mySession['isAdmin']

       if (url.lower().find("8080")) > -1:
           environment = "test" 
       else:
           environment = "production"


       params['environment'] = environment 

       #if user:
       if 'username' in mySession:
          params['userMessage'] = "Signed in" 
          params['user'] = user
          params['sign_out'] = users.CreateLogoutURL('/')
          #params['is_admin'] = (users.IsCurrentUserAdmin() and 'Dev' in os.getenv('SERVER_SOFTWARE'))
          params['is_admin'] = isAdmin 
          #get session variables to display on form 
          #domainKey = users.get_current_user().email() + ":customerDomain";
          domainKey = user + ":customerDomain";
          params['customerDomain'] = memcache.get(domainKey);
          #domainKey = user + ":startTime";
          #params['startedDateTime'] = memcache.get(domainKey);
          params['sign_in'] = None
	  params['userDomain'] = userDomain 
	  params['OneCloudStatus'] = OneCloudStatus 
       else:
          #params['sign_in'] = users.CreateLoginURL(self.request.path)
          params['sign_in'] = users.CreateLoginURL(url)
          params['userMessage'] = "Not signed in" 
          params['user'] = None
          params['is_admin'] = None 
          params['customerDomain'] = None
          params['startedDateTime'] = None
          params['sign_out'] = None
	  params['userDomain'] = None 
	  params['OneCloudStatus'] = None 
          #self.response.out.write(
          #   "<h3> self.request.path = " + self.request.path + "</h3>" +  
          #   "<h3>Debug LoginURL=" + users.CreateLoginURL(self.request.path) + "</h3>");
          #return;
       return params 



def loggedin(self):
    mySession = Session()  # user is stored in Session variable if logged in 
    if 'username' in mySession:
        user = mySession['username']
        if user:
           #self.response.out.write("User=" + user + "<BR>")
           return user 
    log = CumulusLog() 
    log.category = "Debug"
    log.message = "No User in Session, redirecting to /login page" 
    log.put() 
    self.redirect("/login")    



def getLoggedInUser(self): 
    mySession = Session()  # user is stored in Session variable if logged in 
    if 'username' in mySession:
        user = mySession['username']
        if user > ' ':
           #self.response.out.write("User=" + user + "<BR>")
           return user 
	else: 
	   return None 
    else:
        return None 



