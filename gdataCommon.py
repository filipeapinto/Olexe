import StringIO
import gdata.docs
import gdata.docs.service
import gdata.alt.appengine
from datetime import datetime 
from dbModels import Document 
from dbModels import Provider
from dbModels import Subscriber
from dbModels import SubscriberProviderCredentials 
from dbModels import KeyValuePair
from appengine_utilities.sessions import Session 


def GDataXMLDateToPythonDateTime(dateTimeIn):
	  
  #dt1 = "2009-07-28T20:46:21.909Z"   This is the type of date we receive 
  #dt1 = "2009-07-28 20:46:21"        We must scrub to this before using strptime 

  dt1 = dateTimeIn.replace("T"," ")
  dt1 = dt1[:-5]   #get everything to left of last 5 characters 

  #print "dt1=" + dt1

  dt2 = datetime.strptime(dt1, "%Y-%m-%d %H:%M:%S")  #convert xml date/time 
     
  return dt2 


def PrintFeed(feed):
  """Prints out the contents of a feed to the console."""
  print '\n'
  if not feed.entry:
    print 'No entries in feed.\n'
  for entry in feed.entry:
    print 'Encode=%s DocType=%s Resource=%s' % (entry.title.text.encode('UTF-8'), entry.GetDocumentType(), entry.resourceId.text)
  print "\n\n" 

def PrintFeed2(feed):
  """Prints out the contents of a feed to the console."""
  print '\n'
  for entry in feed:
    print 'Encode=%s DocType=%s Resource=%s' % (entry.title.text.encode('UTF-8'), entry.GetDocumentType(), entry.resourceId.text)
  print "\n\n" 

def PrintFeed3(feed):
  """Prints out the contents of a feed to the console."""
  print '\n'
  #feed.sort(feedCompareBy('title')) 
  for entry in feed: 
    print "title=" + entry['title'] + " docId=" + entry['docId'] 
  print "\n\n" 


def feedCompareBy (fieldname):
  def compare_two_dicts (a, b):
      return cmp(a[fieldname], b[fieldname])
  return compare_two_dicts

def feedCompareByDocName():
  def compare_two_dicts (a, b):
      return cmp(a.docName, b.docName) 
  return compare_two_dicts

def GetGDocsAuthenticatedClient(): 
   """
   Logon to Google with the admin user of 3wcloud.com.
   """

   # Tell the client that we are running in single user mode, and it should not
   # automatically try to associate the token with the current user then store
   # it in the datastore.
   client = gdata.docs.service.DocsService()
   gdata.alt.appengine.run_on_appengine(client, store_tokens=False, single_user_mode=True)
   objKeyValuePair = KeyValuePair() 
   userid    = objKeyValuePair.getValueFromKey("KB_Document_Userid") 
   password  = objKeyValuePair.getValueFromKey("KB_Document_Password") 
   client.email = userid
   client.password = password
   # To request a ClientLogin token you must specify the desired service using 
   # its service name.  Neal verified 07/27/09 that login fails without this parm
   # even though some documents indicate that it is optional). 
   # "wise" is the codename for GoogleDocs - see this page:
   # http://ruscoe.net/google/google-account-service-names/ 
   #client.service = 'wise'      #for Google Spreadsheets
   client.service = 'writely'   #for Google Docs (include spreadsheets?) 
   client.accountType = "HOSTED_OR_GOOGLE"
   client.accountType = "HOSTED"
   client.ClientLogin(client.email,client.password)
   return client 

def GetGDocsAuthenticatedClientForCurrentUser(): 
   """
   Logon to Google with the user currently logged on to Cumulus. 
   See more detailed programming/API comments in GetGDocsAuthenticatedClient.
   """

   providerName = "GoogleAppAccount"
   mySession = Session() 
   if not 'subscriberkey' in mySession:
      raise ("no subscriberkey in Session") 

   subscriberkey = mySession['subscriberkey']
   subscriber = Subscriber.get(subscriberkey)
   if not subscriber:
      raise ("Subscriber not found with subscriberkey=" + str(subscriberkey)) 

   query = Provider.gql("where name = :1 ", providerName) 
   LIMIT = 1
   providerList = query.fetch(LIMIT) 
   if len(providerList) > 0:
      provider = providerList[0] 
   else:
      raise Exception("Provider not found with providerName= " + providerName) 
   

   query = SubscriberProviderCredentials.gql("where subscriber = :1 and provider = :2 ", subscriber, provider) 
   LIMIT = 1 
   credentialsList = query.fetch(LIMIT) 
   if len(credentialsList) > 0:
      credentials = credentialsList[0]
   else:
      raise Exception("No credentials found for provider=" + providerName + " and subscriber = " + subscriber.firstname + " "  + subscriber.lastname) 
   
   # Tell the client that we are running in single user mode, and it should not
   # automatically try to associate the token with the current user then store
   # it in the datastore.
   client = gdata.docs.service.DocsService()
   gdata.alt.appengine.run_on_appengine(client, store_tokens=False, single_user_mode=True)
   objKeyValuePair = KeyValuePair() 
   #userid    = subscriber.googleAppsUserid
   #password  = subscriber.googleAppsPassword
   client.email       = credentials.userid
   client.password    = credentials.password
   client.service     = 'writely'   #for Google Docs (include spreadsheets?) 
   client.accountType = "HOSTED"
   client.ClientLogin(client.email,client.password)
   return client 


def GetMatchingFileFeed(argClient, argPrefix, argContains): 
   """
   return a list of Document objects for the given client, 
   whose titles start with a certain prefix, and optional contain a certain string 
   """
   # Query the server for an Atom feed containing a list of your documents.
   gdata.alt.appengine.run_on_appengine(argClient, store_tokens=False, single_user_mode=True)
   documents_feed = argClient.GetDocumentListFeed()
   # Loop through the feed and extract each document entry.
   selectedFilenameFeed = []  # a list of dictionary objects (each containing title and docId) 
   for documentEntry in documents_feed.entry:
     # Display the title of the document on the command line.
     foundMatch = False 
     if documentEntry.title.text.startswith(argPrefix):
        if argContains > " ": 
	   if argContains in documentEntry.title.text:
	    foundMatch = True 
	else: 
	    foundMatch = True 
     if foundMatch: 
           document = Document()
	   document.docName = documentEntry.title.text
	   document.publishedDate = documentEntry.published.text 
           # resourceId.text looks like this: document:ddjjzvdp_89pfwxmphb
	   document.docId   = documentEntry.resourceId.text
           #document.editMediaLink = documentEntry.GetEditMediaLink().href 
           selectedFilenameFeed.append(document) 
   selectedFilenameFeed.sort(feedCompareByDocName()) 
   return selectedFilenameFeed

   #apparently the way to get the properties of the documentEntry is here:
   #http://gdata-python-client.googlecode.com/svn/trunk/pydocs/gdata.docs.html
   #look for GetDocumentType(self) and then look at the arguments of the __init__ method. 


def GetMatchingFileFeed2(argClient, argPrefix, argContains): 

   # Query the server for an Atom feed containing a list of your documents.
   gdata.alt.appengine.run_on_appengine(argClient, store_tokens=False, single_user_mode=True)
   documents_feed = argClient.GetDocumentListFeed()
   # Loop through the feed and extract each document entry.
   selectedFilenameFeed = []  # a list of dictionary objects (each containing title and docId) 
   for documentEntry in documents_feed.entry:
     # Display the title of the document on the command line.
     if documentEntry.title.text.startswith(argPrefix):
        if argContains > " ": 
           if argContains in documentEntry.title.text:
              selectedFilenameFeed.append({"title":documentEntry.title.text,
                                           "docId":documentEntry.resourceId.text,
					   "publishedDate": documentEntry.published.text
					   }) 
        else: 
           selectedFilenameFeed.append({"title":documentEntry.title.text,
                                        "docId":documentEntry.resourceId.text,
					"publishedDate": documentEntry.published.text
					}) 
   selectedFilenameFeed.sort(feedCompareBy('title')) 
   return selectedFilenameFeed


def GetMatchingFileFeed3(argClient, argContains): 
   """
   return a list of Document objects for the given client, 
   and name contains a certain string 
   """
   # Query the server for an Atom feed containing a list of your documents.
   gdata.alt.appengine.run_on_appengine(argClient, store_tokens=False, single_user_mode=True)
   documents_feed = argClient.GetDocumentListFeed()
   # Loop through the feed and extract each document entry.
   selectedFilenameFeed = []  # a list of dictionary objects (each containing title and docId) 
   for documentEntry in documents_feed.entry:
     # Display the title of the document on the command line.
     foundMatch = False 
     if argContains in documentEntry.title.text:
        foundMatch = True 
     else: 
	foundMatch = True 
     if foundMatch: 
           document = Document()
	   document.docName = documentEntry.title.text
	   document.publishedDate = documentEntry.published.text 
           # resourceId.text looks like this: document:ddjjzvdp_89pfwxmphb
	   document.docId   = documentEntry.resourceId.text
           document.editMediaLinkHref = documentEntry.GetEditMediaLink().href 
           selectedFilenameFeed.append(document) 
   selectedFilenameFeed.sort(feedCompareByDocName()) 
   return selectedFilenameFeed

   #apparently the way to get the properties of the documentEntry is here:
   #http://gdata-python-client.googlecode.com/svn/trunk/pydocs/gdata.docs.html
   #look for GetDocumentType(self) and then look at the arguments of the __init__ method. 



def GetFeedByKeyword(argClient, keyword):
   q = gdata.docs.service.DocumentQuery()
   q.text_query = keyword
   q['title'] = '3WC.'
   q['title-exact'] = 'false'
   documentsFeed = argClient.Query(q.ToUri())
   return documentsFeed 


def GetGoogleDocHTMLContents(argClient, argDocId):
   """
   Given a docId, and an already authorized client, 
   grab the HTML contents of a file on google docs 
   """
   exportFormat = "html"
   domain = "docs.google.com" 
   url = "http://" + domain + "/feeds/download/documents/Export?docID=" + argDocId + "&exportFormat=" + exportFormat 

   #TODO - how to test this - also might want retry on other feeds and client.login 
   retries = 0
   htmlFileContents = "" 
   err = "time"  #short for timeout 
   while retries < 5 and "time" in err.lower():
      try:
         htmlFileContents = argClient.Get(url,converter=str)
	 retries = 9999 #we got the file, quit the loop 
      except (Exception), err:
         #TODO specficially look for timeout here, not just any error 
         retries += 1
	 htmlFileContents = str(err) 
	 import logging
	 logging.debug("GetGoogleDocHTMLContents:" + str(err)) 

   return htmlFileContents


def CreateGoogleDoc(argClient, argDocName, argDocContent):
   """
   Create a google document with the given name and content under the 
   current user 
   """
 
   #add new empty document 
   new_entry = gdata.GDataEntry()
   new_entry.title = gdata.atom.Title(text=argDocName)
   category = gdata.atom.Category(scheme=gdata.docs.service.DATA_KIND_SCHEME, term=gdata.docs.service.DOCUMENT_KIND_TERM)
   new_entry.category.append(category)
   created_entry = argClient.Post(new_entry, '/feeds/documents/private/full')
   #     print 'Document now accessible online at:', created_entry.GetAlternateLink().href
   #     print 'GetEditMediaLink:', created_entry.GetEditMediaLink().href

   #append contents to the now-existing document 
   ms = gdata.MediaSource(file_handle=StringIO.StringIO(argDocContent), content_type='text/html', content_length=len(argDocContent))
   updated_entry = argClient.Put(ms, created_entry.GetEditMediaLink().href + '?append=true')


def AppendToGoogleDoc(argClient, argDocId, argDocNameContains, argDocContent):
   """
   Create a google document with the given name and content under the 
   current user 
   """

 
   documents = GetMatchingFileFeed3 (argClient, argDocNameContains)
   if len(documents) > 1:
      raise Exception("More than one document found matching name contains '" + argDocNameContains + "'") 

   

   #append contents to the now-existing document 
   ms = gdata.MediaSource(file_handle=StringIO.StringIO(argDocContent), content_type='text/html', content_length=len(argDocContent))
   #updated_entry = argClient.Put(ms, created_entry.GetEditMediaLink().href + '?append=true')
   updated_entry = argClient.Put(ms, documents[0].editMediaLinkHref + '?append=true')

