#!/usr/bin/env pythonf
# admin: http://localhost:8080/_ah/admin/datastore 

import os
import cgi
import uuid #GUID 
#import apptools
import datetime
import time
import sys
import atom.url
import settings   #this moodule is created from source here: http://code.google.com/appengine/articles/gdata.html
import jsonpickle
from django.utils import simplejson
#import simplejson as json1


#import sessions


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
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from django import shortcuts
#from google.appengine.ext import users
#from userpreferences import UserPreferences

from dbModels import ServiceType
from dbModels import ServiceTypeLegal 
from dbModels import CumulusSession
from dbModels import Subscriber
from dbModels import Order
from dbModels import Service
from dbModels import ServiceOneCloud 
from dbModels import TaskLog
from dbModels import Tasks
from dbModels import Workers
from dbModels import CustomerOrders
from dbModels import CumulusLog 
from dbModels import CumulusDBModelCustomException
from dbModels import PaypalIPN 
from dbModels import KeyValuePair
from dbModels import ServiceRatePlan 
from dbModels import TaskQueueResults 
from dbModels import TaskQueueSeq 
from dbModels import CommonTaskMessage 


from adminReports import ReportWorkers
from adminReports import ReportTasks
from adminReports import ReportServiceTypes
from adminReports import ReportOrders
from adminReports import ReportServices
from adminReports import ReportCustomerOrders
from adminReports import ReportSubscribers
from adminReports import ReportWorkers
from adminReports import ReportSessions
from adminReports import ReportNewsletters
from adminReports import ReportLog
from adminReports import ReportIPN
from adminReports import ReportRatePlans
from adminReports import ReportBundle 
from adminReports import ReportKeyValuePairs
from adminReports import ReportRatePlanSubscriberXref
from adminReports import ReportServiceTypeSubscriberXref
from adminReports import DumpSessionData 
from adminReports import DetailSession
from adminReports import DetailIPN
from adminReports import DetailSubscriber
from adminReports import DetailNewsletter 
from adminReports import DetailLog
from adminReports import DetailTaskStatus
from adminReports import BookChapters
from adminReports import ReportBooks
from adminReports import ReportFeedback
from adminReports import ReportGoals
from adminReports import ReportKnowledgeSources
from adminReports import ReportKnowledgeEvents
from adminReports import ReportProviders
from adminReports import ReportCredentials
from adminReports import ReportTaskStatus
from adminReports import ReportTaskStatusHistory

from adminUpdates import UpdateService
from adminUpdates import UpdateOrder
from adminUpdates import UpdateSession
from adminUpdates import UpdateRatePlan
from adminUpdates import UpdateServiceType
from adminUpdates import UpdateKeyValuePair
from adminUpdates import DeleteServices
from adminUpdates import UpdateDocument
from adminUpdates import UpdateDocumentKeywords
from adminUpdates import UpdateDocuments
from adminUpdates import UpdateBook
from adminUpdates import UpdateFeedback
from adminUpdates import SubmitFeedback
from adminUpdates import UpdateProvider
from adminUpdates import UpdateTask
from adminUpdates import AcceptManualTask
from adminUpdates import CompletedManualTask

from myHome import MyOrders 
from myHome import MyServices 
from myHome import MyHome
from myHome import MyHelpBooks
from myHome import MyHelpKeywords
from myHome import ResumeCustomerOrder
from myHome import DeleteCustomerOrder
from myHome import UpdateGoal 
from myHome import UpdateKnowledgeSource
from myHome import UpdateKnowledgeEvent
from myHome import UpdateCredentials


from commonFunctions import buildLinks 
#from commonFunctions import userLinks
from commonFunctions import adminLinks 
from commonFunctions import loggedin 
from commonFunctions import getLoggedInUser 
from commonFunctions import commonUserCode
from commonFunctions import getSharedTemplateDictionary 
from commonFunctions import MenuLinks 

from commonEmail import CommonEmail 

from commonTaskHandler import CommonTaskHandler 
from commonTaskHandler import TaskCron
from commonTaskHandler import ForceTimeout


#large chunks of code moved to separate python files 
from storeInitialProductBundle import StoreBundle

#import django.conf
#try:
#  django.conf.settings.configure(
#    DEBUG=False,
#    DATETIME_FORMAT="m/d/y h:m:s",
#    TEMPLATE_DEBUG=False,
#    TEMPLATE_LOADERS=(
#      'django.template.loaders.filesystem.load_template_source',
#    ),
#  )
#except (EnvironmentError, RuntimeError):
#  pass

#import jsonpickle
#from jsonpickle import tags

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
oneCloudLinks = [] 


#decided not to use this type of structure:
#languages = {'English':true, 'Spanish',false, 'Portuguese',false, 'Mandarin',true} 

#languages = { 'English': {
#                            'selected': true,
#                            'imageURL': 

class Forms(db.Model): #this is never stored in database 
     serviceCode = db.StringProperty()
     description = db.StringProperty()  
     webpage = db.StringProperty(default="")  
     seq  = db.IntegerProperty()     #the page of the sequence, eg. page 2 or 4 (this field would store 2) 
     ofSeq  = db.IntegerProperty()   #the top of the sequence,  eg. page 2 or 4 (this field would store 4) 
     nextSeq  = db.IntegerProperty()   #the top of the sequence,  eg. page 2 or 4 (this field would store 4) 
     priorSeq  = db.IntegerProperty()   #the top of the sequence,  eg. page 2 or 4 (this field would store 4) 
     selected  = db.BooleanProperty(default=False) 
     pageSubmitted = db.BooleanProperty(default=False)  
     isContactForm = db.BooleanProperty(default=False)  
     askNewReturningCustomer = db.BooleanProperty(default=False)  

forms = [] 
forms.append(Forms(serviceCode="1CloudI", webpage="templates/customer/oneCloudSetupIndiv1.html",      seq=1,ofSeq=5,priorSeq=4,nextSeq=2,description="1 Domain/Language"))
forms.append(Forms(serviceCode="1CloudI", webpage="templates/customer/oneCloudSetupIndiv2.html",      seq=2,ofSeq=5,priorSeq=1,nextSeq=3,description="2 Resume/Web 2.0"))
forms.append(Forms(serviceCode="1CloudI", webpage="templates/customer/oneCloudSetupIndiv3.html",      seq=3,ofSeq=5,priorSeq=2,nextSeq=4,description="3 Bio", askNewReturningCustomer=True))
forms.append(Forms(serviceCode="1CloudI", webpage="templates/customer/commonContactInformation.html", seq=4,ofSeq=5,priorSeq=3,nextSeq=5,description="4 ContactInfo", isContactForm=True))
forms.append(Forms(serviceCode="1CloudI", webpage="templates/customer/commonFormSubmit.html",         seq=5,ofSeq=5,priorSeq=4,nextSeq=1,description="5 Submit"))
forms.append(Forms(serviceCode="register",webpage="templates/customer/commonContactInformation.html", seq=1,ofSeq=2,priorSeq=1,nextSeq=2,description="1 ContactInfo", isContactForm=True))
forms.append(Forms(serviceCode="register",webpage="templates/customer/commonFormSubmit.html",         seq=2,ofSeq=2,priorSeq=1,nextSeq=1,description="2 Submit"))


#sampleAlternateWayToDoLinks = [
#    ['Google', 'http://www.google.com'],
#    ['Wikipedia', 'http://wikipedia.org',
#        ['Spam', 'http://en.wikipedia.org/wiki/Spam_(food)',
#            ['Mystery Meat', 'http://en.wikipedia.org/wiki/Mystery_meat']]],
#    ['Python', 'http://python.org']]


#a list of required fields and the page number they appear on the form 
requiredTextFields1Cloud = {
                  'domain':'1',
                  'registrarURL':'1',
                  'registrarUserid':'1',
                  'registrarPassword':'1',
                  'photo':'2',
                  'resume':'2',
                  'bio':'3',
                  'userEmail':'4',
                  'userPassword':'4',
                  'firstname':'4',
                  'lastname':'4',
                  'address1':'4',
                  'city':'4',
                  'state':'4',
                  'zip':'4' 
                  }

#a list of required fields and the page number they appear on the form 
requiredTextFieldsRegister = {
                  'userEmail':'1',
                  'userPassword':'1',
                  'firstname':'1',
                  'lastname':'1',
                  'address1':'1',
                  'city':'1',
                  'state':'1',
                  'zip':'1' 
                  }

#for each key in this dictionary, we have a list of two values,
#first the page on which the field occurs, then the minimum number of items
#required for that list. 
requiredListFields1Cloud = {
                  'tags':['3',3],
                  }
#                  'languages':['1',1],  #removed the multi-language option on 6/26/09 
requiredListFieldsRegister = {}

class Language(db.Model):  #this is never stored in database 
   name  = db.StringProperty() 
   imageURL = db.StringProperty() 
   selected = db.BooleanProperty() 
   isPrimary = db.BooleanProperty(default=False)

languages = []; 
languages.append(Language(name="English",imageURL="/images/flags/english.jpg",selected=False,isPrimary=True));
languages.append(Language(name="Spanish",imageURL="/images/flags/spanish.jpg",selected=False))
languages.append(Language(name="Portuguese",imageURL="/images/flags/portuguese.jpg",selected=False))
languages.append(Language(name="Mandarin",imageURL="/images/flags/mandarin.jpg",selected=False))

class Upsell(db.Model):  #this is never stored in database 
   name      = db.StringProperty() 
   code      = db.StringProperty() 
   url       = db.StringProperty() 
   selected  = db.BooleanProperty() 


class SocialNetworks(db.Model):  #this is never stored in database 
   category  = db.StringProperty() 
   examples  = db.StringProperty() 
   selected  = db.BooleanProperty() 
   socialUrl = db.StringProperty()  

socialNetworks = []
socialNetworks.append(SocialNetworks(category="Blog",examples="WordPress/BlogSpot/etc...",selected=False,socialUrl="")); 
socialNetworks.append(SocialNetworks(category="Microblog",examples="Twitter...",selected=False,socialUrl="")); 
socialNetworks.append(SocialNetworks(category="Videos",examples="YouTube/Google/etc...",selected=False,socialUrl="")); 
socialNetworks.append(SocialNetworks(category="Pictures",examples="Picasa/Flickr/etc...",selected=False,socialUrl="")); 
socialNetworks.append(SocialNetworks(category="Professional Networking",examples="LinkedIn/Plaxo/etc...",selected=False,socialUrl="")); 
socialNetworks.append(SocialNetworks(category="Friendship Networking",examples="Facebook/Orkut/Bebo/etc...",selected=False,socialUrl="")); 



#loging.getLogger().setLevel(loging.DEBUG)

#class GMT1(tzinfo):
#     def __init__(self):         # DST starts last Sunday in March
#         d = datetime(dt.year, 4, 1)   # ends last Sunday in October
#         self.dston = d - timedelta(days=d.weekday() + 1)
#         d = datetime(dt.year, 11, 1)
#         self.dstoff = d - timedelta(days=d.weekday() + 1)
#     def utcoffset(self, dt):
#         return timedelta(hours=1) + self.dst(dt)
#     def dst(self, dt):
#         if self.dston <=  dt.replace(tzinfo=None) < self.dstoff:
#             return timedelta(hours=1)
#         else:
#             return timedelta(0)
#     def tzname(self,dt):
#          return "GMT +1"


def stripTags(textin):
     fixline = textin.replace("&","&amp;");
     fixline = fixline.replace("<","&lt;");
     fixline = fixline.replace(">","&gt;");
     return fixline;

def PaypalDecode(textin):
     fixline = textin.replace("+"," ");
     fixline = fixline.replace("%40","@");
     fixline = fixline.replace("%3A",":");
     fixline = fixline.replace("%24","$");
     fixline = fixline.replace("%2C",",");
     fixline = fixline.replace("%2F","/");
     return fixline;

def fixdate(datein):
       #another idea to research - discovered when I put date in admin
       #return datetime.datetime(*(time.strptime(value, TimeType._FORMAT)[0:6]))

        position = datein.find(".") 
        date2=datein 
        # remove milliseconds: 2009-05-29 17:44:22.229000 to
        #                      2009-05-29 17:44:22 
        if position > 1: 
           date2 = datein[0:position]
        datetimeTuple = time.strptime(date2, "%Y-%m-%d %H:%M:%S")
        outSeconds = time.mktime(datetimeTuple)
        return outSeconds 

def fix443(argHttpOrHttps,argURL):
   #the atom.url or settings.HOSTNAME started include the port 443 in the URLs, 
   #we need to strip this out when not using https:// 
   #if argHttpOrHttps == "http": 
   #we never really need the port number in the URL 
   argURL = argURL.replace(":443","") 
   return argURL 


def getCommonPaypalForm(argHidden=False):
     #documentation on this page: https://cms.paypal.com/us/cgi-bin/?cmd=_render-content&content_ID=developer/e_howto_html_Appx_websitestandard_htmlvariables
     #describes all the parms you can pass in the form: 
     #a3/p3/t3 are the recurring fees 
     #a3 = Regular Subscription Price
     #p3 = Subscription duration. Specify an integer value in the allowable range for the units of duration that you specify with t3.
     #   This is confusing, but apparently you always set it to 1 if you want to charge weekly/monthly/etc...
     #   If you wanted to charge every 3 months, you would set it to 3. 
     #t3 = M = Monthly 
     #src = 1 (means payments recurr) 
     #sra = 1 reattempt failed recurring payments before canceling
     #a1/p1/t1 is a trial period, which enables us to cause a fixed setup fee 
     #see example here: http://www.jkquilting.com/z_code/Script_Example_35.html 
     #a1 = One Time Setup Fee
     #p1 = 1
     #t1 = "D" - set to trial period to daily, so monthyly charge starts tomorrow (one day later) 
     #
     # above sample also sets the following: 
     #   bn=PP-SubscriptoinsBF 
     #   on1 = "One Time Setup Fee" 
     #   os1 = "$25.00 charged the first day"   (This is the amt of the setup fee) 
     #
     # TODO - we could use field=invoice to pass an invoice number - the issue is that we probably create
     #        the order in BigTable after we get cleared payment from Paypal  
     #cmd = _cart or _xclick-subscriptions

     paypalForm = """
             <body onload="submitform()">
             <div id="myText"> <!-- used in conjunction with JavaScript showDiv and hideDiv --> 
                 &autoSubmitText 
             <form name=PaypalForm action="&paypalPostAction" method="post">
                 <input type="hidden" name="cmd" value="_xclick-subscriptions" />
                 <input type="hidden" name="image_url" value="&imageURL" />
                 <input type="hidden" name="item_name" value="&itemName" />
                 <input type="hidden" name="a3"  value='&recurringAmount' />
                 <input type="hidden" name="p3"  value='&billingInterval' />
                 <input type="hidden" name="t3"  value='&billingPeriod' />
                 <input type="hidden" name="a1"  value='&oneTimeAmount' />
                 <input type="hidden" name="p1"  value='1' />
                 <input type="hidden" name="t1"  value='D' />
                 <input type="hidden" name="rm"  value='2' />  
                 <input type="hidden" name="src" value='1' />
                 <input type="hidden" name="sra" value='1' />
                 <input type="hidden" name="on0" value='Subscription Option:' />
                 <input type="hidden" name="os0" value='$&recurringAmount monthly membership for &productName' />
                 <input type="hidden" name="on1" value='One Time Setup Fee' />
                 <input type="hidden" name="os1" value='$&oneTimeAmount one time setup fee charged first day ' />
                 <input type="hidden" name="no_note" value='1' />
                 <input type="hidden" name="return"        value="&returnURL" />
                 <input type="hidden" name="cancel_return" value="&cancelReturnURL" />
                 <input type="hidden" name="notify_url" value="&notifyURL" />
                 <input type="hidden" name="business" value="&business" />
                 <input type="hidden" name="currency_code" value="USD" />
                 <input type="hidden" name="upload" value="1" />
                 <input type="hidden" name="invoice" value="&invoice" />
                 <input type="image" src="http://3wcloud.com/wp-content/plugins/wordpress-simple-paypal-shopping-cart/images/paypal_checkout.png" name="submit" alt="Make payments with PayPal - it's fast, free and secure!" />
             </form>
             </div>
             </body> 
             """ 

     autoSubmitText = """
             <h2>The form below should auto-submit if you have JavaScript enabled</h2>
             <h2>We have saved your order on our database, but we have not interfaced with Paypal yet</h2> 
             <h2>If you have Javascript disabled, please click the "Payment" button again to continue</h2> 
     """ 
     #this parm allows this common routine to be used by a test data form where user types in fields.
     #or a regular hidden data form. 
     # Ideally-we would also insert tags to show each field - but for now - it's better than nothing.  
     if not argHidden: 
        paypalForm = paypalForm.replace("hidden","text") 
        paypalForm = paypalForm.replace("&autoSubmitText","") 
     else:
        paypalForm = paypalForm.replace("&autoSubmitText",autoSubmitText) 
     return paypalForm 
 
def respond(request, user, template, params=None):
    """Helper to render a response, passing standard stuff to the response.

  Args:
    request: The request object.
    user: The User object representing the current user; or None if nobody
      is logged in.
    template: The template name; '.html' is appended automatically.
    params: A dict giving the template parameters; modified in-place.

  Returns:
    Whatever render_to_response(template, params) returns.

  Raises:
    Whatever render_to_response(template, params) raises.
  """
    if params is None:
      params = {}
    if user:
      params['user'] = user
      params['sign_out'] = users.CreateLogoutURL('/')
      params['is_admin'] = (users.IsCurrentUserAdmin() and
                          'Dev' in os.getenv('SERVER_SOFTWARE'))
    else:
      params['sign_in'] = users.CreateLoginURL(request.path)
    if not template.endswith('.html'):
      template += '.html'
    template = os.path.join(os.path.dirname(__file__),template)
    return shortcuts.render_to_response(template, params)

class TestURL(webapp.RequestHandler):

  def get(self):
     if self.request.url.startswith("https"):
        httpOrHttps = "https"
     else: 
        httpOrHttps = "http"

     self.response.out.write("TestURL httpOrHttps=" + httpOrHttps) 


class TestGDocAPI(webapp.RequestHandler):

  def get(self):

     client = gdata.service.GDataService()
     # Tell the client that we are running in single user mode, and it should not
     # automatically try to associate the token with the current user then store
     # it in the datastore.
     gdata.alt.appengine.run_on_appengine(client, store_tokens=False, single_user_mode=True)
     client.email = 'GoogleAdmin@3wcloud.com'
     client.password = '49ak3014jtiEM'
     # To request a ClientLogin token you must specify the desired service using 
     # its service name.  Neal verified 07/27/09 that login fails without this parm
     # even though some documents indicate that it is optional). 
     # "wise" is the codename for GoogleDocs - see this page:
     # http://ruscoe.net/google/google-account-service-names/ 
     #client.service = 'wise'      #for Google Spreadsheets
     client.service = 'writely'   #for Google Docs (include spreadsheets?) 
     # Request a ClientLogin token, which will be placed in the client's 
     # current_token member.
     client.ProgrammaticLogin() 

     self.response.out.write("<h3>client.ProgrammaticLogin completed</h3>") 



     form_fields = {}

     import urllib 
     form_data = urllib.urlencode(form_fields)
     #logging.debug("paypal form_data=" + form_data) 
     url = "http://docs.nealwalters.com/feeds/download/presentations/Export?docID=3W.KB.OneCloud.Sample01&exportFormat=html"
     #url = "http://docs.nealwalters.com/feeds/download/Export?docID=3W.KB.OneCloud.Sample01&exportFormat=html"

     result = client.Get(url, converter=str)
     self.response.out.write("Google GDocs Response 2: " + result)


     #from google.appengine.api import urlfetch
     #result = urlfetch.fetch(url, payload=form_data, method=urlfetch.GET, headers={}, allow_truncated=False, follow_redirects=True, deadline=None)

     #import logging
     #logging.debug("PaypalCompleted:Response=" + result.content) 
     #self.response.out.write("Google GDocs Response: " + result.content)


     #gd_client = gdata.docs.service.DocsService(email='GoogleAdmin@3wcloud.com',password='49ak3014jtiEM')
     #gd_client.ClientLogin('GoogleAdmin@3wcloud.com', '49ak3014jtiEM')

     #gdata.alt.appengine.run_on_appengine(client)

     # this is if you want an online "Grant" access, but instead we want auto-logon above. 
     #next_url = atom.url.Url('http', settings.HOST_NAME, path='/testGDocAPI2')
     #self.response.out.write("""<html><body>
     #   <a href="%s">Request token for the Google Documents Scope</a>
     #   </body></html>""" % client.GenerateAuthSubURL(next_url,
     #       ('http://docs.google.com/feeds/',), secure=False, session=True))




     new_entry = gdata.GDataEntry()
     gdata.alt.appengine.run_on_appengine(new_entry)
     new_entry.title = gdata.atom.Title(text='MyBlankSpreadsheetTitle')

     category = gdata.atom.Category(scheme=gdata.docs.service.DATA_KIND_SCHEME, 
                                    term=gdata.docs.service.SPREADSHEET_KIND_TERM)
     gdata.alt.appengine.run_on_appengine(category)

     new_entry.category.append(category)

     created_entry = client.Post(new_entry, 'http://docs.google.com/feeds/documents/private/full')



     # in browser - this works: http://docs.nealwalters.com/docs/feeds/documents/private/full 
     # but this does not: 
     # http://docs.google.com/a/3wcloud.com/docs/feeds/documents/private/full 
     # but this does, even though it is not a feed: 
     # http://docs.google.com/a/3wcloud.com/#spreadsheets

     # add line to test mercurial - then change it - then change it again

     #print 'Spreadsheet now accessible online at:', created_entry.GetAlternateLink().href

  def PrintFeed(feed):
    """Prints out the contents of a feed to the console."""
    if not feed.entry:
       self.response.out.write('No entries in feed.\n') 
    for entry in feed.entry:
       self.response.out.write('%s %s %s' % (entry.title.text.encode('UTF-8'), entry.GetDocumentType(), entry.resourceId.text)) 


class ConvertTasks(webapp.RequestHandler):

  def get(self):
     query = Tasks.gql("");    # get matching customerDomain 
     LIMIT = 1000 
     taskList = query.fetch(LIMIT,offset=0);
     self.response.out.write("Number of Tasks Retrieved=" + str(len(taskList)))
     counter = 0 
     for task in taskList:
         #self.response.out.write("taskCode=" + task.taskCode)
         if task.processCode == "iCloud": 
            task.processCode = "oneCloudIndiv" 
            serviceType = ServiceType.gql("where serviceCode = :1", task.taskCode) 
            task.serviceType = serviceType; 
            task.put() 
            counter += 1
         if task.processCode == "weCloud": 
            task.processCode = "oneCloudOrg" 
            serviceType = ServiceType.gql("where serviceCode = :1", task.taskCode) 
            task.serviceType = serviceType; 
            task.put() 
            counter += 1
     self.response.out.write("<h3>Rows Updated = " + str(counter) + "</h3>")



class StoreModOrder(webapp.RequestHandler):
  """
  This creates a test record to help prove database structure and reports layout, 
  by forcing a condition that we might have more in the future, 
  i.e. a many-to-many relationship between service and order. 
  """
  def get(self):

     #first, copy the order db-key to the list of dbkeys to switch from one to many 
     #serviceList = Service.all().fetch(1000) 
     #for service in serviceList:
     #   service.orders.append (service.order.key())
     #   service.put()

     self.response.out.write("<h3>StoreModOrder Step 1 Order-to-Orders Completed</h3>") 

     serviceId = 26287
     service = Service.get_by_id(serviceId) 
     if not service:
        self.response.out.write("<h3>Service not found with id=" + str(serviceId) + "</h3>")
        return 

     order1 = Order() 
     order1.orderDate = datetime.datetime.now() 
     order1.subscriber = service.subscriber 
     if service.domain: 
        order1.domain = service.domain 
     order1.apiClientId = "auto" 
     order1.orderType = "Change" 
     order1.priority = 3 #normal 
     order1.orderState = "open.not_running"
     order1.financialStatus = "Complementary" 
     order1.put() 

     self.response.out.write("<h3>StoreModOrder: Order1 Stored </h3>") 

     order2 = Order() 
     order2.orderDate = datetime.datetime.now() 
     order2.subscriber = service.subscriber 
     if service.domain: 
        order2.domain = service.domain 
     order2.apiClientId = "auto" 
     order2.orderType = "Cancel" 
     order2.priority = 3 #normal 
     order2.orderState = "open.not_running"
     order2.financialStatus = "Complementary" 
     order2.put() 

     self.response.out.write("<h3>StoreModOrder: Order2 Stored </h3>") 

     #get a specific service, and attach a the above new order to it. 
     service.orders.append(order1.key())
     service.orders.append(order2.key())
     service.put() 

     self.response.out.write("<h3>StoreModOrder Service Updated with 2 new Orders</h3>") 



class StoreLegals(webapp.RequestHandler):

  def get(self):

     serviceTypeLegal = ServiceTypeLegal(); 
     serviceTypeLegal.code              = '1CloudI'
     serviceTypeLegal.legalTerms         = """
        This is the OneCloud-Individual legal terms that will eventually be copied from 
        Google App Account, Google Acount, You-Tube, Picsas, etc... 
     """
     serviceTypeLegal.put(); 

     serviceTypeLegal = ServiceTypeLegal(); 
     serviceTypeLegal.code               = '1CloudOrg'
     serviceTypeLegal.legalTerms         = """
        This is the OneCloud-Organization legal terms that will eventually be copied from 
        Google App Account, Google Acount, You-Tube, Picsas, etc... 
     """
     serviceTypeLegal.put(); 

     serviceTypeLegal = ServiceTypeLegal(); 
     serviceTypeLegal.code               = '1CloudFam'
     serviceTypeLegal.legalTerms         = """
        This is the OneCloud-Family legal terms that will eventually be copied from 
        Google App Account, Google Acount, You-Tube, Picsas, etc... 
     """
     serviceTypeLegal.put(); 

     self.response.out.write("""
          <h1>StoreLegals Completed - Use Admin Tool to View Rows</h1><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
      """)

class StoreRows(webapp.RequestHandler):

  def get(self):

     self.response.out.write("""
          <h1>StoreRows Completed - Use Admin Tool to View Rows</h1><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
      """)

class StartTask(webapp.RequestHandler):
  """
  Allow user to use browser to enter the following syntax 
  http://localhost:8080/startTask?task=add&value1=5&value2=10
  or 
  http://localhost:8080/startTask?processCode=test01 
  and to write a task to the task queue.
  This is just a simple test to learn how the task queue works. 
  """
  def get(self):
     errorFlag = False 

     task = self.request.get("task") 
     if task == "add": 
       #if self.request.get("task") <= " ":
       #    self.response.out.write("<h3>Missing ?task=xxxx on URL</h3>")
       #    errorFlag = true 
       if self.request.get("value1") <= " ":
           self.response.out.write("<h3>Missing &value1=xxxx on URL</h3>")
           errorFlag = true 
       if self.request.get("value2") <= " ":
           self.response.out.write("<h3>Missing &value2=xxxx on URL</h3>")
           errorFlag = true 
       if errorFlag:
          return 

       task = self.request.get('task') 
       value1 = self.request.get('value1') 
       value2 = self.request.get('value2')

       # Add the task to the default queue.
       taskqueue.add(url='/taskHandler', 
           params={'task': task, 
                   'value1': value1, 
                   'value2': value2
                   })
       logging.info('/StartTask wrote to default queue with processCode=' + processCode) 
       msg = """
          <h1>ProcessCode=&processCode stored to default queue</h1><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
          """
       msg = msg.replace("&processCode",processCode)
       self.response.out.write(msg) 
       self.response.out.write("<br/><br/> at time=" + str(datetime.datetime.now())) 
       

     processCode = self.request.get("processCode") 
     if processCode[0:4] == "test":
       objCommonTaskMessage = CommonTaskMessage() 
       objCommonTaskMessage.processCode = processCode
       objCommonTaskMessage.currentSeqNum = 0
       objCommonTaskMessage.taskStatusId = 0
       objCommonTaskMessage.orderId = 14522
       objCommonTaskMessage.subscriberId = 14515
       objCommonTaskMessage.serviceId = 14711 
       objCommonTaskMessage.generalText = "This is my mini-blog" 
       objCommonTaskMessage.generalObject = "some pickled object??" 
       objCommonTaskMessage.isManual = False 
       #set the next task code, and write back to task/queue       
       #strPickledObject = jsonpickle.encode(objCommonTaskMessage)
       #pickler1 = jsonpickle.Pickler() 
       #strPickledObject = pickler1.flatten(objCommonTaskMessage) 

       strPickledObject = jsonpickle.encode(objCommonTaskMessage) 

       #strPickledObject = json1.dumps(objCommonTaskMessage) 
       taskqueue.add(url='/commonTaskHandler', 
               method='Post',
               payload = str(strPickledObject)
               )  
       msg = """
          <h1>ProcessCode=&processCode stored to default queue</h1><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
          """
       msg = msg.replace("&processCode",processCode)
       self.response.out.write(msg) 
       self.response.out.write("<br/><br/> at time=" + str(datetime.datetime.now())) 

    
class TaskHandler(webapp.RequestHandler):
  """
  Tasks written to the TaskQueue, for purposes of this test, 
  always go to url /taskHandler?task=add&value1=5&value2=10
  """
  def post(self):

     debugText = "" 
     for item in self.request.arguments():
        debugText += "  Item=" + item + " value=" + self.request.get(item)


     if self.request.get("task") <= " ":
         raise "Parm task missing on Post debugText=" + str(debugText)
     if self.request.get("value1") <= " ":
         raise "Parm task missing on Post"
     if self.request.get("value2") <= " ":
         raise "Parm task missing on Post"

     task = self.request.get('task') 
     value1 = self.request.get('value1') 
     value2 = self.request.get('value2') 

     if task not in ['add', 'multiply']:
         raise "task not defined "

     if task == "add": 
        response = int(value1) + int(value2) 
        request = str(value1) + "+" + str(value2) 

     if task == "multiply": 
        response = int(value1) * int(value2) 
        request = str(value1) + "*" + str(value2) 
    
     #save results in database 
     taskQueueResults = TaskQueueResults() 
     taskQueueResults.task     = task
     taskQueueResults.request  = str(request)
     taskQueueResults.response = str(response)
     taskQueueResults.put() 


     query = TaskQueueSeq.gql("WHERE currentTask = :1", task)
     LIMIT = 10
     taskQueueSeqList = query.fetch(LIMIT,offset=0);      
     if len(taskQueueSeqList) < 1:
         raise "Missing ?task=xxxx on URL"

     #now based on our database, kick off the next logical task in the sequence 
     nextTask =  taskQueueSeqList[0].nextTask 
     if nextTask != "END":
        taskqueue.add(url='/taskHandler', 
            params={'task': nextTask, 'value1': value1, 'value2': value2})

    

class StoreTaskQueueSeq(webapp.RequestHandler):

  def get(self):

     taskQueueSeq1 = TaskQueueSeq()
     taskQueueSeq1.currentTask = "add"
     taskQueueSeq1.nextTask    = "multiply"
     taskQueueSeq1.put() 

     taskQueueSeq2 = TaskQueueSeq()
     taskQueueSeq2.currentTask = "multiply"
     taskQueueSeq2.nextTask    = "END"
     taskQueueSeq2.put() 

     self.response.out.write("""
          <h1>StoreTaskQueueSeq Completed - Use Admin Tool to View Rows</h1><br><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
      """)


class StoreSubscribers(webapp.RequestHandler):

  def get(self):


     sub1 = Subscriber(); 
     sub1.firstname = "test-fn"
     sub1.lastname = "test-ln"
     sub1.address1 = "1234 Elm Street"
     sub1.city = "Dallas"
     sub1.state = "TX" 
     sub1.userEmail = "nwalters@sprynet.com" 
     sub1.userPassword = "temp1234"
     sub1.put(); 

     self.response.out.write("""
          <h1>StoreSubscribers Completed - Use Admin Tool to View Rows</h1><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
      """)

class StoreRowsOld(webapp.RequestHandler):

  def get(self):
     worker1 = Workers(); 
     worker1.workerEmail = 'nwalters@3WCloud.com'.lower(); 
     worker1.workerLastName          = 'Walters'
     worker1.workerFirstName         = 'Neal'
     worker1.workerTitle             = 'Co-Owner'
     worker1.workerStatus            = 'Available'
     worker1.workerPassword          = 'test1234' 
     worker1.workerIsAdmin           = False

     worker1.dateTimeCreated         = datetime.datetime.now(); 
     worker1.dateTimeLastModified    = datetime.datetime.now(); 
     worker1.userEmailCreated        = 'nwalters@3WCloud.com';
     worker1.userEmailLastModified   = 'nwalters@3WCloud.com';
     worker1.put(); 

     self.response.out.write("""
          <h1>StoreRows CustomerOrders Completed - Use Admin Tool to View Rows</h1><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
      """)

     cust1 = CustomerOrders();
     cust1.domain                  = 'test.com'
     cust1.processCode             = 'xCloud'
     cust1.lastname                = 'Doe'
     cust1.firstname               = 'John'
     cust1.companyname             = 'ABC Enterprises' 
     cust1.email                   = 'jd@hotmail.com'
     cust1.orderDateTime           = datetime.datetime.now();
     cust1.xmldata                 = '<customerOrder></customerOrder>'
     cust1.put(); 

     task1 = Tasks(); 
     task1.taskCode                = 'AGA';
     task1.taskDescription         = 'Add Google Account'
     task1.sequence                = 100;
     task1.estimatedCompletionTime = 7  #minutes 
     task1.dateTimeCreated         = datetime.datetime.now(); 
     task1.dateTimeLastModified    = datetime.datetime.now(); 
     task1.userEmailCreated        = 'nwalters@3WCloud.com';
     task1.userEmailLastModified   = 'nwalters@3WCloud.com';
     task1.processCode             = 'xCloud'; 
     task1.put(); 

     task2 = Tasks(); 
     task2.taskCode                = 'VerDom';
     task2.taskDescription         = 'Verify Domain (using CNAME)'
     task2.sequence                = 200;
     task2.estimatedCompletionTime = 5  #minutes 
     task2.dateTimeCreated         = datetime.datetime.now(); 
     task2.dateTimeLastModified    = datetime.datetime.now(); 
     task2.userEmailCreated        = 'nwalters@3WCloud.com';
     task2.userEmailLastModified   = 'nwalters@3WCloud.com';
     task2.processCode             = 'xCloud'; 
     task2.put(); 

     worker1 = Workers(); 
     worker1.workerEmail = 'nwalters@3WCloud.com'.lower();  
     worker1.workerLastName          = 'Walters'
     worker1.workerFirstName         = 'Neal'
     worker1.workerTitle             = 'Co-Owner'
     worker1.workerStatus            = 'Available'
     worker1.dateTimeCreated         = datetime.datetime.now(); 
     worker1.dateTimeLastModified    = datetime.datetime.now(); 
     worker1.userEmailCreated        = 'nwalters@3WCloud.com';
     worker1.userEmailLastModified   = 'nwalters@3WCloud.com';
     worker1.put(); 

     worker2 = Workers(); 
     worker2.workerEmail = 'nwalters@3WCloud.com'.lower(); 
     worker2.workerLastName          = 'Pinto'
     worker2.workerFirstName         = 'Filipe'
     worker2.workerTitle             = 'Co-Owner'
     worker2.workerStatus            = 'Available'
     worker2.dateTimeCreated         = datetime.datetime.now(); 
     worker2.dateTimeLastModified    = datetime.datetime.now(); 
     worker2.userEmailCreated        = 'nwalters@3WCloud.com';
     worker2.userEmailLastModified   = 'nwalters@3WCloud.com';
     worker2.put(); 

     
     self.response.out.write("""
          <h1>StoreRows Completed - Use Admin Tool to View Rows</h1><br>
          <a href=''>Back to Home Page</a>&nbsp;&nbsp;
          <a href="report">Report</a>
      """)


class ReportTaskLogs(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def post(self):
     ReportTaskLogs.get(self);

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     #if self.hasValidUser():
     customerDomain = self.request.get("customerDomain")
     if customerDomain != 'ALL':
       query = TaskLog.gql("WHERE customerDomain = :1", customerDomain);  # get matching customerDomain 
     else:
       query = TaskLog.gql("");  # get all rows 
     LIMIT = 1000
     TaskLogs = query.fetch(LIMIT,offset=0);


     #if TaskLogs.count(TaskLog) > 0:
     #self.renderPage('templates/reportTaskLogs.html', {"TaskLogs": TaskLogs}) 

     params = {}
     params = commonUserCode(params,self.request.url)
     debugText = ""

     query = CustomerOrders.gql("")  #no where clause needed
     LIMIT = 1000
     customerOrdersList = query.fetch(LIMIT,offset=0);


     self.renderPage('templates/reportTaskLogs.html', 
                     {"TaskLogs": TaskLogs, 
                      "userMessage": params['userMessage'],
                      "sign_in": params['sign_in'],
                      "sign_out": params['sign_out'],
                      "user": params['user'],
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "customerDomain": customerDomain,
                      "customerOrdersList": customerOrdersList, 
                      "debugText": debugText,
                      "now": datetime.datetime.now()
                      }
                     ) 
        


#end of class 


class CustomersXml(webapp.RequestHandler):

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     query = CustomerOrders.gql("")  #no where clause needed
     LIMIT = 1000
     customerOrdersList = query.fetch(LIMIT,offset=0);
     self.response.headers['Content-Type'] = "text/xml"
     self.response.out.write("<CustomerOrders>") 
     for custOrd in customerOrdersList:
        #self.response.out.write(stripTags(custOrd.to_xml()));  #don't strip tags if content text/xml
        self.response.out.write(custOrd.to_xml());
     self.response.out.write("</CustomerOrders>") 

class TasksXml(webapp.RequestHandler):

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     query = Tasks.gql("")  
     LIMIT = 1000
     taskList = query.fetch(LIMIT,offset=0);
     self.response.headers['Content-Type'] = "text/xml"
     self.response.out.write("<Tasks>") 
     for task in taskList:
        self.response.out.write(task.to_xml());
     self.response.out.write("</Tasks>") 

class TaskLogsXml(webapp.RequestHandler):

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     query = TaskLog.gql("")  #no where clause needed
     LIMIT = 1000
     taskLogList = query.fetch(LIMIT,offset=0);
     self.response.headers['Content-Type'] = "text/xml"
     self.response.out.write("<TaskLogs>") 
     for tasklog in taskLogList:
        self.response.out.write(tasklog.to_xml());
     self.response.out.write("</TaskLogs>") 

class XmlExtract(webapp.RequestHandler):

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     tableName = self.request.get("tablename")
     query = db.GqlQuery("SELECT * FROM " + tableName);
     LIMIT = 1000
     recordsRetrievedList = query.fetch(LIMIT,offset=0);
     self.response.headers['Content-Type'] = "text/xml";
     self.response.out.write("<" + tableName + ">"); 
     for item in recordsRetrievedList:
        self.response.out.write(item.to_xml());
     self.response.out.write("</" + tableName + ">");



class Menu(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     params = {}
     params = commonUserCode(params,self.request.url)

     self.renderPage('templates/menu.html', 
                     {"userMessage": params['userMessage'],
                      "sign_in": params['sign_in'],
                      "sign_out": params['sign_out'],
                      "user": params['user'],
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "customerDomain": params['customerDomain'],
                      "now": datetime.datetime.now()
                      }
                     ) 


class Main(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     params = {}
     params = commonUserCode(params,self.request.url)

     self.renderPage('templates/main.html', 
                     {"userMessage": params['userMessage'],
                      "sign_in": params['sign_in'],
                      "sign_out": params['sign_out'],
                      "user": params['user'],
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "customerDomain": params['customerDomain'],
                      "now": datetime.datetime.now()
                      }
                     ) 



class UpdateCustomerOrder(webapp.RequestHandler):

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
        custord = CustomerOrders.get(self.request.get('key')) 
     else: 
        #set fields so they don't all say "None" 
        custord = CustomerOrders() 
        custord.domain = ''
        custord.companyname = ''
        custord.email = ''
        custord.firstname = ''
        custord.lastname = ''
        custord.processCode = ''
        custord.orderDateTime = datetime.datetime.now()
        custord.key = ''

     #self.response.out.write("got here")
     #return
     self.renderPage('templates/updateCustomerOrder.html', 
                     {"userMessage": params['userMessage'],
                      "sign_in": params['sign_in'],
                      "sign_out": params['sign_out'],
                      "user": params['user'],
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "currentUser": currentUser,
                      "custord":custord, 
                      "debugText": debugText,
                      "now": datetime.datetime.now()
                      }
                     ) 

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = mySession['username'] 

     #TODO - need to check no duplicate domain name/product combo before storing a potential duplicate one 

     #for add, create new object, for update, get data from database 
     if self.request.get('key') > ' ': 
        custord = CustomerOrders.get(self.request.get('key')) 
     else: 
        #set fields so they don't all say "None" 
        custord = CustomerOrders()

     #now set fields 
     custord.domain = self.request.get('domain')
     custord.companyname = self.request.get('companyname')
     custord.email = self.request.get('email')
     custord.firstname = self.request.get('firstname')
     custord.lastname = self.request.get('lastname')
     custord.processCode = self.request.get('processCode')
     formdate = self.request.get('orderDateTime')
     custord.orderDateTime = datetime.datetime.fromtimestamp(fixdate(formdate));
     custord.userEmailCreated = currentUser 

     custord.put() 

     debugText = debugText + "&nbsp;&nbsp; Put()" 
     self.redirect("/menu")


     #self.renderPage('templates/updateCustomerOrder.html', 
     #                {"userMessage": params['userMessage'],
     #                "sign_in": params['sign_in'],
     #                 "sign_out": params['sign_out'],
     #                 "user": currentUser,
     #                "environment": params['environment'],
     #                 "is_admin": str(mySession['isAdmin']),
     #                 "currentUser": currentUser,
     #                "custord":custord, 
     #                 "debugText": debugText,
     #                 "now": datetime.datetime.now()
     #                 }
     #                ) 






class MyProfile(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()
     from addressHelpers import states 
     from addressHelpers import continents 
     from addressHelpers import countries
     from addressHelpers import timezones
     from addressHelpers import cellproviders 

     if not 'subscriberkey' in mySession:
        self.response.out.write("<h3>Session data - please login</h3>") 
        self.redirect("/login")    
        return 

     subscriberkey = mySession['subscriberkey']
     subscriber = Subscriber.get(subscriberkey) 

     #make sure the previously selected timezone shows up as the value in the select/list 
     for timezone in timezones:
        if timezone.value == subscriber.timezone: 
           timezone.selected = True 
        else:
           timezone.selected = False  

     #make sure the previously selected cellprovider shows up as the value in the select/list 
     #for cellprovider in cellproviders:
     #   if cellprovider.value == subscriber.cellprovider: 
     #      cellprovider.selected = True 
     #   else:
     #      cellprovider.selected = False 

     #make sure the previously selected state shows up as the value in the select/list 
     for state in states:
        if state.value == subscriber.state: 
           state.selected = True 
        else:
           state.selected = False 

     #make sure the previously selected country shows up as the value in the select/list 
     for country in countries:
        if country.value == subscriber.country: 
           country.selected = True 
        else:
           country.selected = False 


     templateDictionaryLocal = {"subscriber": subscriber,
                      "timezones": timezones, 
                      "states": states,
                      "countries": countries,
                      "continents": continents
                      }
                               
     serviceCode = "" 
     page = "" 
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/myProfile.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = mySession['username'] 

     #TODO - need to check no duplicate domain name/product combo before storing a potential duplicate one 

     #modify only - no add from here 
     subscriber = Subscriber.get(self.request.get('key')) 
     subscriber.userEmailLastModified = currentUser 
     subscriber.dateTimeLastModified = datetime.datetime.now()

     #now set fields 
     subscriber.userEmail           = self.request.get('userEmail') 
     # todo - create a separate password reset function 
     subscriber.firstname           = self.request.get('firstname')   
     subscriber.lastname            = self.request.get('lastname')   
     subscriber.organizationname    = self.request.get('orgname')   
     subscriber.address1            = self.request.get('address1')       
     subscriber.address2            = self.request.get('address2')      
     subscriber.city                = self.request.get('city')       
     subscriber.state               = self.request.get('state')       
     subscriber.zip                 = self.request.get('zip')       
     subscriber.country             = self.request.get('country') 
     subscriber.phone               = self.request.get('phoneland')       
     #subscriber.phoneland           = self.request.get('phoneland')       
     #subscriber.phonecell           = self.request.get('phonecell')       
     #subscriber.cellprovider        = self.request.get('cellprovider')       
     #subscriber.cellproviderother   = self.request.get('cellproviderother')       
     subscriber.timezone            = float(self.request.get('timezone')) 
     subscriber.put()
     
     #self.response.out.write("country=" + subscriber.country) 
     #return 

     log = CumulusLog()    
     log.category = "MyProfile:Post" 
     log.ipaddress = self.request.remote_addr 
     log.message = "Customer updated profile:" + subscriber.userEmail 
     log.put() 

     self.redirect("/myHome")    


#=======================================================
# START of Updates 
#=======================================================


class UpdateWorker(webapp.RequestHandler):

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
        worker = Workers.get(self.request.get('key')) 
     else: 
        #set fields so they don't all say "None" 
        worker = Workers() 
        worker.workerEmail = ''
        worker.workerFirstName = ''
        worker.workerLastName = ''
        worker.workerStatus = 'Available'
        worker.workerTitle = ''
        worker.key = ''

     templateDictionaryLocal = {"worker": worker,}
                               
     templateDictionaryGeneral = getSharedTemplateDictionary("/reportWorkers",self.request.url) 
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/updateWorker.html', templateDictionaryLocal)
                     

  def post(self):
     debugText = "" 
     mySession = Session()
     # no need to worry about SQL injection if you do this type of GQL: 
     # http://groups.google.com/group/google-appengine/browse_thread/thread/292cf47de337d709/c1b208f1516e11ea?lnk=gst&q=injection#c1b208f1516e11ea
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = mySession['username'] 

     #TODO - need to check no duplicate domain name/product combo before storing a potential duplicate one 

     #for add, create new object, for update, get data from database 
     if self.request.get('key') > ' ': 
        worker = Workers.get(self.request.get('key')) 
        worker.userEmailLastModified = currentUser 
        worker.dateTimeLastModified = datetime.datetime.now()
     else: 
        #set fields so they don't all say "None" 
        worker = Workers()
        worker.userEmailCreated = currentUser 
        worker.dateTimeCreated = datetime.datetime.now()

     #now set fields 
     worker.workerEmail = self.request.get('email')
     worker.workerFirstName = self.request.get('firstname')
     worker.workerLastName = self.request.get('lastname')
     worker.workerStatus = self.request.get('status')
     worker.workerTitle = self.request.get('title')
     worker.workerPassword = self.request.get('password')
     worker.put() 

     debugText = debugText + "&nbsp;&nbsp; Put()" 
     self.redirect("/menu")    






class SubscriberAdmin(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()
     user = loggedin(self)

     subscriberkey = self.request.get('subscriberkey')
     if  subscriberkey < ' ': 
        self.response.out.write("<h3>Key not found on URL</h3>") 
        return 

     isAdmin = False 
     if 'isAdmin' in mySession:
         isAdmin = mySession['isAdmin']

     if not isAdmin: 
        self.response.out.write("<h3>Admin Authority Required to Perform this Function</h3>") 
        return 

     subscriber = Subscriber.get(subscriberkey) 
     if not subscriber: 
        self.response.out.write("<h3>Subscriber not found with key on URL</h3>") 
        return 
        

    
     command = self.request.get("command") 
     if command == "MakeAdmin": 
        subscriber.isAdmin = True 
        subscriber.put() 
        self.response.out.write("<h3>Changed subscriber to isAdmin=True</h3>")
        return 
     elif command == "RemoveAdmin": 
        subscriber.isAdmin = False 
        subscriber.put() 
        self.response.out.write("<h3>Changed subscriber to isAdmin=False</h3>")
        return 
     elif command == "MakeStaff": 
        subscriber.isWorker = True 
        subscriber.put() 
        self.response.out.write("<h3>Changed subscriber to isWorker=True</h3>")
        return 
     elif command == "RemoveStaff": 
        subscriber.isWorker = False 
        subscriber.put() 
        self.response.out.write("<h3>Changed subscriber to isWorker=False</h3>")
        return 
     else: 
        self.response.out.write("<h3>Unrecognized Command</h3>")
        return 
        

#=======================================================
# End of Updates 
#=======================================================

#=======================================================
# Start of WebServices 
#=======================================================


class GetSubscribers(webapp.RequestHandler):
  def get(self):
     #query = db.GqlQuery("SELECT * FROM Subscriber WHERE serviceCode = :1", "oneCloudI") 
     query = db.GqlQuery("SELECT * FROM Subscriber") 
     LIMIT = 1000
     subscriberList = query.fetch(LIMIT,offset=0)

     #for subscriber in subscriberList:
         #was trying to provide missing fields in order to use Django built-in serializer 
         #objmeta = _meta() 
         #setattr(subscriber,"_meta",objmeta) 
         #setattr(subscriber,"_get_pk_val","")
     
     #json = serializers.serialize("json", subscriberList) 
     pickler1 = jsonpickle.Pickler() 

     json = pickler1.flatten(subscriberList) 
     self.response.headers['Content-Type'] = "application/json";
     self.response.out.write(json) 

     #return HttpResponse(json, mimetype="application/json") 

#=======================================================
# End of WebServices 
#=======================================================


#=======================================================
# Start of Test Routines 
#=======================================================

#several proof of concept methods 
class TestGuid(webapp.RequestHandler):

  def get(self):

    guid = str(uuid.uuid4())
    self.response.out.write("Guid=" + guid) 



class TestPutKey(webapp.RequestHandler):

  def get(self):

     #shows that we can store a row in table and get it's key immediately after 
     session = CumulusSession() 
     session.dateTimeCreated = datetime.datetime.now() 
     session.dateTimeModified = session.dateTimeCreated

     session.domain            = "TestDomain.com"
     session.put() 
     self.response.out.write(session.key())




                                          
class TestGetByParents(webapp.RequestHandler):

  def get(self):
     
                    
     query = db.GqlQuery("SELECT * FROM ServiceType WHERE serviceCode = :1","oneCloudVideo2") 
     LIMIT = 10
     serviceTypeListParent = query.fetch(LIMIT,offset=0)

     parentKey = serviceTypeListParent[0].key()
     query2 = db.GqlQuery("SELECT * FROM ServiceType WHERE ancestor is :1",parentKey) 
     serviceTypeListChildren = query2.fetch(LIMIT,offset=0) 
     for serviceType in serviceTypeListChildren:
        self.response.out.write("code=" + serviceType.serviceCode + "<BR>") 
     



class ResumeDownload(webapp.RequestHandler):
  """
  Allow admin to download a resume that a oneCloudIndividual submitted
  """

  def get(self):
   
     key = self.request.get("servicekey")
     if key < " ":
        self.response.out.write("<h3>No ?servicekey= parameter found on the URL <h3>") 
        return 

     service = Service.get(key) 
     if not service: 
        self.response.out.write("<h3>Service not found with key=" + key + "<h3>") 
        return 

     if not isinstance(service,ServiceOneCloud): 
        self.response.out.write("<h3>This service is not of type 'ServiceOneCloud' and may not have a resume.<h3>") 
        return 

     # content-type for Microsoft Word Doc (resume) = "application/msword" 
     # see: http://www.w3schools.com/media/media_mimeref.asp 
     self.response.headers['Content-Type'] = "application/msword"
     self.response.out.write(service.resume)  


class ClearSession(webapp.RequestHandler):

  def get(self):

     mySession = Session()
     mySession.clear() 
     log = CumulusLog()    
     log.category = "ClearSessionf:Get" 
     log.ipaddress = self.request.remote_addr 
     log.message = "" 
     log.put() 

     self.response.out.write("<h3>Session State has been Cleared</h3>")
     self.response.out.write("Login again here: <a href='/login'>Customer Login</a>")  
     self.response.out.write(" OR: <a href='/formHandler?serviceCode=1CloudI&page=1'>Fill out a new oneCloud Individual setup form</a>")  


class TestPhoto(webapp.RequestHandler):

  def get(self):

     self.response.out.write("<h3>Start Demo 1 User Photo</h3>")
     self.response.out.write("<img src='userPhoto'>")
     self.response.out.write("<h3>End Demo 1 User Photo</h3>")

     self.response.out.write("<h3>Start Demo 2 User Photo</h3>")
     self.response.out.write("<img src='userPhotoFromService?key=ahgzd2Nsb3VkLWNvbS1wcm92aXNpb25pbmdyDwsSB1NlcnZpY2UY3JQBDA'>")
     self.response.out.write("<h3>End Demo 2 User Photo</h3>")




def localtime(offset):
     currdatetime = datetime.datetime.now() 
     return  currdatetime.replace(hour = currdatetime.hour + offset)


class TestCommonEmail(webapp.RequestHandler):
  """
   Test the template/render and common/email in dbModels.py 
  """
  def get(self):
     commonEmail = CommonEmail()
     emailTitle = "3WCloud.com Test Common Email" 
     templateName = "templates/customer/email_welcome.html"
     to = "nwalters@sprynet.com"
     firstname = "Neal" 
     commonEmail.sendMailFromTemplate(to, firstname, emailTitle, templateName) 
      
     self.response.out.write("<h2>End TestCommonEmail") 


class TestPaypalButton(webapp.RequestHandler):
  """
  Experimenting with different ways to detect that the user clicked on the Paypal image 
  instead of a regular "Submit" button 
  """
  def get(self):
      self.response.out.write("<form name='myform' method='post' action='/testPaypalButton'>")  
      self.response.out.write("<br><input type=image value='submit' src='https://fpdbs.paypal.com/dynamicimageweb?cmd=_dynamic-image&pal=4K4HRRVKBJNJU'>")
      self.response.out.write("<input type='hidden' name='submit' value='submit'>")
      self.response.out.write("<a href='javascript:document.myform.submit()' onclick='return val_form_this_page()'>")
      self.response.out.write("<br><img src='https://fpdbs.paypal.com/dynamicimageweb?cmd=_dynamic-image&pal=4K4HRRVKBJNJU'>")
      self.response.out.write("</form>") 

  def post(self):
      self.response.out.write("<BR>submit=" + self.request.get("submit") ) 
      self.response.out.write("<BR>image="  + self.request.get("image") )
      #show x/y coordinates of where on image user clicked (for <input type='image'... 
      self.response.out.write("<BR>x="  + self.request.get("x") )
      self.response.out.write("<BR>y="  + self.request.get("y") )


class TestPaypalRecurringPayment(webapp.RequestHandler):

  def get(self):

     amount = 100.00 
     itemName = "OneCloud" 
     currencyCode = "USD"
     paymentAction = "Sale"
     returnURL =  atom.url.Url('http', settings.HOST_NAME, path='/paid')
     cancelURL =  atom.url.Url('http', settings.HOST_NAME, path='/paidnot')

     invoice = "12345"   #pass the order-id to Paypal so Paypal will pass it back to the returnURL 

     returnURL       =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalCompleted?parm1=1'))
     cancelReturnURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalFailure'))
     notifyURL       =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalIPN'))


     paypalForm = getCommonPaypalForm(False)  #parm tells to hide all fields 

     objKeyValuePair = KeyValuePair() 
     imageURL   = objKeyValuePair.getValueFromKey("Paypal_Image_URL") 
     PaypalMode = objKeyValuePair.getValueFromKey("PaypalMode") 
     business = "temp"  #set variable outside of scope 
     oneTimeAmount = 0 
     recurringAmount = 0 
     paypalPostAction = "temp"

     self.response.out.write("<h3> PaypalMode=" + PaypalMode + "<h3>") 

     if PaypalMode.upper() == "TEST": 
        oneTimeAmount   = 25.00
        recurringAmount = 12.00
        paypalPostAction = objKeyValuePair.getValueFromKey("Paypal_URL_Sandbox") 
        business = objKeyValuePair.getValueFromKey("Paypal_Seller_Account_Sandbox") 
        self.response.out.write("<h3> Test PayPal Seller Account:Business=" + business + "<h3>") 
     elif PaypalMode.upper() == "PROD":
        oneTimeAmount   = 25.00
        recurringAmount = 12.00
        paypalPostAction = objKeyValuePair.getValueFromKey("Paypal_URL_Production") 
        business = objKeyValuePair.getValueFromKey("Paypal_Seller_Account_Production") 
        self.response.out.write("<h3> Prod PayPal Seller Account:Business=" + business + "<h3>") 
     else:
        self.response.out.write("<h2>PaypalMode=" + PaypalMode + " but expecting value of 'PROD' or 'TEST' </h2>") 
        return 
       
        
     billingPeriod   = "M"
     billingInterval = "1"

     productName = "One Cloud Individual-Test"
     itemName    = "One Cloud Individual-Test"

     if self.request.url.startswith("https"):
        httpOrHttps = "https"
     else: 
        httpOrHttps = "http"

     returnURL       =  str(atom.url.Url(httpOrHttps, settings.HOST_NAME, path='/PaypalCompleted?parm1=1'))
     cancelReturnURL =  str(atom.url.Url(httpOrHttps, settings.HOST_NAME, path='/PaypalFailure'))
     notifyURL       =  str(atom.url.Url(httpOrHttps, settings.HOST_NAME, path='/PaypalIPN'))

     #substitute variable in the big form above 
     #  any variables that are numbers must be wrapped with the str() function before being used in the replace! 
     paypalForm = paypalForm.replace("&imageURL",str(imageURL)) 
     paypalForm = paypalForm.replace("&business",str(business)) 
     paypalForm = paypalForm.replace("&returnURL",returnURL) 
     paypalForm = paypalForm.replace("&cancelReturnURL",cancelReturnURL) 
     paypalForm = paypalForm.replace("&oneTimeAmount",str(oneTimeAmount)) 
     paypalForm = paypalForm.replace("&recurringAmount",str(recurringAmount)) 
     paypalForm = paypalForm.replace("&cancelReturnURL",cancelReturnURL) 
     paypalForm = paypalForm.replace("&billingPeriod",billingPeriod) 
     paypalForm = paypalForm.replace("&billingInterval",str(billingInterval)) 
     paypalForm = paypalForm.replace("&productName",productName) 
     paypalForm = paypalForm.replace("&itemName",itemName)
     paypalForm = paypalForm.replace("&paypalPostAction",paypalPostAction) 
     paypalForm = paypalForm.replace("&invoice",invoice)
     #paypalForm = paypalForm.replace("&token",token)
     paypalForm = paypalForm.replace("&notifyURL",notifyURL)


     self.response.out.write("<h2>The form and button below submits a data form to Paypal</h2>") 
     self.response.out.write(paypalForm)


     

class TestPaypalPost(webapp.RequestHandler):

  def get(self):
     paypalForm = """
             <form action="https://www.paypal.com/us/cgi-bin/webscr" method="post">
                 <input type="hidden" name="cmd" value="_xclick-subscriptions" />
                 <input type="hidden" name="image_url" value="http://3wcloud.com/images/PaypalLogo.png" />
                 <input type="hidden" name="item_name" value="oneCloud-Individual" />
                 <input type="hidden" name="a3" value='0.01' />
                 <input type="hidden" name="p3" value='1' />
                 <input type="hidden" name="t3" value='M' />
                 <input type="hidden" name="a1" value='0.01' />
                 <input type="hidden" name="p1" value='1' />
                 <input type="hidden" name="t1" value='D' />
                 <input type="hidden" name="src" value='1' />
                 <input type="hidden" name="sra" value='1' />
                 <input type="hidden" name="on0" value='Subscription Option:' />
                 <input type="hidden" name="os0" value='$12 monthly membership ' />
                 <input type="hidden" name="on1" value='One Time Setup Fee' />
                 <input type="hidden" name="os1" value='$25 one time setup fee charged first day ' />
                 <input type="hidden" name="no_note" value='1' />
                 <input type="image" src="http://3wcloud.com/wp-content/plugins/wordpress-simple-paypal-shopping-cart/images/paypal_checkout.png" name="submit" alt="Make payments with PayPal - it's fast, free and secure!" />
                 <input type="hidden" name="return"        value="&returnURL" />
                 <input type="hidden" name="cancel_return" value="&cancelReturnURL" />
                 <input type="hidden" name="business" value="&business" />
                 <input type="hidden" name="currency_code" value="USD" />
                 <input type="hidden" name="upload" value="1" />
                 <input type="hidden" name="rm" value="2" />
             </form>
             """
     paypalForm = paypalForm.replace("&business",business) 
     paypalForm = paypalForm.replace("&returnURL",returnURL) 
     paypalForm = paypalForm.replace("&cancelReturnURL",cancelReturnURL) 
     self.response.out.write(paypalForm) 





class TestPaypalPostSuccess(webapp.RequestHandler):
  """
  This simulates a response from a successful Paypal checkout.
  It shows a form on the screen, the tester can change the values and click the submit button,
  to post data to /PaypalSuccess which will then process the data.  
  This was built by taking an actualy payment to Paypal, and capturing the data sent back.
  Then it was turned into a form, so we could type in diferent values to simulate a 
  result from Paypal. See 3WC.IT.Cumulus.Requirements for full list/sample of data returned 
  from Paypal.  The sample below only includes fields that we are likely to process, use,  
  and/or store in BigTable. 
  """ 

  def get(self):
     paypalForm = """
             <h1>Post data to /PaypalSuccess</h1>
             <form action="/PaypalCompleted" method="post">
             <table border=1>
             <tr><td>payer_email</td><td><input type="text" name="payer_email" size=30 value="nwalters@sprynet.com" /></td><tr>
             <tr><td>receiver_email</td><td><input type="text" name="receiver_email" size=30 value="ComTrans@m2msys.net" /></td><tr>
             <tr><td>business</td><td><input type="text" name="business" size=30 value="ComTrans@m2msys.net" /></td><tr>
             <tr><td>first_name</td><td><input type="text" name="first_name" value="Neal" /></td><tr>
             <tr><td>last_name</td><td><input type="text" name="last_name" value="Walters" /></td><tr>
             <tr><td>address_name</td><td><input type="text" name="address_name" size=30 value="Amerisoft Inc." /></td><tr>
             <tr><td>address_street</td><td><input type="text" name="address_street" size=30 value="1770 Plummer Dr." /></td><tr>
             <tr><td>address_city</td><td><input type="text" name="address_city" value="Rockwall" /></td><tr>
             <tr><td>address_state</td><td><input type="text" name="address_state" value="" /></td><tr>
             <tr><td>address_zip</td><td><input type="text" name="address_zip" value="75087" /></td><tr>
             <tr><td>address_country</td><td><input type="text" name="address_country" value="United States" /></td><tr>
             <tr><td>address_country_code</td><td><input type="text" name="address_country_code" value="US" /></td><tr>
             <tr><td>residence_country</td><td><input type="text" name="residence_country" value="" /></td><tr>
             <tr><td>mc_amount1</td><td><input type="text" name="mc_amount1" value="" /></td><tr>
             <tr><td>invoice</td><td><input type="text" name="invoice" value="" /></td><tr>
             <tr><td>payer_status value</td><td><input type="text" name="payer_status value" value="verified" /></td><tr>
             <tr><td>txn_type</td><td><input type="text" name="txn_type" value="subscr_signup" /></td><tr>
             <tr><td>address_status</td><td><input type="text" name="address_status" value="confirmed" /></td><tr>
             <tr><td>amount1</td><td><input type="text" name="amount1" value="0.01" /></td><tr>
             <tr><td>amount3</td><td><input type="text" name="amount3" value="0.01" /></td><tr>
             <tr><td>mc_amount3</td><td><input type="text" name="mc_amount3" value="0.01" /></td><tr>
             <tr><td>mc_currency</td><td><input type="text" name="mc_currency" value="USD" /></td><tr>
             <tr><td>subscr_date</td><td><input type="text" name="subscr_date" size=30  value="08:02:27 Jul 17, 2009 PDT" /></td><tr>
             <tr><td>reattempt</td><td><input type="text" name="reattempt" value="1" /></td><tr>
             <tr><td>period1</td><td><input type="text" name="period1" value="D" /></td><tr>
             <tr><td>period3</td><td><input type="text" name="period3" value="M" /></td><tr>
             <tr><td>merchantReturn.x</td><td><input type="text" name="merchantReturn.x" value="Return To Merchant" /></td><tr>
             <tr><td>verify_sign</td><td><input type="text" name="verify_sign" size=90 value="AcOuvvvFPlQkmaeXrB-PMTyQSqsbAsc0T8-JMHfjFdXd5VzObQtJbvj8" /></td><tr>
             <tr><td>auth value</td><td><input type="text" name="auth value" size=120 value="DUacgDpwJRZfil3RTaDAC0q1w3AvCRcr6dWtoOoGRSdGrCXiw3DbsOF4Fd06cOZuOH_dwmYNntdXcEwS" /></td><tr>
             <tr><td>payer_id</td><td><input type="text" name="payer_id" value="4K4HRRVKBJNJU" /></td><tr>
             <tr><td>recurring</td><td><input type="text" name="recurring" value="1" /></td><tr>
             <tr><td>notify_version</td><td><input type="text" name="notify_version" value="2.8" /></td><tr>
             <tr><td>charset</td><td><input type="text" name="charset" value="windows-1252" /></td><tr>
             <tr><td>form_charset</td><td><input type="text" name="form_charset" value="UTF-8" /></td><tr>
             <tr><td>&nbsp;</td><td><input type=submit></td></tr>
             </table>
             """

     self.response.out.write(paypalForm) 



class PaypalCompleted(webapp.RequestHandler):
  """
  When we send a customer to Paypal, we pass a returnURL /PaypalCompleted, and Paypal posts
  data back to this page (see documentation for a sample). 
  This allows us to flag the order as paid and store the appropriate ServiceRatePlan table. 
  Must read: http://www.pdncommunity.com/pdn/board/message?board.id=basicpayments&thread.id=368
  Data is posted here using "Get" as follows: 
  http://3wcloud-com-provisioning.appspot.com/PaypalCompleted?parm1=1&tx=4YS2961785975132E
  &st=Completed&amt=25.00&cc=USD&cm=&item_number=
  &sig=fM9xlVOhARLi2Dje%2fSyejSoeSdFA2eFAUdJ%2fiwxcBvWFoM3uFCqCLxtP%2fSHmZqoaR8Ox19J7idhFKDA9AI7MLqH8AEE2rXVfB%2bhKVjlH%2fLwGIZjUAbDj4QBIt1aJHpf%2fXhR1FhC4NgKk3niQwYiFjI5ZcXBEkIjMw2FE2f2r%2fzA%3d
  PDT Variables are documented here: 
  https://cms.paypal.com/us/cgi-bin/?cmd=_render-content&content_ID=developer/e_howto_html_IPNandPDTVariables
  """

  def get(self):
     #TODO - put paypal requirements here  
     #Paypal does not pass the invoice (order#) here, so we have to get it from Session variable

     mySession = Session() 

     objKeyValuePair = KeyValuePair() 
     PaypalMode = objKeyValuePair.getValueFromKey("PaypalMode") 
     paypalPostAction = "temp"
     identityToken = "temp" 

     import logging
     logging.debug("PaypalMode=" + str(PaypalMode)) 

     #NOTE: There is no currencyType in BigTable so amounts are stored as pennies! 
     #      So below we use the get methods that take care of the divide by 100 


     if PaypalMode.upper() == "TEST": 
        paypalPostAction = objKeyValuePair.getValueFromKey("Paypal_URL_Sandbox") 
        identityToken = objKeyValuePair.getValueFromKey("Paypal_PDT_Token_Sandbox") 
     elif PaypalMode.upper() == "PROD":
        paypalPostAction = objKeyValuePair.getValueFromKey("Paypal_URL_Production") 
        identityToken = objKeyValuePair.getValueFromKey("Paypal_PDT_Token_Production") 
     else:
        self.response.out.write("<h2>PaypalMode=" + PaypalMode + " but expecting value of 'PROD' or 'TEST' </h2>") 
        return 

     logging.debug("paypalPostAction=" + paypalPostAction) 

     #Call Paypal-API to validate that the transaction we received is legal
     #The transactoin we get, only has about 3 fields.  When we make the API call below,
     #we then receive back 20+ fields. 

     txValue = self.request.get("tx") 

     form_fields = {
         "cmd":            "_notify-synch",
         "tx":             txValue, 
         "at":             identityToken
     }

     import urllib 
     form_data = urllib.urlencode(form_fields)
     logging.debug("paypal form_data=" + form_data) 
     url = paypalPostAction

     from google.appengine.api import urlfetch
     result = urlfetch.fetch(url, payload=form_data, method=urlfetch.POST, headers={}, allow_truncated=False, follow_redirects=True, deadline=None)

     import logging
     logging.debug("PaypalCompleted:Response=" + result.content) 
     self.response.out.write("Paypal Response: " + result.content)
     
     #response should include the word "SUCCESS" or "FAIL" and the following name/value pairs: 
     #first_name, last_name, payment_status, payer_email, payment_gross, mc_currency, custom 
     #However, the data comes in one long screen, without & between them, only "\n"

     selectedContent = result.content

     if result.content.startswith("SUCCESS"):
        selectedContent = result.content[8:]


     if result.content.startswith("FAIL"):
        selectedContent = result.content[6:]
        #TODO - what else if it fails? This should only occur if fraudalent/spoofing situation 
        #   or program error.  
        self.response.out.write(results.content) 
        return 

     #Test code to find that this data was delimited by \n 
     #for j in range(0,45):
     #   char = selectedContent[j:j+1]
     #   logging.debug("j=" + str(j) + "  ascii=" + char + "  ascii=" + str(ord(char)))


     #resultDict = cgi.parse_qs(result.content)  #reverse of url.encode 

     #this is what the data actually looks like... with more fields 
     #selectedContent = "mc_gross=12.00\ninvoice=26305\nprotection_eligibility=Eligible"
     delimiter = "\n"   #line feed (but no carriage-return) 
     resultVars = selectedContent.split(delimiter) 
     logging.debug("len(resultVars)=" + str(len(resultVars))) 
     #debug only 
     for item in resultVars:
         logging.debug("item=" + item) 

     resultDict = {} 
     for item in resultVars:
         subSplit = item.split("=")    #get the left of = sign and the right of = sign 
         if len(subSplit) == 2:
            resultDict.update({subSplit[0]:subSplit[1]})
            #logging.debug(subSplit[0] + "=" + subSplit[1]) 
         #else:
            #the very last item in list will hit this situation 
            #logging.debug("length subsplit=" + str(len(subSplit)) + " on item=" + str(item)) 

     paypalIPN = PaypalIPN()    #database kind/table 
     paypalIPN.source = "PDT"   #payment direct transfer 

     for item in resultDict: 
        #self.response.out.write("<BR>" + item + "=" + resultDict[item])
        #PaypalDecode translates things like %3A to : and + to " " 
        setattr(paypalIPN, item, PaypalDecode(str(resultDict[item])))   
     paypalIPN.put()    

     self.response.out.write("<H1>PayPal Completed</H1>") 

     #we passed the id (not the key) to Paypal 
     id = int(resultDict['invoice']) 
     order = Order.get_by_id(id)            #retrieve existing non-paid order 
     if not order: 
        self.response.out.write("<h3>order not found with id=" + id + "<h3>") 
        return 

     #mark each service as paid amd store the serviceRatePlan connection 
     for service in order.services:
        serviceRatePlan = ServiceRatePlan()   
        serviceRatePlan.service = service 

        serviceRatePlan.ratePlan = service.holdRatePlan 
        serviceRatePlan.dateTimeCreated = datetime.datetime.now() 
        serviceRatePlan.paymentType     = "Paypal"

        #the following fields are all posted to this page from Paypal
        serviceRatePlan.payerEmail       = resultDict['payer_email']
        #serviceRatePlan.payerId         = self.request.get("payer_id")
        #serviceRatePlan.auth            = self.request.get("auth")
        serviceRatePlan.subscriptionId   = resultDict['subscr_id']
        serviceRatePlan.paymentStatus    = resultDict['payment_status']
        serviceRatePlan.put() 

     #because of redirect below - these two messages should not display 
     self.response.out.write("<h2>ServiceRatePlanStored </h2>") 

     if serviceRatePlan.paymentStatus == "Completed":
        order.financialStatus = "PayPal.paid"
     elif serviceRatePlan.paymentStatus == "Pending":
        order.financialStatus = "PayPal.pending"
     #supposed only two values are Completed and Pending, but just in case... 
     else:
        order.financialStatus = "PayPal." + serviceRatePlan.paymentStatus
     order.put() 
     self.response.out.write("<h2>FinancialStatus updated on Order Record </h2>") 

     if resultDict['payment_status'] == "Completed" and resultDict['payment_type'] == "instant":
        mySession['myHomeMessage'] = objKeyValuePair.getValueFromKey("msgPaypalPaid") 
     elif resultDict['payment_status'] == "Completed" and resultDict['payment_type'] == "echeck":
        mySession['myHomeMessage'] = objKeyValuePair.getValueFromKey("msgPaypalPending") 

     self.redirect("/myHome")
 

class PaypalFailure(webapp.RequestHandler):
  """
  When we send a customer to Paypal, we pass a returnURL /PaypalFailure, 
  if the user cancels before making the payment, Paypal returns to this page 
  (so far, I don't believe it posts any data)... so we just need to reroute them 
  some appropriate page with a message. 
  TODO: Probably need to set order.financialStatus to PayPal.user_cancelled
  but not sure how to get current order - unless we save in session variable. 
  """

  def get(self):
     self.response.out.write("<H3>PayPal Failure/GET</H3>") 
     #for item in self.request.arguments():
     #    self.response.out.write("<BR>" + item + " value=" + self.request.get(item)) 
     self.redirect("/myHome")

  def post(self):
     self.response.out.write("<H1>PayPal Success/POST</H1>") 
     for item in self.request.arguments():
         self.response.out.write("<BR>" + item + " value=" + self.request.get(item)) 
     #TODO - set a message and redirect to home page 



class PaypalIPNHandler(webapp.RequestHandler):
  """
  Designed to be used with this page:
  https://beta-developer.paypal.com/us/cgi-bin/devscr?cmd=_ipn-link-session
  Cannot post to localhost because we are behind router.  Can only test on appspot, such as:
  http://3wcloud-com-provisioning.appspot.com/PaypalIPN
  We simply store all their data into a BigTable row 
  NOTE: Since the database table/kind name is PaypalIPN, this web class 
  cannot have the exact same name. 
  """

  def get(self):
     self.response.out.write("<H1>PayPalIPN designed for POST only, but you tried GET</H1>") 

  def post(self):
     
     import logging 

     paypalIPN = PaypalIPN() 
     paypalIPN.source = "IPN"

     payment_status = "" 
     payment_type = "" 


     #use Expando class and setattr to create on-the-fly database columns 
     #setattr(x, 'foobar', 123) is equivalent to x.foobar = 123.
     for item in self.request.arguments():
        #turn of logging in loop to reduce CPU/resource utilization 
        #logging.debug("Item=" + item + " Value=" + str(self.request.get(item)))
        setattr(paypalIPN, item, self.request.get(item))

        #certain variables we need to act upon 
        if item == "txn_type": 
           txnType = self.request.get(item)
        if item == "invoice": 
           orderId = self.request.get(item)
        if item == "payment_type": 
           payment_type = self.request.get(item)
        if item == "payment_status": 
           payment_status = self.request.get(item)
            

     #store an audit-trail of all data sent from Paypal in table "PaypalIPN" 
     paypalIPN.put()  
     
     # if user cancels from Paypal website, the Paypal notifies us via the IPN interface, 
     # and we need to turn off his service. 
     # TODO: Need Business Process what to do in case of cancellation. 
     #       For example, what to email, what else to turn off 
     #       ask customer reason... etc... 
     #       Are there any human steps involved here, or totally automated. 

     order = Order.get_by_id(int(orderId)) 
     if not order:
           log = CumulusLog()  
           #TODO - create category or flag that says this item needs further research 
           log.category = "PaypalIPN:Post:MissingOrderId" 
           log.message = "OrderId= " + orderId + " not found, payment_type=" + payment_type + " payment_status" + payment_status
           log.ipaddress = self.request.remote_addr 
           log.put() 
           logging.info(log.category + " " + log.message)
           return 

     if txnType == "subscr_cancel":
        order.financialStatus = "PayPal.user_cancelled" 
        order.put()
        #Now store a new "delete" order which can start a business-process to perform 
	#the necessary steps of the cancellation (yet to be determined) 
	order2 = Order() 
	order2.orderDate = datetime.datetime.now() 
	order2.subscriber = order.subscriber 
	order2.domain = order.domain 
        order2.apiClientId = "PaypalIPN" 
        order2.orderType = "Cancel" 
	order2.priority = 3 #normal 
	order2.orderState = "open.not_running" 
	order2.put() 
	#now update the xref from the services to orders 
	#the original service had an "add" order, and now add the "cancel" order to its list of order keys 
        for service in order.services:
	    #import logging
	    #for orderx in service.orders: 
	    #   logging.debug("Existing order (before append)=" + orderx.id())
	    service.orders.append(order2.key())
	    #for orderx in service.orders: 
	    #   logging.debug("Orders After append=" + orderx.id())
	    service.put() 

     if payment_status == "Completed" and payment_type == "echeck": 
     #in this scenario - payment was received 3-5 days after original Paypal order
     #so we have to go back to order/service and update a few fields. 

     #TODO - the following is BAD - if order has many services - this could cause big problems.
     #probably need to pass rateplan key to Paypal and back 
     #serviceRatePlan.ratePlan = order.services[0].serviceType.ratePlan
     #serviceRatePlan.order = order 
        for service in order.services:
           query = ServiceRatePlan.gql('WHERE service = :1 ', service.key())
           LIMIT = 100 
           serviceRatePlanList = query.fetch(LIMIT,offset=0) 

           #serviceRatePlan was probably stored by the PDT in PaypalSuccess 
           if len(serviceRatePlanList) > 0:
              for serviceRatePlan in serviceRatePlanList: 
                 serviceRatePlan.paymentStatus    = payment_status
                 serviceRatePlan.put() 
           else: 
	   #but if not stored then, let's store it now 
              serviceRatePlan = ServiceRatePlan()   
              serviceRatePlan.service = service 

              serviceRatePlan.ratePlan        = service.holdRatePlan 
              serviceRatePlan.dateTimeCreated = datetime.datetime.now() 
              serviceRatePlan.paymentType     = "Paypal"

              #the following fields are all posted to this page from Paypal
              serviceRatePlan.payerEmail       = self.request.get('payer_email')
              serviceRatePlan.subscriptionId   = self.request.get('subscr_id')
              serviceRatePlan.paymentStatus    = self.request.get('payment_status')
              serviceRatePlan.put() 



     if payment_status == "Completed" : 
        order.financialStatus = "PayPal.paid"
     elif payment_status == "Pending":
        order.financialStatus = "PayPal.pending" 
     elif payment_status == "":
        #nothing to do when blank (usually associated with subscr_signup/subscr_cancel) 
        pass
     #supposedly the only two legal values are "Completed" and "Pending", but just in case... 
     else:
        #don't set this, because we have a "choice" limitation on this field in the db.model 
        #order.financialStatus = "PayPal." + serviceRatePlan.paymentStatus
        log = CumulusLog()  
        #TODO - create category or flag that says this item needs further research 
        log.category = "PaypalIPN:Post:UnexpectedStatus" 
        log.message = "OrderId= " + orderId + " unexpected payment status=" + payment_status 
        log.ipaddress = self.request.remote_addr 
        log.put() 

     order.put() 

     #Normally, PaypalIPN is called from Paypal and there is no user interface,
     #it just returns an http Status=200 to Paypal
     #but when testing by posting a test/form, the following messages can be useful. 

     #because of redirect below - these two messages should not display 
     self.response.out.write("<h2>ServiceRatePlanStored </h2>") 


# Here is list of txn_type's from the IPN developers guide: 
# Credit card chargeback if the case_type variable contains chargeback
#adjustment A dispute has been resolved and closed
#cart Payment received for multiple items; source is Express Checkout or the PayPal Shopping Cart.
#express_checkout Payment received for a single item; source is Express Checkout
#masspay Payment sent using MassPay
#merch_pmt Monthly subscription paid for Website Payments Pro
#new_case A new dispute was filed
#recurring_payment Recurring payment received
#recurring_payment_profile_created
#send_money Payment received; source is the Send Money tab on the PayPal website
#subscr_cancel Subscription canceled
#subscr_eot Subscription expired
#subscr_failed Subscription signup failed
#subscr_modify Subscription modified
#subscr_payment Subscription payment received
#subscr_signup Subscription started
#virtual_terminal Payment received; source is Virtual Terminal
#web_accept Payment received; source is a Buy Now, Donation, or Auction Smart Logos button

class TestPaypalOneTimePayment(webapp.RequestHandler):

  def get(self):

     amount = 100.00 
     itemName = "OneCloud" 
     currencyCode = "USD"
     paymentAction = "Sale"
     business = "nwalters@sprynet.com" 
     returnURL =  atom.url.Url('http', settings.HOST_NAME, path='/paid')
     cancelURL =  atom.url.Url('http', settings.HOST_NAME, path='/paidnot')

     paypalURL = "https://api.sandbox.paypal.com"       # sandbox/test server  
     paypalURL = "https://api.paypal.com"               # real non-production server 
     paypalURL = "https://www.paypal.com/cgi-bin/webscr" 

     token = "temp" #to be returned from prior API 
     imageURL = ""  # The URL of the 150x50-pixel image displayed as your logo in the upper left corner of the PayPal checkout pages.
                    # Default - Your business name, if you have a Business account, or your email address, if you have Premier or Personal account.


     #paypalURL = (paypalURL + "/webscr?cmd=_express-checkout&token=" + token + 
     #             "&image_url=" + str(imageURL) + 
     #             "&AMT=" + str(amount) + "&CURRENCYCODE=" + currencyCode + 
     #            "&PAYMENTACTION" + paymentAction + 
     #            "&RETURNURL=" + str(returnURL) + "&CANCELURL=" + str(cancelURL)) 

     #https://www.paypal.com/us/us/us/webscr?cmd=_express-checkout&token=temp&image_url=&AMT=100.0&CURRENCYCODE=USD&PAYMENTACTIONSale=&RETURNURL=http%3a//localhost%3a8080/paid&CANCELURL=http%3a//localhost%3a8080/paidnot&amount=100.0&item_nameOneCloud=&business=nwalters%40sprynet.com&return=http%3a//localhost%3a8080/paid&cancel_return=http%3a//localhost%3a8080/paidnot&PPREDIRECT=BdNlV9FjTzXL7DaHXpAT4ntPgWGj3JPPMB9kIvic7B9soSxCeHBdn6Ghe9G5XWXVL9btR2ZomY8aoYmAAnn28nBJ36FjtKOYc3wsLLDnkQrmkKx0IE1LSoPTSQHb9Lu02c2AZ9ubY5gqJRxEDWKs3hTy42BxTJDIPpH39k1BA10WMm-P3N0AY7MOWkae0b3e04IYYztNSHIQflgXlXzSTs6y8my6WvkNpNDc0tl72MUZ7pyy6izDjpT3sofIGzDorh2YJgnAdha5eUmtsUCThQgLnSGa09Xm1ivShVGTbCVDZL5RlzGq28kEkuaH0cb0gtwi60&dispatch=50a222a57771920b6a3d7b606239e4d529b525e0b7e69bf0224adecfb0124e9bdd7275a399ffdb50357d51bfcb4404a73fa1a53f5df1ed53
     #paypalURL = ( 
     #             "&image_url=" + str(imageURL) + 
     #             "&amount=" + str(amount) + 
     #            "&item_name" + itemName + 
     #            "&business=" + business + 
     #            "&return=" + str(returnURL) + 
     #            "&cancel_return=" + str(cancelURL)
     #            ) 

     paypalForm = """
             <form action="https://www.paypal.com/us/cgi-bin/webscr" method="post">
                 <input type="hidden" name="image_url" value="http://3wcloud.com/images/PaypalLogo.png" />
                 <input type="hidden" name="item_name_1" value="Basic iCloud Student Beta" />
                 <input type="hidden" name="amount_1" value='0.01' />
                 <input type="hidden" name="quantity_1" value="1" />
                 <input type='hidden' name='item_number' value='' />
                 <input type="hidden" name="shipping_1" value="0" />
                 <input type="image" src="http://3wcloud.com/wp-content/plugins/wordpress-simple-paypal-shopping-cart/images/paypal_checkout.png" name="submit" alt="Make payments with PayPal - it's fast, free and secure!" />
                 <input type="hidden" name="return" value="http://3wcloud.com" />
                 <input type="hidden" name="business" value="nwalters@sprynet.com" />
                 <input type="hidden" name="currency_code" value="USD" />
                 <input type="hidden" name="cmd" value="_cart" />
                 <input type="hidden" name="upload" value="1" />
             </form>
             """
     self.response.out.write("The button below submits a data form to Paypal<BR><BR>") 
     self.response.out.write(paypalForm)

     #instead of using above - to urlencode - we have to build dictionary 
     #url_fields = {
     #    "image_url":     str(imageURL),
     #    "amount":        str(amount),
     #    "item_name":     itemName,
     #    "business":      business,
     #    "return":        str(returnURL),
     #    "cancel_return": str(cancelURL)
     #    }


     #import urllib
     #self.response.out.write ("<BR>Encoded1=" + urllib.urlencode(url_fields) + "<BR>")
     #paypalURLEncoded = paypalURL + "?" + urllib.urlencode(url_fields)
     #self.response.out.write ("<BR>Encoded2=" + paypalURLEncoded + "<BR>")

     #self.response.out.write("<br><a href='" + paypalURLEncoded + "'>")
     #self.response.out.write("<br><img src='https://fpdbs.paypal.com/dynamicimageweb?cmd=_dynamic-image&pal=4K4HRRVKBJNJU'>")
     #self.response.out.write("</a>")
     

class PaypalAPI(webapp.RequestHandler):

  def callAPI(self, method, argDict):

     #credentials for Beta.Sandbox
     #api_username = "nealwa_1247851416_biz_api1.nealwalters.com"
     #api_password = "1247851425"
     #api_signature = "ACUe-E7Hjxmeel8FjYAtjnx-yjHAA7Q0j6LAsi8pll6JsJFZ4ZO3YVIe"

     #These important secret passwords are stored in database so they won't be visible in the code. 
     #Only someone with Admin access to DataViewer should be able to view or change these keys. 
     objKeyValuePair = KeyValuePair() 
     api_username  = objKeyValuePair.getValueFromKey("Paypal_API_Username") 
     api_password  = objKeyValuePair.getValueFromKey("Paypal_API_Password") 
     api_signature = objKeyValuePair.getValueFromKey("Paypal_API_Signature") 

     version = "58.0" 
     #url = "https://api-3t.paypal.com/nvp"               # real production server 
     url = "https://api-3t.beta-sandbox.paypal.com/nvp"       # sandbox/test server  



     form_fields = {
         "USER":           api_username,
         "PWD":            api_password,
         "SIGNATURE":      api_signature,
         "METHOD":         method,                
         "VERSION":        version
     }
     form_fields.update(argDict) 

     import urllib 
     form_data = urllib.urlencode(form_fields)

     #webapp.response.out.write("<H2>Passing these values</H2>") 
     #webapp.response.out.write("<BR>form_fields=" + str(form_data) + "<HR>") 
     #for item in form_fields:
     #   webapp.response.out.write("<BR>" + item + "=" + form_fields[item])

     from google.appengine.api import urlfetch
     result = urlfetch.fetch(url, payload=form_data, method=urlfetch.POST, headers={}, allow_truncated=False, follow_redirects=True, deadline=None)

     #unquote = urllib.unquote(result.content) 
     #webapp.response.out.write("<BR><BR>result unquoted=" + unquote) 
     #webapp.response.out.write("Result=" + str(result.content) + "<HR>") 

     resultDict = cgi.parse_qs(result.content) 

     #webapp.response.out.write("<BR><BR>")
     #for item in result.headers:
     #    webapp.response.out.write("<BR>" + item + "=" + str(result.headers[item])) 
     # above code displays the following headers/values 
     #date value=Fri, 17 Jul 2009 16:41:25 GMT
     #content-length value=236
     #content-type value=text/plain; charset=utf-8
     #connection value=close
     #server value=Apache

     return resultDict 



  def getToken(self, argAmount):

     method = "SetExpressCheckout" 
     #not sure why these two returnURL fields are required, but get error if they are omitted 
     returnURL       =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalSuccess'))
     cancelReturnURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalFailure'))


     additional_form_fields_dict = {
         "NOSHIPPING":     "1",                     #1= no shipping address fields shown in Paypal pages 
         "ReturnURL":      returnURL,
         "CancelURL":      cancelReturnURL,
         "AMT":            argAmount,
         "L_BILLINGTYPE0": "MerchantInitiatedBilling"
         }

     resultDict = self.callAPI(method, additional_form_fields_dict) 

     if 'TOKEN' in resultDict: 
        return resultDict['TOKEN'][0]  
     else:
        errorMsg = ""
        for item in resultDict: 
            errorMsg += "<BR>" + item + "=" + str(resultDict[item][0])
        raise errorMsg 


class StoreKeyValues(webapp.RequestHandler):
  """
  http://site/storeKeyValues?key=ALL  to store all keys here 
  http://site/storeKeyValues?key=5  with some specific key # 
  """

  def get(self):

     key = self.request.get("key")

     if key == "ALL" or key == "1":
       kvp1 = KeyValuePair() 
       kvp1.kvpKey = "Paypal_Seller_Account_Sandbox" 
       kvp1.kvpValue = "test1_1248285054_biz@nealwalters.com"
       kvp1.kvpIsSecure = False  
       kvp1.put() 
       self.response.out.write("<BR>Stored " + kvp1.kvpKey)

     if key == "ALL" or key == "2":
       kvp2 = KeyValuePair() 
       kvp2.kvpKey = "Paypal_Seller_Account_Production" 
       kvp1.kvpValue = "ComTrans@m2msys.net"
       kvp2.kvpIsSecure = False 
       kvp2.put() 
       self.response.out.write("<BR>Stored " + kvp2.kvpKey)

     if key == "ALL" or key == "3":
       kvp3 = KeyValuePair() 
       kvp3.kvpKey = "Paypal_Image_URL" 
       kvp3.kvpValue = "http://3wcloud.com/images/PaypalLogo.png"
       kvp3.kvpIsSecure = False  
       kvp3.put() 
       self.response.out.write("<BR>Stored " + kvp3.kvpKey)

     if key == "ALL" or key == "4":
       kvp4 = KeyValuePair() 
       kvp4.kvpKey = "isServiceDeleteEnabled" 
       kvp4.kvpValue = "True"  #this is a string, not a boolean  
       kvp4.kvpIsSecure = False  
       kvp4.kvpDoc = "When set to 'True', allows admin to delete Services (and associated order).  When set to 'False', even Admin cannot delete services." 
       kvp4.put() 
       self.response.out.write("<BR>Stored " + kvp4.kvpKey)

     if key == "ALL" or key == "5":
       kvp5 = KeyValuePair() 
       kvp5.kvpKey = "msgPaypalPaid" 
       #TODO - different products might need different messages here 
       #      so question - should this message be stored in the ServiceType table?  
       kvp5.kvpValue = "Payment has been recorded for your order.  We will contact you within two business days when we completed setup of your oneCloud." 
       kvp5.kvpIsSecure = False  
       kvp5.kvpDoc = "This message is displayed on home page after user completes Paypal paymetn for an order" 
       kvp5.put() 
       self.response.out.write("<BR>Stored " + kvp5.kvpKey)

     if key == "ALL" or key == "6":
       kvp6 = KeyValuePair() 
       kvp6.kvpKey = "PaypalMode" 
       kvp6.kvpValue = "TEST"  #this is a string, not a boolean  
       kvp6.kvpIsSecure = False  
       kvp6.kvpDoc = "When set to 'TEST', uses Paypal Sandbox. when set to 'PROD' uses real Paypal account." 
       kvp6.put() 
       self.response.out.write("<BR>Stored " + kvp6.kvpKey)

     if key == "ALL" or key == "7":
       kvp7 = KeyValuePair() 
       kvp7.kvpKey = "Paypal_PDT_Token_Sandbox" 
       kvp7.kvpValue = "dfahzI2nTsjYAVcUIjyiHTanVCQ9zlZY28UJzvS0xzC3aGl1a8ECrbyZmsm"
       kvp7.kvpIsSecure = False  
       kvp7.kvpDoc = "Sandbox - assigned by Paypal when enabling PDT (Payment Data Transfer)." 
       kvp7.put() 
       self.response.out.write("<BR>Stored " + kvp7.kvpKey)
     
     if key == "ALL" or key == "8":
       kvp8 = KeyValuePair() 
       kvp8.kvpKey = "Paypal_PDT_Token_Production" 
       kvp8.kvpValue = "NOT-AVAILABLE-YET"
       kvp8.kvpIsSecure = False  
       kvp8.kvpDoc = "Live/Production - assigned by Paypal when enabling PDT (Payment Data Transfer)." 
       kvp8.put() 
       self.response.out.write("<BR>Stored " + kvp8.kvpKey)

     if key == "ALL" or key == "9":
       kvp9 = KeyValuePair() 
       kvp9.kvpKey = "Paypal_URL_Sandbox" 
       kvp9.kvpValue = "https://www.beta-sandbox.paypal.com/us/cgi-bin/webscr"
       kvp9.kvpIsSecure = False  
       kvp9.kvpDoc = "Sandbox - the URL used to post Paypal HTML form data to Paypal" 
       kvp9.put() 
       self.response.out.write("<BR>Stored " + kvp9.kvpKey)

     if key == "ALL" or key == "10":
       kvp10 = KeyValuePair() 
       kvp10.kvpKey = "Paypal_URL_Production" 
       kvp10.kvpValue = "https://www.paypal.com/us/cgi-bin/webscr"
       kvp10.kvpIsSecure = False  
       kvp10.kvpDoc = "Live/Production - the URL used to post Paypal HTML form data to Paypal" 
       kvp10.put() 
       self.response.out.write("<BR>Stored " + kvp10.kvpKey)

     if key == "ALL" or key == "11":
       kvp11 = KeyValuePair() 
       kvp11.kvpKey = "KB_Document_Userid" 
       kvp11.kvpValue = "googleadmin@3wcloud.com"
       kvp11.kvpIsSecure = False  
       kvp11.kvpDoc = "Userid used to search related documents for knowledge base/keywords" 
       kvp11.put() 
       self.response.out.write("<BR>Stored " + kvp11.kvpKey)

     if key == "ALL" or key == "12":
       kvp12 = KeyValuePair() 
       kvp12.kvpKey = "KB_Document_Password" 
       kvp12.kvpValue = "49ak3014jtiEM"
       kvp12.kvpIsSecure = True  
       kvp12.kvpDoc = "Password for userid used to search related documents for knowledge base/keywords" 
       kvp12.put() 
       self.response.out.write("<BR>Stored " + kvp12.kvpKey)


     if key == "ALL" or key == "13":
       kvp13 = KeyValuePair() 
       kvp13.kvpKey = "msgPaypalPending" 
       #TODO - different products might need different messages here 
       #      so question - should this message be stored in the ServiceType table?  
       kvp13.kvpValue = "We will begin provisioning your order as soon as your Paypal echeck clears." 
       kvp13.kvpIsSecure = False  
       kvp13.kvpDoc = "This message is displayed on home page after user completes Paypal an echeck payment for an order" 
       kvp13.put() 
       self.response.out.write("<BR>Stored " + kvp13.kvpKey)


     if key == "ALL" or key == "14":
       file = open('templates/googleDocKnowledgeEventBookTemplate.html')
       content = file.read()
       file.close()
       kvp14 = KeyValuePair() 
       kvp14.kvpKey = "knowledgeEventBookTemplate" 
       #TODO - different products might need different messages here 
       #      so question - should this message be stored in the ServiceType table?  
       kvp14.kvpValue = "kvpValueLong"
       kvp14.kvpValueLong = content 
       kvp14.kvpIsSecure = False  
       kvp14.kvpDoc = "HTML for adding a knowledge event to a Google Document" 
       kvp14.put() 
       self.response.out.write("<BR>Stored " + kvp14.kvpKey)
       

     self.response.out.write("<h2>Completed: Stored StoreKeyValues</h2>") 



class TestPaypalAPIGetBalance(webapp.RequestHandler):

  def get(self):

     method = "GetBalance" 
     additional_form_fields_dict = {}

     objPaypalAPI = PaypalAPI()
     resultDict = objPaypalAPI.callAPI(method, additional_form_fields_dict) 

     self.response.out.write("<H2>Response</H2>") 
     for item in resultDict: 
        self.response.out.write("<BR>" + item + "=" + str(resultDict[item][0]))

     self.response.out.write("<br><br><h3>End Demo User Paypal</h3>")



class TestPaypalAPIGetToken(webapp.RequestHandler):

  def get(self):
     amount = 100.00 
     objPaypalAPI = PaypalAPI()
     token = objPaypalAPI.getToken(amount) 
     self.response.out.write("Token=" + token)  
     


class TestPaypalAPIGetToken2(webapp.RequestHandler):

  def get(self):

     method = "SetExpressCheckout" 
     amount = 0.01 
     returnURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalSuccess'))
     cancelReturnURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalFailure'))


     additional_form_fields_dict = {
         "NOSHIPPING":     "1",                     #1= no shipping address fields shown in Paypal pages 
         "ReturnURL":      returnURL,
         "CancelURL":      cancelReturnURL,
         "AMT":            amount,
         "L_BILLINGTYPE0": "MerchantInitiatedBilling"
         }

     objPaypalAPI = PaypalAPI()
     resultDict = objPaypalAPI.callAPI(method, additional_form_fields_dict) 

     self.response.out.write("<H2>Response</H2>") 
     for item in resultDict: 
        self.response.out.write("<BR>" + item + "=" + str(resultDict[item][0]))

     self.response.out.write("<br><br><h3>End Demo User Paypal</h3>")


def localtime(offset):
     currdatetime = datetime.datetime.now() 
     return  currdatetime.replace(hour = currdatetime.hour + offset)


class TestLocalTime(webapp.RequestHandler):

  def get(self):

     self.response.out.write("<BR>GMT now Time=" + str(datetime.datetime.now()))
     currdatetime = datetime.datetime.now() 
     offset = -6 
     showdatetime = currdatetime.replace(hour = currdatetime.hour + offset)
     self.response.out.write("<BR>Local Time=" + str(showdatetime))
     self.response.out.write("<BR>Local Time=" + str(localtime(offset)))
     return 

     #TODO - read Subscriber/Session table to get timezone offset 
     #retrieve any data already entered 
     
     mySession = Session()
     if not 'sessionkey' in mySession:
        self.error(404)
     else: 
        sessionkey = mySession['sessionkey']
  

class TestMail(webapp.RequestHandler):

  def get(self):

     message = mail.EmailMessage()
     #can optionally pass parms in constructor like this: 
     #message = mail.EmailMessage(sender="support@example.com",
     #                       subject="Your account has been approved")

     message.sender = "Neal Walters <googleadmin@3wcloud.com>"
     message.subject = "Welcome to oneCloud 4"
     message.to = "Neal Walters <nwalters@sprynet.com>" 
     message.html = """
<h3>Dear Customer</h3>,

This is your welcome email...

The 3WCloud.com Team
"""

     message.send()
     self.response.out.write("Mail sent to: " + message.to); 




class TestCode(webapp.RequestHandler):
  """
   This routine allows the developer to do a quick syntax check on the develpment server
   by typing in http://localhost:8080/testCode in the browser URL. 
   There are times, the developer is testing in the GAE server, but before making 
   a full upload, at least needs to check for basic syntax errors identified by interpreter. 
  """
  def get(self):

     self.response.out.write("<h3>No compile errors</h3>") 




class TestSpeed(webapp.RequestHandler):
  """
  Test potential issue of slowness when using the Session() class. 
  """
  def get(self):

     mySession = Session() 
     mySession['x'] = 'test'

     #if 'somevar' in mySession:   
     #   self.response.out.write("Var found") 

     self.response.out.write("<h1>Was this fast or not?  testSpeed</h1>") 





class TestSpeed(webapp.RequestHandler):
  """
  Test potential issue of slowness when using the Session() class. 
  """
  def get(self):

     mySession = Session() 
     mySession['x'] = 'test'

     #if 'somevar' in mySession:   
     #   self.response.out.write("Var found") 

     self.response.out.write("<h1>Was this fast or not?  testSpeed</h1>") 



class TestSpeed2(webapp.RequestHandler):
  """
  Test potential issue of slowness when using the Session() class. 
  """
  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
        params = {} 
        params = commonUserCode(params,self.request.url)

        genericText = "<h1>Was this fast or not? testSpeed3</h1>" 
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)

        self.renderPage('templates/reportGenericText.html', templateDictionaryGeneral)



class TestSpeed3(webapp.RequestHandler):
  """
  Test potential issue of slowness when using the Session() class. 
  """
  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
        params = {} 
        params = commonUserCode(params,self.request.url)

        genericText = "<h1>Was this fast or not?  testSpeed3</h1>" 
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)

        showLinks = [] 
        templateDictionaryGeneral = {
                      "environment": "SpeedTest",
                      "is_admin": True,
                      "currentUser": "nwalters@sprynet.com",
                      "debugText": debugText,
                      "userLinks":showLinks,
                      "now": datetime.datetime.now()
                      }

        self.renderPage('templates/reportGenericText.html', templateDictionaryGeneral)


class TestSpeed4(webapp.RequestHandler):
  """
  Test potential issue of slowness when using the Session() class. 
  """
  def get(self):

        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)

        self.response.out.write("<h1>Was this fast or not?  testSpeed4 </h1>") 


#=======================================================
# START Misc Routines 
#=======================================================
  

class UserPhoto(webapp.RequestHandler):

  def get(self):

     #retrieve any data already entered  
     mySession = Session()
     if not 'sessionkey' in mySession:
        self.error(404)
        #self.response.out.write("Please logon to an existing session, or go to form 2 and upload a photo... in order to test photo functionaltiy");  
     else: 
        sessionkey = mySession['sessionkey']
        #debugText = debugText + "Existing Session = " + str(sessionkey) + "<br/>"  
  

     # retrieve existing user/session row from database table  
     if sessionkey:
        session = CumulusSession.get(sessionkey) 
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(session.photo) 

class UserPhotoFromService(webapp.RequestHandler):
  """
  This routine is used as follows:  <img src="UserPhotoFromService?key=xxxxxxxxx"> 
  and actually returns the image that can be placed on a web page. 
  The user can then do right-click save/image if he wants to save it to disk. 
  """
  def get(self):

     key = self.request.get("key")
     if key < " ":
        self.response.out.write("<h3>No ?key= parameter found on the URL <h3>") 
        return 

     service = Service.get(key) 
     if not service: 
        self.response.out.write("<h3>Subscriber not found with key=" + key + "<h3>") 
        return 

     if not isinstance(service,ServiceOneCloud): 
        self.response.out.write("<h3>This service is not of type 'ServiceOneCloud' and may not have a resume.<h3>") 
        return 

     self.response.headers['Content-Type'] = "image/png"
     self.response.out.write(service.photo) 


def getFileSuffix (filename, webapp):
    #webapp.response.out.write("getFileSuffix: filename=" + str(filename) + "<BR>") 
    if filename: 
       parts = filename.partition(".") 
       suffix = ""
       if len(parts) > 1:
          suffix = parts[2]
       return suffix  
    else:
       return '' 

def getPrettySuffixList (suffixList): 
      prettySuffixes = " Valid suffixes are: " 
      suffixCounter = 0 
      for suffix in suffixList:
         if suffixCounter > 0: 
           prettySuffixes += ", " 
         prettySuffixes += suffix 
         suffixCounter += 1 
      return prettySuffixes 

def ShowValidateFormButton(session,minPage,maxPage):
   """
   Set result to True if all pages between minPage and maxPage have been submitted
   """
   if not session:
      return False 
   if maxPage < minPage + 1:
      raise "invalid parameters maxPage must be greater than minPage"
   if not False in session.pagesSubmitted[minPage:maxPage]:
      return True 
   return False 

def ShowSubmitErrors(session, forms, serviceCode, includeHyperlinks, self): 
   """
   Loop through all variables in dictionary requiredTextFields1Cloud 
   and see if that variable has a value in our current session object.
   If not - and user has submitted data (pageSubmitted) for this page, b
   then build error message to display on form. 
   Need "self" webapp passed here so we can write error message to web page. 
   """
   mySession = Session()
   envBreak = "<BR>" 
   counter = 0 
   errorCounter = 0 
   requiredFieldsMessage = "" 

   # ----BEGIN ---- #added 07/07/09 when "register" form implemented 
   if serviceCode == "1CloudI":
      requiredTextFields = requiredTextFields1Cloud
      requiredListFields = requiredListFields1Cloud
   elif serviceCode == "register":
      requiredTextFields = requiredTextFieldsRegister
      requiredListFields = requiredListFieldsRegister 
   else:
      self.response.out.write("Error at 1483: no code created for serviceCode=" + serviceCode)
      return 
   # ----END ---- #added 07/07/09  

   if not session: 
      #this avoids an index/subscript problem 
      #self.response.out.write("<h3>Lost session variables - please logon again</h3>")  
      self.redirect("/login")    
      return 


   #-----BEGIN --- Added 07/08/09 
   submitButtonText = ""
   if 'submitButtonText' in mySession:
       submitButtonText = mySession['submitButtonText'] 
   if submitButtonText != "Continue as Returning Customer" and not session.isSaveAndComeBack:
      query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1", session.userEmail) 
      LIMIT = 1 
      returnURL = "" 
      subscriberList = query.fetch(LIMIT,offset=0);
      if len(subscriberList) > 0: 
          #page of email - must lookup in dictionary 
          page = requiredTextFields['userEmail']
          #mySession['contactPageValidationErrors'] = True 
          requiredFieldsMessage += ("<LI>Email already exists for another customer account: " + 
                    "(<a href='formHandler?serviceCode=" + serviceCode + 
                     "&page=" + str(page) + "'>page " + 
                     str(page) + "</a>)" + 
                     " (Note: you can check out as 'returning customer' if you wish to use an existing account)" + 
                     envBreak + 
                     "<!-- debug:submitButtonText=" + submitButtonText + "-->" ) 
               
           
   #-----END ----- Added 07/08/09 


   #-----BEGIN --- Added 06/30/2009 
   if not True in session.pagesSubmitted:
      #self.response.out.write("returning 'NoData'") 
     return "NoData" 
   #-----END ----- Added 06/30/2009 

   #-----BEGIN --- Added 07/05/2009 
   if not includeHyperlinks:   #hyperlinks is set to True only on last page (page 5) 
      minPage = 0 
      maxPage = 3  #zero-based 
      # if any page not submitted yet, then don't show the "Valdate Form" or "Submit" button 
      if False in session.pagesSubmitted[minPage:maxPage]:
         return "NoButton" 
   #-----END ----- Added 07/05/2009  



   #-----BEGIN --- Added 07/3/2009 
   #this field is hard-coded here  - added 07/03/2009 - TODO - make it more generic  
   if serviceCode == "1CloudI":                      #added 07/07/09 when "register" form implemented 
      if not session.legalTermsAccepted: 
         page = 3 
         requiredFieldsMessage += ("<LI>Legal Terms not accepted " + 
                  "(<a href='formHandler?serviceCode=" + serviceCode + 
                   "&page=" + str(page) + "'>page " + 
                  str(page) + "</a>)" + envBreak )

   #TODO Catch this error if user uploads a photo that is beyond limit:
   # File "c:\Program Files\Google\google_appengine\google\appengine\api\apiproxy_stub.py", line 75, in MakeSyncCall
   # 'The request to API call %s.%s() was too large.' % (service, call))
   # RequestTooLargeError: The request to API call datastore_v3.Put() was too large.

   photoFileSuffix  = getFileSuffix(session.photoFilename, self)
   #self.response.out.write("PhotoFileSuffix=" + photoFileSuffix + "<BR>") 
   resumeFileSuffix = getFileSuffix(session.resumeFilename, self) 
   #self.response.out.write("ResumeFileSuffix=" + resumeFileSuffix + "<BR>") 

   validPhotoFileSuffixes  = ['jpg','png','gif'] 
   validResumeFileSuffixes = ['txt','pdf','doc','docx'] 

   if resumeFileSuffix:
     if resumeFileSuffix > ' ': 
       if not resumeFileSuffix in validResumeFileSuffixes:
         page = 2 
         requiredFieldsMessage += ("<LI>Resume file type = " + 
                   resumeFileSuffix + ". " + 
                   getPrettySuffixList(validResumeFileSuffixes) + 
                  " (<a href='formHandler?serviceCode=" + serviceCode + 
                   "&page=" + str(page) + "'>page " + 
                  str(page) + "</a>)" + envBreak )

   if photoFileSuffix:
     if photoFileSuffix > ' ':
       if not photoFileSuffix in validPhotoFileSuffixes:
          page = 2 
          requiredFieldsMessage += ("<LI>Photo file type = " + 
                   photoFileSuffix + ". " + 
                   getPrettySuffixList(validPhotoFileSuffixes) + 
                  " (<a href='formHandler?serviceCode=" + serviceCode + 
                   "&page=" + str(page) + "'>page " + 
                  str(page) + "</a>)" + envBreak )
       
   #-----END --- Added 07/03/2009 


   pagenum = 0 
   try:
     for var in requiredTextFields.keys():
       counter = counter + 1 
       #print str(counter) + " " + var 
       pagenum = int(requiredTextFields[var])

       
         #Originally when showing errors at bottom of page, we only wanted to show
         #error for pages that had been submitted, but now we are showing errors only
         #on page 5 - so we should show all errors - even if user skipped a page. 
       #if session.pagesSubmitted[pagenum-1]:   #zero based 
       if True:   # still here to maintain indentation 
         addPage = False 
         if not var in CumulusSession.__dict__:
            errorCounter = errorCounter + 1
            requiredFieldsMessage = (requiredFieldsMessage + 
                   "<LI>Required field: '" + var + 
                   "' has missing value ")
            addPage = True 
         else:
            errorCounter = errorCounter + 1
            #samples of what getattr does 
            #value = obj.attribute
            #value = getattr(obj, "attribute") 
            value = getattr(session,var)
            if value <= '' or not value or value == "Select One":
               requiredFieldsMessage = (requiredFieldsMessage + 
                   "<LI>Required field: '" + var + 
                   "' has blank value ") 
               addPage = True 
         if addPage: 
            if includeHyperlinks: 
                requiredFieldsMessage += ("(<a href='formHandler?serviceCode=" + serviceCode + 
                   "&page=" + str(requiredTextFields[var]) + "'>page " +
                  requiredTextFields[var] + "</a>)" + envBreak )
            else: 
                requiredFieldsMessage += (" (page " + 
                  requiredTextFields[var] + ")" + envBreak )
            #check to see if this is contact page 
            #(the purpose is that if a user did a "Save Data and Come Back Later" then he had not yet 
            #provided all the necessary contact fields) 
            #isContactPage = False 
            #for form in forms: 
            #   if form.serviceCode = serviceCode and form.isContactForm and form.seq = requiredTextFields[var]:
            #      isContactPage = True 
            #if isContactPage: 
            #   mySession['contactPageValidationErrors'] = True 

              

   except (Exception), e:
       #have to bubble up error 
       return ("ERROR: pagenum=" + str(pagenum) + " (from which we subtract 1)<BR>" + 
               "size of session.pagesSubmitted=" + str(len(session.pagesSubmitted)) + "<BR>" + 
              str(e) ) 


   #now check that list fields have the required minimum quantity 
   for var in requiredListFields.keys():
       counter = counter + 1 
       #print str(counter) + " " + var
       page = int(requiredListFields[var][0])
       minNumElements = requiredListFields[var][1]

       
       #if pageSubmitted[page]:
       #if forms[formSubscript].pageSubmitted: 
       #NOTE: kept getting errors here! Occassional loss of session variables in dev environment? 
       
         #Originally when showing errors at bottom of page, we only wanted to show
         #error for pages that had been submitted, but now we are showing errors only
         #on page 5 - so we should show all errors - even if user skipped a page. 
       #if session.pagesSubmitted[pagenum-1]:   #zero based 
       if True:   # still here to maintain indentation 
         addPage = False 
         #if not var in CumulusSession.__dict__ and session.pagesSubmitted[page]: 
         if not var in CumulusSession.__dict__: 
            errorCounter = errorCounter + 1 
            requiredFieldsMessage = (requiredFieldsMessage + 
                   "<LI>Required field: '" + var + 
                   "' must have at least " + str(minNumElements) + 
                   " value(s) but found none") 
            addPage = True
         else:
            #samples of what getattr does 
            #value = obj.attribute
            #value = getattr(obj, "attribute") 
            value = getattr(session,var)
            #tags always has six elements, event if they are blank 
            #so we have to count the number of non-blank elements 
            #numElements = len(value) 
            numElements = 0 
            for element in value:
               if element > ' ':
                  numElements = numElements + 1 
            #requiredFieldsMessage = (requiredFieldsMessage + 
            #       "Debug: '" + var + 
            #      " len(value) = " + str(numElements)) 
            #State & CellCarrier has a default of "Select One" 
            if numElements < minNumElements: 
               errorCounter = errorCounter + 1
               requiredFieldsMessage = (requiredFieldsMessage + 
                   "<LI>Fewer than required values: '" + var + 
                   "' must have at least " + str(minNumElements) + 
                   " value(s) but found " + str(numElements) + " ") 
               addPage = True
         if addPage: 
            if includeHyperlinks: 
                requiredFieldsMessage += ("(<a href='formHandler?serviceCode=" + serviceCode + 
                   "&page=" + str(page) + "'>page " + 
                  str(page) + "</a>)" + envBreak )
            else: 
                requiredFieldsMessage += (" (page " + 
                  str(page) + ")" + envBreak )


   if requiredFieldsMessage > '':
      #imagetag = "<img src='/images/missing-required-attributes-thumb.png' align='top'><br/>"
      imagetag = "" #removed per defect/enhancement list 7/2/09 
      # add OL tags and image 
      requiredFieldsMessage = imagetag + "<OL>" + requiredFieldsMessage + "</OL>"
      return requiredFieldsMessage 
   else:
      return False; 

#=======================================================
# START Specific Customer Data Entry Forms 
#=======================================================



class CumulusFormHandler(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     debugText = "" 
     if self.request.get('page') < ' ': 
        self.response.out.write("<H3>Missing ?page= (page number) on URL</h3>") 
        self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
        return 
     if self.request.get('serviceCode') < ' ': 
        self.response.out.write("<H3>Missing &servicecode=value on URL</h3>") 
        self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
        return 
     page = int(self.request.get('page')) 
     serviceCode = self.request.get('serviceCode') 


     #retrieve any data already entered  
     mySession = Session()
     if not 'sessionkey' in mySession:
        sessionkey = None 
     else: 
        sessionkey = mySession['sessionkey']

     global forms 

     #find the subscript in the forms array that contains our current page 
     formSubscript = 0 
     booMatch = False 
     maxPagenum = '0'
     askNewReturningCustomer = False 

     for form in forms: 
        #self.response.out.write("form.seq=" + str(form.seq) + " form.serviceCode=" + form.serviceCode + "<BR>") 
        if form.seq == page and form.serviceCode == serviceCode:   
           booMatch = True 
           maxPagenum = form.ofSeq 
           askNewReturningCustomer = form.askNewReturningCustomer
           break 
        formSubscript += 1 
     if not booMatch: 
        self.response.out.write("<H3>page or serviceCode not found as valid in forms array</h3>") 
        self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
        return 

     log = CumulusLog()    
     log.category = "FormHandler:Get" 
     log.message = "ServiceCode=" + serviceCode + " page=" + str(page) + " formSubscript=" + str(formSubscript) 
     log.ipaddress = self.request.remote_addr 
     log.put() 


     #create a new record if necessary, otherwise retrieve prior one 
     if sessionkey:
        try:
           session = CumulusSession.get(sessionkey)   #retrieve session record from BigTable Database 
        except (Exception), e: 
           self.response.out.write("sessionkey=" + str(sessionkey) + "<BR>") 
           self.response.out.write(str(e)  + "<BR>") 
           self.response.out.write("Debug location: 1769 <BR>") 
           return 
        
        #session = CumulusSession.get_by_key_name(sessionkey)
        if session: 
           session.dateTimeModified = datetime.datetime.now() 
           log = CumulusLog()    
           log.category = "FormHandler:Get" 
           log.message = ( "sessionkey=" + str(sessionkey) + 
                         " firstname=" + str(session.firstname) + 
                         " lastname= " + str(session.lastname) + 
                         " state=" + str(session.state) ) 
           log.ipaddress = self.request.remote_addr 
           log.put() 
        else:
           session = CumulusSession()
           session.createNewEmptySession(serviceCode) 
           log = CumulusLog()    
           log.category = "FormHandler:Get" 
           log.message = "A) Created New Empty Session because sessionkey=" + str(sessionkey) + " was not found in DB" 
           log.ipaddress = self.request.remote_addr 
           log.put() 

     else: 
        session = CumulusSession()
        session.createNewEmptySession(serviceCode) 
        log = CumulusLog()    
        log.category = "FormHandler:Get" 
        log.message = "A) Created New Empty Session because sessionkey=" + str(sessionkey) + " did not exist "   
        log.ipaddress = self.request.remote_addr 
        log.put() 

     sessionkey = session.key() 
     mySession['sessionkey'] = sessionkey 

     #------------------------------------------------
     # Now special prep logic for different pages 
     #------------------------------------------------

     #keep other special URL parmaters in the action to preserve them 
     if self.request.get("resubmitOrderKey") > " ": 
       action = "formHandler?serviceCode=" + serviceCode + "&page=" + str(page) + "&resubmitOrderKey=" + self.request.get("resubmitOrderKey")
     else:
       action = "formHandler?serviceCode=" + serviceCode + "&page=" + str(page)
     

     if forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv1.html": 
        from addressHelpers import registrars 
        for arrRegistrar in registrars: 
            if arrRegistrar.value == session.registrarURL: 
                arrRegistrar.selected = True 
            else:   #not sure why values don't set to false automatically 
                arrRegistrar.selected = False 

        for dblanguage in session.languages:
            for arrlanguage in languages: 
                if arrlanguage.name == dblanguage: 
                   arrlanguage.selected = True 
                else:   #not sure why values don't set to false automatically 
                   arrlanguage.selected = False 

        showSubmitErrorsVar = ShowSubmitErrors(session, forms, serviceCode, False, self)
        #if isinstance(showSubmitErrorsVar,string):
        #  if showSubmitErrorsVar[0:5] == "ERROR": 
        #     self.response.out.write(showSubmitErrorsVar) 
        #     return 
        #showValidateFormButtonVar = ShowValidateFormButton(session,0,3)  #zero based  
        #self.response.out.write("showSubmitErrorsVar=" + str(showSubmitErrorsVar)) 
        #return 

        templateDictionaryLocal = {"languages":languages,
                                   "registrars":registrars,
                                   "session":session,
                                   "action":action,
                                   "showSubmitErrors": showSubmitErrorsVar,
                                   "pagenum": self.request.get('page'),
                                   "skipErrorsAtBottom":  "N",
                                   "askNewReturningCustomer":  askNewReturningCustomer,
                                   "maxPagenum": maxPagenum,
                                  }
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
        templateDictionaryLocal.update(templateDictionaryGeneral)

        self.renderPage(forms[formSubscript].webpage, templateDictionaryLocal)

     elif forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv2.html": 

        #preset any form values here 
        itemnum = 0 
        for dbsocialsite in session.socialSites:
            for arrsocialnetwork in socialNetworks: 
                if arrsocialnetwork.category == dbsocialsite: 
                   arrsocialnetwork.selected = True 
                   arrsocialnetwork.socialUrl = session.socialURLs[itemnum]; 
            itemnum = itemnum + 1 

        showSubmitErrorsVar = ShowSubmitErrors(session, forms, serviceCode, False, self)
        #if showSubmitErrorsVar[0:5] == "ERROR": 
        #   self.response.out.write(showSubmitErrorsVar) 
        #   return 
        #showValidateFormButtonVar = ShowValidateFormButton(session,0,3)  #zero based  
        #self.response.out.write("showSubmitErrorsVar=" + showSubmitErrorsVar) 


        templateDictionaryLocal = {"socialNetworks": socialNetworks,
                                   "session":session,
                                   "action":action,
                                   "showSubmitErrors": showSubmitErrorsVar, 
                                   "pagenum": self.request.get('page'),
                                   "skipErrorsAtBottom":  "N",
                                   "askNewReturningCustomer":  askNewReturningCustomer,
                                   "maxPagenum": maxPagenum,
                                  }
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
        templateDictionaryLocal.update(templateDictionaryGeneral)

        self.renderPage(forms[formSubscript].webpage, templateDictionaryLocal)

     elif forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv3.html": 
        #we always want to display six tags on the form, but the user can enter/save fewer,
        #so we repad up to six tags if necessary 
        numBlankTagsNeeded = 6 - len(session.tags) 
        for x in range(numBlankTagsNeeded):
           session.tags.append('') 

        query = ServiceTypeLegal.gql("where code = :1", serviceCode)  #no where clause needed
        LIMIT = 1 
        serviceTypeLegalList = query.fetch(LIMIT,offset=0) 
        legalTerms = "Not-Available for serviceCode=" + serviceCode 
        if len(serviceTypeLegalList) > 0: 
           legalTerms = serviceTypeLegalList[0].legalTerms 


        showSubmitErrorsVar = ShowSubmitErrors(session, forms, serviceCode, False, self)
        #if showSubmitErrorsVar[0:5] == "ERROR": 
        #   self.response.out.write(showSubmitErrorsVar) 
        #   return 
        #showValidateFormButtonVar = ShowValidateFormButton(session,0,3)  #zero based  

        templateDictionaryLocal = {   "session":session,
                                      "action":action,
                                      "showSubmitErrors":  showSubmitErrorsVar,
                                      "pagenum": self.request.get('page'),
                                      "skipErrorsAtBottom":  "N",
                                      "askNewReturningCustomer":  askNewReturningCustomer,
                                      "legalTerms": legalTerms, 
                                      "maxPagenum": maxPagenum 
                                     }
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
        templateDictionaryLocal.update(templateDictionaryGeneral)

        self.renderPage(forms[formSubscript].webpage, templateDictionaryLocal)

     elif forms[formSubscript].webpage == "templates/customer/commonContactInformation.html":  
        #self.response.out.write("<BR>commonContactInformation.html 1 maxPagenum=" + str(maxPagenum) + " formSubscript=" + str(formSubscript)) 

        #if user is already logged on and he clicked "Continue as Returning Customer" button... 
        #we will copy his user info and skip over this page 
        user = getLoggedInUser(self)
        submitButtonText = ""
        if 'submitButtonText' in mySession:
           submitButtonText = mySession['submitButtonText'] 

        log = CumulusLog()    
        log.category = "ContactForm:Get" 
        log.message = "Logged-On-User=" + str(user) + " submitButtonText=" + str(submitButtonText) 
        log.ipaddress = self.request.remote_addr 
        log.put() 

        if user and submitButtonText == "Continue as Returning Customer": 
           log = CumulusLog()   
           log.category = "ContactForm:Get" 
           log.message = "Logged-On User=" + user 
           log.ipaddress = self.request.remote_addr 
           log.put() 

           query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1", user) 
           LIMIT = 10
           returnURL = "" 
           subscriberList = query.fetch(LIMIT,offset=0);
           if len(subscriberList) > 0: 
              subscriber = subscriberList[0]
              subscriber.copySubscriberInfoToSession(sessionkey) 

           #Skip the contact info page, go directly to the submit page 
           nextpage = forms[formSubscript+1].seq   #find the next form in the array, and use it's seq #  
           nextURL = "formHandler?serviceCode=" + serviceCode + "&page=" + str(nextpage) 
           if not session.isSaveAndComeBack:
             #if user did full register, or ordered another product, then we have all valid fields for 
             #his subscriber record.  However, if we clicked "SaveAndComeBack", then an incomplete 
             #subscriber record was stored with only username/password in it (and a boolean flag
             #called "isSaveAndComeBack".  Thus, he needs to complete firstname, lastname, address, etc... 
             self.redirect(nextURL)
             log = CumulusLog()    
             log.category = "ContactForm:Get" 
             log.message = "nextURL=" + nextURL + " formSubscript+1=" + str(formSubscript + 1)
             log.ipaddress = self.request.remote_addr 
             log.put() 
           else:
             log = CumulusLog()    
             log.category = "ContactForm:Get" 
             log.message = "User is a 'SaveAndComeBack' user that needs to complete contact info" 
             log.ipaddress = self.request.remote_addr 
             log.put() 

  
        from addressHelpers import states 
        from addressHelpers import continents 
        from addressHelpers import countries
        from addressHelpers import timezones
        #from addressHelpers import cellproviders 

        if not session.timezone:
           session.timezone = float(-5);           # set to some USA Timezone if not yet specified 

        #make sure the previously selected timezone shows up as the value in the select/list 
        for timezone in timezones:
           if timezone.value == session.timezone: 
              timezone.selected = True 
           else:
              timezone.selected = False  

        #make sure the previously selected state shows up as the value in the select/list 
        for state in states:
           if state.value == session.state: 
              state.selected = True 
           else:
              state.selected = False 

        #make sure the previously selected country shows up as the value in the select/list 
        for country in countries:
           if country.value == session.country: 
              country.selected = True   
           else: 
              country.selected = False 

        showSubmitErrorsVar = ShowSubmitErrors(session, forms, serviceCode, False, self)
        #if showSubmitErrorsVar[0:5] == "ERROR": 
        #   self.response.out.write(showSubmitErrorsVar) 
        #   return 
        #showValidateFormButtonVar = ShowValidateFormButton(session,0,3)  #zero based  

        #self.response.out.write("<BR>commonContactInformation.html 2 maxPagenum=" + str(maxPagenum) + " formSubscript=" + str(formSubscript)) 

        templateDictionaryLocal = {
                                   "session":session,
                                   "action":action,
                                   "timezones": timezones, 
                                   "states": states,
                                   "countries": countries,
                                   "continents": continents,
                                   "showSubmitErrors": showSubmitErrorsVar, 
                                   "pagenum": self.request.get('page'),
                                   "maxPagenum": maxPagenum,
                                   "skipErrorsAtBottom":  "N"
                                  } 
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
        templateDictionaryLocal.update(templateDictionaryGeneral)

        self.renderPage(forms[formSubscript].webpage, templateDictionaryLocal)

     elif forms[formSubscript].webpage == "templates/customer/commonFormSubmit.html":  
        #This is the final page where we show all form submsission errors 
        #and tell the user to submit 

        #do not revalidate if user is just coming back to try to pay again 
        showSubmitErrorsVar = False 
        if self.request.get("resubmitOrderKey") <= "": 
           showSubmitErrorsVar = ShowSubmitErrors(session, forms, serviceCode, True, self)
         

        templateDictionaryLocal = {   "session":session,
                                      "action":action,
                                      "showSubmitErrors":  showSubmitErrorsVar,
                                      "skipErrorsAtBottom":  "Y",
                                      "pagenum": self.request.get('page'),
                                      "maxPagenum": maxPagenum,
                                     }
                               
        templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
        templateDictionaryLocal.update(templateDictionaryGeneral)

        self.renderPage(forms[formSubscript].webpage, templateDictionaryLocal)

     else: 
        #TODO - better error handling here? 
        self.response.out.write("<H3>Unknown page number on URL page=" + str(page) + "</h3>") 
        return 
        


  #class CumulusFormHandler(webapp.RequestHandler):
  def post(self):

     debugText = "" 
     params = {} 
     params = commonUserCode(params,self.request.url)

     mySession = Session()
     debugText = "" 
     if self.request.get('page') < ' ': 
        self.response.out.write("<H3>Missing ?page= (page number) on URL</h3>") 
        self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
        return 
     if self.request.get('serviceCode') < ' ': 
        self.response.out.write("<H3>Missing &servicecode=value on URL</h3>") 
        self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
        return 

     page = int(self.request.get('page')) 
     serviceCode = self.request.get('serviceCode') 
     log = CumulusLog()    
     log.category = "FormHandler:Post" 
     log.message = "SubmittButtonText=" + self.request.get('submit') + " ServiceCode=" + serviceCode + " page=" + str(page) 
     log.ipaddress = self.request.remote_addr 
     log.put() 

     if not 'sessionkey' in mySession:
        sessionkey = None 
     else: 
        sessionkey = mySession['sessionkey']
        

     global forms 
     #if 'forms' not in mySession:
        #TODO - add URL and better error-handling here for user who times-out 
        ##self.response.out.write("<H3>Forms not found in Session (Debug Location 1864)</h3>") 
        ##self.response.out.write("<H3>Potential time-out of session variables, please logon or start form again</H3>")
        #if mySession == None:
        #  self.response.out.write("mySession = None") 
        #else: 
        #  self.response.out.write("Items found in session=<BR>") 
        #  for item in mySession:
        #     self.response.out.write("item=" + str(item) + "<BR>")
        #return 

     #forms = mySession['forms'] 

     #self.response.out.write ("Form Check: <BR>") 
     #for form in forms: 
     #   self.response.out.write(" form.seq=" + str(form.seq) + " form.serviceCode=" + form.serviceCode + " Visited=" + str(form.pageSubmitted) + "<BR>") 

        

     #find the subscript in the forms array that contains our current page 
     formSubscript = 0 
     booMatch = False 
     for form in forms: 
        #self.response.out.write("form.seq=" + str(form.seq) + " form.serviceCode=" + form.serviceCode + "<BR>") 
        if form.seq == page and form.serviceCode == serviceCode:   
           booMatch = True 
           break 
        formSubscript += 1 

     if not booMatch: 
        self.response.out.write("<H3>page or serviceCode not found as valid in forms array</h3>") 
        self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
        return 

     #if form[formSubscript[.seq == form[formSubscript].ofSeq:

     #self.response.out.write("pageSubmitted set to true for subscript=" + str(formSubscript) )
     #return 


     #create a new record if necessary, otherwise retrieve prior one 
     if sessionkey:
        session  = CumulusSession.get(sessionkey) 
        #session = CumulusSession.get_by_key_name(sessionkey)
        session.dateTimeModified = datetime.datetime.now() 
     else: 
        #create a new item in database 
        session = CumulusSession()
        session.dateTimeCreated = datetime.datetime.now() 
        session.dateTimeModified = session.dateTimeCreated  #set to exact same time 
        session.serviceCode = serviceCode 

     pageSubscript = page - 1 
     #forms[formSubscript].pageSubmitted = True 

     #this is crude attempt to clean-up weird errors below 
     if len(session.pagesSubmitted) == 0: 
        session.pagesSubmitted = [False] * 12 
        session.put() 

     if len(session.pagesSubmitted) >= pageSubscript: 
       try:
         session.pagesSubmitted[pageSubscript] = True         #zero based 
       except (Exception), e:
         self.response.out.write("Error location 1978 <BR>") 
         self.response.out.write("page=" + str(page) + "<BR>") 
         self.response.out.write(str(e) + "<BR>") 
     else: 
       self.response.out.write("Error location 1982 <BR>") 
       self.response.out.write("page=" + str(page) + " pageSubscript=" + str(pageSubscript) + "<BR>") 
       if not session:
          self.response.out.write("Session is None<BR>") 
       self.response.out.write("Size = " + str(len(session.pagesSubmitted)) + "<BR>") 
       counter = 0 
       for page in session.pagesSubmitted:
            self.response.out.write("<br/>" + str(counter) + " " + str(page)) 
            counter += 1 
       return

     needUpdateSession = False 
     submitButtonText = "" 
     if 'submitButtonText' in mySession:
        submitButtonText = mySession['submitButtonText'] 



     if forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv1.html":  
        #now set fields from the user's form data 
        tempDomain = self.request.get('domain')
        session.domain             = self.request.get('domain')
        mySession['userDomain']    = session.domain   #save in session variables 

        #registrar might be in select-box, or might be typed in
        session.registrarURL       = self.request.get('registrarURL')
        if self.request.get('registrarURL2') > " ": 
           session.registrarURL2    = self.request.get('registrarURL2')
        else: 
           session.registrarURL2    = ""
        
        session.registrarUserid    = self.request.get('registrarUserid')
        session.registrarPassword  = self.request.get('registrarPassword')
        session.languages          = self.request.get_all('language')
        session.primaryLanguage    = self.request.get('primaryLanguage') 
        session.otherLanguages     = self.request.get('otherLanguages')
        #session.otherLanguageNotes = self.request.get('otherLanguageNotes')  #REMOVED 
        session.ipaddress          = self.request.remote_addr 
        needUpdateSession = True 

     elif forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv2.html":  
        #user can upload two files: 1) word.doc of resume, and 2) photo 
        #we must store in database, and figure out how to extract later. 
        #Note: user might go to this page, and NOT change his resume, 
        #so we should only replace data when he reuploads new files. 

        #self.response.out.write("Filename=" + filename + "<BR>") 
        #self.response.out.write("Suffix=" + suffix + "<BR>") 
        #return 

        #validFileTypes = []
        #if not suffix in validFileTypes: 
           

        strResume       = self.request.get('resume')
        if len(strResume) > 0:
           session.resume  = db.Blob(strResume) 
           session.resumeFilename = self.request.POST['resume'].filename

        strPhoto        = self.request.get('photo')
        if strPhoto > '':
           session.photo   = db.Blob(strPhoto) 
           session.photoFilename  = self.request.POST['photo'].filename

        #session.socialSites    = self.request.get_all('socialSite')

        #don't want to store the blank URLs in the database  
        newSocialURLs = [] 
        newSocialSites = [] 
        counter = 0 
        for socialUrl in self.request.get_all('socialUrl'): 
            if socialUrl > '': 
                 newSocialURLs.append(socialUrl) 
                 newSocialSites.append(socialNetworks[counter].category) 
            counter +=  1 
        session.socialURLs  = newSocialURLs
        session.socialSites = newSocialSites 
        needUpdateSession = True 

     elif forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv3.html":  
        #self.response.out.write("legalTerms=" + self.request.get("acceptLegalTerms")) 
        #return 
        #now set fields from the user's form data 
        session.bio                   = self.request.get('bio')
        session.tags                  = self.request.get_all('tag')
        #session.specialInstructions  = self.request.get('specialInstructions')
        session.legalTerms            = self.request.get('legalTerms')

        if self.request.get("acceptLegalTerms") == "on": 
           session.legalTermsAccepted = True 
        else: 
           session.legalTermsAccepted = False 
        needUpdateSession = True 

     elif forms[formSubscript].webpage == "templates/customer/commonContactInformation.html":  
        #now set fields from the user's form data 
        session.firstname           = self.request.get('firstname').capitalize()   
        session.lastname            = self.request.get('lastname').capitalize()   
        session.organizationname    = self.request.get('orgname')   
        session.address1            = self.request.get('address1').capitalize()          
        session.address2            = self.request.get('address2').capitalize()         
        session.city                = self.request.get('city').capitalize()          
        session.state               = self.request.get('state')       
        session.zip                 = self.request.get('zip')       
        session.country             = self.request.get('country') 
        session.phone               = self.request.get('phone')       
        #session.phoneland           = self.request.get('phoneland')       
        #session.phonecell           = self.request.get('phonecell')       
        #session.cellprovider        = self.request.get('cellprovider')       
        #session.cellproviderother   = self.request.get('cellproviderother')       
        session.timezone            = float(self.request.get('timezone')) 
        session.userEmail           = self.request.get('userEmail').lower()  
        session.userPassword        = self.request.get('userPassword') 
        needUpdateSession = True 

     if needUpdateSession:
        session.put() 
        log = CumulusLog()     
        log.category = "CumulusSession.put()" 
        log.message = "domain=" + str(session.domain) + " key=" + str(session.key()) 
        log.ipaddress = self.request.remote_addr 
        log.put() 
     mySession['sessionkey'] = session.key()

     debugText = debugText + "&nbsp;&nbsp; Put()" 

     if self.request.get('submit')[0:4] == "Save":  
        self.redirect("/oneCloudSetupIndivSave?serviceCode=" + serviceCode)
        return    # 07/09/2009 - immediate switch to new page 

     nextpage = 0 

     #remember that we usually get to page 2 post when users clicks "Continue" on page 1
     if self.request.get('submit')[0:8] == "Continue": 
        nextpage = forms[formSubscript].nextSeq 
        log = CumulusLog()    
        log.category = "FormHandler:Post" 
        log.message = "got into 'Continue' logic nextpage=" + str(nextpage) 
        log.ipaddress = self.request.remote_addr 
        log.put() 

     mySession['submitButtonText'] = self.request.get('submit')

     #this logic has to be after the "Continue" logic above which sets the redirectPageAfterLogin 
     if self.request.get('submit') == "Continue as Returning Customer":
        user = loggedin(self) 

        log = CumulusLog()    
        log.category = "FormHandler:Post" 
        log.message = "got into 'Continue as Returning Customer' logic, user=" + str(user)  
        log.ipaddress = self.request.remote_addr 
        log.put() 

        #/fpdbs.paypal.com/dynamicimageweb?cmd=_dynamic-image&pal=4K4HRRVKBJNJU">

        #NOTE: The user might already be logged-in, in which case we can fill-in his contact info. 
        #Otherwise, allow him to login, then fill-out his contact info. 
        if not user: 
           #this short-circuits the normal logic flow, and instead of asking user for contact info
           #we send him to log-in form (after performing the normal update for the page he is on via the code above) 
           mySession['redirectPageAfterLogin'] = "formHandler?serviceCode=" + serviceCode + "&page=" + str(nextpage) 
           self.redirect("/login")    
           #must return to force immediate redirect 
           return 


     if self.request.get('submit')[0:6] == "Submit": 
        #only on page 3 do we save the "Submit" button, TODO: in future, as other products are added 
        #this will not always be page 3 but the page before the contact page. 
        if forms[formSubscript].webpage == "templates/customer/oneCloudSetupIndiv3.html":  
           mySession['submitButtonText'] = self.request.get('submit') 
        #nextpage = forms[formSubscript].nextSeq 
        if serviceCode == "1CloudI":
           #self.response.out.write("value=" + self.request.get("resubmitOrderKey"))
           #return 
           if self.request.get("resubmitOrderKey") > " ": 
              #in the case of resubmitting an order to clear up a missing Payment
              #we need to pass the order key 
              self.redirect("/oneCloudSetupIndivSubmit?serviceCode=" + serviceCode + "&resubmitOrderKey=" + self.request.get("resubmitOrderKey"))
              return
           else:
              self.redirect("/oneCloudSetupIndivSubmit?serviceCode=" + serviceCode) 
              return
        if serviceCode == "register":
           self.redirect("/register") 
           return 

     if self.request.get('submit')[0:4] == "Back": 
        nextpage = forms[formSubscript].priorSeq 

     if self.request.get('submit') == "Validate Form": 
        nextpage = forms[formSubscript].ofSeq   #jump to last page 

     #todo - how to handle data from the upsell order page 
     if self.request.get('submit')[0:5] == "Order": 
        nextpage = 1 

     if nextpage > 0: 
       #find the subscript in the forms array that contains our current page 
       #formSubscript = self.lookupFormSubscriptByPage(forms, nextpage, serviceCode)
       URL = "formHandler?serviceCode=" + serviceCode + "&page=" + str(nextpage) 
       self.redirect(URL) 
       

     #invalid fall through logic 
     #TODO: probably need to change this to throw an exception 
     self.response.out.write("<H3>No Button Handler Redirect for Button Clicked (debug location=2781) ButtonValue=" + self.request.get('submit') + "</h3>") 


#This is outside of the above class so can be shared by other classes 
def lookupFormSubscriptByPage(forms, pagenum, serviceCode): 
       booMatch = False 
       formSubscript = 0 
       for form in forms: 
         #self.response.out.write("form.seq=" + str(form.seq) + " form.serviceCode=" + form.serviceCode + "<BR>") 
         if form.seq == pagenum and form.serviceCode == serviceCode:   
            booMatch = True 
            break 
         formSubscript += 1 

       if not booMatch: 
         self.response.out.write("<H3>page or serviceCode not found as valid in forms array</h3>") 
         self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
         return 

       return formSubscript 




class Register(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     #we get here when user FormManager serviceCode = "Register" and user clicks "Submit" on last page 

     #retrieve any data already entered  
     mySession = Session()
     if not 'sessionkey' in mySession:
        self.response.out.write("<h1>No Session data exists to register new user.</h1>")
        return 

     sessionkey = mySession['sessionkey']
     session = CumulusSession.get(sessionkey) 
     try:
       session.registerSubscriber()
     except (CumulusDBModelCustomException), e:
        self.response.out.write("<h1>registerSubscriber Raised Error: " + str(e) + "</h1>")
        #text = sys.exc_info()
        #self.response.out.write(text) 
        return 
       
     self.redirect("/myHome")



#This is outside of the above class so can be shared by other classes 
def lookupFormSubscriptByPage(forms, pagenum, serviceCode): 
       booMatch = False 
       formSubscript = 0 
       for form in forms: 
         #self.response.out.write("form.seq=" + str(form.seq) + " form.serviceCode=" + form.serviceCode + "<BR>") 
         if form.seq == pagenum and form.serviceCode == serviceCode:   
            booMatch = True 
            break 
         formSubscript += 1 

       if not booMatch: 
         self.response.out.write("<H3>page or serviceCode not found as valid in forms array</h3>") 
         self.response.out.write("<H3>Press your browser's back key to return to the previous page</H3>")
         return 

       return formSubscript 




class OneCloudSetupIndivSave(webapp.RequestHandler):
  """ Saves session variable (not order) """ 

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):

     mySession = Session()

     if not 'sessionkey' in mySession:
        sessionkey = None 
        flag = " (SessionKey Not Found)" 
     else: 
        sessionkey = mySession['sessionkey'] 
        flag = " (SessionKey Found)" 
 
     log = CumulusLog()    
     log.category = "OneCloudSetupIndivSave:Get" 
     log.ipaddress = self.request.remote_addr 
     log.message = "sessionkey=" + str(sessionkey) + flag 
     log.put() 

     log = CumulusLog()    
     log.category = "OneCloudSetupIndivSave:Get" 
     log.ipaddress = self.request.remote_addr 
     log.message = "temp" 

     #create a new record if necessary, otherwise retrieve prior one 
     if sessionkey:
        session = CumulusSession.get(sessionkey) 
        session.dateTimeModified = datetime.datetime.now() 
        log.message = "retrieved existing sessionkey=" + str(sessionkey) + " Domain=" + str(session.domain)
     else: 
        session = CumulusSession()
        session.dateTimeCreated  = datetime.datetime.now() 
        session.dateTimeModified = session.dateTimeCreated
        session.serviceCode      = self.request.get('serviceCode')
        session.pagesSubmitted = [False] * 12  #go ahead and init for 12 pages, even though we will probably have less 
        log.message = "no sessionkey available, creating new CumulusSession()" 

     log.put() 
     

     #TODO - need to check no duplicate domain name/product combo before storing a potential duplicate one 
     if session.userEmail > ' ' and session.userPassword > ' ': 
        returnURL = atom.url.Url('http', settings.HOST_NAME, path='/login')
        specialMessage = ("We have saved your data under the email/password you provided previously." + 
                         "<br/><br/>You can return to this web page to login and continue: <br/>" + 
                         "<a href='" +  str(returnURL) + "'>" + str(returnURL) + "</a>" )
        #specialMessage = None   # un-comment this line when you want to test re-save with same user 
        showUserPass = "N" 
     else:
        specialMessage = None 
        showUserPass = "Y" 

     orderpage = "formHandler?serviceCode=" + self.request.get('serviceCode') + "&page=1"

     self.renderPage('templates/customer/register.html', 
                     {"showUserPass": showUserPass, 
                      "specialMessage": specialMessage, 
                      "orderpage":orderpage,
                      "now": datetime.datetime.now()
                      }
                     ) 



  def post(self):

     mySession = Session()

     if not 'sessionkey' in mySession:
        sessionkey = None 
        flag = " (SessionKey Not Found)" 
     else: 
        sessionkey = mySession['sessionkey'] 
        flag = " (SessionKey Found)" 
 
     log = CumulusLog()    
     log.category = "OneCloudSetupIndivSave:Post" 
     log.ipaddress = self.request.remote_addr 
     log.message = "sessionkey=" + str(sessionkey) + flag 
     log.put() 

     log = CumulusLog()    
     log.category = "OneCloudSetupIndivSave:Post" 
     log.ipaddress = self.request.remote_addr 
     log.message = "temp" 

     #create a new record if necessary, otherwise retrieve prior one 
     if sessionkey:
          session  = CumulusSession.get(sessionkey) 
          session.dateTimeModified = datetime.datetime.now() 
          sessionkey = session.key
          log.message = "retrieved existing sessionkey=" + str(sessionkey) + " Domain=" + str(session.domain)
     else: 
          session = CumulusSession()
          session.dateTimeCreated  = datetime.datetime.now() 
          session.dateTimeModified = session.dateTimeCreated
          session.serviceCode      = "1CloudI" 
          session.pagesSubmitted   = [False] * 12  #go ahead and init for 12 pages, even though we will probably have less 
          log.message = "no sessionkey available, creating new CumulusSession()" 

     log.put() 

     # don't allow two people to use same email 
     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1", self.request.get('log')) 
     LIMIT = 2 
     returnURL = "" 
     subscriberList = query.fetch(LIMIT,offset=0);

     if len(subscriberList) > 0: 
        specialMessage = "<font color=red>That email is already in use, please use a different email.</font><br/><br/>" 
        showUserPass = "N"  #force the form to show the user/password fields again 
     else:
        session.userEmail          = self.request.get('log').lower() 
        session.userPassword       = self.request.get('pwd')
        session.isSaveAndComeBack = True 
        session.put() 
        showUserPass = "N" #don't show the user/password fields again, only the specialMessage 

        #Now we have to store a subscriber record, even though most of it is empty. 
        #This is to avoid two different logins, as all logins are done by the "Subscriber" table. 
        subscriber = Subscriber() 
        subscriber.userEmail    = session.userEmail 
        subscriber.userPassword = session.userPassword 
        if session.firstname: 
           subscriber.firstname = session.firstname 
        if session.lastname: 
           subscriber.lastname = session.lastname

        subscriber.put() 

        returnURL = atom.url.Url('http', settings.HOST_NAME, path='/login')
        specialMessage = ("We have saved your data under the email/password that you just provided." + 
                         "<br/><br/>You can return to this web page to login and continue: <br/>" + 
                         "<a href='" +  str(returnURL) + "'>" + str(returnURL) + "</a>" )

        #send email so user won't forget URL and his username 
        message = mail.EmailMessage()
        message.sender = "Neal Walters <googleadmin@3wcloud.com>"
        message.subject = "3WCloud.com - Link to Continue Your Order" 
        message.to = self.request.get('log')
        specialMessage += ("<BR>Your username is the email address used in this email." + 
                           "<BR><BR>The 3WCloud.com Team") 
        message.html = specialMessage 
        message.send()


     self.renderPage('templates/customer/register.html', 
                     {"showUserPass": showUserPass,
                      "specialMessage": specialMessage, 
                      "now": datetime.datetime.now()
                      }
                     )  





class OneCloudSetupIndivSubmit(webapp.RequestHandler):
  """ Saves Subscriber, Order, Service to Database """ 

  ### todo - what if user changes data when he clicks "Submit" - need to test that it is saved 

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):

     debugText = "" 
     SUBMIT = True 


     mySession = Session()

     if not 'sessionkey' in mySession:
        sessionkey = None 
     else: 
        sessionkey = mySession['sessionkey']

     #we shouldn't be here without a session, but possible session timeout...  
     if not sessionkey:
        self.response.out.write("<h3>Lost session information, please logon again. </h3>")
        url = atom.url.Url('http', settings.HOST_NAME, path='/login')
        self.response.out.write ("<a href='" + str(url) + "'>" + str(url) + "</a>")
        return

     #get the session record 
     session = CumulusSession.get(sessionkey) 
     if not session:
        self.response.out.write ("<h3>Error: No session record exists with sessionkey = " + str(sessionkey) + "</h3>") 
        return

     ##########################  SUBMIT THE ORDER ############################################## 
     # If user cancelled from paypal, his order is submitted, then he can choose to resubmit,
     # in which case we don't need to store the order again, only run through the Paypal Logic. 
     orderKey = self.request.get("resubmitOrderKey") 
     if orderKey > "": 
        order = Order.get(orderKey)  #retrieve previous order 
     else: 
        order = Order() 
        #TODO - when we add new products, we will have to call different methods here 
        orderKey = order.SubmitOneCloud(session) 
     ###########################################################################################

     mySession['orderKey'] = orderKey  #used to correlate on the PaypalSuccess or PaypalFailure
                                       #when user returns from Paypal 


     serviceCode = self.request.get('serviceCode') 
     query = db.GqlQuery("SELECT * FROM ServiceType WHERE code = :1 ", serviceCode)   
     LIMIT = 2 
     serviceTypeList = query.fetch(LIMIT,offset=0)
     if len(serviceTypeList) == 0: 
        self.response.out.write("<h2>No ServiceType found for serviceCode=" + serviceCode + "</h2>") 
        return 

     serviceType = serviceTypeList[0] 
    
     #These two lines maybe old logic - when we are sending user to login form instead of home page 
     dynamicHTML = "Your order has been submitted, we will complete your setup within 2 business days." 
     showUserPass = "N"

     #We send form to browser, then let brower auto-post back to Paypal 
     #This javascripts hides the entire div tag called myText, and only shows it after 4 seconds.
     #Usually the page will auto-submit within 4 seconds.
     #If user has JavaScript disabled, the hideDiv won't hide, and the text should be shown from 
     #the start. 
     javascript = """
<SCRIPT language="JavaScript">
function submitform()
{
  hideDiv();
  document.PaypalForm.submit();
  window.setTimeout(showDiv,4000);  // show the div text after 4 seconds (in case auto-submit fails) 
}
function hideDiv() {
    if (document.getElementById) { // DOM3 = IE5, NS6
        document.getElementById('myText').style.visibility = 'hidden'; 
        }
    else {
        if (document.layers) { // Netscape 4
            document.hideShow.visibility = 'hidden';
    }
    else { // IE 4
        document.all.hideShow.style.visibility = 'hidden';
        }
    }
} 
function showDiv()
{
   if (document.getElementById) { // DOM3 = IE5, NS6
       document.getElementById('myText').style.visibility = 'visible';
      }
   else {
      if (document.layers) { // Netscape 4
          document.hideShow.visibility = 'visible';
   }
   else { // IE 4
      document.all.hideShow.style.visibility = 'visible';
   }
} 
}
</SCRIPT>
     """

     paypalForm = getCommonPaypalForm(True)  #parm tells to hide all fields 

     objKeyValuePair = KeyValuePair() 
     imageURL   = objKeyValuePair.getValueFromKey("Paypal_Image_URL") 
     PaypalMode = objKeyValuePair.getValueFromKey("PaypalMode") 
     business = "temp"  #set variable outside of scope 
     paypalPostAction = "temp"

     import logging
     logging.debug("PaypalMode=" + str(PaypalMode)) 

     #NOTE: There is no currencyType in BigTable so amounts are stored as pennies! 
     #      So below we use the get methods that take care of the divide by 100 

     if not serviceType.ratePlan: 
        self.response.out.write("<h1>No ratePlan associated with this serviceType.  Admin must fix.</h1>")
        return 
     recurringAmount   = str(serviceType.ratePlan.getRecurringAmount())
     oneTimeAmount     = str(serviceType.ratePlan.getOnetimeAmount())
     logging.debug("oneTimeAmount=" + oneTimeAmount) 
     logging.debug("recurringAmount=" + recurringAmount) 

     if PaypalMode.upper() == "TEST": 
        paypalPostAction = objKeyValuePair.getValueFromKey("Paypal_URL_Sandbox") 
        business = objKeyValuePair.getValueFromKey("Paypal_Seller_Account_Sandbox") 
     elif PaypalMode.upper() == "PROD":
        paypalPostAction = objKeyValuePair.getValueFromKey("Paypal_URL_Production") 
        business = objKeyValuePair.getValueFromKey("Paypal_Seller_Account_Production") 
     else:
        self.response.out.write("<h2>PaypalMode=" + PaypalMode + " but expecting value of 'PROD' or 'TEST' </h2>") 
        return 
       
        
     #objPaypalAPI = PaypalAPI()
     #token = objPaypalAPI.getToken(oneTimeAmount) 


     if not serviceType.ratePlan: 
        self.response.out.write("<h2>RatePlan is not associated with serviceCode=" + serviceCode + "</h2>") 
        return 
        
     billingPeriod   = serviceType.ratePlan.billingPeriod
     billingInterval = serviceType.ratePlan.billingInterval 

     productName = serviceType.name 
     itemName    = serviceType.name 

     invoice = str(order.key().id())   #pass the order-id to Paypal so Paypal will pass it back to the returnURL 

     if self.request.url.startswith("https"):
        httpOrHttps = "https"
     else: 
        httpOrHttps = "http"

     returnURL       =  str(atom.url.Url(httpOrHttps, settings.HOST_NAME, path='/PaypalCompleted?parm1=1'))
     cancelReturnURL =  str(atom.url.Url(httpOrHttps, settings.HOST_NAME, path='/PaypalFailure'))
     notifyURL       =  str(atom.url.Url(httpOrHttps, settings.HOST_NAME, path='/PaypalIPN'))

     returnURL       = fix443(httpOrHttps,returnURL) 
     cancelReturnURL = fix443(httpOrHttps,cancelReturnURL) 
     notifyURL       = fix443(httpOrHttps,notifyURL) 

     #substitute variable in the big form above 
     #  any variables that are numbers must be wrapped with the str() function before being used in the replace! 
     paypalForm = paypalForm.replace("&imageURL",str(imageURL)) 
     paypalForm = paypalForm.replace("&business",str(business)) 
     paypalForm = paypalForm.replace("&oneTimeAmount",str(oneTimeAmount)) 
     paypalForm = paypalForm.replace("&recurringAmount",str(recurringAmount)) 
     paypalForm = paypalForm.replace("&cancelReturnURL",cancelReturnURL) 
     paypalForm = paypalForm.replace("&billingPeriod",billingPeriod) 
     paypalForm = paypalForm.replace("&billingInterval",str(billingInterval)) 
     paypalForm = paypalForm.replace("&productName",productName) 
     paypalForm = paypalForm.replace("&itemName",itemName)
     paypalForm = paypalForm.replace("&paypalPostAction",paypalPostAction) 
     paypalForm = paypalForm.replace("&invoice",invoice)
     #paypalForm = paypalForm.replace("&token",token)
     paypalForm = paypalForm.replace("&notifyURL",notifyURL)
     paypalForm = paypalForm.replace("&returnURL",returnURL) 
     paypalForm = paypalForm.replace("&cancelReturnURL",cancelReturnURL) 


     #for now, keep a log of the Paypal form (for potential debugging) 
     log = CumulusLog()    #log invalid signins  
     log.category  = "OneCloudSetupIndivSubmit:Get:PaypalForm" 
     log.message   = "httpOrHttps=" + httpOrHttps + " returnURL=" + returnURL + " notifyURL=" + notifyURL 
     log.ipaddress = self.request.remote_addr 
     log.largeText = paypalForm   #saved to db without the Javascript 
     log.put() 

     #For first test, send the above and ignore what is below. 
     #The above form has auto-script to auto-submit form to Paypal. 
     self.response.out.write(javascript + paypalForm) 
     return 


#=======================================================
# END Specific Customer Data Entry Forms 
#=======================================================

class OrderPage(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def post(self):
     ReportTaskLogs.get(self);

  def get(self):
     debugText = ""

     #look for ?parm=ALL on the URL 
     if self.request.get('parm') == 'ALL': 
        query = ServiceType.gql("")  #no where clause needed
        #outText +=  genericReportTitle + "\n"
     else: 
        query = ServiceType.gql("where code = :1", self.request.get('serviceCode'))  #no where clause needed
        #outText += ( "<h3>Sellable ServiceTypes - and related Bundles</h3>\n")

     LIMIT = 1000
     serviceTypeList = query.fetch(LIMIT,offset=0)

     if len(serviceTypeList) < 1: 
        self.response.out.write("<h3>ServiceCode (product) not found </h3>") 
        return 

     if len(serviceTypeList) > 1: 
        self.response.out.write("<h3>More than one matching ServiceCode was found </h3>") 
        return 

     #what if he picked two products already?  
     serviceType = serviceTypeList[0]  #should only be one item in list (at subscript=0)  

     #assuming for now that upsells are not recursive/nested 


     stUpsells = db.get(serviceType.upsells)

     #todo - past a list to the form - and let the form do the formatting 
     subCounter = 0 
     upsells = [] 
     for upsell in stUpsells: 
         subCounter += 1 
         #if subCounter == 1:
         #   outText += ( "  <UL>\n")   #don't print unless we have at least one child
         #outText += ( "<LI><a href='order?serviceCode=" + self.request.get('serviceCode') + 
         #           "&relatedServiceCode=" + upsell.code + "'>" + 
         #           upsell.name +  "</a></LI>\n") 
         upsellItem = Upsell() 
         upsellItem.name = upsell.name 
         upsellItem.url = ("order?serviceCode=" + self.request.get('serviceCode') + 
                    "&relatedServiceCode=" + upsell.code)
         upsellItem.selected = False   #TODO: need to store this in session variable 
         upsells.append(upsellItem) 

     #if subCounter > 0:
     #    outText += ( "  </UL>\n")  #don't print unless we have at least one child



     if self.request.get('parm') == 'ALL': 
        # Report Above showed "ALL" (if parm was set, 
        # so now, just give a list of only the sellable products (without the bundles/expansion) 
        query = ServiceType.gql("where isSellable = :1", True)  #no where clause needed
        LIMIT = 1000
        serviceList = query.fetch(LIMIT,offset=0)

        #outText += ( "<h3>All Sellable ServiceTypes</h3>\n")
        #outText += ( "<OL>\n")

        #for service in serviceList:
        #   outText += ( "<LI>" + service.code + "&nbsp;&nbsp; name='" + service.name + "'" ) 
        #outText += ( "</OL>\n")

     serviceTypeDetail = None 
     if self.request.get('relatedServiceCode') > " ": 
        query = ServiceType.gql("where code = :1", self.request.get('relatedServiceCode'))  #no where clause needed
        LIMIT = 1000
        serviceTypeListUpsells = query.fetch(LIMIT,offset=0)
        serviceTypeDetail = serviceTypeListUpsells[0] 

        

     templateDictionaryLocal = {"upsells": upsells, 
                                "serviceType": serviceType,
                                "serviceTypeDetail": serviceTypeDetail 
                               }
                               
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/customer/order.html', templateDictionaryLocal)

        
#end of class 




#=======================================================
# START of Login/Logout... 
#=======================================================


class Login(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     log = CumulusLog()    #log invalid signins  
     log.category = "Login:Get" 
     log.message = "" 
     log.ipaddress = self.request.remote_addr 
     log.put() 


     #Can no longer clear session variables here - 07/08/2009 - because
     #user can fill out partial form, then login on as "returning customer" 
     #mySession = Session()
     #mySession.clear()       #clean-up any junk session variables 

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']

     signinError = ""


     self.renderPage('templates/customer/signin.html', 
                     {"postback": "N", 
                      "action": "login", 
                      "signinError": signinError,
                      "now": datetime.datetime.now()
                      }
                     ) 

  def post(self):

     debugText = "" 
     #mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     #currentUser = mySession['username'] 

     username = self.request.get("log").lower()
     password = self.request.get("pwd")


     #retrieve session row based on email/password 
     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1 AND userPassword = :2", username, password) 
     LIMIT = 10
     subscriberList = query.fetch(LIMIT,offset=0);

     if len(subscriberList) == 0: 
        signinError = "Username/password combination not found" 
        self.renderPage('templates/customer/signin.html', 
                     {"postback": "Y", 
                      "action": "login", 
                      "signinError": signinError,
                      "now": datetime.datetime.now()
                      }
                     ) 
        log = CumulusLog()    #log invalid signins  
        log.category = "Login:Failed" 
        log.message = username + "/" + password 
        log.username = username 
        log.ipaddress = self.request.remote_addr 
        log.put() 
        return   #return now so the redirect below doesn't go back to MyHome
                 #thus losing the signinError message 
     else:        
        mySession = Session() 
        mySession['subscriberkey'] = subscriberList[0].key()  
        mySession['username'] = username
        subscriber = subscriberList[0] 
        if subscriber.isAdmin: 
           mySession['isAdmin'] = True 
        else:
           mySession['isAdmin'] = False 

        optionalLogMessage = "" 
        #It's possible that user was entering form data, and selected to "Continue as Returning Customer".
        #In this scenario, the session data so far was not identified to his userid/password, 
        #so now we need to add it. 
        if 'sessionkey' in mySession:
           sessionkey = mySession['sessionkey']
           #create a new record if necessary, otherwise retrieve prior one 
           session = CumulusSession.get(sessionkey)   #retrieve session record from BigTable Database 
           #database needs this key to be in lower case sense where clause is case sensitive 
           session.userEmail = username.lower() 
           session.userPassword = password 
           session.put() 
           optionalLogMessage = " /Existing Session Data Updated with user/pass" 


        query = db.GqlQuery("SELECT * FROM Service WHERE subscriber = :1 ", subscriber) 
        LIMIT = 100
        serviceList = query.fetch(LIMIT,offset=0);
        if len(serviceList) > 0:   
           #in case user has multiple services, we can't assume oneCloud is the first service 
           for service in serviceList: 
              if isinstance(service,ServiceOneCloud) and service.serviceState == "Active":
                 mySession['userDomain'] = service.domain  
                 mySession['OneCloudStatus'] = service.serviceState 
                 optionalLogMessage += "OneCloudStatus=" + service.serviceState
              else:
                 optionalLogMessage += "OneCloudStatus is not undefined???" 
        else:
              optionalLogMessage += "No Services for this user" 

        #custom log in bigTable 
        log = CumulusLog() 
        log.category = "Login:Succeeded" 
        log.username = subscriber.userEmail 
        log.message = optionalLogMessage
        log.ipaddress = self.request.remote_addr 
        log.put() 


     submitButtonText = "" 
     redirectPageAfterLogin = "" 
     if 'submitButtonText' in mySession:
        submitButtonText = mySession['submitButtonText'] 
        if 'redirectPageAfterLogin' in mySession:
           redirectPageAfterLogin = mySession['redirectPageAfterLogin'] 
        if 'redirectPageAfterLogin' in mySession:
           mySession.delete_item('redirectPageAfterLogin')
        if 'submitButtonText' in mySession:
           mySession.delete_item('submitButtonText')


     if submitButtonText == "Continue as Returning Customer": 
        self.redirect(redirectPageAfterLogin) 
     else:
        self.redirect("/myHome")



class Logout(webapp.RequestHandler):   #for employees, not customers 

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     mySession = Session()

     #custom log in bigTable 
     log = CumulusLog() 
     log.category = "Logout" 
     log.ipaddress = self.request.remote_addr 
     if 'username' in mySession: 
        log.message = mySession['username']
     else: 
        log.message = "lost username from session state" 
     log.put() 

     mySession.clear() 
     self.redirect("login") 



class LostPassword(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     log = CumulusLog()   
     log.category = "LostPass:Get" 
     log.message = "" 
     log.ipaddress = self.request.remote_addr 
     log.put() 


     #Can no longer clear session variables here - 07/08/2009 - because
     #user can fill out partial form, then login on as "returning customer" 
     #mySession = Session()
     #mySession.clear()       #clean-up any junk session variables 

     params = {} 
     params = commonUserCode(params,self.request.url)
     #debugText = "currentUser=" + currentUser 
     currentUser = params['user']

     signinError = ""


     self.renderPage('templates/customer/signin.html', 
                     {"postback": "N", 
                      "action": "/lostpassword", 
                      "signinError": signinError,
                      "lostPassword": "Y",
                      "now": datetime.datetime.now()
                      }
                     ) 


  def post(self):
     userEmail =  self.request.get("log").lower() 

     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1", userEmail) 
     LIMIT = 1 
     subscriberList = query.fetch(LIMIT,offset=0);

     if len(subscriberList) > 0: 
         subscriber = subscriberList[0] 
         guid = str(uuid.uuid4())

         subscriber.resetPasswordGuid = guid 
         subscriber.resetPasswordRequestDateTime = datetime.datetime.now() 
         #subscriber.resetPasswordGuid = guid 
         #subscriber.resetPasswordRequestDateTime = datetime.datetime.now() 
         subscriber.put() 

         log = CumulusLog()   
         log.category = "LostPassword:Post" 
         log.message = "Valid: Email=" + userEmail + " Updated: key=" + str(subscriber.key().id()) + "guid=" + guid 
         log.ipaddress = self.request.remote_addr 
         log.put() 

         if self.request.url.startswith("https"):
            httpOrHttps = "https"
         else: 
            httpOrHttps = "http"
         strURL = str(atom.url.Url('http', settings.HOST_NAME, path='/resetPassword?code=' + guid))

         message = mail.EmailMessage() 
         message.sender = "Neal Walters <googleadmin@3wcloud.com>"
         message.subject = "3WCloud - Password Reset"
         message.to = userEmail
         message.html = """
<h3>Dear Customer</h3>,
<BR><BR>
Please follow this link to reset your password: 
<a href='""" + strURL + """'>""" + strURL + """</a>
<BR><BR>
Please note, this does not change your password on any of the sites that we set up for you. 
<BR><BR>
The 3WCloud.com Team
"""

         message.send()
         signinError = "Email has been sent to user above" 
     else:
         signinError = "Email has been sent"   #slightly different message for debugging 
                                               #but ambigous for users who might be trying to type in 
                                               #totally made-up emails 
         log = CumulusLog()   
         log.category = "LostPassword:Post" 
         log.message = "Invalid: Email=" + userEmail
         log.ipaddress = self.request.remote_addr 
         log.put() 


     self.renderPage('templates/customer/signin.html', 
                     {"postback": "N", 
                      "action": "/lostpassword", 
                      "signinError": signinError,
                      "lostPassword": "Y",
                      "now": datetime.datetime.now()
                      }
                     ) 



class ResetPassword(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
     log = CumulusLog()   
     log.category = "ResetPass:Get" 
     log.message = "" 
     log.ipaddress = self.request.remote_addr 
     log.put() 

     query = db.GqlQuery("SELECT * FROM Subscriber WHERE resetPasswordGuid = :1", self.request.get('code')) 
     LIMIT = 1 
     subscriberList = query.fetch(LIMIT,offset=0);

     userEmail = "" 
     if len(subscriberList) > 0: 
         subscriber = subscriberList[0] 
         userEmail = subscriber.userEmail
         signinError = "Reset Password Above"
     else:
         signinError = "ERROR: Reset code not found " 

     action = "/resetpassword"


     self.renderPage('templates/customer/signin.html', 
                     {"postback": "N", 
                      "action": action, 
                      "signinError": signinError,
                      "lostPassword": "N",
                      "resetPassword": "Y",
                      "userEmail": userEmail, 
                      "resetCode": self.request.get('code'),
                      "now": datetime.datetime.now()
                      }
                     ) 


  def post(self):
     userEmail =  self.request.get("log").lower() 
     resetCode = self.request.get("resetCode") 

     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1 and resetPasswordGuid = :2", userEmail, resetCode) 
     LIMIT = 1 
     subscriberList = query.fetch(LIMIT,offset=0);

     if len(subscriberList) > 0: 
         subscriber = subscriberList[0] 

         #update database fields   
         subscriber.resetPasswordGuid = ""
         subscriber.userPassword = self.request.get("pwd")
         subscriber.put() 

         log = CumulusLog()   
         log.category = "ResetPassword:Post" 
         log.message = "Valid: Email=" + userEmail  
         log.ipaddress = self.request.remote_addr 
         log.put()  

         signinError = "Password has been reset" 

         #set sesssion variables as if user had just done a valid login, then send him to home page 
         mySession = Session() 
         mySession['username'] = userEmail 
         mySession['subscriberkey'] = subscriber.key()  
         if subscriber.isAdmin: 
            mySession['isAdmin'] = True 
         else:
            mySession['isAdmin'] = False 

     else: 
         signinError = "ERROR: username or resetCode not found"  

     self.redirect("/myHome")




class FileUpload(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     self.renderPage('templates/fileUpload.html', vars)

  def post(self):
     user = loggedin(self)
     if not user:
        return;     #stop user if not logged in  
     fileContents = self.request.get('upfile')
     position = fileContents.find("<",0,3)
     if position == -1: 
        self.response.out.write(
             "<h3><font color='red'>No XML in File</font></h3>");
        return; 
     #parser = make_parser()
     self.response.out.write("File Contents=<br/>" + stripTags(fileContents))
     self.response.out.write("<h3>Start Parsing</h3>") 


     global XMLRESULTS, XMLFIELDTYPE, XMLFIELD, XMLVALUES
     XMLRESULTS = "empty: "
     parser1 = parseString(fileContents,XmlContentHandler());
     #try:
     #   parser1 = parseString(fileContents,XmlContentHandler());
     #except (Exception), e:
     #   self.response.out.write("<font color=red>EXCEPTION=" + str(e) + "</font><br/>"); 
     #   self.response.out.write(
     #   "XMLField=" + XMLFIELD + 
     #   " XMLFieldType=" + XMLFIELDTYPE + 
     #   " XMLFieldValue=" + XMLVALUES + 
     #   " <br/>"
     #    );
     self.response.out.write("<font color=green>XMLResults=</font>" + XMLRESULTS); 

#end of class 

class XmlContentHandler(ContentHandler): 
   def __init__ (self):
      ContentHandler.__init__(self);
      self.depth = 0;
      self.output = ''; 
      #XMLRESULTS = ''; 
   def startElement (self, tagname, attributes):
      global XMLRESULTS, XMLVALUES, XMLFIELD, XMLFIELDTYPE, OBJ
      XMLVALUES = ""
      dic = {"Workers": Workers, "CustomerOrders": CustomerOrders, "TaskLog": TaskLog, "Tasks": Tasks}
      #XMLRESULTS = XMLRESULTS + "Start-TagFound=" + tagname + "<br/>";
      matchTagname = "entity"; 
      if tagname == matchTagname:  
         XMLRESULTS = XMLRESULTS + "Found start tag=" + matchTagname + "<br/>"; 
         for attribute in attributes.getNames():
            matchAttrname = "kind"
            if attribute == matchAttrname:
               kind = str(attributes.getValue(attribute));  #str to convert unicode to string? 
               XMLRESULTS = XMLRESULTS + "TableName (Kind)=" + kind + "<br/>"; 
               OBJ = dic[kind]();
      matchTagname = "property"; 
      if tagname == matchTagname:  
         XMLRESULTS = XMLRESULTS + "Found start tag=" + matchTagname + "<br/>"; 
         for attribute in attributes.getNames():
            if attribute == "name":
               XMLFIELD = attributes.getValue(attribute); 
               XMLRESULTS = XMLRESULTS + " attribute=name " + " fieldname=" + XMLFIELD; 
            if attribute == "type":
               XMLFIELDTYPE = attributes.getValue(attribute); 
               XMLRESULTS = XMLRESULTS + " attribute=type " + " fieldtype=" + XMLFIELDTYPE;
         
   def characters(self,chars):
      global XMLVALUES
      XMLVALUES = XMLVALUES + chars; 

   def endElement (self, tagname):
      global XMLRESULTS, XMLVALUES, XMLFIELD, XMLFIELDTYPE
      XMLRESULTS = XMLRESULTS + " End-TagFound=" + tagname + "<br/>";
      matchTagname = "entity";
      if tagname == matchTagname:  #Tagname 
         XMLRESULTS = XMLRESULTS + " End-Tag-Found=" + matchTagname + "<br/>"; 
         XMLRESULTS = XMLRESULTS + " PUT ";
         OBJ.put(); 
      processedFieldType = False 
      if tagname == "property":  
         XMLRESULTS = (XMLRESULTS + "<BR>Found end property tag=" + 
            " FieldType=" + XMLFIELDTYPE + " Value=" + XMLVALUES + "<br/>");
         #processedFieldType = False 
         if XMLFIELDTYPE == "gd:when": 
            XMLRESULTS = (XMLRESULTS + " SetDate");
            position = XMLVALUES.find(".") 
            if position > 1: 
               XMLVALUES = XMLVALUES[0:position]
            datetimeTuple = time.strptime(XMLVALUES, "%Y-%m-%d %H:%M:%S");
            #setattr(OBJ,XMLFIELD,datetime.datetime(datetimeTuple.tm_year, 
            #                                       datetimeTuple.tm_mon,
            #                                       datetimeTuple.tm_mday,
            #                                       datetimeTuple.tm_hour,
            #                                       datetimeTuple.tm_min,
            #                                       datetimeTuple.tm_sec))
            #shorter way to do the same: 
            realDateTime = datetime.datetime.fromtimestamp(time.mktime(datetimeTuple));
            setattr(OBJ,XMLFIELD,realDateTime); 
            processedFieldType == True;
            XMLRESULTS = (XMLRESULTS + " End:SetDate");
         elif XMLFIELDTYPE == "int": 
            XMLRESULTS = (XMLRESULTS + " SetInt");
            realInt = int(XMLVALUES) 
            setattr(OBJ,XMLFIELD,realInt); 
            processedFieldType == True;
            XMLRESULTS = (XMLRESULTS + " End:SetInt");
         elif XMLFIELDTYPE == "bool": 
            XMLRESULTS = (XMLRESULTS + " SetBoolean");
            realInt = bool(XMLVALUES) 
            setattr(OBJ,XMLFIELD,realInt); 
            processedFieldType == True;
            XMLRESULTS = (XMLRESULTS + " End:SetBoolean");
         elif XMLFIELDTYPE != "null":   #don't do a "setattr" on NULL fields 
            XMLRESULTS = (XMLRESULTS + "SetDefault");
            setattr(OBJ,XMLFIELD,XMLVALUES); 
            XMLRESULTS = (XMLRESULTS + "End:SetDefault");
      XMLRESULTS = (XMLRESULTS + "end:EndElement");

      #ideas for future: From this post: 
      # http://www.python-forum.org/pythonforum/viewtopic.php?f=3&t=13106 
      # if the strings you have match the names of the classes you can
      #name = "A"
      #new_object = globals()[name]()
      #print(new_object.name)


class Test(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     vars = {'x': "My value for x" }
     self.renderPage('templates/test.html', vars)


#end of class 

class Fix1(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values))

  def get(self):
     sessionkey = "ahgzd2Nsb3VkLWNvbS1wcm92aXNpb25pbmdyDgsSB1Nlc3Npb24Y7QQM"
     session = CumulusSession.get(sessionkey) 
     session.userEmail = "nwalters@sprynet.com" 
     session.userPassword = "temp1234" 
     session.put() 
     self.response.out.write("Session update completed"); 
     return 


     #mySession = Session()
     #mySession.delete_item('sessionkey')
     #return 

     query = Subscriber.gql(""); 
     LIMIT = 1000
     subscriberList = query.fetch(LIMIT,offset=0);
     for subscriber in subscriberList:
        if subscriber.userEmail in ["nwalters@sprynet.com","nealwalters@nealwalters.com","fpinto@filipe-pinto.com"]:
           subscriber.isAdmin = True 
        subscriber.put() 

     self.response.out.write("Updates to subscriber (for isAdmin) completed"); 

  def getold(self):
     query = Session.gql("order by lastname, firstname "); 
     LIMIT = 1000
     sessionList = query.fetch(LIMIT,offset=0);
     for session in sessionList:
        if session.userEmail == "fredflintstone@yahoo.com": 
           session.pagesSubmitted = [False,True,False,True] + [False] * 8 
        else: 
           session.pagesSubmitted = [False] * 12
        session.put() 

     self.response.out.write("Updates to session (for pagesSubmitted) completed"); 


#end of class 



class Fix2(webapp.RequestHandler):

  def get(self):
         #subscriber.get('ahgzd2Nsb3VkLWNvbS1wcm92aXNpb25pbmdyEgsSClN1YnNjcmliZXIY8YQBDA')
         key = 'ahgzd2Nsb3VkLWNvbS1wcm92aXNpb25pbmdyEQsSClN1YnNjcmliZXIYoAMM'
         guid = str(uuid.uuid4())

         #resetPasswordRequestDateTime = db.DateTimeProperty(auto_now=False)
         #resetPasswordGuid   = db.StringProperty()    

         subscriber = Subscriber.get(key) 
         if subscriber: 
           subscriber.resetPasswordGuid = guid 
           subscriber.resetPasswordRequestDateTime = datetime.datetime.now() 
           #subscriber.resetPasswordRequestDateTime = "bad data" 
           subscriber.garbage = "bad data" 
           subscriber.isWorker = False 
           subscriber.put()
           self.response.out.write("Subscriber updated with reset password info guid=" + guid) 
         else: 
           self.response.out.write("Subscriber not found key=" + key) 
            

class FixRatePlan(webapp.RequestHandler):

  def get(self):

     self.response.out.write("<h3>FixRatePlan Starting</h3>") 

     serviceList = Service.all().fetch(1000) 
     for service in serviceList:
        service.ratePlan = service.serviceType.ratePlan
        service.put()

     self.response.out.write("<h3>FixRatePlan Step 1 Completed</h3>") 

     serviceRatePlanList = ServiceRatePlan.all().fetch(1000) 
     for serviceRatePlan in serviceRatePlanList: 
         serviceRatePlan.service = serviceRatePlan.order.services[0]
         serviceRatePlan.put()

     self.response.out.write("<h3>FixRatePlan Step 2 Completed</h3>") 

            



class Fix2(webapp.RequestHandler):

  def get(self):
         #subscriber.get('ahgzd2Nsb3VkLWNvbS1wcm92aXNpb25pbmdyEgsSClN1YnNjcmliZXIY8YQBDA')
         key = 'ahgzd2Nsb3VkLWNvbS1wcm92aXNpb25pbmdyEQsSClN1YnNjcmliZXIYoAMM'
         guid = str(uuid.uuid4())

         #resetPasswordRequestDateTime = db.DateTimeProperty(auto_now=False)
         #resetPasswordGuid   = db.StringProperty()    

         subscriber = Subscriber.get(key) 
         if subscriber: 
           subscriber.resetPasswordGuid = guid 
           subscriber.resetPasswordRequestDateTime = datetime.datetime.now() 
           #subscriber.resetPasswordRequestDateTime = "bad data" 
           subscriber.garbage = "bad data" 
           subscriber.isWorker = False 
           subscriber.put()
           self.response.out.write("Subscriber updated with reset password info guid=" + guid) 
         else: 
           self.response.out.write("Subscriber not found key=" + key) 
            

class FixUserPass(webapp.RequestHandler):

  def get(self):

     email = "nealwalters@nealwalters.com"
     countUpdates = 0 
     subscriberList = Subscriber.gql("where userEmail = :1",email).fetch(1000) 
     for subscriber in subscriberList:
        subscriber.googleAppsUserid = email 
        subscriber.googleAppsPassword = "nw21214em" 
        countUpdates += 1 
        subscriber.put() 

     email = "nwalters@sprynet.com"
     subscriberList = Subscriber.gql("where userEmail = :1",email).fetch(1000) 
     for subscriber in subscriberList:
        subscriber.googleAppsUserid = email 
        subscriber.googleAppsPassword = "nw21214em" 
        countUpdates += 1 
        subscriber.put() 

     self.response.out.write("<h3>FixUserPass Completed updates=" + str(countUpdates) + "</h3>") 


class FixSubscriberDate(webapp.RequestHandler):

  def get(self):

     self.response.out.write("<h3>FixSubscriberDate Starting</h3>") 

     subscriberList = Subscriber.all().fetch(1000) 
     for subscriber in subscriberList:
        subscriber.dateTimeCreated = datetime.datetime.now() 
        subscriber.put() 

     self.response.out.write("<h3>FixSubscriberDate Step 1 Completed</h3>") 




class Provision(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    #-------- Following was for debug only ---------
    #self.response.out.write(
    #     "<h3>Template/Filename=" + fileName + "</h3>");
    #for k, v in values.iteritems():
    #   self.response.out.write(
    #     "<h3>Debug key=" + k + "</h3>");
    #   if k == 'params': 
    #      for k2, v2 in values['params'].iteritems():
    #        if isinstance(v2,str):
    #            self.response.out.write(
    #             "<h3>&nbsp;&nbsp;Debug2 key=" + k2 + " value=" + v2 + "</h3>");
    #        else:
    #            self.response.out.write(
    #              "<h3>&nbsp;&nbsp;Debug2 key=" + k2 + " " + stripTags(str(type(v2))) + "</h3>");
          
    self.response.out.write(template.render(path, values))

  def post(self):
    user = loggedin(self)
    if not user:
        return;     #stop user if not logged in  
       
    ynChangeSession = self.request.get('ynChangeSession');
    customerDomain = self.request.get('customerDomain');
    debugText = "" 
    resultFlag = -1; 
    processCode = self.request.get('processCode');

    mySession = Session()  #or own user is stored in Session variable
    if 'username' in mySession:
        user = mySession['username']
    else: 
        user = ""


    #if ynChangeSession is not None: 
    if ynChangeSession == "Y":
       debugText = debugText + "Setting Session Variables" 
       #domainKey = users.get_current_user().email() + ":customerDomain"
       domainKey = user + ":customerDomain"
       memcache.set(domainKey, customerDomain, CACHE_SECONDS)

    ynStartTask = self.request.get('ynStartTask')       
    if ynStartTask == "Y": 
       taskCode    = self.request.get('taskCode');
       debugText = debugText + " Got startTask with taskcode=" + taskCode; 
       taskLog1 = TaskLog(); 
       taskLog1.taskCode = taskCode; 
       #domainKey = users.get_current_user().email() + ":customerDomain";
       domainKey = user + ":customerDomain";
       taskLog1.customerDomain = memcache.get(domainKey);
       #taskLog1.workerEmail = users.get_current_user().email();
       taskLog1.workerEmail = user
       holdtime = datetime.datetime.now(); 
       taskLog1.eventStartedDateTime = holdtime;
       taskLog1.resultFlag = -1;  # -1 started (not completed) 
       #save time so we can update this record when user clicks the "TaskCompleted" button
       #domainKey = users.get_current_user().email() + ":startTime"
       #memcache.set(domainKey, holdtime, CACHE_SECONDS) 
       #--- UPDATE HERE -----
       taskLog1.put();  #save to BigTable database 
       debugText = debugText + " Stored new row" 
    
    ynCompleteTask = self.request.get('ynCompleteTask')       
    if ynCompleteTask == "Y": 
       taskCode       = self.request.get('taskCode');
       issues         = self.request.get('issues');
       resultFlagWeb  = self.request.get('resultFlag'); 

       resultFlag = -1; 
       if resultFlagWeb == "Success":
          resultFlag = 0;
       if resultFlagWeb == "Issues":
          resultFlag = 1;
       if resultFlagWeb == "ShowStopper":
          resultFlag = 2;
       if resultFlag == -1: 
          debugText = debugText + " Invalid value of resultFlagWeb=" + resultFlagWeb + ";" 

       mySession = Session()  #or own user is stored in Session variable
       if 'username' in mySession:
          user = mySession['username']
       else: 
          user = ""

       #domainKey = users.get_current_user().email() + ":startTime"
       #domainKey = user + ":startTime"
       #startedTime = memcache.get(domainKey);
       #domainKey = users.get_current_user().email() + ":customerDomain";
       domainKey = user + ":customerDomain";
       customerDomain = memcache.get(domainKey);
       debugText = debugText + " Complete Task; "
       #taskLogs = TaskLog.gql("SELECT * FROM TaskLog where taskCode = '" + taskCode + 
       #         "' and workerEmail = '" + users.get_current_user().email() + 
       #         "' and eventStartedDateTime = '" + startedTime + "'");
       #taskLogs = TaskLog.gql("SELECT * FROM TaskLog where taskCode = :1 " + 
       #taskLogs = db.GqlQuery("SELECT * FROM TaskLog where taskCode = :1 " + 
       #         " and workerEmail = :2 " +  
       #              " and eventStartedDateTime = :3",
       #                taskCode, 
       #                users.get_current_user().email(), 
       #                startedTime);  

       startedTime = self.request.get('taskStartedDateTime'); 
       #doesn't really have to be same workerEmail ... another worker might fix 
       #query = db.GqlQuery("SELECT * FROM TaskLog where taskCode = :1 " + 
       #         " and workerEmail = :2  and customerDomain = :3",
       #                taskCode, 
       #                users.get_current_user().email(),
       #                customerDomain
       #            );
       query = db.GqlQuery("SELECT * FROM TaskLog where taskCode = :1 " + 
                " and customerDomain = :2",
                taskCode, 
                customerDomain
                );

       taskLogs = query.fetch(1000); 
       
       debugText = debugText + " Query taskLogs Where customerDomain = " + str(customerDomain) + " taskCode=" + str(taskCode);
       debugText = debugText + "Len(taskLogs)=" + str(len(taskLogs)) 

       #if len(taskLogs) == 0:
       #   debugText = " <h1><font color='red'>No rows returned </font></h1>" 

       #else:   
       #debugText = debugText + "Rows Returned; " 
       #debugText = debugText + "&nbsp;&nbsp; len(taskLogs) = " + len(taskLogs); 
       for taskLog in taskLogs:
           debugText = debugText + " Row: StartedDateTime=" + str(taskLog.eventStartedDateTime);
           taskLog.eventCompletedDateTime = datetime.datetime.now(); 
           if issues > " ": 
              taskLog.issues = issues; 
              debugText = debugText + "Issues Changed";
           else: 
              debugText = debugText + "Issues Not Changed";
           taskLog.resultFlag = resultFlag; 
           #--- UPDATE HERE -----
           taskLog.put();  #update row back to BigTable database 
           debugText = debugText + "Updated Row; " 

    # NOW - just go run the get routine so we don't repeat logic 
    self.common(debugText);

  def getTasks(self, processCode):    
     query = Tasks.gql("WHERE processCode = :1 ORDER BY sequence", processCode);   
     LIMIT = 1000
     TasksList = query.fetch(LIMIT,offset=0);
     return TasksList

  def get(self):
     if not loggedin(self):
         return 
     self.common(self);


  def common(self,debugText):
     #self.response.out.write("loggedin=" + str(loggedin()))
     #user = users.get_current_user()
     #if user == None: 
     #   self.response.out.write(
     #     "<h3>Error: Please login to use this function<br/>" + 
     #     "<a href='" + 
     #     users.CreateLoginURL(self.request.path) + "?processCode=" + self.request.get('processCode') + 
     #     "'>Login</a></h3>")
     #   return;

     query = CustomerOrders.gql("")  #no where clause needed
     LIMIT = 1000
     customerOrdersList = query.fetch(LIMIT,offset=0);
        
     processCode = self.request.get('processCode');
     if processCode < ' ': 
        self.response.out.write(
          "<h3>Error:URL should contains process code, for example /reportTasks?processCode=xCloud</h3>");
        return;

     params = {}
     params = commonUserCode(params,self.request.url)

     if not params['customerDomain']:
        self.response.out.write(
          "<h3><font color='red'>Warning: Please select a customer domain</font></h3>");
        TasksList = None 
        
     else: 
      TasksList = self.getTasks(processCode)
      for task in TasksList:
        #this essentially "joins" and finds the corresponding rows in the TaskLog 
        #to the current taskCode that we are looping on. 
        #No need to match on email, because two different works might work on same customer/domain. 
        #TODO: need to add processCode to db-table and to this where clause 
        query = TaskLog.gql(
            "WHERE customerDomain = :1 and taskCode  = :2", 
            params['customerDomain'], task.taskCode);   
        LIMIT = 25
        TaskLogList = query.fetch(LIMIT,offset=0);
        task.ynStartedNotStored = "N";
        task.ynCompletedNotStored = "N";
        task.priorIssuesNS = "N"; 
        task.debug = "Len(TaskLogList)=" + str(len(TaskLogList)) + "<BR>Domain=" + str(params['customerDomain']);
        for tasklog in TaskLogList:
           task.ynStartedNotStored = "Y";  # just the fact we found a match means the task started 
           task.debug = task.debug + "<BR>" + " TaskLogResult=" + str(tasklog.resultFlag);
           task.eventStartedDateTimeNS = tasklog.eventStartedDateTime
           task.eventCompletedDateTimeNS = tasklog.eventCompletedDateTime
           #Concatenate all prior issues to show on form 
           if tasklog.issues: 
              #task.debug = task.debug + " debug1"
              if task.priorIssuesNS == "N":
                 task.priorIssuesNS = stripTags(tasklog.issues);  # no break on the first row 
                 task.debug = task.debug + " debug2=" + task.priorIssuesNS
              else: 
                 task.priorIssuesNS = task.priorIssuesNS + "<BR>" + stripTags(tasklog.issues);
                 task.debug = task.debug + " debug3=" + task.priorIssuesNS
           if tasklog.resultFlag == 0: 
              task.ynCompletedNotStored = "Y";
        #     TasksList.remove(task)    #remove the item from the list so it won't display 
        task.debug = task.debug + "<BR>ynStarted=" + task.ynStartedNotStored
        task.debug = task.debug + "<BR>ynCompleted=" + task.ynCompletedNotStored
        

     params['Tasks'] = TasksList 
     params['processCode'] = processCode

     #respond(request, user, template, params=None):
     #return respond(self.request, users.get_current_user(), 'templates\provision', params);  

     self.renderPage('templates/provision.html', 
                     {"Tasks": TasksList, 
                      "processCode": processCode,
                      "userMessage": params['userMessage'],
                      "sign_in": params['sign_in'],
                      "sign_out": params['sign_out'],
                      "user": params['user'],
                      "environment": params['environment'],
                      "is_admin": params['is_admin'],
                      "customerDomain": params['customerDomain'],
                      "customerOrdersList": customerOrdersList, 
                      "debugText": debugText,
                      "now": datetime.datetime.now()
                      }
                     ) 
     #                 "startedDateTime": params['startedDateTime'],
     #self.renderPage('templates/provision.html', 
     #                {"params": params }
     #                ) 

       #self.renderPage('templates/provision.html', params)
       #return respond(self.request, user, 'templates/provision', {'TaskLog': TaskLog})


#end of class 


def test_main():
 # This is the main function for profiling 
 # We've renamed our original main() above to real_main()
 #  Neal Note: to use this rename this routine to main() and rename the 
 #  original main to real_main().  To turn it off, reverse this. 
 #  Rename this routine to anything other than main, and rename real_main back to main. 
 import cProfile, pstats
 prof = cProfile.Profile()
 prof = prof.runctx("real_main()", globals(), locals())
 print "<pre>"
 stats = pstats.Stats(prof)
 stats.sort_stats("time")  # Or cumulative
 stats.print_stats(80)  # 80 = how many to print
 # The rest is optional.
 # stats.print_callees()
 # stats.print_callers()
 print "</pre>"


def main():
     #the request handlers must be specified in the instantiation tuple here...
     #first parm is "locatorMapping" and second parm is debug=True/False 
     #Here - you tie your page links to a class that handles that page. 
     #The first pair in each each row below can be a RegEx.
     #mySession = Session() 
     application = webapp.WSGIApplication([ ('/', MyHome), 
                                            ("/provision", Provision), 
                                            ("/reportTaskLogs",         ReportTaskLogs), 
                                            ("/reportTasks.*",          ReportTasks), 
                                            ("/reportServiceTypes.*",   ReportServiceTypes), 
                                            ("/reportCustomerOrders",   ReportCustomerOrders), 
                                            ("/reportOrders",           ReportOrders), 
                                            ("/reportServices",         ReportServices), 
                                            ("/reportWorkers",          ReportWorkers), 
                                            ("/reportSubscribers",      ReportSubscribers), 
                                            ("/reportSessions",         ReportSessions), 
                                            ("/reportRatePlans",        ReportRatePlans), 
                                            ("/reportNewsletters",      ReportNewsletters), 
                                            ("/reportBundle",           ReportBundle), 
                                            ("/reportKeyValuePairs",    ReportKeyValuePairs), 
                                            ("/reportLog",              ReportLog), 
                                            ("/reportGoals",            ReportGoals), 
                                            ("/reportBooks",            ReportBooks), 
                                            ("/reportFeedback",         ReportFeedback), 
                                            ("/reportTaskStatus",       ReportTaskStatus), 
                                            ("/reportTaskStatusHistory", ReportTaskStatusHistory), 
                                            ("/reportProviders",        ReportProviders), 
                                            ("/reportCredentials",      ReportCredentials), 
                                            ("/reportKnowledgeSources", ReportKnowledgeSources), 
                                            ("/reportKnowledgeEvents",  ReportKnowledgeEvents), 
                                            ("/reportRatePlanSubscriberXref", ReportRatePlanSubscriberXref), 
                                            ("/reportServiceTypeSubscriberXref", ReportServiceTypeSubscriberXref), 
                                            ("/reportIPN",        ReportIPN), 
                                            ("/detailIPN",        DetailIPN),
                                            ("/fileUpload", FileUpload), 
                                            ("/order", OrderPage), 
                                            ("/formHandler", CumulusFormHandler), 
                                            ("/register", Register), 
                                            ("/oneCloudSetupIndivSave", OneCloudSetupIndivSave),
                                            ("/oneCloudSetupIndivSubmit", OneCloudSetupIndivSubmit),
                                            ("/menu", Menu), 
                                            ("/myHome", MyHome), 
                                            ("/myhome", MyHome), 
                                            ("/home", MyHome), 
                                            ("/Home", MyHome), 
                                            ("/myHelpBooks", MyHelpBooks), 
                                            ("/myHelpKeywords", MyHelpKeywords), 
                                            ("/bookChapters", BookChapters), 
                                            ("/main", Main), 
                                            ("/lostpassword", LostPassword), 
                                            ("/resetpassword", ResetPassword), 
                                            ("/resetPassword", ResetPassword), 
                                            ("/login", Login), 
                                            ("/logout", Logout), 
                                            ("/testMail", TestMail), 
                                            ("/testCode",TestCode),
                                            ("/testSpeed",TestSpeed),
                                            ("/testSpeed3",TestSpeed3),
                                            ("/testSpeed2",TestSpeed2),
                                            ("/testSpeed4",TestSpeed4),
                                            ("/testPhoto", TestPhoto), 
                                            ("/userPhoto", UserPhoto), 
                                            ("/userPhotoFromService", UserPhotoFromService), 
                                            ("/testCommonEmail", TestCommonEmail), 
                                            ("/testPaypal", TestPaypalRecurringPayment), 
                                            ("/testPaypalButton", TestPaypalButton), 
                                            ("/testPaypalPostSuccess", TestPaypalPostSuccess), 
                                            ("/testPaypalPost", TestPaypalPost), 
                                            ("/testPaypalOneTime", TestPaypalOneTimePayment), 
                                            ("/testPaypalAPIGetBalance", TestPaypalAPIGetBalance), 
                                            ("/testPaypalAPIGetToken", TestPaypalAPIGetToken), 
                                            ("/PaypalIPN", PaypalIPNHandler), 
                                            ("/PaypalCompleted", PaypalCompleted), 
                                            ("/PaypalFailure", PaypalFailure), 
                                            ("/testLocalTime", TestLocalTime), 
                                            ("/testURL",TestURL), 
                                            ("/resumeDownload", ResumeDownload), 
                                            ("/testGetByParents", TestGetByParents), 
                                            ("/testGDocAPI", TestGDocAPI), 
                                            ("/dumpSessionData", DumpSessionData), 
                                            ("/userPhoto", UserPhoto), 
                                            ("/guid", TestGuid), 
                                            ("/putkey", TestPutKey), 
                                            ("/xmlExtract", XmlExtract), 
                                            ("/resumeCustomerOrder", ResumeCustomerOrder), 
                                            ("/deleteCustomerOrder", DeleteCustomerOrder), 
                                            ("/updCustomerOrder", UpdateCustomerOrder), 
                                            ("/updKeyValuePair", UpdateKeyValuePair), 
                                            ("/updSession", UpdateSession), 
                                            ("/updateSession", UpdateSession), 
                                            ("/updRatePlan", UpdateRatePlan), 
                                            ("/updKnowledgeEvent", UpdateKnowledgeEvent), 
                                            ("/updTask", UpdateTask), 
                                            ("/acceptManualTask", AcceptManualTask), 
                                            ("/completedManualTask", CompletedManualTask), 
                                            ("/updBook", UpdateBook), 
                                            ("/updWorker", UpdateWorker), 
                                            ("/updService", UpdateService), 
                                            ("/updOrder", UpdateOrder), 
                                            ("/updGoal", UpdateGoal), 
                                            ("/updProvider", UpdateProvider), 
                                            ("/updKnowledgeSource", UpdateKnowledgeSource), 
                                            ("/updFeedback", UpdateFeedback), 
                                            ("/submitFeedback", SubmitFeedback), 
                                            ("/updDocument", UpdateDocument), 
                                            ("/updDocumentKeywords", UpdateDocumentKeywords), 
                                            ("/updCredentials", UpdateCredentials), 
                                            ("/updDocuments", UpdateDocuments), 
                                            ("/deleteServices", DeleteServices), 
                                            ("/updServiceType", UpdateServiceType), 
                                            ("/customersxml", CustomersXml), 
                                            ("/subscriberAdmin", SubscriberAdmin), 
                                            ("/tasksxml", TasksXml), 
                                            ("/tasklogsxml", TaskLogsXml), 
                                            ("/convertTasks", ConvertTasks), 
                                            ("/detailLog", DetailLog), 
                                            ("/detailTaskStatus", DetailTaskStatus), 
                                            ("/detailSubscriber", DetailSubscriber), 
                                            ("/detailNewsletter", DetailNewsletter), 
                                            ("/detailSession", DetailSession), 
                                            ("/getSubscribers", GetSubscribers), 
                                            ("/fix1", Fix1), 
                                            ("/fix2", Fix2), 
                                            ("/fixUserPass", FixUserPass), 
                                            ("/fixSubscriberDate", FixSubscriberDate), 
                                            ("/fixRatePlan", FixRatePlan), 
                                            ("/clearsession", ClearSession), 
                                            ("/clearSession", ClearSession), 
                                            ("/ClearSession", ClearSession), 
                                            ("/sessionClear", ClearSession), 
                                            ("/myProfile",  MyProfile), 
                                            ("/myOrders",   MyOrders), 
                                            ("/myServices", MyServices), 
                                            ("/startTask",         StartTask), 
                                            ("/taskHandler",       TaskHandler),
                                            ("/commonTaskHandler",       CommonTaskHandler),
                                            ("/taskCron",                TaskCron),
                                            ("/forceTimeout",            ForceTimeout),
                                            ("/storeModOrder",     StoreModOrder), 
                                            ("/storeTaskQueueSeq", StoreTaskQueueSeq), 
                                            ("/storeRows",         StoreRows), 
                                            ("/storeBundle",       StoreBundle), 
                                            ("/storeLegals",       StoreLegals), 
                                            ("/storeKeyValues",    StoreKeyValues), 
                                            ("/storeSubscribers",  StoreSubscribers)
                                            
                                          ], 
                           debug=True)
     run_wsgi_app(application)

if __name__ == '__main__':
  main()

  