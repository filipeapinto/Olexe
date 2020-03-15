class TestGDocAPI(webapp.RequestHandler):

  def get(self):

     client = gdata.service.GDataService()
     # Tell the client that we are running in single user mode, and it should not
     # automatically try to associate the token with the current user then store
     # it in the datastore.
     gdata.alt.appengine.run_on_appengine(client, store_tokens=False, single_user_mode=True)
     client.email = '***'
     client.password = '***'
     # To request a ClientLogin token you must specify the desired service using 
     # its service name.
     # "wise" is the codename for GoogleDocs - see this page:
     # http://ruscoe.net/google/google-account-service-names/ 
     client.service = 'wise'  
     # Request a ClientLogin token, which will be placed in the client's 
     # current_token member.
     client.ProgrammaticLogin() 

     #gd_client = gdata.docs.service.DocsService(email='*****',password='***')
     #gd_client.ClientLogin('GoogleAdmin@3wcloud.com', '***')

     gdata.alt.appengine.run_on_appengine(client)

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
