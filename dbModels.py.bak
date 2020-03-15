
from google.appengine.ext import db 
from google.appengine.ext.db import polymodel
from appengine_utilities.sessions import Session 
from google.appengine.api import mail

from commonEmail import CommonEmail 

import os
import datetime
import logging
from re import *

#from: http://www.wellho.net/resources/ex.php4?item=y115/currency.py
def formatCurrency(amount):
    temp = "%.2f" % amount
    profile = compile(r"(\d)(\d\d\d[.,])")
    while 1:
        temp, count = subn(profile,r"\1,\2",temp)
        if not count: break
    return "$" + temp


class CumulusDBModelCustomException(Exception):
   def __init__(self, value):
      self.parameter = value
   def __str__(self):
      return repr(self.parameter)



class CumulusSession(db.Model):
  ipaddress           = db.StringProperty() 
  dateTimeCreated     = db.DateTimeProperty(auto_now=False)
  dateTimeModified    = db.DateTimeProperty(auto_now=False)
  userEmail           = db.StringProperty()
  userPassword        = db.StringProperty()
  domain              = db.StringProperty()
  registrarURL        = db.StringProperty()
  registrarUserid     = db.StringProperty()
  registrarPassword   = db.StringProperty() 
  primaryLanguage     = db.StringProperty() 
  pagesSubmitted      = db.ListProperty(bool)  #keeps track of each page user submitted data on 
  languages           = db.StringListProperty()   #stores multiple languages 
  socialSites         = db.StringListProperty()   #e.g. FaceBook, LinkedIn, Picasa, YouTube, Orkut 
  socialURLs          = db.StringListProperty()   #user's URL to reach his social home page(s), corresponds to prior list 
  otherLanguages      = db.StringProperty()   
  otherLanguageNotes  = db.TextProperty()         #> 500 bytes, not indexed though 
  photo               = db.BlobProperty() 
  photoFilename       = db.StringProperty() 
  resume              = db.BlobProperty() 
  resumeFilename      = db.StringProperty() 
  bio                 = db.StringProperty(multiline=True)       #160 characters 
  tags                = db.StringListProperty()   #form suggested 3 to 6 tags 
  specialInstructions = db.TextProperty()  
  legalTerms          = db.TextProperty()  
  legalTermsAccepted  = db.BooleanProperty(default=False)
  serviceCode         = db.StringProperty() 
  firstname           = db.StringProperty()       
  lastname            = db.StringProperty()       
  organizationname    = db.StringProperty()       
  address1            = db.StringProperty()       
  address2            = db.StringProperty()       
  city                = db.StringProperty()       
  state               = db.StringProperty()       
  zip                 = db.StringProperty()    
  country             = db.StringProperty() #TODO - add this to forms  
  phone               = db.StringProperty()       
  timezone            = db.FloatProperty()     #might be -3.5 
  submitted           = db.BooleanProperty(default=False) #has user submitted this order? 
  isSaveAndComeBack   = db.BooleanProperty(default=False) #cannot skip contact page in this case. 
  
  def createNewEmptySession(self,serviceCode): 
     self.dateTimeCreated  = datetime.datetime.now() 
     self.dateTimeModified = self.dateTimeCreated  #exact same time 
     self.serviceCode      = serviceCode
     self.pagesSubmitted = [False] * 12  #go ahead and init for 12 pages, even though we will probably have less 
     self.put() 
     return  
   

  def registerSubscriber(self): 
     #see if already there 
     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1", self.userEmail) 
     LIMIT = 10
     log = CumulusLog() 

     subscriberList = query.fetch(LIMIT,offset=0) 
     subscriber = Subscriber()  #need scope to get to subscriber even if not found 
     log.message = "SubmitOneCloud: Subscriber:" + str(subscriber.userEmail) + " Subscriber not found - will add new one" 
     #Note: no error if subscriber not found, we will store one now. 
     action = "ADD" 
     if len(subscriberList) > 0: 
        raise CumulusDBModelCustomException("Cannot Register an Existing User: " + str(subscriber.userEmail))
        #subscriber = subscriberList[0] 
        #log.message = "SubmitOneCloud: Subscriber:" + subscriber.userEmail + " exists, will be updated" 
        #action = "MOD" 

     subscriber.firstname = self.firstname 
     subscriber.lastname = self.lastname 
     subscriber.organizationname = self.organizationname
     subscriber.address1 = self.address1 
     subscriber.address2 = self.address2 
     subscriber.city = self.city 
     subscriber.state = self.state 
     subscriber.zip = self.zip 
     subscriber.country = self.country 
     subscriber.phone = self.phone
     subscriber.timezone = self.timezone 
     subscriber.userEmail = self.userEmail
     subscriber.userPassword = self.userPassword 
     subscriber.hasOrders = False 
     subscriber.salesPerson = "NA"     # TODO - ??? 

     #only when adding a new subscriber, do this logic 
     if action == "ADD": 
       if self.userEmail == "NealWalters@NealWalters.com" or self.userEmail == "FPinto@Filipe-Pinto.com" or self.userEmail == "nwalters@sprynet.com":
          subscriber.isAdmin = True 
       else: 
          subscriber.isAdmin = False 
          subscriber.isWorker = False 

     subscriber.put()   #might add or might modify 

     #change the isSubmitted flag on the session so user cannot submit it again later 
     #(The "MyHome" page shows all orders that were started but not submitted,
     # and for user-registration, that would not make sense) 
     self.submitted = True 
     self.put() 

     #set username to allow user to still be "loggedin" 
     mySession = Session() 
     mySession['username'] = subscriber.userEmail 

     commonEmail = CommonEmail()
     #commonEmail.SendWelcomeEmail(subscriber.userEmail, subscriber.firstname)
     emailTitle = "3WCloud.com Registration Confirmation" 
     templateFilename = "templates/customer/email_welcome.html"
     commonEmail.sendMailFromTemplate(subscriber.userEmail, subscriber.firstname, emailTitle, templateFilename)

     log.message = str(subscriber.userEmail) + " " + str(subscriber.firstname) + " " + str(subscriber.lastname) 
     log.category = "Registration" 
     #log.ipaddress = self.request.remote_addr 
     log.put() 

     return  
   
class Subscriber(db.Model):
  firstname           = db.StringProperty()       
  lastname            = db.StringProperty()       
  organizationname    = db.StringProperty()       
  address1            = db.StringProperty()       
  address2            = db.StringProperty()       
  city                = db.StringProperty()       
  state               = db.StringProperty()       
  zip                 = db.StringProperty()       
  country             = db.StringProperty()  
  phone               = db.StringProperty()  
  timezone            = db.FloatProperty()     #might be -3.5 (can contain fractions) 
  userEmail           = db.StringProperty()
  userPassword        = db.StringProperty()
  salesPerson         = db.StringProperty()
  paymentType         = db.StringProperty(choices=('paypal','creditcard')) 
  isAdmin             = db.BooleanProperty(default=False) 
  isWorker            = db.BooleanProperty(default=False) 
  isOrderSubmitted    = db.BooleanProperty(default=False) 
  hasOrders           = db.BooleanProperty(default=False) 
  hasUnsubscribed     = db.BooleanProperty(default=False)   #ADDED 08/03/09 
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)
  resetPasswordRequestDateTime = db.DateTimeProperty(auto_now=False)
  resetPasswordGuid   = db.StringProperty()    
  googleAppsUserid    = db.StringProperty()
  googleAppsPassword  = db.StringProperty()

  def copySubscriberInfoToSession(self, sessionkey): 
     log = CumulusLog()    #log invalid signins  
     log.category = "copySubscriberInfoToSession" 
     log.message = "subscriber.userEmail=" + str(self.userEmail) 
     #log.ipaddress = self.request.remote_addr 
     log.put() 

     session = CumulusSession.get(sessionkey) 
     if session:
        session.firstname = self.firstname 
        session.lastname = self.lastname 
        session.organizationname = self.organizationname
        session.address1 = self.address1 
        session.address2 = self.address2 
        session.city = self.city 
        session.state = self.state 
        session.zip = self.zip 
        session.country = self.country 
        session.phone = self.phone
        session.timezone = self.timezone 
        session.userEmail = self.userEmail
        session.userPassword = self.userPassword 
	session.put() 
     else: 
        raise Exception("Subscriber.copySubscriberInfoToSession: sessionkey=" + sessionkey + " does not return a valid CumulusSession row from database") 

class Feedback(db.Model):
  submittedDateTime        = db.DateTimeProperty(auto_now=False)
  subscriber               = db.ReferenceProperty(Subscriber, collection_name='subscriber_feedback')
  rating                   = db.IntegerProperty()    #5-star rating: number between 1 to 5 (5=best, 1=worst)
  comments                 = db.TextProperty()       #free form paragraph text
  relatedURL               = db.StringProperty()     #page where feedback originated
  feedbackType             = db.StringProperty(choices=('feedback','defect','ticket'),default='feedback')
  department               = db.StringProperty(choices=('software','billing','resources','support','website'),default='website')
#checkbox fields available when users choose 1=bad or 2=poor on rating 
  isDefect                 = db.BooleanProperty(default=False)
  isCumbersome             = db.BooleanProperty(default=False)
  isUgly                   = db.BooleanProperty(default=False)
  isImStuck                = db.BooleanProperty(default=False)
  
#the following fields are set by internal admins only, user will probably not see these
  adminStatus              = db.StringProperty(choices=('software','billing','resources','support'))
  adminPriority            = db.IntegerProperty()  #number between 1-10, 10 is highest priority 


class RatePlan(db.Model):
  code                    = db.StringProperty()     # short code/name - 10 charactes - unique! 
  name                    = db.StringProperty()     # upto about 25-32 characters (often similar to or same as serviceTypeName)
  description             = db.StringProperty()     # lengthy description 
  recurringAmount         = db.IntegerProperty()     
  onetimeAmount           = db.IntegerProperty()     
  billingPeriod           = db.StringProperty(choices=('M','W','D','Y'), default='W') 
  billingInterval         = db.IntegerProperty(default=1)
           #(1 = one period above, such as once per month, put for example 3 for every 3 months) 
  numberOfPayments        = db.IntegerProperty(default=0)
           #rarely used, only to limit number of payments (example $10 for 3 months then stop) 
  dateTimeCreated     = db.DateTimeProperty(auto_now=False)
  dateTimeModified    = db.DateTimeProperty(auto_now=False)
  userCreated         = db.StringProperty()
  userModified        = db.StringProperty()

  def getRecurringAmount(self):
      return float(self.recurringAmount)  / 100 
  def getRecurringAmountFormatted(self):
      return formatCurrency(self.getRecurringAmount()) 
  def setRecurringAmount(self,value):
      self.recurringAmount =   int(float(value) * 100)

  def getOnetimeAmount(self):
      return float(self.onetimeAmount)  / 100 
  def getOnetimeAmountFormatted(self):
      return formatCurrency(self.getOnetimeAmount()) 
  def setOnetimeAmount(self,value):
      self.onetimeAmount =   int(float(value) * 100)

class ServiceType(db.Model): 
  code                  = db.StringProperty()     # short code/name - 10 charactes - unique! 
  name                  = db.StringProperty()     # upto about 18-25 characters 
  infrastructureName    = db.StringProperty()     # such as GoDaddy, YouTube, Picasa, etc... 
  ratePlan              = db.ReferenceProperty(RatePlan, collection_name='ServiceType_RatePlan')
  description           = db.StringProperty()     # long description 
  isSellable            = db.BooleanProperty(default=False) #can a customer order this? 
  isBillingOnly         = db.BooleanProperty(default=True) #can a customer order this? 
  isProvisioningOnly    = db.BooleanProperty(default=True) #can a customer order this? 
  salesWhatIsIt            = db.StringProperty(multiline=True)  
  salesWhyYouNeedIt        = db.StringProperty(multiline=True)  
  salesWhatsInItForYou     = db.StringProperty(multiline=True)  
  salesHowDoesItWork       = db.StringProperty(multiline=True)  
  salesSpecialInstructions = db.StringProperty(multiline=True)  
  children              = db.ListProperty(db.Key)   #hierarchy of serviceTypes
  upsells               = db.ListProperty(db.Key)   #items to offer customer related to this serviceType
  dateTimeCreated       = db.DateTimeProperty(auto_now=False)
  dateTimeModified      = db.DateTimeProperty(auto_now=False)
  userCreated           = db.StringProperty()
  userModified          = db.StringProperty()
  
  @property
  def parents(self):
      return ServiceType.gql('WHERE children = :1 ', self.key())
  def upsellFor(self):
      return ServiceType.gql('WHERE upsells  = :1 ', self.key())


class ServiceTypeLegal(db.Model):  
  """
   Keep the legal agreements in a different table so as not to slow down the 99% of queries
   that do not need the legal information. 
  """
  code                = db.StringProperty()     # short code/name - 10 charactes - unique! 
  legalTerms          = db.BlobProperty() 


class PaypalIPN(db.Expando):
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)
  source              = db.StringProperty() 



#TODO - resolve how to have multiple orders per one service (example: Add, Change, Cancel  
class Order(db.Model): 
  orderDate                = db.DateTimeProperty(auto_now=False)
  subscriber               = db.ReferenceProperty(Subscriber, collection_name='subscriber_orders')
  domain                   = db.StringProperty() 
  requestedCompletionDate  = db.DateTimeProperty(auto_now=False)
  actualCompletionDate     = db.DateTimeProperty(auto_now=False)
  apiClientId              = db.StringProperty()     # which program stored this row 
  description              = db.StringProperty()     # future use 
  #subProducts             = db.StringListProperty() #bundle of sub-products 
  orderType                = db.StringProperty(choices=('Add','Change','Cancel')) 
  priority                 = db.IntegerProperty()   #1=Expedite, 2=High, 3=Norm, 4=Medium, 5=Low 
  #services                = db.StringListProperty()  #change to keys 
  #failedServices          = db.StringListProperty() #change to keys 
  orderState               = db.StringProperty(
                                 choices=('open','open.not_running',
                                 'open.not_running.not_started',
                                 'open.not_running.suspended', 'open.running',
                                 'closed','closed.completed','closed.aborted',
                                 'closed.aborted.byclient','closed.aborted.byserver'
                                 ))
  financialStatus        = db.StringProperty(
                                 choices=(
				 'PayPal.not_paid',
                                 'PayPal.checkout_cancelled',
                                 'PayPal.user_cancelled',
                                 'PayPal.paid',
                                 'PayPal.pending',
                                 'Complementary'
                                 ))

  @property
  def services(self):
      query = Service.gql('WHERE order = :1 ', self.key())
      LIMIT = 1000
      serviceList = query.fetch(LIMIT,offset=0) 
      return serviceList

  #NOTE: orders are only deleted by deleting services 
  #the service has cascading delete logic to call the order.delete method 
  #(or also through a trick (of putting &delete=True on the /updateOrder page) 


  def SubmitOneCloud(self, session): 
     #lookup subscriber 
     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1", session.userEmail) 
     LIMIT = 1000
     log = CumulusLog() 

     subscriberList = query.fetch(LIMIT,offset=0) 
     subscriber = Subscriber()  #need scope to get to subscriber even if not found 
     log.message = "SubmitOneCloud: Subscriber:" + str(subscriber.userEmail) + " Subscriber not found - will add new one" 
     #Note: no error if subscriber not found, we will store one now. 
     action = "ADD" 
     if len(subscriberList) > 0: 
        subscriber = subscriberList[0] 
        log.message = "SubmitOneCloud: Subscriber:" + subscriber.userEmail + " exists, will be updated" 
        action = "MOD" 
     #log.ipaddress = self.request.remote_addr 
     log.category = "Debug" 
     log.put() 

     #change the isSubmitted flag on the session so user cannot submit it again later 
     session.submitted = True 
     session.put() 
 
     #We may have a rather empty subscriber table - i.e. with just a user/pass in it,
     #because if user saves his data, the subscriber is created then. 
     #So now, we must update all subscriber fields with the current info 
     #or potentiall store a new one.  

     subscriber.firstname = session.firstname 
     subscriber.lastname = session.lastname 
     subscriber.organizationname = session.organizationname
     subscriber.address1 = session.address1 
     subscriber.address2 = session.address2 
     subscriber.city = session.city 
     subscriber.state = session.state 
     subscriber.zip = session.zip 
     subscriber.country = session.country 
     subscriber.phone = session.phone
     subscriber.timezone = session.timezone 
     subscriber.userEmail = session.userEmail
     subscriber.userPassword = session.userPassword 
     subscriber.hasOrders = True 
     subscriber.salesPerson = "NA"     # TODO - ??? 

     #only when adding a new subscriber, do this logic 
     if action == "ADD": 
       if session.userEmail.lower() == "nealwalters@nealwalters.com" or session.userEmail == "fpinto@filipe-pinto.com":
          subscriber.isAdmin = True 
       else: 
          subscriber.isAdmin = False 
          subscriber.isWorker = False 

     subscriber.put()   #might add or might modify 
     
     #set username to allow user to still be "loggedin" 
     mySession = Session() 
     mySession['username'] = subscriber.userEmail 

     #lookup serviceType (needed for reference in child records) 
     query = db.GqlQuery("SELECT * FROM ServiceType WHERE code = :1", session.serviceCode) 
     LIMIT = 1000
     serviceTypeList = query.fetch(LIMIT,offset=0)
     serviceType = ServiceType()  #need scope to get to subscriber even if not found 
     if len(serviceTypeList) == 0: 
        raise Exception("serviceType not found") 
     else:
        serviceType = serviceTypeList[0] 


     #store the order itself 
     
     self.orderDate = datetime.datetime.now() 
     self.subscriber = subscriber 
     self.domain = session.domain 
     self.apiClientId = "Order.Submit" 
     self.orderType = "Add" 
     self.priority = 3  # normal priority 
     self.orderState = "open.not_running"  #TODO - Verify with Filipe 
     self.financialStatus = "PayPal.not_paid"     #added 07/21/09 - assuming now Paypal is only payment method 
                                                  #after we return from Paypal, we will update this status. 

     self.put()   #store the Order 

     service = ServiceOneCloud()   # build the related service and store it  

     # foreign keys 
     service.serviceType         = serviceType  
     service.subscriber          = subscriber 
     service.order               = self   
     service.orders.append(self.key())   #this is the one to many relationship from services back to orders
     service.ratePlan            = serviceType.ratePlan   

     #normal fields 
     service.serviceState        = "Inactive" 
     service.domain              = session.domain 
     service.bio                 = session.bio
     service.primaryLanguage     = session.primaryLanguage 
     service.languages           = session.languages 
     service.socialSites         = session.socialSites 
     service.socialURLs          = session.socialURLs 
     service.photo               = session.photo 
     service.resume              = session.resume 
     service.photoFilename       = session.photoFilename
     service.resumeFilename      = session.resumeFilename 
     service.tags                = session.tags 
     service.specialInstructions = session.specialInstructions 

     service.put() 

     commonEmail = CommonEmail()
     emailTitle = "3WCloud.com OneCloud Order Confirmation" 
     templateFilename = "templates/customer/email_OneCloudOrderConfirm.html"
     commonEmail.sendMailFromTemplate(subscriber.userEmail, subscriber.firstname, emailTitle, templateFilename)

     return self.key() 




class KeyValuePair(db.Model): 
  kvpKey            = db.StringProperty() 
  kvpValue          = db.StringProperty() 
  kvpValueLong      = db.TextProperty() 
  kvpIsSecure       = db.BooleanProperty(default=False)  #used to hide certain values (such as Paypal password ) on report screens 
                                                         #could potential do some encryption on the kvpValue associated with this row. 
  kvpDoc            = db.TextProperty() 
  dateTimeCreated         = db.DateTimeProperty(auto_now=False)
  dateTimeLastModified    = db.DateTimeProperty(auto_now=True)
  userEmailCreated        = db.StringProperty()
  userEmailLastModified   = db.StringProperty() 
  

  def getValueFromKey(self, argKey): 
     query = db.GqlQuery("SELECT * FROM KeyValuePair WHERE kvpKey = :1", argKey) 
     LIMIT = 1
     kvpList = query.fetch(LIMIT,offset=0) 
     if len(kvpList)== 1:
        # 08/13/2009 - need the ability to have text over 500 bytes for html/templates for GoogleDocs/KnowledgeEvents 
        if kvpList[0].kvpValue == "kvpValueLong":
          return kvpList[0].kvpValueLong 
        else:
          return kvpList[0].kvpValue
     else:
        raise "getValueFromKey failed against table KeyValuePair for key=" + argKey 


class CumulusLog(db.Model): 
  category            = db.StringProperty() 
  level               = db.StringProperty() 
  message             = db.StringProperty() 
  dateTime            = db.DateTimeProperty(auto_now=True) 
  ipaddress           = db.StringProperty() 
  username            = db.StringProperty() 
  largeText           = db.TextProperty() 


class Service(polymodel.PolyModel): 
  serviceState        = db.StringProperty(choices=('Active','Inactive')) 
  serviceType         = db.ReferenceProperty(ServiceType, collection_name='serviceType_services')
  subscriber          = db.ReferenceProperty(Subscriber, collection_name='subscriber_servicse')
  order               = db.ReferenceProperty(Order, collection_name='order_services')
  orders              = db.ListProperty(db.Key)
  #this holds rate plan at time order was made, so serviceRatePlan can be properly stored 
  #after Paypal payment clears (which could be several days later) 
  holdRatePlan        = db.ReferenceProperty(RatePlan, collection_name='service_rateplan')
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)


  @property
  #above "orders" only includes keys - this returns the entire related order records
  def getOrders(self):
      orderList = Order.get(self.orders)  #get method support a list of keys (as well as a single key) 
      return orderList

  def delete(self):

      logging.debug("Service.delete()") 
      #cascading delete - delete each "child" so we don't get referential integrity problem later 
      query = ServiceRatePlan.gql('WHERE order = :1 ', self.key())
      LIMIT = 1000
      serviceRatePlanList = query.fetch(LIMIT,offset=0) 
      for serviceRatePlan in serviceRatePlanList:
          #serviceRatePlan.order.delete() 
          serviceRatePlan.delete() 

      for orderKey in self.orders:
          order = Order.get(orderKey)
	  logging.debug("Delete orderKey=" + str(orderKey)) 
	  order.delete() 
      
      #self.order.delete()  - now handled by loop above 
      super(Service, self).delete() 
      logging.debug("ServiceDelete completed") 



class ServiceOneCloud(Service): 
  domain               = db.StringProperty()    
  languages            = db.StringListProperty()   #stores multiple languages 
  socialSites          = db.StringListProperty()   #e.g. FaceBook, LinkedIn, Picasa, YouTube, Orkut 
  socialURLs           = db.StringListProperty()   #user's URL to reach his social home page(s), corresponds to prior list 
  primaryLanguage      = db.StringProperty()   
  otherLanguages       = db.StringProperty()   
  #otherLanguageNotes  = db.TextProperty()         #> 500 bytes, not indexed though 
  photo                = db.BlobProperty() 
  resume               = db.BlobProperty() 
  photoFilename        = db.StringProperty()   
  resumeFilename       = db.StringProperty()   
  bio                  = db.StringProperty(multiline=True)       #160 characters 
  tags                 = db.StringListProperty()   #form suggested 3 to 6 tags 
  specialInstructions  = db.TextProperty()  


class ServiceRatePlan(db.Model):  
  """
    This associates a subscriber's order/service to a RatePlan. 
  """
  ratePlan            = db.ReferenceProperty(RatePlan, collection_name='servicerateplan_rateplan')
  order               = db.ReferenceProperty(Order,    collection_name='servicerateplan_order')
  service             = db.ReferenceProperty(Service,  collection_name='servicerateplan_service')
  dateTimeCreated     = db.DateTimeProperty(auto_now=False)
  paymentType         = db.StringProperty() 
  payerEmail          = db.StringProperty()   #Paypal email account
  payerId             = db.StringProperty()   #Paypal provided, for example: 4K4HRRVKBJNJU
  auth                = db.StringProperty()   #Paypal provided auth 
  subscriptionId      = db.StringProperty()   #Paypal provided subscr_id
  paymentStatus       = db.StringProperty()   #Completed, Pending, ??? 


class Document(db.Model):
  """
  These represent KB articles that were created as Google Documents. 
  The CMS/KB part of Cumulus can display the HTML from the GoogleDoc on the web page. 
  """
  docId                  = db.StringProperty()
  docName                = db.StringProperty()   
  keywords               = db.ListProperty(db.Key)
  title                  = db.StringProperty()   
  subtitle               = db.StringProperty()   
  summary                = db.StringProperty(multiline=True) 
  authorName             = db.StringProperty()  
  authorEmail            = db.StringProperty() 
                            #could use MIME media type as well?   http://www.iana.org/assignments/media-types/
  mediaType              = db.StringProperty(choices=('article','blog','audio','video','picture','link'))
  isGDoc                 = db.BooleanProperty(default=False) 
  isExternalLink         = db.BooleanProperty(default=False) 
  externalLink           = db.StringProperty() 
  language               = db.StringProperty()   #English,Spanish, etc... 
                            #could potentially have "length" attribute to show user approximate size of article 
  dateTimePublished       = db.DateTimeProperty(auto_now=False)
  dateTimeCreated         = db.DateTimeProperty(auto_now=False)
  dateTimeLastModified    = db.DateTimeProperty(auto_now=True)
  userEmailCreated        = db.StringProperty()
  userEmailLastModified   = db.StringProperty() 

  def isUnique(self): 
     #TODO: might be able to read the index here and speed-up this unique test 
     query = db.GqlQuery("SELECT * FROM Document WHERE docName = :1", self.docName) 
     LIMIT = 1 
     docList = query.fetch(LIMIT,offset=0) 
     if len(docList) > 0: 
        return False 
     return True 


class Book(db.Model):
  """
  Book contents are stored in GoogleDocs, referenced by the Documents table, and indexed 
  by the Keywords table.  Keywords might contain book01:chapter01.
  This table defines the first part of the prefix "book01" and associates it with a
  more human book title.  This allows "books" to be associated with service types. 
  """
  name                   = db.StringProperty()
  keywordPrefix          = db.StringProperty() 
  appliesTo              = db.StringProperty(choices=('ALL','serviceType')) 
  serviceType            = db.ReferenceProperty(ServiceType, collection_name='ServiceType_Book')

  

class Keywords(db.Model):
  """
  Keywords for indexing Documents  
  """
  keyword                = db.StringProperty()
  referenceCounter       = db.IntegerProperty() 
  @property 
  def documents(self):
     docList = Document.gql("WHERE keywords = :1 order by docName", self.key()).fetch(1000) 
     return docList 

  def addIfNotExists(self): 
     query = db.GqlQuery("SELECT * Keywords WHERE keyword = :1", self.keyword) 
     LIMIT = 1 
     keywordList = query.fetch(LIMIT,offset=0) 
     if len(keywordList) == 0: 
        self.put() 


  #def put(self): 
  #   query = db.GqlQuery("SELECT * FROM Document WHERE docName = :1", self.docName) 
  #   LIMIT = 1 
  #   docList = query.fetch(LIMIT,offset=0) 
  #   if len(docList) > 0: 
  #      return False 
  #   super.put()   #this didn't work, next line was recommended, but I haven't tested yet 
  #   super(Document, self).put()   




class DocumentXref(db.Model):
  """
  Creates a many-to-many relationship between document and serviceType.
  Some of the KB screens might allow user to pick a serviceType such as "YouTube"
  and then we show all documents related.
  NOTE: Neal has not yet implemented this, because we can put the serviceType 
  as just another keyword in the Document table, or a special keyword with a prefix, 
  such as "serviceType:YouTube" for example. 
  """
  serviceType            = db.ReferenceProperty(ServiceType, collection_name='serviceType_documentXref')
  document               = db.ReferenceProperty(Document,    collection_name='document_documentXref')
  serviceType            = db.StringProperty() 


class TaskLog(db.Model):
  customerDomain         = db.StringProperty()
  workerEmail            = db.StringProperty()   # db.UserProperty()
  taskCode               = db.StringProperty()
  eventStartedDateTime   = db.DateTimeProperty(auto_now=False)
  eventCompletedDateTime = db.DateTimeProperty(auto_now=False)
  resultFlag             = db.IntegerProperty()  #-1=started 0=Competed Success, 1=See Issues, 2=ShowStopper 
  issues                 = db.StringProperty(required=False,multiline=True)
  debug                  = db.StringProperty()


class TaskStatus(db.Model): 
  processCode                  = db.StringProperty() 
  currentTaskCode              = db.StringProperty() 
  currentTaskError             = db.TextProperty() 
  currentSeqNum                = db.IntegerProperty() 
  numOfRetries                 = db.IntegerProperty() 
  isManual                     = db.BooleanProperty()  
  isManualAccepted             = db.BooleanProperty() 
  isManualNotificationComplete = db.BooleanProperty() 
  isInRetriesExceededState     = db.BooleanProperty() 
  acceptedBySubscriber         = db.ReferenceProperty(Subscriber, collection_name='subscriber_taskStatus')
  dateTimeCurrTaskStarted      = db.DateTimeProperty(auto_now=False)
  dateTimeCurrTaskCompleted    = db.DateTimeProperty(auto_now=False)
  dateTimeProcessStarted       = db.DateTimeProperty(auto_now=False)
  dateTimeProcessCompleted     = db.DateTimeProperty(auto_now=False)
  dateTimeManualNotification   = db.DateTimeProperty(auto_now=False)
  dateTimeManualAccepted       = db.DateTimeProperty(auto_now=False)
  dateTimeErrorNotification    = db.DateTimeProperty(auto_now=False)
  jsonPickledCommonTaskMsg     = db.TextProperty() 

  def createHistory(self):
     taskStatusHistory = TaskStatusHistory()
     taskStatusHistory.processCode               = self.processCode 
     taskStatusHistory.currentTaskCode           = self.currentTaskCode 
     taskStatusHistory.currentTaskError          = self.currentTaskError 
     taskStatusHistory.currentSeqNum             = self.currentSeqNum 
     taskStatusHistory.dateTimeCurrTaskStarted   = self.dateTimeCurrTaskStarted 
     taskStatusHistory.dateTimeCurrTaskCompleted = self.dateTimeCurrTaskCompleted 
     taskStatusHistory.dateTimeProcessStarted    = self.dateTimeProcessStarted 
     taskStatusHistory.dateTimeProcessCompleted  = self.dateTimeProcessCompleted 
     taskStatusHistory.instanceId                = self.key().id() 
     taskStatusHistory.isManual                  = self.isManual
     taskStatusHistory.isManualAccepted          = self.isManualAccepted 
     taskStatusHistory.dateTimeManualAccepted    = self.dateTimeManualAccepted 
     taskStatusHistory.acceptedBySubscriber      = self.acceptedBySubscriber 
     taskStatusHistory.put() 
     return taskStatusHistory.key() 

class TaskStatusHistory(db.Model): 
  processCode                = db.StringProperty()
  currentTaskCode            = db.StringProperty()
  instanceId                 = db.IntegerProperty()  #this was the row id of the TaskStatus 
  currentTaskError           = db.TextProperty() 
  currentSeqNum              = db.IntegerProperty() 
  dateTimeCurrTaskStarted    = db.DateTimeProperty(auto_now=False)
  dateTimeCurrTaskCompleted  = db.DateTimeProperty(auto_now=False)
  dateTimeProcessStarted     = db.DateTimeProperty(auto_now=False)
  dateTimeProcessCompleted   = db.DateTimeProperty(auto_now=False)
  isManual                     = db.BooleanProperty()  
  isManualAccepted             = db.BooleanProperty() 
  dateTimeManualAccepted       = db.DateTimeProperty(auto_now=False)
  acceptedBySubscriber         = db.ReferenceProperty(Subscriber, collection_name='subscriber_taskStatusHistory')


class Tasks(db.Model):
  #serviceType             = db.ReferenceProperty(ServiceType, collection_name='serviceType_Tasks')
  taskCode                = db.StringProperty()
  taskDescription         = db.StringProperty()
  processCode             = db.StringProperty()
  estimatedCompletionTime = db.IntegerProperty() #minutes 
  sequence                = db.IntegerProperty() 
  isManual                = db.BooleanProperty()
  dateTimeCreated         = db.DateTimeProperty(auto_now=False)
  dateTimeLastModified    = db.DateTimeProperty(auto_now=True)
  userEmailCreated        = db.StringProperty()
  userEmailLastModified   = db.StringProperty() 


class Workers(db.Model):
  workerEmail             = db.StringProperty()
  workerLastName          = db.StringProperty()
  workerFirstName         = db.StringProperty()
  workerTitle             = db.StringProperty()
  workerStatus            = db.StringProperty()
  workerPassword          = db.StringProperty()
  workerIsAdmin           = db.BooleanProperty()
  dateTimeCreated         = db.DateTimeProperty(auto_now=False)
  dateTimeLastModified    = db.DateTimeProperty(auto_now=True)
  userEmailCreated        = db.StringProperty()
  userEmailLastModified   = db.StringProperty()


class CustomerOrders(db.Model):
  domain                  = db.StringProperty()
  processCode             = db.StringProperty()
  lastname                = db.StringProperty()
  firstname               = db.StringProperty()
  companyname             = db.StringProperty()
  email                   = db.StringProperty()
  orderDateTime           = db.DateTimeProperty(auto_now=True)
  xmldata                 = db.StringProperty()
  userEmailCreated        = db.StringProperty()

class TaskQueueResults(db.Model):  
  """
    Experiment by saving data from a task/queue  
  """
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)
  task                = db.StringProperty() 
  request             = db.StringProperty() 
  response            = db.StringProperty() 


class TaskQueueSeq(db.Model):  
  """
    Experiment by saving data from a task/queue  
  """
  currentTask         = db.StringProperty()  
  nextTask            = db.StringProperty() 



class Goal(db.Model):  
  """
    allows subscribers to define their own goals and associate knowledge learning back to goals 
  """
  name                   = db.StringProperty()  
  subscriber             = db.ReferenceProperty(Subscriber, collection_name='subscriber_goal')
  goalType               = db.StringProperty(choices=('Education','Career','Personal','Family','Charity')) 
  startDate              = db.DateTimeProperty() 
  plannedCompletionDate  = db.DateTimeProperty() 
  dateTimeCreated        = db.DateTimeProperty(auto_now=False)
  dateTimeModified       = db.DateTimeProperty(auto_now=False)
  shareWithFriends       = db.BooleanProperty() 

  def getKnowledgeSources(self):
     query = db.GqlQuery("SELECT * FROM KnowledgeSource WHERE goal = :1", self) 
     LIMIT = 1000
     knowledgeSourceList = query.fetch(LIMIT,offset=0)
     return knowledgeSourceList


class KnowledgeSource(db.Model):  
  """
    allows subscribers to define their own goals and associate knowledge learning back to goals 
  """
  name                   = db.StringProperty()  
  shortName              = db.StringProperty()  #this is used in Google Filename 
  isbn                   = db.StringProperty()  #could do lookup from Amazon 
  subscriber             = db.ReferenceProperty(Subscriber, collection_name='subscriber_knowledgesource')
  goal                   = db.ReferenceProperty(Goal, collection_name='goal_knowledgesource')
  knowledgeType          = db.StringProperty(choices=('book','meeting','conference','video','audio','periodical','vacation','class')) 
  authorName             = db.StringProperty()  
  pages                  = db.IntegerProperty()
  minutes                = db.IntegerProperty()
  meetingLocation        = db.StringProperty()  
  meetingStartDateTime   = db.DateTimeProperty(auto_now=False)
  meetingStopDateTime    = db.DateTimeProperty(auto_now=False)
  docId                  = db.StringProperty()  
  dateTimeCreated        = db.DateTimeProperty(auto_now=False)
  dateTimeModified       = db.DateTimeProperty(auto_now=False)


class KnowledgeEvent(db.Model):  
  """
    allows subscribers to define their own goals and associate knowledge learning back to goals 
  """
  subscriber             = db.ReferenceProperty(Subscriber, collection_name='subscriber_KnowledgeEvent')
  knowledgeSource        = db.ReferenceProperty(KnowledgeSource, collection_name='KnowledgeSource_KnowledgeEvent')
  eventType              = db.StringProperty(choices=('started','completed chapter','completed','remember')) 
  payloadType            = db.StringProperty(choices=('text','video','audio')) 
  microBlog              = db.StringProperty(multiline=True)    #max length 140 for Twitter 
  dateTimeCreated        = db.DateTimeProperty(auto_now=False)
  dateTimeModified       = db.DateTimeProperty(auto_now=False)


class Provider(db.Model):  
  """
    allows subscribers to define their own goals and associate knowledge learning back to goals 
  """
  name                   = db.StringProperty() 
  description            = db.StringProperty() 
  sampleServices         = db.StringProperty() 

  def delete(self):
     """
       Don't allow "orphaned" children.  If children exist, don't allow delete of the parent. 
     """
     query = SubscriberProviderCredentials.gql("WHERE provider = :1", self) 
     LIMIT = 1  #only need one child to prevent a delete of this provider 
     subscriberProviderCredentialsList = query.fetch(LIMIT,offset=0)
     if len(subscriberProviderCredentialsList) == 0:
        super(Provider, self).delete() 
     else: 
        raise Exception("Cannot delete because some subscribers have credentials associated to this provider")


class SubscriberProviderCredentials(db.Model):  
  """
    allows subscribers to define their own goals and associate knowledge learning back to goals 
  """
  subscriber             = db.ReferenceProperty(Subscriber, collection_name='subscriber_credentials') 
  provider               = db.ReferenceProperty(Provider,   collection_name='provider_credentials')   
  #accountName           = db.StringProperty()  #for example, YouTube Channel name - Filipe 08/11/09 said he could look this up with a "GET" 
  userid                 = db.StringProperty()  
  password               = db.StringProperty()  
  dateTimeCreated        = db.DateTimeProperty(auto_now=False)
  dateTimeModified       = db.DateTimeProperty(auto_now=False) 


class CommonTaskMessage(object):    #not stored in database 
  def __init__(self): 
      processCode = "oneCloudI-Setup"
      taskCode = "GoDaddyNewAccount" 
      currentSeqNum = 100 
      taskStatusId = 14801    #for all database access to taskStatus, if zero/null, then store new one  
      orderId = 14522
      subscriberId = 14515
      serviceId = 14711 
      generalText = "This is my mini-blog" 
      generalObject = "some pickled object??" 
      isManual = False 
