'''
Created on Aug 20, 2009

@author: fpinto

Synopsis:
    This module tests the google.py module from the
    twccloudsrv package.
    
    The test class doesn't derive from unittest. The reason
    is because we need to have tests that never run the same
    exact configuration twice.


Date      Author        Description
--------  ------------- -------------------------------------------------------
09-04-09  fpinto        Converted old ad-hoc tests to be within the context of
                        a class.   
09-09-09  fpinto        Separated the GSite tests onto a new class.
                        Created a new class to test GSiteHelper
09-25-09  fpinto        Created a class TGDocument to test GDocument 
09-28-09  fpinto        Added the classes TGCalendarService, TGCalendar, 
                        TGEmailService and TGEmail, TGDomainService
'''
import unittest
from twccloudsrv.google import *
import jsonpickle
import random


DEFAULT_FIRST_NAME    = '****'
DEFAULT_LAST_NAME     = '****'
DEFAULT_ADMIN_EMAIL   = '****'
DEFAULT_ADMIN_PHONE   = '****'
DEFAULT_TITLE         = '****'
DEFAULT_COUNTRY       = '****'
DEFAULT_LOGIN_NAME    = '****'
DEFAULT_EMAIL         = '****' 
DEFAULT_PASSWORD      = '****'
DEFAULT_DOMAIN_NAME   = '****'
DEFAULT_SITE_NAME     = '****'
DEFAULT_SITE_URL      = '****'


class TGHSession():


    def test_get(self,
                 email       = DEFAULT_EMAIL,
                 login_name  = DEFAULT_LOGIN_NAME,
                 password    = DEFAULT_PASSWORD,
                 domain_name = DEFAULT_DOMAIN_NAME,
                 debug       = False):
        '''
        Synopsis:
            Creates a new Google Hosted Account Session
        Arguments:
             email       = DEFAULT_EMAIL,
             login_name  = DEFAULT_LOGIN_NAME,
             password    = DEFAULT_PASSWORD,
             domain_name = DEFAULT_DOMAIN_NAME,
             debug       = False        
        Expected results:
            No errors
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-login_name: %s\n-password: %s\n-debug: %s' % \
                  (email,login_name,password,str(debug)) 
        session = GHSession(debug=True)
        session.email       = email
        session.password    = password
        session.login_name  = login_name 
        session.domain_name = domain_name       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        
        assert success, error
        
class TGHAccount():        
        
    def test_get(self,
                 email       = DEFAULT_EMAIL,
                 login_name  = DEFAULT_LOGIN_NAME,
                 password    = DEFAULT_PASSWORD,
                 domain_name = DEFAULT_DOMAIN_NAME,
                 deep        = False,
                 debug       = False):
        '''
        Synopsis:
            Gets the details of a Google Hosted Account
        Arguments:
             email       = DEFAULT_EMAIL,
             login_name  = DEFAULT_LOGIN_NAME,
             password    = DEFAULT_PASSWORD,
             domain_name = DEFAULT_DOMAIN_NAME,
             deep        = False,
             debug       = False
        Expected Results:
            JSON of the account
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-login_name: %s\n-password: %s\n-deep: %s\n-debug: %s' % \
                  (email,login_name,password,str(deep),str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            my_account = GHAccount()
            success = my_account.get(session)
            if not success:
                error = my_account.error
            else:
                print 'Results:\n-' + jsonpickle.encode(my_account)
        
        assert success, error

    def test_post(self,
                  domain_name,
                  debug=False):
        '''
        Test:
            Creates a new Google Hosted Account.
        Arguments:
            domain_name
            debug=False        
        Expected results:
            CNAME to add to the DNS server
        '''
        print self.test_post.__doc__
        print 'Arguments:\n-domain_name: %s\n-debug: %s' % \
                  (domain_name,str(debug)) 
        my_account= GHAccount()
        my_account.debug         = debug
        my_account.domain_name   = domain_name
        my_account.first_name    = DEFAULT_FIRST_NAME
        my_account.last_name     = DEFAULT_LAST_NAME
        my_account.email         = DEFAULT_ADMIN_EMAIL
        my_account.phone         = DEFAULT_ADMIN_PHONE
        my_account.country       = DEFAULT_COUNTRY
        my_account.job_title     = DEFAULT_TITLE
        my_account.password      = DEFAULT_PASSWORD
        success = my_account.post()
        if not success:
            error = my_account.error
        else:
            print 'Please add the following CNAME to your domain :' + my_account.verification_cname
    
        assert success, error
              
                
    def test_put(self):
        '''
        Synopsis:
            I'm not sure yet on how to write this test
        Expected results:
            ?
        '''

        #Creating the email account
        my_email_service = GmailService()
        #adding the email service to the account.
        my_account.put(my_email_service)    
        #create the calendar account
        my_calendar_service = GoogleCalendarService()
        #adding the email calendar to the Google App account.
        my_account.put(my_email_service) 



class TGSiteService():
    '''
    Synopsis:
        Tests the GSiteService class
    '''
    
    def test_get(self,
                 email       = DEFAULT_EMAIL,
                 login_name  = DEFAULT_LOGIN_NAME,
                 password    = DEFAULT_PASSWORD,
                 domain_name = DEFAULT_DOMAIN_NAME,
                 deep        = False,
                 debug       = False):
        '''
        Synopsis:
            Gets the details of a Google Site Service. Corresponds
            to doing a get on part of the Google Hosted Account
            that defines the overall site configuration.
        Arguments:
             email       = DEFAULT_EMAIL,
             login_name  = DEFAULT_LOGIN_NAME,
             password    = DEFAULT_PASSWORD,
             domain_name = DEFAULT_DOMAIN_NAME,
             deep        = False,
             debug       = False
        Expected Results:
            JSON of the Site Service (Site configuration)
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-login_name: %s\n-password: %s\n-deep: %s\n-debug: %s' % \
                  (email,login_name,password,str(deep),str(debug)) 

        session = GHSession(debug=True)
        session.email    = email
        session.password = password        
        success = session.get()
        if not success:
            error = session.error
        else:
            #getting GSiteService
            srv = GSiteService()
            success = srv.get(session)
            if not success:
                error = srv.error
            else:
                print jsonpickle.encode(srv)
        
        assert success, error  


class TGSiteHelper():

    def test_RemoveSpace(self):
        '''
        Synopsis:
            Test the remove space function
        '''
        dict = ' { "test 1" : " ekjk sdfdskj"    ,    "kdjf dsflikds sdfsdf"     :    "ksdjfsdkfj sdfds"   }   '
        print GSiteHelper._rm_space(dict)


class TGSite():
    '''
    Synopsis:
    '''        

    def test_get(self,
                 site_url = DEFAULT_SITE_URL,
                 email    = DEFAULT_EMAIL,
                 password = DEFAULT_PASSWORD,
                 debug=True):
        '''
        Synopsis:
            Gets information on website
        Arguments:
            site_url = DEFAULT_SITE_URL
            email    = DEFAULT_EMAIL
            password = DEFAULT_PASSWORD
            debug    = True
        Expected Results
            JSON with website
        '''
        print self.test_get.__doc__
        print '\n\nArguments:\n-site url: %s\n-email: %s\n-password: %s\n-debug: %s' % \
                  (site_url,email,password,str(debug)) 
        
        session = GHSession(debug=debug)
        session.email       = email
        session.password    = password
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the Site
            site = GSite()
            site.url = site_url
            success  = site.get(session, type='all')
            if not success:
                error = site.error
            else:
                print 'JSON: ' + jsonpickle.encode(site) 
        
        assert success, error  

    def test_post(self,site_url,
                       site_name   = DEFAULT_SITE_NAME,
                       email       = DEFAULT_EMAIL,
                       login_name  = DEFAULT_LOGIN_NAME,
                       password    = DEFAULT_PASSWORD,
                       domain_name = DEFAULT_DOMAIN_NAME,
                       debug       = False):
        '''
        Synopsis:
            Creates a new site.
        Arguments:
           site_url
           site_name   = DEFAULT_SITE_NAME
           email       = DEFAULT_EMAIL
           login_name  = DEFAULT_LOGIN_NAME
           password    = DEFAULT_PASSWORD
           domain_name = DEFAULT_DOMAIN_NAME
           debug       = False
        Expected Results:
            JSON of the Site Service (Site configuration)
        '''
        print self.test_post.__doc__
        print 'Arguments:\n-site url: %s\n-site name: %s\n-email: %s\n-login_name: %s\n-password: %s\n-debug: %s' % \
                  (site_url,site_name,email,login_name,password,str(debug)) 
        
        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the Site
            site = GSite()
            site.name         = site_name
            site.url          = site_url
            site.description  = 'test site description'
            site.is_public    = True
            site.tags         = ['tag1','tag2','tag3','tag4','tag5','','tag6']
            site.theme        = 'Iceberg' 
            success = site.post(session)
            if not success:
                error = site.error
            else:
                print 'successfully created site'
        
        assert success, error 

    def test_put_info(self,site_url,
                           type        = None,
                           email       = DEFAULT_EMAIL,
                           password    = DEFAULT_PASSWORD,
                           debug       = False):
        '''
        Synopsis:
            Changes the site general info settings.
        Arguments:
           site_url
           Type        = None
           email       = DEFAULT_EMAIL
           password    = DEFAULT_PASSWORD
           debug       = False
        Expected Results:
            JSON of the Site Service (Site configuration)
        '''
        print self.test_put_info.__doc__
        print 'Arguments:\n-site url: %s\n-type: %s\n-email: %s\n-password: %s\n-debug: %s' % \
                  (site_url,type,email,password,str(debug)) 
        
        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            site = GSite()
            site.url= site_url
            #######################################################
            #
            # Updating general info
            #
            # Note: this is a test without first doing a get
            #
            #######################################################               
            success = site._put_info(session, title='Project rt', 
                                              show_title = False, 
                                              tags = ['bpm','complex adaptive systems'],
                                              description = 'This is Filipe Pinto website',
                                              locale = 'en')
            if not success:
                error = site.error
            else:
                print 'successfully updated site general information'
                
        assert success, error
                
    def test_put_sharing(self,site_url,
                              type        = None,
                              email       = DEFAULT_EMAIL,
                              password    = DEFAULT_PASSWORD,
                              debug       = False):
        '''
        Synopsis:
            Changes the site sharing settings.
        Arguments:
           site_url
           Type        = None
           email       = DEFAULT_EMAIL
           password    = DEFAULT_PASSWORD
           debug       = False
        Expected Results:
            JSON of the Site Service (Site configuration)
        '''
        print self.test_put_sharing.__doc__
        print 'Arguments:\n-site url: %s\n-type: %s\n-email: %s\n-password: %s\n-debug: %s' % \
                  (site_url,type,email,password,str(debug)) 
        
        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            site = GSite()
            site.url= site_url                    
            #######################################################
            # Updating sharing info - adding
            #######################################################
            admin_list  = ['test1@nealwalters.com','test2@nealwalters.com']
            admin_email = {'subject': 'Come help me with my oneCloud',
                           'body'   : 'I\'m inviting you to become an administrator of my oneCloud. Thank you',
                           'doCc'   : True}
            
            success = site._put_sharing(session, 'administrator', admin_list, 'add', admin_email)
            
            collab_list = ['test3@nealwalters.com','test4@nealwalters.com']
            collab_email= {'subject': 'Come help me with my oneCloud',
                           'body'   : 'I\'m inviting you to become an administrator of my oneCloud. Thank you',
                           'doCc'   : True}

            success = site._put_sharing(session, 'collaborator', collab_list, 'add', collab_email)
            
            viewer_list = ['test5@nealwalters.com','test6@nealwalters.com']
            viewer_email = {'subject':'Come help me with my oneCloud',
                           'body'   : 'I\'m inviting you to become an administrator of my oneCloud. Thank you',
                           'doCc'   : True}

            success = site._put_sharing(session, 'viewer', viewer_list, 'add', viewer_email)

            #######################################################
            #
            # Updating sharing info - Removing
            #
            #######################################################
            admin_list  = ['test1@nealwalters.com']
            success = site._put_sharing(session, 'administrator', admin_list, 'remove')            
            collab_list = ['test3@nealwalters.com']
            success = site._put_sharing(session, 'collaborator', collab_list, 'remove')
            viewer_list = ['test5@nealwalters.com']
            success = site._put_sharing(session, 'viewer', viewer_list, 'remove')
            
            #######################################################
            # Changing site collaborator wide sharing settings
            #######################################################
            #making site public opening it to guests
            success = site._put_sharing(session, 'guest',['#public'],'add')
            #not allowing domain users to edit 
            success = site._put_sharing(session, 'collaborator',['#domain'],'remove')

        assert success, error

    def test_put_attachment(self,site_url,
                                 type        = None,
                                 email       = DEFAULT_EMAIL,
                                 password    = DEFAULT_PASSWORD,
                                 debug       = False):
        '''
        Synopsis:
            Changes the site general attachment settings.
        Arguments:
           site_url
           Type        = None
           email       = DEFAULT_EMAIL
           password    = DEFAULT_PASSWORD
           debug       = False
        Expected Results:
            JSON of the Site Service (Site configuration)
        '''
        print self.test_put_attachment.__doc__
        print 'Arguments:\n-site url: %s\n-type: %s\n-email: %s\n-password: %s\n-debug: %s' % \
                  (site_url,type,email,password,str(debug)) 
        
        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            site = GSite()
            site.url= site_url          
            #loading file from disk
            site._put_attachments(session, 'upload', 'File1-test1.png', '/files', content_type='image/x-png',
                                   uri =  'file://C:\\Documents and Settings\\fpinto\\My Documents\\2-3wcloud\\images\\3wcloud-facebook.com.png')
            
            #loading file from web
            site._put_attachments(session, 'upload', 'Resume.doc', '/files', content_type='application/msword',
                                   uri =  'http://www.filipe-pinto.com/resume/filipe_pinto_resume_v0409.doc?attredirects=0')

            #removing file loaded from disk
            site._put_attachments(session, 'remove', 'File1-test1.png', '/files')
            
            #removing file from web
            site._put_attachments(session, 'remove', 'Resume.doc', '/files')
            
        assert success, error
            
    def test_put_layout(self,site_url,
                             type        = None,
                             email       = DEFAULT_EMAIL,
                             password    = DEFAULT_PASSWORD,
                             debug       = False):
        '''
        Synopsis:
            Changes the site layout settings.
        Arguments:
           site_url
           Type        = None
           email       = DEFAULT_EMAIL
           password    = DEFAULT_PASSWORD
           debug       = False
        Expected Results:
            JSON of the Site Service (Site configuration)
        '''
        print self.test_put_layout.__doc__
        print 'Arguments:\n-site url: %s\n-type: %s\n-email: %s\n-password: %s\n-debug: %s' % \
                  (site_url,type,email,password,str(debug)) 
        
        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #######################################################
            # Updating layout info
            #######################################################

            site = GSite()
            site.url= site_url            
            
            success  = site._put_layout(session, theme = 'iceberg')
            if not success:
                error = site.error
            else:
                print 'successfully updated site'
            
            #######################################################
            # Adding text box
            #######################################################
            '''
            component = GSiteComponent(generate=True)
            component.content = 'this is my bio.  I\' really crazy about starting new companies.'
            component.type    = 'min-textbox'
            component.is_hide_title = False
            component.title = 'Bio'
            component.operation = 'add'
            list=[]
            list.append(component)
            success  = site._put_layout(session, components=list)
            if not success:
                error = site.error
            else:
                print 'successfully updated site'
                
            '''            
            #######################################################
            # removing text box
            #######################################################
            '''
            component = GSiteComponent()
            component.type      = 'min-textbox'
            component.title     = 'bio'
            component.operation = 'remove'
            list=[]
            list.append(component)
            success  = site._put_layout(session, components=list)
            if not success:
                error = site.error
            else:
                print 'successfully updated site'
            '''    

            '''
            #######################################################
            # Adding countdown
            #######################################################
            '''
            '''
            component = GSiteComponent(generate=True)
            component.from_date_utc = '1123459200000'
            component.type          = 'min-countdown'
            component.is_hide_title = False
            component.event = 'Days till ABPMP exam'
            component.operation = 'add'
            list=[]
            list.append(component)
            success  = site._put_layout(session, components=list)
            if not success:
                error = site.error
            else:
                print 'successfully updated site'
            '''    
            '''
            #######################################################
            # removing text box
            #######################################################
            component = GSiteComponent()
            component.type      = 'min-countdown'
            component.event     = 'Days till ABPMP exam'
            component.operation = 'remove'
            list=[]
            list.append(component)
            success  = site._put_layout(session, components=list)
            if not success:
                error = site.error
            else:
                print 'successfully updated site'
            '''
            
            
                        
        assert success, error  
        
    def test_delete(self, site_url,
                           email       = DEFAULT_EMAIL,
                           login_name  = DEFAULT_LOGIN_NAME,
                           password    = DEFAULT_PASSWORD,
                           domain_name = DEFAULT_DOMAIN_NAME,
                           debug       = False):
        '''
        Synopsis:
            deletes a website
        Expected Results:
            message - "Site successfully deleted'
        '''
        print self.test_delete.__doc__
        print 'Arguments:\n-site name: %s\n-email: %s\n-login_name: %s\n-password: %s\n-debug: %s' % \
                  (site_url,email,login_name,password,str(debug))
         
        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the Site
            my_site = GSite()
            my_site.url         = site_url
            success = my_site.delete(session)
            if not success:
                error = my_site.error
            else:
                print 'successfully deleted site'
        
        assert success, error  

        
class TGSitePage():        


    def test_get(self,site_url,page_relative_uri,
                      email       = DEFAULT_EMAIL,
                      login_name  = DEFAULT_LOGIN_NAME,
                      password    = DEFAULT_PASSWORD,
                      domain_name = DEFAULT_DOMAIN_NAME,
                      debug       = False):
        '''
        Synopsis:
            Retrieves the low level info
            associated with a GSite Page
        Expected Results:
            Json pickle of the GSitePage object
        '''    
        print self.test_get.__doc__
        print 'Arguments:'
        print ' site url          : %s' % site_url
        print ' page_relative_uri : %s' % page_relative_uri
        print ' login name        : %s' % login_name
        print ' password          : %s' % password
        print ' domain name       : %s' % domain_name
        print ' email             : %s' % email
        print ' debug             : %s' % debug   

        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the page
            page = GSitePage()
            page.relative_uri = page_relative_uri
            success = page.get(session, site_url)
            if not success:
                error = page.error
            else:
                print 'WebPage: '  + jsonpickle.encode(page)
                
        assert success, error

        
    def test_post(self,site_url,
                       page_relative_uri,
                       page_title,
                       page_content,
                       email       = DEFAULT_EMAIL,
                       login_name  = DEFAULT_LOGIN_NAME,
                       password    = DEFAULT_PASSWORD,
                       domain_name = DEFAULT_DOMAIN_NAME,
                       debug       = False):
        '''
        Synopsis:
            Creates a new Google Site Page on a site
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' site url          : %s' % site_url
        print ' page_relative_uri : %s' % page_relative_uri
        print ' page title        : %s' % page_title
        print ' page content      : %s' % page_content
        print ' login name        : %s' % login_name
        print ' password          : %s' % password
        print ' domain name       : %s' % domain_name
        print ' email             : %s' % email
        print ' debug             : %s' % debug   

        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the page
            page = GSitePage()
            page.relative_uri = page_relative_uri
            page.title        = page_title
            page.layout       = 'one-column'
            page.content      = page_content    
            success = page.post(session, site_url)
            if not success:
                error = page.error
            else:
                #adding the correct content
                success = page.put(session,site_url,page_content)
                if not success:
                    error = page.error
                
        assert success, error

    def test_put(self,site_url,
                               page_relative_uri,
                               page_title,
                               page_content,
                               email       = DEFAULT_EMAIL,
                               login_name  = DEFAULT_LOGIN_NAME,
                               password    = DEFAULT_PASSWORD,
                               domain_name = DEFAULT_DOMAIN_NAME,
                               debug       = False):
        '''
        Synopsis:
            Changes the content of a page already created.
            First it does a get, and then updates the content
            of the page.
        Expected Results:
        '''    
        print self.testGSitePagePost.__doc__
        print 'Arguments:'
        print ' site url          : %s' % site_url
        print ' page_relative_uri : %s' % page_relative_uri
        print ' page title        : %s' % page_title
        print ' page content      : %s' % page_content
        print ' login name        : %s' % login_name
        print ' password          : %s' % password
        print ' domain name       : %s' % domain_name
        print ' email             : %s' % email
        print ' debug             : %s' % debug   

        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the page
            page = GSitePage()
            page.relative_uri = page_relative_uri
            page.title        = page_title
            page.layout       = 'one-column'
            page.content      = page_content    
            success = page.post(session, site_url)
            if not success:
                error = page.error
                
        assert success, error

    def test_delete(self,site_url,
                               page_relative_uri,
                               delete_children = True,
                               email       = DEFAULT_EMAIL,
                               login_name  = DEFAULT_LOGIN_NAME,
                               password    = DEFAULT_PASSWORD,
                               domain_name = DEFAULT_DOMAIN_NAME,
                               debug       = False):
        '''
        Synopsis:
            Deletes a page.
        Expected Results:
        '''    
        print self.test_delete.__doc__
        print 'Arguments:'
        print ' site url          : %s' % site_url
        print ' page_relative_uri : %s' % page_relative_uri
        print ' delete_children   : %s' % str(delete_children)
        print ' login name        : %s' % login_name
        print ' password          : %s' % password
        print ' domain name       : %s' % domain_name
        print ' email             : %s' % email
        print ' debug             : %s' % debug   

        session = GHSession(debug=debug)
        session.email       = DEFAULT_LOGIN_NAME
        session.password    = DEFAULT_DOMAIN_NAME
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:
            #creating the page
            page = GSitePage()
            page.relative_uri = page_relative_uri
            success = page.delete(session, site_url)
            if not success:
                error = page.error
                
        assert success, error

class TGOneCloudProfessional():

    def test_post(self,
                         site_url    = DEFAULT_SITE_URL,
                         email       = DEFAULT_EMAIL,
                         password    = DEFAULT_PASSWORD,
                         debug       = False):
        '''
        Synopsis:
            Creates a oneCloudProfessional.
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' site url          : %s' % site_url
        print ' password          : %s' % password
        print ' email             : %s' % email
        print ' debug             : %s' % debug  
        
        my_site = GOneCloudProfessional(email,password,root=site_url,debug = True,over_write=True)
        my_site.owner_first_name = 'Filipe'
        my_site.owner_last_name  = 'Pinto'
        my_site.tags             = ['tag_1','tag_2','tag_3','tag_4','tag_5','tag_6']
        success = my_site.post()
        if not success:
            error = my_site.error

        assert success, error
        
class TGDocService():
    '''
    Synopsis:
        Represents the GDocService
    '''
    def test_put(self, 
                 email=DEFAULT_EMAIL,
                 password=DEFAULT_PASSWORD,
                 debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            srv = GDocService()
            success = srv.put(session,webaddress='docs_test')
            if not success:
                error = srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(srv)
        
        assert success, error   

    
    def test_get(self,email=DEFAULT_EMAIL,password=DEFAULT_PASSWORD,debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            doc_srv = GDocService()
            success = doc_srv.get(session)
            if not success:
                error = 'There was an error: ' + doc_srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(doc_srv)
        
        assert success, error    
        
class TGDocument():
    
    def test_put(self):
        '''
        Synopsis:
            Creates a GDoc.
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' password          : %s' % DEFAULT_PASSWORD
        print ' email             : %s' % DEFAULT_EMAIL
        #print ' debug             : %s' % debug 
        
        session = GHSession()
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        session.service     = 'writely'
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:         
            doc = GDocument()
            doc.title = 'test_'+''.join(random.choice(string.letters) for i in xrange(15))
            doc.post(session)
            if not success:
                error = doc.error

        assert success, error   
        
    def test_post(self):
        '''
        Synopsis:
            Creates a GDoc.
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' password          : %s' % DEFAULT_PASSWORD
        print ' email             : %s' % DEFAULT_EMAIL
        #print ' debug             : %s' % debug 
        
        session = GHSession()
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        session.service     = 'writely'
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:         
            doc = GDocument()
            doc.title = 'test_'+''.join(random.choice(string.letters) for i in xrange(15))
            doc.post(session)
            if not success:
                error = doc.error

        assert success, error        


class TGDomainService():
    '''
    Synopsis:
        Test the GDomainService
    '''
    def test_put(self, 
                 email=DEFAULT_EMAIL,
                 password=DEFAULT_PASSWORD,
                 debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_put.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            srv = GDomainService()
            success = srv.put(session, support_contact_text='This is a test')
            if not success:
                error = srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(srv)
        
        assert success, error   


    def test_get(self,email=DEFAULT_EMAIL,password=DEFAULT_PASSWORD,debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            srv = GDomainService()
            success = srv.get(session)
            if not success:
                error = 'There was an error: ' + srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(srv)
        
        assert success, error    


class TGCalendarService():
    '''
    Synopsis:
        Test the GCalendarService
    '''
    def test_put(self, 
                 email=DEFAULT_EMAIL,
                 password=DEFAULT_PASSWORD,
                 debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_put.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            srv = GCalendarService()
            success = srv.put(session,domain_sharing='FREEBUSY',public_sharing='FREEBUSY')
            if not success:
                error = srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(srv)
        
        assert success, error   

    
    def test_get(self,email=DEFAULT_EMAIL,password=DEFAULT_PASSWORD,debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            srv = GCalendarService()
            success = srv.get(session)
            if not success:
                error = 'There was an error: ' + srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(srv)
        
        assert success, error    
        
class TGCalendar():
    
    def test_put(self):
        '''
        Synopsis:
            Tests the GCalendar
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' password          : %s' % DEFAULT_PASSWORD
        print ' email             : %s' % DEFAULT_EMAIL
        #print ' debug             : %s' % debug 
        
        session = GHSession()
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        session.service     = 'cal'
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:         
            doc = GDocument()
            doc.title = 'test_'+''.join(random.choice(string.letters) for i in xrange(15))
            doc.post(session)
            if not success:
                error = doc.error

        assert success, error   
        
    def test_post(self):
        '''
        Synopsis:
            Creates a GDoc.
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' password          : %s' % DEFAULT_PASSWORD
        print ' email             : %s' % DEFAULT_EMAIL
        #print ' debug             : %s' % debug 
        
        session = GHSession()
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        session.service     = 'writely'
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:         
            doc = GDocument()
            doc.title = 'test_'+''.join(random.choice(string.letters) for i in xrange(15))
            doc.post(session)
            if not success:
                error = doc.error

        assert success, error        

class TGEmailService():
    '''
    Synopsis:
        Test the GEmailService
    '''
    def test_put(self, 
                 email=DEFAULT_EMAIL,
                 password=DEFAULT_PASSWORD,
                 debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            email_srv = GEmailService()
            success = email_srv.put(session,webaddress='docs_test')
            if not success:
                error = email.error
            else:
                print 'Results:\n-' + jsonpickle.encode(email_srv)
        
        assert success, error   

    
    def test_get(self,email=DEFAULT_EMAIL,password=DEFAULT_PASSWORD,debug=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        print self.test_get.__doc__
        print 'Arguments:\n-email: %s\n-password: %s\n-debug: %s' % \
                  (email,password,str(debug)) 
        session = GHSession(debug=True)
        session.password    = password
        session.email       = email       
        success = session.get()
        if not success:
            error = 'Error : ' + session.error
        else:
            doc_srv = GDocService()
            success = doc_srv.get(session)
            if not success:
                error = 'There was an error: ' + doc_srv.error
            else:
                print 'Results:\n-' + jsonpickle.encode(doc_srv)
        
        assert success, error    
        
class TGEmail():
    
    def test_put(self):
        '''
        Synopsis:
            Tests the GCalendar
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' password          : %s' % DEFAULT_PASSWORD
        print ' email             : %s' % DEFAULT_EMAIL
        #print ' debug             : %s' % debug 
        
        session = GHSession()
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        session.service     = 'writely'
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:         
            doc = GDocument()
            doc.title = 'test_'+''.join(random.choice(string.letters) for i in xrange(15))
            doc.post(session)
            if not success:
                error = doc.error

        assert success, error   
        
    def test_post(self):
        '''
        Synopsis:
            Creates a GDoc.
        Expected Results:
        '''    
        print self.test_post.__doc__
        print 'Arguments:'
        print ' password          : %s' % DEFAULT_PASSWORD
        print ' email             : %s' % DEFAULT_EMAIL
        #print ' debug             : %s' % debug 
        
        session = GHSession()
        session.email       = DEFAULT_EMAIL
        session.password    = DEFAULT_PASSWORD
        session.service     = 'writely'
        #getting a session
        success = session.get()
        if not success:
            error = session.error
        else:         
            doc = GDocument()
            doc.title = 'test_'+''.join(random.choice(string.letters) for i in xrange(15))
            doc.post(session)
            if not success:
                error = doc.error

        assert success, error        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    #unittest.main()
    
    '''
    GSession
    '''
    #t_ghsession = TGHSession()
    #t_ghsession.test_get(debug= True)

    '''
    GHAccount
    '''
    #t_gaccount = TGHAccount()
    #t_gaccount.test_post('Maria-djalman.com.br')
    #t_gaccount.test_get()
    #t_gaccount.test_put()
    
    '''
    GDomainService
    '''

    t_gdomainsrv = TGDomainService()
    #t_gdomainsrv.test_get()
    t_gdomainsrv.test_put()


    '''
    GSiteService
    '''
    #t_gsite_service = TGSiteService()
    #t_gsite_service.test_post()
    #t_gsite_service.test_get()
    #t_gsite_service.test_put()

    '''
    GSiteHelper
    '''
    #gsite_helper   = TGSiteHelper()
    #my_helper.test_RemoveSpace()
    
    '''
    GSite
    '''
    #t_gsite = TGSite()
    #t_gsite.test_delete('projectx')
    #t_gsite.test_post('projectx', site_name='Project X', debug= True)
    #t_gsite.test_get('projectx',debug=False)
    #t_gsite.test_put_info('projectx',debug=True)
    #t_gsite.test_put_sharing('projectx',debug=True)
    #t_gsite.test_put_attchment('projectx',debug=True)
    #t_gsite.test_put_layout('projectx',debug=True)

    '''
    GSitePage
    '''
    #t_gsite_page = TGSitePage()
    #t_gsite_page.test_post('projectx', '/Synopsis','Synopsis','<h1>Synopsis</h1><p>This page describes the objectives of the project</p>',debug=True)
    #t_gsite_page.test_get('projectx', '/Synopsis',debug=True)    
    #t_gsite_page.test_delete('projectx', '/synopsis', delete_children=True)
    
    
    '''
    GOneCloudProfessional
    '''
    
    #t_onecloud_professional = TGOneCloudProfessional()
    #t_onecloud_professional.test_post()
    
    '''
    GDocService
    '''

    #t_gdocsrv = TGDocService()
    #t_gdocsrv.test_get()
    #t_gdocsrv.test_put()

    
    '''
    GDocument
    '''
    
    #unittest.main()
    #t_gdocument = TGDocument()
    #t_gdocument.test_post()
    
    
    '''
    GCalendarService
    '''

    #t_gcalsrv = TGCalendarService()
    #t_gcalsrv.test_get()
    #t_gcalsrv.test_put()

    
    '''
    GCalendar
    '''
    
    #unittest.main()
    #t_gdocument = TGDocument()
    #t_gdocument.test_post()
    
    
    '''
    GEmailService
    '''

    #t_gcalsrv = TGCalendarService()
    #t_gdocsrv.test_get()
    #t_gdocsrv.test_put()

    
    '''
    GEmail
    '''
    
    #unittest.main()
    #t_gdocument = TGDocument()
    #t_gdocument.test_post()
    