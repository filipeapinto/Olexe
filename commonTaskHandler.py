import datetime 
import jsonpickle
import simplejson 
import time
import urllib 
import atom.url
import settings   #this moodule is created from source here: http://code.google.com/appengine/articles/gdata.html
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError

from dbModels import CommonTaskMessage 
from dbModels import Tasks 
from dbModels import TaskStatus
from dbModels import TaskStatusHistory
from dbModels import CumulusLog
from dbModels import Subscriber
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
import logging

class CommonTaskHandler(webapp.RequestHandler):

  def post(self):

    logging.info('-----------------------CommonTaskHandler: post----------------------') 
    body = self.request.body
    headers = self.request.headers
    taskRetryCount = 0
    if 'X-AppEngine-TaskRetryCount' in headers:
       taskRetryCount = headers['X-AppEngine-TaskRetryCount']
    logging.info("payload=" + body + "\n\n") 
    logging.info("taskRetryCount=" + taskRetryCount) 
    if int(taskRetryCount) > 10:  
       # we don't want the task queues to keep retrying forever 
       # TODO - maybe delete corresponding taskStatus - not sure yet> 
       self.LogAndNotifyError(taskStatus) 
       return 
       

    #unpickle parm here
    objCommonTaskMessage = jsonpickle.decode(body) 
    #objCommonTaskMessage = json1.loads(self.request.get('pickledCommonMessage'))
    #unpickler1 = jsonpickle.Unpickler() 
    #objCommonTaskMessage = unpickler1.restore(body) 
    logging.info ("UnPickled Class.Name=" + objCommonTaskMessage.__class__.__name__)
    #for key in objCommonTaskMessage.__dict__: 
    #   logging.info(key + "=" + objCommonTaskMessage.__dict__[key] )

    #update database - task - starting date/time, set next step to null 
    if objCommonTaskMessage.taskStatusId == 0: 
       logging.info ("taskStatusId=0 - special first time logic") 
       #this is the first time we have seen this process, so we need to initial it and get the first task code 
       isNewTask = True 
       taskStatus = TaskStatus() 
       taskStatus.processCode               = objCommonTaskMessage.processCode 
       taskStatus.dateTimeCurrTaskStarted   = datetime.datetime.now() 
       taskStatus.dateTimeCurrTaskCompleted = taskStatus.dateTimeCurrTaskStarted
       taskStatus.dateTimeProcessStarted    = taskStatus.dateTimeCurrTaskStarted
       taskStatus.currentSeqNum = -1 
       taskStatus.numOfRetries = 0 
       taskStatus.isInRetriesExceededState = False 
       taskStatus.jsonPickledCommonTaskMsg = body 
       taskStatus.put() 
       #Now that we have the key, let's put the row-id into the encoded object,
       #we must make sure that the value is not 0 again for future posts 
       #(especially after a manual step) so that this initialization logic doesn't run again. 
       #thus the need for the second put 
       objCommonTaskMessage.taskStatusId = taskStatus.key().id() 
       taskStatus.jsonPickledCommonTaskMsg = jsonpickle.encode(objCommonTaskMessage)  
       taskStatus.put() 

       taskStatusHistoryKey = taskStatus.createHistory() 
       objCommonTaskMessage.taskStatusId = taskStatus.key().id() 
       self.getAndPostNextTask(objCommonTaskMessage, taskStatusHistoryKey)
       return 



    #else we are moving forward with the next step in a chain, 
    #so we need to set the taskCode and start time for that task 
    isNewTask = False 
    taskStatus = TaskStatus.get_by_id(objCommonTaskMessage.taskStatusId) 
    if not taskStatus: 
       #allow to finsih with 200 status otherwise the task qeueue will keep resubmitting the same data 
       #raise Exception("no taskStatus database row found with taskStatusId = " + str(objCommonTaskMessage.taskStatusId))
       logging.error("no taskStatus database row found with taskStatusId = " + str(objCommonTaskMessage.taskStatusId))
       return 
    #update the task code start/time for this task 
    taskStatus.dateTimeCurrTaskStarted     = datetime.datetime.now()
    taskStatus.dateTimeCurrTaskCompleted   = None   
    taskStatus.currentTaskCode             = objCommonTaskMessage.taskCode 
    taskStatus.currentSeqNum               = objCommonTaskMessage.currentSeqNum
    if hasattr(objCommonTaskMessage, 'isManual'):
       taskStatus.isManual                    = objCommonTaskMessage.isManual 
    else:
       taskStatus.isManual = False 
    taskStatus.put() 

    logging.info("taskCode=" + taskStatus.currentTaskCode + " isManual=" + str(taskStatus.isManual) + " Seq=" + str(objCommonTaskMessage.currentSeqNum)) 

    if taskStatus.isManual:
       self.InviteManualWorkersForTask(taskStatus) 
       return 
       

    if objCommonTaskMessage.taskCode == "TwitterMicroblog": 
       #objTwitterReq = ossTwitterMicroblog 
       #todo - lookup database credentials for this subscriber for Twitter 
       #objTwitterReq.user = subcriberProviderCredentials.user
       #objTwitterReq.password = subcriberProviderCredentials.password 
       #objTwitterReq.microblog = objCommonTaskMessage.generalText 
       #objTwitter = ossTwitterSrv 
       #success, objTwitterResp = objTwitter.post(objTwitterReq) 
       logging.info("Simulating TwitterMicroblog") 
       success = True
       #strError = objTwitterResp.error 
       strError = ""
    elif objCommonTaskMessage.taskCode == "FacebookMicroblog": 
       #objFacebookReq = ossFacebookMicroblog 
       #todo - lookup database credentials for this subscriber for Facebook  
       #objFacebookReq.user = subcriberProviderCredentials.user
       #objFacebookReq.password = subcriberProviderCredentials.password 
       #objFacebookReq.microblog = objCommonTaskMessage.generalText 
       #objFacebook = ossFacebookSrv 
       #success, objFacebookResp = objFacebook.post(objFacebookReq) 
       logging.info("Simulating FacebookMicroblog") 
       success = True
       #strError = objFacebookResp.error 
       strError = ""
    elif objCommonTaskMessage.taskCode == "Delay15": 
       logging.debug("Delay15:Start") 
       strURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/forceTimeout?sleepSeconds=15'))
       form_fields = {}
       form_data = urllib.urlencode(form_fields)
       try:
         result = urlfetch.fetch(strURL, payload=form_data, method=urlfetch.GET, headers={}, allow_truncated=False, follow_redirects=True, deadline=10)
         logging.debug("Delay15:Back from URLFetch result=" + result.content) 
       except (DownloadError), e:
         logging.debug("Raising error") 
         raise ("Download Error - probably time exceeded \n" + str(e))
       #try to force Google 30 second timeout 
       success = True
       strError = "" 
    elif objCommonTaskMessage.taskCode == "DelayAsync15": 
       #Neal was thinking this might be a way around the 10 second limit, but it is not 
       #so this code was never completed, it's just here to remind me that async call is possible:
       #http://code.google.com/appengine/docs/python/urlfetch/asynchronousrequests.html
       logging.debug("DelayAsync15:Start") 
       strURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/forceTimeout?sleepSeconds=15'))
       form_fields = {}
       form_data = urllib.urlencode(form_fields)
       rpc = urlfetch.create_rpc() 
       urlfetch.make_fetch_call(rpc,strURL)
       try:
         result = urlfetch.fetch(strURL, payload=form_data, method=urlfetch.GET, headers={}, allow_truncated=False, follow_redirects=True, deadline=10)
         logging.debug("Delay15:Back from URLFetch result=" + result.content) 
       except (DownloadError), e:
         logging.debug("Raising error") 
         raise ("Download Error - probably time exceeded \n" + str(e))
       #try to force Google 30 second timeout 
       success = True
       strError = "" 
    elif objCommonTaskMessage.taskCode == "Delay40": 
       #try to force Google 10 second timeout on URLFetch 
       logging.debug("Delay40:Start") 
       strURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/forceTimeout?sleepSeconds=40'))
       form_fields = {}
       form_data = urllib.urlencode(form_fields)
       logging.debug("URL=" + strURL)
       result = urlfetch.fetch(strURL, payload=form_data, method=urlfetch.GET, headers={}, allow_truncated=False, follow_redirects=True, deadline=10)
       logging.debug("Delay40:Back from URLFetch result=" + result.content) 
       success = True
       strError = "" 
    elif objCommonTaskMessage.taskCode == "TestError": 
       success = False
       strError = """
       Something bad happened: Traceback (most recent call last):
  File "c:\Program Files\Google\google_appengine\google\appengine\ext
\webapp\__init__.py", line 501, in __call__
    handler.get(*groups)
  File "d:\GoogleAppEngine\3WCloud.com.Provisioning\provisioning.py",
line 746, in get
    strPickledObject = json1.dumps(objCommonTaskMessage)
  File "d:\GoogleAppEngine\3WCloud.com.Provisioning\simplejson
\__init__.py", line 230, in dumps
    return _default_encoder.encode(obj)
  File "d:\GoogleAppEngine\3WCloud.com.Provisioning\simplejson
\encoder.py", line 202, in encode
    chunks = list(chunks)
  File "d:\GoogleAppEngine\3WCloud.com.Provisioning\simplejson
\encoder.py", line 434, in _iterencode
    o = _default(o)
  File "d:\GoogleAppEngine\3WCloud.com.Provisioning\simplejson
\encoder.py", line 177, in default
    raise TypeError(repr(o) + " is not JSON serializable")
TypeError: <dbModels.CommonTaskMessage instance at 0x0CC07A58> is not
JSON serializable  
    """ 
    elif objCommonTaskMessage.taskCode == "GoDaddyNewAccount": 
       #objGodaddyAccount = ossGodaddyAccount
       #THIS IS THE "MAP" of data in BigTable to call GoDaddyService 
       #todo - lookup database credentials for this subscriber for Facebook  
       #does logic to create unique godaddy user go here or in OSS layer? 
       #objGodaddyAccount.user = subcriberProviderCredentials.user
       #objGodaddyAccount.password = subcriberProviderCredentials.password 
       #objGodaddyAccount.domain = service.domainName 
       #loop until not timeout: 
       #success, objGodaddyAccount = objGodaddyAccount.post() 
       #strError = objGodaddyAccount.error 
       success = True
       #strError = objFacebookResp.error 
       strError = ""
    else: 
       pass


    if success: 
       #update TaskStatus that this task successfully finished 
       taskStatus.dateTimeCurrTaskCompleted = datetime.datetime.now()
       taskStatus.put() 
       taskStatusHistoryKey = taskStatus.createHistory() 

       self.getAndPostNextTask(objCommonTaskMessage, taskStatusHistoryKey) 

    else: 
       #update same database row with the error 
       taskStatus.currentTaskError = strError 
       taskStatus.put() 

       log = CumulusLog()    
       log.category = "TaskError" 
       log.level = "Error" 
       #log.ipaddress = self.request.remote_addr #not really relevant for BPM/Task-Manager 
       log.message = "Process=" + objCommonTaskMessage.processCode + " Task=" + objCommonTaskMessage.taskCode + " Error=<see largeText>" 
       log.largeText = strError
       log.put() 
       return 

       
       #cron job, reads table and resubmits the steps that timed-out more than 30-seconds ago. 


  def getAndPostNextTask(self, objCommonTaskMessage, taskStatusHistoryKey): 
  
    nextSeqNum = objCommonTaskMessage.currentSeqNum + 1 
    logging.info("nextSeqNum=" + str(nextSeqNum) + " processCode=" + objCommonTaskMessage.processCode + "\n\n") 
    query = Tasks.gql("WHERE sequence > :1 and processCode = :2", nextSeqNum, objCommonTaskMessage.processCode)
    LIMIT = 1  #just get the one next record with the next higher sequence number 
    taskList = query.fetch(LIMIT,offset=0)
    logging.info("After DB Query: len(taskList)=" + str(len(taskList)) + "\n\n") 
    if len(taskList) < 1:  
       #then we are done, cuz no more tasks for this process code 
       self.UpdateDatabaseForEndProcess(objCommonTaskMessage, taskStatusHistoryKey)
       return 
    #if taskList[0].processCode != objCommonTaskMessage.processCode:
       #then we are done because we found
       # BUT query was changed to look for same process code above so we don't need this "IF" 
       #UpdateDatabaseForEndProcess(objCommonTaskMessage)
    
    logging.info("nextTaskCode=" + taskList[0].taskCode + " seq=" + str(taskList[0].sequence) ) 
    #set the next task code and seqNum, and write back to task/queue       
    objCommonTaskMessage.taskCode       = taskList[0].taskCode 
    objCommonTaskMessage.currentSeqNum  = taskList[0].sequence 
    objCommonTaskMessage.isManual       = taskList[0].isManual 
    strPickledObject = jsonpickle.encode(objCommonTaskMessage) 
    logging.info("strPickledObject to taskQueue = " + strPickledObject) 

    taskqueue.add(url='/commonTaskHandler', 
               method='Post',
               payload = str(strPickledObject)
               ) 


  def UpdateDatabaseForEndProcess(self, objCommonTaskMessage, taskStatusHistoryKey): 
       logging.info("UpdateDatabaseForEndProcess - delete taskStatus where id = " + str(objCommonTaskMessage.taskStatusId)) 
       taskStatus = TaskStatus.get_by_id(objCommonTaskMessage.taskStatusId) 
       if not taskStatus: 
          raise Exception("no taskStatus database row found with taskStatusId = " + str(objCommonTaskMessage.taskStatusId))
       #update the task code start/time for this task 
       #taskStatus.dateTimeProcessCompleted = datetime.datetime.now()
       #taskStatus.currentTaskCode = "None"
       taskStatus.delete()   #taskStatus table should only show running instances of tasks 

       taskStatusHistory = TaskStatusHistory.get(taskStatusHistoryKey) 
       if not taskStatusHistory: 
          logging.error("No existing taskStatusHistory record for key = " + str(taskStatusHistoryKey)) 
       taskStatusHistory.dateTimeProcessCompleted = datetime.datetime.now() 
       taskStatusHistory.put() 


  def InviteManualWorkersForTask(self, taskStatus): 
       #find people who are eligible to do manual tasks (based on the isWorker flag in the subscriber table) 
       #(each contractor/employee will have an entry in the subscriber table) 
       logging.info("InviteManualWorkersForTask") 
       query = Subscriber.gql("WHERE isWorker = :1 ", True) 
       LIMIT = 100 
       subscriberList = query.fetch(LIMIT,offset=0)  
       logging.info("After DB Query: len(subscriberList)=" + str(len(subscriberList)) + "\n\n") 
       for subscriber in subscriberList:
           self.NotifyWorker(taskStatus, subscriber) 
       if len(subscriberList) == 0: 
          logging.error("No workers found to perform manual task (no subscribers have isWorker flag set)") 
          #end without updating dateTimeManualNotification
          return

       #update database row to show that we have sent emails to workers 
       taskStatus.isManualNotificationComplete  = True 
       taskStatus.dateTimeManualNotification = datetime.datetime.now() 
       taskStatus.put() 


  def NotifyWorker(self, taskStatus, subscriber):

    message = mail.EmailMessage()
    message.sender = "Neal Walters <googleadmin@3wcloud.com>"
    message.subject = "3WCloud - Manual Work Request " 
    message.to = subscriber.userEmail  
    message.html = """
ProcessCode:  &processCode   Task: &taskid   TaskCode: &taskCode 
<br/><br/>
To accept this work request and attempt to complete it in the next 15 minutes, click here: <br/>
    <a href='&url'>&url</a> 
"""
    strURL =  str(atom.url.Url('http', settings.HOST_NAME, 
        path='/acceptManualTask?id=' + str(taskStatus.key().id()) + "&key=" + str(taskStatus.key()) + "&subscriberKey=" + str(subscriber.key())))

    message.html = message.html.replace("&processCode",taskStatus.processCode) 
    message.html = message.html.replace("&taskId",str(taskStatus.key().id())) 
    message.html = message.html.replace("&taskCode",taskStatus.currentTaskCode) 
    message.html = message.html.replace("&url",strURL) 

    message.send()
    logging.info("Email:url = " + strURL) 




class TaskCron(webapp.RequestHandler):

  def get(self):
    
    log = CumulusLog()    
    log.category = "CronJob"
    log.level = "Info" 
    #log.ipaddress = self.request.remote_addr #not really relevant for BPM/Task-Manager 
    log.message = "Start TaskCron - Simulator" 
    log.put() 

    #restart any timeouts 

    query = TaskStatus.gql("where isInRetriesExceededState = :1", False) 
    LIMIT = 1  #just get the one next record with the next higher sequence number 
    taskStatusList = query.fetch(LIMIT,offset=0)
    logging.info("After DB Query: len(taskStatusList)=" + str(len(taskStatusList)) + "\n\n") 
    for taskStatus in taskStatusList:
        if not taskStatus.dateTimeProcessCompleted: 
           timeDiff = datetime.datetime.now() - taskStatus.dateTimeCurrTaskStarted
           #TODO - change to or add logging.info here - 
           #because self.response.out.write does not apply to cron jobs 
           #but is useful when testing from browser 
           self.response.out.write("timeDiff =" + str(timeDiff))  #1:12:38.358000 
           self.response.out.write(" &nbsp;&nbsp;&nbsp; timeDiff seconds=" + str(timeDiff.seconds)) 

           if timeDiff.seconds > 60:  #if timed-out more than one minute ago 

              if taskStatus.numOfRetries < 3:  
                 varCountdown = 0       #no delay - try again ASAP 
              #elif taskStatus.numRetries < 6: 
              #   varCountdown = 600    #10 minutes = 10x60 seconds 
              #elif taskStatus.numRetries < 9: 
              #   varCountdown = 6000   #1 hour = 10*60*60 seconds 
              else:
                 #notify someone 
                 varCountdown = -1 
                 self.LogAndNotifyError(taskStatus) 
                
              if varCountdown != -1:
                #then resubmit to queue 
                objCommonTaskMessage = jsonpickle.decode(taskStatus.jsonPickledCommonTaskMsg) 
                #must refresh the object values with current db values 
                #so that the restart will continue where it let off 
                objCommonTaskMessage.currentSeqNum = taskStatus.currentSeqNum 
                objCommonTaskMessage.taskCode      = taskStatus.currentTaskCode
                objCommonTaskMessage.taskStatusId  = taskStatus.key().id() 
                strPickledObject = jsonpickle.encode(objCommonTaskMessage) 

                taskqueue.add(url='/commonTaskHandler', 
                        method='Post',
                        countdown=varCountdown,
                        payload = str(strPickledObject)
                        ) 
                taskStatus.jsonPickledCommonTaskMsg = strPickledObject 
                taskStatus.numOfRetries += 1
                taskStatus.put()                  #update retry/count 
                self.response.out.write("<br/>Resubmitted taskId=" + str(taskStatus.key().id()))
 


  def LogAndNotifyError(self, taskStatus):

    notificationList = "Neal Walters <nwalters@sprynet.com>" 
    message = mail.EmailMessage()
    #can optionally pass parms in constructor like this: 
    #message = mail.EmailMessage(sender="support@example.com",
    #                       subject="Your account has been approved")

    message.sender = "Neal Walters <googleadmin@3wcloud.com>"
    message.subject = "CUMULUS ERROR ALERT: Task has exceed max retries TaskId=" + str(taskStatus.key().id())
    message.to = notificationList 
    message.html = """
    ProcessCode: &processCode   Task: &taskId   TaskCode: &taskCode 
    """

    message.html = message.html.replace("&processCode", taskStatus.processCode) 
    message.html = message.html.replace("&taskId",      str(taskStatus.key().id())) 
    message.html = message.html.replace("&taskCode",    taskStatus.currentTaskCode) 

    message.send()

    #update database row to show that we have sent email and that task should no longer be restarted 
    taskStatus.isInRetriesExceededState  = True 
    taskStatus.dateTimeErrorNotification = datetime.datetime.now() 
    taskStatus.put()  



class ForceTimeout(webapp.RequestHandler):
  def get(self):
     startTime = datetime.datetime.now() 
     sleepSeconds = self.request.get("sleepSeconds") 
     time.sleep(float(sleepSeconds))
     stopTime = datetime.datetime.now() 
     timespan = stopTime - startTime 
     #self.response.headers['Content-Type'] = "application/json";
     response = "dummyresponse slept for " + sleepSeconds + " Elapsed Time=" + str(timespan)
     logging.info(response)
     self.response.out.write(response)

#=======================================================
# End of WebServices 
#=======================================================

