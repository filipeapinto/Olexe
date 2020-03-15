
from google.appengine.ext import db 
from google.appengine.ext.db import polymodel
from appengine_utilities.sessions import Session 
from google.appengine.api import mail

from commonEmail import CommonEmail 

import os
import datetime
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



class PaypalIPNTest(db.Model):   #can remove this soon 07/23/09 
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)
  item                = db.StringListProperty()
  itemValue           = db.StringListProperty()


class PaypalIPN(db.Expando):
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)
  source              = db.StringProperty() 


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
       if self.userEmail == "NealWalters@NealWalters.com" or self.userEmail == "FPinto@Filipe-Pinto.com":
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
  dateTimeCreated     = db.DateTimeProperty(auto_now=True)
  resetPasswordRequestDateTime = db.DateTimeProperty(auto_now=False)
  resetPasswordGuid   = db.StringProperty()    

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


  def delete(self):
      #cascading delete - delete each "child" so we don't get referential integrity problem later 
      query = ServiceRatePlan.gql('WHERE order = :1 ', self.key())
      LIMIT = 1000
      serviceRatePlanList = query.fetch(LIMIT,offset=0) 
      for serviceRatePlan in serviceRatePlanList:
          serviceRatePlan.delete() 


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
        return kvpList[0].kvpValue 
     else:
        raise "getValueFromKey failed against table KeyValuePair for key=" + argKey 


class CumulusLog(db.Model): 
  category            = db.StringProperty() 
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

  def delete(self):
      self.order.delete() 
      super(Service, self).delete() 

  @property
  #above "orders" only includes keys - this returns the entire related order records
  def getOrders(self):
      orderList = Order.get(self.orders)  #get method support a list of keys (as well as a single key) 
      return orderList

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
  keywords               = db.StringListProperty()

  def isUnique(self): 
     query = db.GqlQuery("SELECT * FROM Document WHERE docName = :1", self.docName) 
     LIMIT = 1 
     docList = query.fetch(LIMIT,offset=0) 
     if len(docList) > 0: 
        return False 
     return True 
     
  def put(self): 
     query = db.GqlQuery("SELECT * FROM Document WHERE docName = :1", self.docName) 
     LIMIT = 1 
     docList = query.fetch(LIMIT,offset=0) 
     if len(docList) > 0: 
        return False 
     super.put() 




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


class Tasks(db.Model):
  #serviceType             = db.ReferenceProperty(ServiceType, collection_name='serviceType_Tasks')
  taskCode                = db.StringProperty()
  taskDescription         = db.StringProperty()
  processCode             = db.StringProperty()
  estimatedCompletionTime = db.IntegerProperty() #minutes 
  sequence                = db.IntegerProperty() 
  dateTimeCreated         = db.DateTimeProperty(auto_now=False)
  dateTimeLastModified    = db.DateTimeProperty(auto_now=True)
  userEmailCreated        = db.StringProperty()
  userEmailLastModified   = db.StringProperty() 
  #the following fields are used only to pass data to template 
  debug                   = db.StringProperty(multiline=True) 
  ynStartedNotStored      = db.StringProperty()  #used to pass data to template only 
  ynCompletedNotStored    = db.StringProperty()  #used to pass data to template only 
  priorIssuesNS           = db.StringProperty(required=False,multiline=True)
  eventStartedDateTimeNS    = db.DateTimeProperty(auto_now=False)
  eventCompletedDateTimeNS  = db.DateTimeProperty(auto_now=False)

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

