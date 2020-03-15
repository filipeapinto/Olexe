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
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

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


