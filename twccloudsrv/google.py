'''
Created on Jun 25, 2009

@author: fpinto

Synopsis:
    This module represents a Google Hosted Account and Google Account API
    
    
Todo:
    09-04-09 - fpinto - during tests I noticed that GHAccount.post() was
                        hanging. The account was created but this is not
                        a reasonable situation.  Next time I touch this
                        method will retrofit Beautiful
    
    

Date      Author        Description
--------  ------------- -------------------------------------------------------
09-04-09  fpinto        Retrofit BeautifulSoup to parse forms and hidden fields
                        on GHSession.get().
                        Performed several improvements so users can populate 
                        email or "domain & login name".
                        Added code to check input parameters on GHSession.get()
09-05-09  fpinto        Created GSiteHelper class to contain any methods that 
                        are shared across GSite classes.
                        Created method GSiteHelper._set_uri_token
                        Created method GSiteHelper._set_json
09-09-09  fpinto        Created a new GSiteHelper method to remove only spaces
                        that occur outside the brakets
09-13-09  fpinto        Added Gsite.get and corresponding sub gets: info,
                        sharing, layout, attachments
                        Added Gsite.put and corresponding sub puts: info,
                        sharing, layout, attachments
09-17-09  fpinto        Added Site._put_info()
09-21-09  fpinto        Added GSite.put_assessment_add, GSite.put_assessment_remove 
09-25-09  fpinto        Added client to GHSession
09-26-09  fpinto        Started coding GDocsService
09-28-09  fpinto        Coded GCalendarService.get and GCalendarService.put()
                        Coded GHServiceHelper to perform static methods common to
                        all services. 
09-29-09  fpinto        Coded GDomainService.get and GDomainService.put()
                        Refactoring of GSite.get
'''

import sys
import re
import uuid
import urllib
import string
import urlparse
import urllib2
import cookielib
import jsonpickle
import random
import gdata.docs.service
from BeautifulSoup import BeautifulSoup,SoupStrainer
from twccloudsrv.base import (Service         ,
                              ProviderAccount ,
                              ProviderSession ,
                              VideoService    , Video,
                              EmailService    , Email,
                              CalendarService , Calendar, 
                              PhotoService    , Photo,
                              DocumentService , Document,
                              SiteService     , Site, SiteComponent, SitePage, OneCloudTemplate,
                              HostedDomainService)

from twccloudsrv.util import WebTools

#Google Variables  - this are candidates to bigtable integration
GOOGLE_PROVIDER_NAME                       ="Google"
GOOGLE_HOSTED_ACCOUNT_SET_DOMAIN_URL       = 'http://www.google.com/a/cpanel/domain/new'
GOOGLE_FORM_NAME_PAGE_1                    ='domainEntry'
SERVICE_EMAIL_CONFIRMATION                 = 'zuper@3wcloud.com'
SERVICE_EMAIL_CONFIRMATION_SMTP_IN         =''
SERVICE_EMAIL_CONFIRMATION_PASSWORD        = ''
GOOGLE_DOMAIN_VERIFICATION_ATTEMP_PERIOD   = 48   #number of hours during which domain verfication will be attempted
GOOGLE_DOMAIN_VERIFICATION_ATTEMP_INTERVAL = 10 #number of minutes between attempts 

GSITE_SHARING_EMAIL  = {'subject':'Come help me with my oneCloud',
                        'body'   :'I\'m inviting you to to be part of my own oneCloud. Thank you',
                        'doCc'   :True}


class GHSession(ProviderSession):
    '''
    Represents a session in Google Hosted Accounts.
    The session has a cookiejar and http opener that
    responsible to maintain the state among calls
    to the different APIs
    '''
    def __init__(self, debug=False):
        '''
        constructor
        '''
        super(GHSession,self).__init__()
        self.domain_name  = ''
        self.connection   = None
        self.cookiejar    = cookielib.CookieJar()
        self.urlopener    = urllib2.OpenerDirector()
        self.client       = None                      #google API
        self.service      = None

        debug_level = 0
        if debug:
            debug_level = 1
            self.debug = debug
        
        #building the urllib2 session opener
        try:
            self.urlopener.add_handler(urllib2.HTTPHandler(debuglevel=debug_level))
            self.urlopener.add_handler(urllib2.HTTPSHandler(debuglevel=debug_level))
            self.urlopener.add_handler(urllib2.HTTPDefaultErrorHandler())
            self.urlopener.add_handler(urllib2.HTTPErrorProcessor())
            self.urlopener.add_handler(urllib2.HTTPRedirectHandler())
            self.urlopener.add_handler(urllib2.HTTPCookieProcessor(self.cookiejar))
        except Exception, ex:
            self.error = 'unexpected error while defining session uri opener' + ex.message
            raise Exception(ex.message)
     
    def get(self):
        '''
        Synopsis:
            Returns an authenticated session to Google
            Hosted Services.
        Arguments:
            Service  : 'None','writely'
        Exceptions:
        Returns:
        '''
        ##########################################################################
        #
        #checking mandatory attributes
        #
        ##########################################################################
        if self.password == '':
            self.error = 'Password name cannot be empty!'
            return False
        
        if self.email =='':        
            if self.login_name=='' or self.domain_name=='':
                self.error = 'Email, or the combination "Login Name" and "Domain" cannot be empty!'
                return False
            else:
                self.email = string.join(self.login_name,self.domain_name,'@')
        else:
            email_parsed = string.split(self.email,'@')
            if len(email_parsed)<>2:
                self.error = 'email incorrectly configured'
                return False
            email_domain = email_parsed[1]
            email_name   = email_parsed[0]
            if self.domain_name<>'':
                if self.domain_name<>email_domain:
                    self.error = 'Email and domain don\'t match'
                    return False
            if self.login_name<>'':
                if self.login_name <> email_name:
                    self.error = 'Login name and domain don\'t match'
                    return False
            if self.domain_name == '':
                self.domain_name = email_domain
                
        # determining the type of authentication based on the service
        if   self.service == None:
            if not self._get_low_level(): return False
        elif self.service <> None:
            if not self._get_client(): return False
            
        return True
     
    def _get_client(self): 
        '''
        Synopsis:
            Returns a regular Google client object.         
        Arguments:
        Exceptions:
        Returns:
        '''
        self.client = gdata.docs.service.DocsService()
        self.client.email       = self.email
        self.client.password    = self.password
        self.client.accountType = 'HOSTED'
        self.client.service     = self.service
        try:
            self.client.ClientLogin(self.client.email,self.client.password)
        except Exception, ex:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to get client login. Unexpected error message: %s'  % str(ex.message)
            return False
        return True
            
    def _get_low_level(self):
        '''
        Synopsis:
            Returns a valid urlopener necessary for the 
            other classes to work.        
        Arguments:
        Exceptions:
        Returns:
        '''
        ###################################################################
        #
        #  Getting to login form
        #
        ###################################################################
        #setting the uri
        uri = 'https://www.google.com/a/' + self.domain_name #+ '/ServiceLogin'        
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = self.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + str(ex.reason)
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()                     
        #asserting we're on the right place
        pattern = '@'+self.domain_name
        if len(re.findall(pattern, content))== 0 :
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s using pattern %s in content %s' % (uri,pattern,content)
            return False

        ###################################################################'
        #  Posting credentials'
        ###################################################################'        
        form = 'gaia_loginform'
        pattern = SoupStrainer('form', {'id':form})
        node = BeautifulSoup(content, parseOnlyThese=pattern)
        if node==None:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find form % in content %s' % (form,content)
            return False
        else:
            uri = node.form['action']
            inputs  = node.findAll('input',{'type':'hidden'})
            data=dict()
            for input in inputs:  data[input['name']]=input['value']
        #setting the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'  
        data['Email'           ] = string.split(self.email,'@')[0]
        data['Passwd'          ] = self.password
        data['PersistentCookie'] = 'yes'                #check box to stay signed in
        data['signIn'          ] = 'Sign in'        
        #defining the request
        request = urllib2.Request(uri, data=urllib.urlencode(data),headers=headers)
        try:
            response = self.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
        else:
            content = response.read()
        #Asserting login errors
        pattern = 'id="CPanelMenuDashboard"'
        results = re.findall(pattern, content)
        if len(results)==0:
            #checking for login errors
            pattern = '<div.*?class="errormsg".*?>(.*?)</div>'
            results = re.findall(pattern, content, re.S)
            if len(results)>0:
                self.error = str(results)
            else:
                self.error = self.__class__.__name__+'.'+ \
                             sys._getframe().f_code.co_name + \
                             ' @line:' + str(sys._getframe().f_lineno) + \
                             '\nUnable assert uri %s using pattern %s in content %s' % (uri,pattern,content)                
            return False
        else:
            return True


class GDomainService(HostedDomainService):
    '''
    Represents the domains being hosted on the Google
    hosted account
    '''
    def __init__(self):
        '''
        constructor
        '''
        #general settings
        self.organization_name      = None
        self.support_contact_text   = None
        self.language               = None
        self._language_code         = None
        self.loc                    = None
        self.time_zone              = None
        self._time_zone_code        = None
        self.is_add_new_services    = None
        self.is_enable_pre_releases = None
        self.is_ssl                 = None
        self.control_panel          = None
        self._is_ctrl_next_gen      = None
        #account information
        #domain names
        #appereance
        #hidden attributes
        self._at                    = None
        self._key                   = None
        
    #content    
    def get_is_ctrl_next_gen(self):
        if self.control_panel == 'Next generation':
            return True
        else:
            return False
    
    is_ctrl_next_gen = property(get_is_ctrl_next_gen,'This determines if control is next gen')
    
    def get(self,session):
        '''
        Synopsis:
            Returns the domain configurations, and the
            hidden attributes of the webpage. The timezone
            is retrieved by performing another query.
        Arguments:
            Authenticated session
        Exceptions:
        Returns
        '''
        ###################################################################
        #  Getting to CPanel Service Site Settings
        ###################################################################
        #setting the uri
        uri='https://www.google.com/a/cpanel/' + session.domain_name + '/DomainSettings'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        #Parsing content with BeautifulSoup
        ###################################################################
        try:
            html = BeautifulSoup(content)
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nException message: ' + ex.message
            return False
        #Processing inputs
        inputs= html.findAll('input',{'type':'text'})
        for input in inputs:
            if input.has_key('name'):
                if   input['name']=='organizationName'  : 
                    self.organization_name       = input['value']
        #Processing checkboxes
        inputs= html.findAll('input',{'type':'checkbox'})
        for input in inputs:
                if   input['name']=='appFeatures'       :
                    self.is_enable_pre_releases  = jsonpickle.decode(input['value'])
                elif input['name']=='defaultNewServices':
                    self.is_add_new_services     = jsonpickle.decode(input['value'])
                elif input['name']=='forceSSL'          :
                    self.is_ssl                  = jsonpickle.decode(input['value'])
        #Processing radio buttons
        inputs= html.findAll('input',{'type':'radio'})
        for input in inputs:
            if input['name'] == 'controlPanelUI' and input.has_key('checked'):
                #if input['id']=='uinextgen' and input['value']=='true':
                if input['id']=='uinextgen':
                    self.control_panel = 'Next generation'
                else:
                    self.control_panel = 'Standard'
        #Processing textareas
        textareas = html.findAll('textarea')
        for textarea in textareas:
            if  textarea['name']=='supportContactText'  : 
                self.support_contact_text       = str(textarea.string)
        #Processing pulldowns
        pulldowns = html.findAll('select')
        for pulldown in pulldowns:
            if   pulldown['name']=='defaultLocale':
                options = pulldown.findAll('option')
                for option in options: 
                 if option.has_key('selected'):
                     self.language = str(option.string)
                     self._language_code =option['value']
                     break         
            if   pulldown['name']=='loc':
                options = pulldown.findAll('option')
                for option in options: 
                 if option.has_key('selected'):
                     self.language = str(option.string)
                     self.loc =option['value']
                     break  
        #retrieving the hidden inputs
        inputs= html.findAll('input',{'type':'hidden'})
        for input in inputs:
            if input['name']=='key': self._key = input['value']
            if input['name']=='at' : self._at  = input['value']
        ###############################################################
        # Retrieving the timezone
        ###############################################################                       
        uri='https://www.google.com/a/cpanel/' + session.domain_name + '/Timezone?xh=1'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##############################################################
        # Retrieving the timezone
        #                    
        #<option selected value="140">(GMT-05:00) Eastern Time</option>
        #
        ##############################################################
        pattern = '<option selected value="(.*?)">(.*?)</option>'
        results = re.findall(pattern, content, re.I)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find pattern "%s" in content "%s"' % (pattern,content)
            return False
        self._time_zone_code = results[0][0]
        self.time_zone       = results[0][1]
        
        return True

    def put(self,session,organization_name      = None,
                         support_contact_text   = None,
                         language_code          = None,
                         time_zone_code         = None,
                         is_add_new_services    = None,
                         is_enable_pre_releases = None,
                         is_ssl                 = None,
                         control_panel          = None):
        '''
        Synopsis:
            Changes the domain configurations
        Arguments:
            Authenticated session
            organization_name      = None
            support_contact_text   = None
            language               = None
            time_zone              = None
            is_add_new_services    = None
            is_enable_pre_releases = None
            is_ssl                 = None
            control_panel          = None            
        Exceptions:
        Returns        
        '''
        #retrieving current info
        if not self.get(session): return False
        #determining delta
        dirty = False
        if organization_name      is not None:
            self.organization_name      = organization_name
            dirty                       = True
        if support_contact_text   is not None:
            self.support_contact_text   = support_contact_text
            dirty                       = True
        if language_code          is not None:
            self.language               = language
            dirty                       = True
        if time_zone_code         is not None:
            self.time_zone              = time_zone
            dirty                       = True
        if is_add_new_services    is not None:
            self.is_add_new_services    = is_add_new_services
            dirty                       = True
        if is_enable_pre_releases is not None:
            self.is_enable_pre_releases = is_enable_pre_releases
            dirty                       = True 
        if control_panel          is not None:
            self.control_panel          = control_panel
            dirty                       = True
        #checking if there are any changes
        if not dirty:
            self.error = 'No attributes were to be changed'
            return False
        #########################################################################
        #Posting changes
        #########################################################################
        uri =  'https://google.com/a/cpanel/' + session.domain_name + '/DomainSettings' 
        #########################################################################
        #Content-Type: multipart/form-data; boundary=---------------------------17673466415141
        #Content-Length: 1293
        #
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="at"
        #
        #s0rmIfSL-nypJG0rxtWb8dFj00M
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="key"
        #
        #filipe-pinto.com
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="organizationName"
        #
        #Filipe Pinto oneCloud
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="supportContactText"
        #
        #In case you need assistance please contact administrator.
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="defaultLocale"
        #
        #en
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="loc"
        #
        #
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="timezone"
        #
        #140
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="defaultNewServices"
        #
        #true
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="appFeatures"
        #
        #true
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="forceSSL"
        #
        #true
        #-----------------------------17673466415141
        #Content-Disposition: form-data; name="controlPanelUI"
        #
        #true
        #-----------------------------17673466415141--\
        ##########################################################################
        token = ''.join(random.choice(string.digits) for i in xrange(15))
        NL                = '\r\n'
        http_content_type = 'multipart/form-data; boundary=' + ''.join('-' for i in xrange(27))+ token 
        content_length    = '1293'    #hardcoded so i don't have the code the real number
        separator         = NL + ''.join('-' for i in xrange(29))+ token 
        #defining the body
        body = str('Content-Type: ' + http_content_type  + NL + \
               'Content-Length: ' + content_length + NL + separator + NL+\
               'Content-Disposition: form-data; name="at"' + NL + NL +\
               self._at + separator  + NL +\
               'Content-Disposition: form-data; name="key"' + NL + NL + \
               self._key + separator  + NL +\
               'Content-Disposition: form-data; name="organizationName"' + NL +NL + \
               self.organization_name + separator + NL +\
               'Content-Disposition: form-data; name="supportContactText"' + NL + NL + \
               self.support_contact_text + separator + NL +\
               'Content-Disposition: form-data; name="defaultLocale"' + NL +NL + \
               self._language_code + separator + NL +\
               'Content-Disposition: form-data; name="loc"' + NL +NL + \
               self.loc + separator + NL +\
               'Content-Disposition: form-data; name="timezone"' + NL +NL + \
               self._time_zone_code + separator + NL +\
               'Content-Disposition: form-data; name="defaultNewServices"' + NL +NL + \
               string.lower(str(self.is_add_new_services)) + separator + NL +\
               'Content-Disposition: form-data; name="appFeatures"' + NL +NL + \
               string.lower(str(self.is_enable_pre_releases)) + separator + NL +\
               'Content-Disposition: form-data; name="forceSSL"' + NL +NL + \
               string.lower(str(self.is_ssl)) + separator + NL +\
               'Content-Disposition: form-data; name="controlPanelUI"' + NL +NL + \
               string.lower(str(self.is_ctrl_next_gen)) + separator + '--')
 
        print body               
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = http_content_type
        #defining the request
        request = urllib2.Request(uri, body, headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        #Checking post success
        #print content
        return True

class GHServicesHelper():
    '''
    Synopsis:
        Represents a class that has common functions across all the
        services.
    '''
    @staticmethod
    def post_webaddress(session,service,webaddress):
        '''
        Synopsis:
        Arguments:
            service : name of service - cl,mail,jotspot,writely
        Exceptions:
        Returns:
        '''
        #checking for parameter accuracy
        if service not in ['cl','mail','jotspot','writely']:
            return False
        #setting the uri
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/CustomUrl?s=' + service        
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + str(ex.reason)
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()                     
        #asserting we're on the right place
        pattern = 'Change URL for Docs'
        if len(re.findall(pattern, content))== 0 :
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s using pattern "%s" in content \n%s' % (uri,pattern,content)
            return False        
        ###################################################################
        #Posting value
        ###################################################################   
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/CustomUrl'
        form = 'c'
        pattern = SoupStrainer('form', {'name':form})
        node = BeautifulSoup(content, parseOnlyThese=pattern)
        if node==None:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find form % in content %s' % (form,content)
            return False
        else:
            inputs  = node.findAll('input',{'type':'hidden'})
            data=dict()
            for input in inputs:  data[input['name']]=input['value']
        #setting the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'  
        data['perServiceInput.urlType-writely'         ] = 'custom'
        data['perServiceInput.customSubdomain-writely' ] = webaddress
        #there's already a hidden attribute with this name
        #data['actionInput.CONTINUE'                    ] = 'Continue &raquo;'        
        #defining the request
        request = urllib2.Request(uri, data=urllib.urlencode(data)+ '&actionInput.CONTINUE=Continue+%C2%BB',headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
        else:
            content = response.read() 
        ########################################################
        # Check for any errors
        ########################################################
        pattern = '<span.*?class="errormsg".*?>(.*?)</span>'
        results = re.findall(pattern, content, re.S)
        if len(results)<>0:
            for result in results: self.error = self.error + result + '\n'
            return False
        else:
            return True

        

class GHAccount(ProviderAccount):
    '''
    Synopsis:
        This class represents a Google Hosted Account.
        
        
        GHA-------------------------------Account Owner/Administrator
              |
              -Domain Service
              |
              -Calendar Service
              |
              -Email Service 
              |
              -Docs Service
              |
              -Sites Service
              |
              -Chat Service
              |
              -Mobile Service
              |
              -GoogleApp Services (not yet implement)
              |
              -Contacts Services (not yet implemented)
              |
              Other - (undefined at the this time)

    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(GHAccount,self).__init__()
        self.domain_name=''
        
        self.first_name         = ''
        self.last_name          = ''
        self.email              = ''
        self.domain_name        = ''
        self.phone              = ''
        self.country            = ''
        self.job_title          =''
        self.status             = '' 
        self.verification_cname = ''
        #self.cookiejar          = cookielib.CookieJar()

    def get(self,session,deep=None,type=None):
        '''
        Synopsis:
            Returns the details of the account
        Arguments:
            session: a GHASession
            deep   : whether to retrieve additional information
            type   : the type of service to get details
                     example 'website','domain','documents'
        Exception:
        Returns:
            Success
        Scraping notes for developers:
            In order to get the details of the account, need to get
            current in the Dashboard home page, using the session
            coookie. That means that the GHSession.domain_name needs to
            populated.
        '''
        
        if session.domain_name=='':
            self.error = 'Please define the domain_name in the GHSession object'
            return False


        ###################################################################
        #
        #  Getting to CPanel Dashboard
        #
        ###################################################################
   
        #setting the uri
        uri = 'https://www.google.com/a/cpanel/'+session.domain_name+'/Dashboard'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()

        ###################################################################
        #
        #  Asserting correct page
        #
        ###################################################################
             
        #asserting we're on the right place
        pattern = '@'+self.domain_name
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        
        ###################################################################
        #
        #  Getting the service details'
        #
        #  Services are listed in two different places because to 3WC'
        #  the domain hosting is a service, of a Google type of account'
        #  General services, what Google calls services are listed in the'
        #
        #
        ###################################################################           

        #retrieve services from <div  id="dash2">
        pattern = '<ul id="services">(.*?)</div>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        #retrieving the service info
        pattern='<li (class="clrflt"|class="")>.*?class="(.*?)".*?<span>.*?</span>.*?<span>.*?(Active|Not Active).*?</span>'
        results = re.findall(pattern,results[0], re.S)
        if len(results)==0:
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        else:                          #creating the GHAccount service list
            for result in results:
                active=False
                if   result[1]=='docs'     and result[2]=='Active':
                    service = GDocsService()
                    active = True
                elif result[1]=='email'    and result[2]=='Active':
                    service = GmailService()
                    active = True
                elif result[1]=='calendar' and result[2]=='Active':
                    service = GCalendarService()
                    active = True
                elif result[1]=='sites'    and result[2]=='Active':
                    service = GSiteService()
                    active = True
                elif result[1]=='mobile'   and result[2]=='Active':
                    service = Service()
                    active = True
                elif result[1]=='chat'     and result[2]=='Active':
                    service = Service()
                    active = True

                if active: self.services.append(service)

        ###################################################################
        #
        #  Getting additional details on the services
        #
        #  Not yet implemented
        #
        ##################################################################

        if deep:
            for service in self.services:
                if not service.get():
                    self.error = service.error
                    return False        


        ###################################################################
        #
        #  Getting the HostedDomain Service details
        #
        #  needs to determine who is the owner of the account
        #  and retrieve the user details. Google joins this services
        #  with the account, and we don't
        #
        ###################################################################

        #setting the uri
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/User?userName=fpinto'        

        return True
        
    def post (self):
        '''
        Synopsis:
            Creates a new Google Hosted Account
        Arguments:
        Exception:
        Returns:
            Success: True of False.
            If False look for object.error attribute
        Todo:
            implement a OpenerDirector constructor
        '''
        ###################################################################
        #determining whether mandatory attributes were set
        ###################################################################
        if   self.domain_name   == '' : 
                self.error = 'domain name can\'t be empty'
                return False       
        elif self.first_name    == '':
                self.error = 'first name can\'t be empty'
                return False       
        elif self.last_name     == '':
                self.error = 'last name can\'t be empty'
                return False                   
        elif self.email         == '':
                self.error = 'email can\'t be empty'
                return False       
        elif self.phone         == '':
                self.error = 'phone can\'t be empty'
                return False       
        elif self.country       == '':
                self.error = 'country can\'t be empty'
                return False
        elif self.job_title     == '':
                self.error = 'job title can\'t be empty'
                return False
        elif self.password      == '':
                self.error = 'password can\'t be empty'
                return False                    
        
        ###################################################################
        #creating the uri opener. Without an account
        #there's actually no concept of a ProviderSession
        ###################################################################
        try:     
            debug_level = 0
            if self.debug: debug_level = 1
            cookiejar=cookielib.CookieJar()
            opener = urllib2.build_opener(
                            urllib2.HTTPHandler(debuglevel=debug_level),
                            urllib2.HTTPSHandler(debuglevel=debug_level),
                            urllib2.HTTPCookieProcessor(cookiejar))
            urllib2.install_opener(opener)
        except Exception,ex:
            self.error = 'Unknown error while building opener - ' + ex.message
            return False
        ###################################################################
        #
        #  Step 1 - Getting to new account domain page
        #
        ###################################################################
        
        #defining initial uri (all others will be read from HTML
        uri = GOOGLE_HOSTED_ACCOUNT_SET_DOMAIN_URL
        #creating a Firefox browser
        host = urlparse.urlparse(uri)[1]
        headers = WebTools.firefox_headers()    
        #headers['Connection']= 'keep-alive'
        #headers['Keep-Alive']= '300'
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submitting the request
        try:
            response = urllib2.urlopen(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #  Asserting correct page
        pattern='I want to use an existing domain name'
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find form pattern %s in %s' % (pattern,content)
            return False

        ###################################################################
        #
        #  Step 2 - Setting the domain
        #
        ###################################################################
        #retrieving form content and uri
        pattern = '<form action="(.*?)" method="POST" name="domainEntry"(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('domainEntry',pattern,content)
            return False
        else:
            uri     = results[0][0]
            if urlparse.urlparse(uri)[1]=='': uri = 'http://'+ host + uri
            content = results[0][1]
        #Retrieving hidden attributes
        pattern='input.*?type=["|\']hidden["|\'].*?name=["|\'](.*?)["|\'].*?(id=["|\'].*?["|\'])*value=["|\'](.*?)["|\']'
        hidden_inputs = re.findall(pattern,content, re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2] 
        #setting the body
        #data['newDomain'     ]= 'false'         #hidden field - retrieved above
        #data['page'          ]= 'start'         #hidden field - retrieved above
        data['submitButton'  ]= 'Get Started'    #retrieve from Firebug
        data['ownDomain'     ]= 'true'           #retrieve from Firebug
        data['existingDomain']= self.domain_name
        #setting the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded' 
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
        #submitting the request
        try:
            response = urllib2.urlopen(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #  Asserting correct page       
        pattern = '(step 2 of 3)'
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        
        ################################################################################
        #                                                                               
        # Step 3 - Sign up for account                                                  
        #
        ################################################################################'   
        #retrieving form content and uri
        pattern = '<form.*?action="(.*?)".*?method="POST".*?id="standardSignUp"(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('standardSignUp',pattern,content)
            return False
        else:
            uri     = results[0][0]
            if urlparse.urlparse(uri)[1]=='': uri = 'http://'+ host + uri
            content = results[0][1]
        #Retrieving hidden attributes
        pattern='input.*?type=["|\']hidden["|\'].*?name=["|\'](.*?)["|\'].*?(id=["|\'].*?["|\'])*value=["|\'](.*?)["|\']'
        hidden_inputs = re.findall(pattern,content, re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2]         
        #setting the body
        #data['action'          ] = 'signup'              #hidden attributes
        #data['numberOfUser'    ] = '50'                  #hidden attributes
        #data['domainName'      ] = self.domain_name      #hidden attributes
        data['country'         ] = self.country
        data['domainAdminCheck'] = 'true'
        data['email'           ] = self.email
        data['firstName'       ] = self.first_name
        data['jobTitle'        ] = self.job_title
        data['lastName'        ] = self.last_name
        data['newDomainSubmit' ] = 'Continue'
        data['orgEmailAccount' ] = 'false'
        data['orgEmailSolution'] = ''    
        data['orgName'         ] = self.first_name+self.last_name+'oneCloud'
        data['orgSize'         ] = '7'
        data['orgType'         ] = '12'
        data['phone'           ] = self.phone
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
        #submitting the request
        try:
            response = urllib2.urlopen(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()        
        #  Asserting correct page
        pattern = '(step 3 of 3)'
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False               
       
        ################################################################################'
        #                                                                               '
        # Step 4 - Sign up for account                                                  '
        #
        # Note: this step the post doesn't define a new URL and instead we post
        #       to the current URL
        #                                                                               '
        ################################################################################'
        #defining the uri
        uri = response.geturl()
        #retrieving form content
        pattern = '<form.*?method="POST".*?id="educationAdminSetup"(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('standardSignUp',pattern,content)
            return False
        else:
            content = results[0]
        #Retrieving hidden attributes
        pattern='input.*?type=["|\']hidden["|\'].*?name=["|\'](.*?)["|\'].*?(id=["|\'].*?["|\'])*value=["|\'](.*?)["|\']'
        hidden_inputs = re.findall(pattern,content, re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2]  
        #setting the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'        
        #setting the body
        #data['action'           ] = 'adminSetup'        #hidden attribute
        data['adminSetup'       ] = 'I accept. Continue with set up &raquo;'
        data['newPassword.alpha'] = self.password
        data['newPassword.beta' ] = self.password
        data['newUserName'      ] = self.first_name  
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
        #submitting the request
        try:
            response = urllib2.urlopen(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read() 
        #  Asserting correct page
        pattern = 'Welcome to Google Apps'
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        
        ################################################################################
        #                                                                               
        # Step 5 - Picking CNAME verification   
        #                                               
        # Note: this is a form where we decide to verify the domain with CNAME
        #       the form "POST" actually is a get that takes as an argument
        #       "verificationtypes=cnamever"                                                                        
        ################################################################################     
        #setting uri
        #uri = response.geturl()#
        uri = 'https://www.google.com/a/cpanel/'+self.domain_name+'/VerifyDomainOwnership?verificationtypes=cnameVer'
        #setting the headers
        headers.pop('Content-Type')
        #defining the request
        request = urllib2.Request(uri,headers=headers) 
        #submitting the request
        try:
            response = urllib2.urlopen(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #  Asserting CNAME
        pattern = '<p id="valKey">.*?<b>(.*?)</b>'
        results = re.findall(pattern, content, re.S)
        if len(results)== 0 :
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        else:
            self.verification_cname = results[0]
            return True

    def put(self,service):
        '''
        '''
        #self.service_list.append(service)
        return True


    def delete(self):
        '''
        '''
        return True


class YouTubeService(VideoService):
    '''
    Represents a YouTube Account
    '''
    def __init__(self):
        pass
    

    def get(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def post(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def put(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        pass

    def delete(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True

    
class YTVideo(Video):
    '''
    Represents a YouTube Video
    '''
    def __init__(self):
        pass
    
    
    def get(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def post(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def put(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        pass

    def delete(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True

class GmailService(EmailService):
    '''
    Represents the GMAIL service of a Google Hosted Account.
    '''
    
    def __init__(self):
        '''
        GmailService initializer
        '''
        pass

    def get(self):
        '''
        '''
        return True


    def post(self):
        '''
        '''
        return True
    
    def put(self):
        '''
        '''
        return True    

    def delete(self):
        '''
        '''
        return True  

class Gmail(Email):
    '''
    Represents an individual email.
    '''
    
    def __init__(self):
        '''
        GmailService initializer
        '''
        return True

    def get(self):
        '''
        '''
        return True


    def post(self):
        '''
        '''
        return True
    
    def put(self):
        '''
        '''
        return True    

    def delete(self):
        '''
        '''
        return True    

    
class GDocService(DocumentService):
    '''
    Represents the Google Documents Service
    '''
    def __init__(self):
        super(GDocService,self).__init__()
        self.is_full_share = None
        self.webaddress    = None
    
    def get(self,session):
        '''
        Synopsis:
            Retrieve the service settings:
            -Webaddress
            -sharing option
        Arguments:
        Exceptions:
        Returns:
        '''
        ###################################################################
        #  Getting Doc Setting page
        ###################################################################
        #setting the uri
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/DocsSettings'        
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + str(ex.reason)
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()                     
        #asserting we're on the right place
        pattern = 'Docs settings'
        if len(re.findall(pattern, content))== 0 :
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s using pattern %s in content %s' % (uri,pattern,content)
            return False
        ###################################################################
        #Parsing content with BeautifulSoup
        ###################################################################
        try:
            html = BeautifulSoup(content)
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nException message: ' + ex.message
            return False
        ########################################################################
        #Scraping the page
        ########################################################################
        self.webaddress = str(html.findAll('a',{'id':'docsLink'})[0].string)
        if html.findAll('input',{'id':'fullshare'})[0]['value']=='0':
            self.is_full_share = True
        else:
            self.is_full_share = False

        return True
 
    def put(self,session,webaddress=None):
        '''
        Synopsis:
            Updates the service settings which include:
            - Webaddress
            - Sharing options
        Arguments:
            session
        Exceptions:
        Returns:
        '''
        if webaddress is not None:
            if not GHServiceHelper.post_webaddress(session, 'writely', webaddress):
                return False            
        
    def delete(self):
        '''
        Synopsis:
            Disables the service
        Arguments:
        Exceptions:
        Returns:
        '''
        pass

class GDocument(Document):
    '''
    '''
    def __init__(self):
        '''
        '''
        super (GDocument,self).__init__()
        self._entry    = gdata.GDataEntry()
        self._title    = None
        self._category = gdata.atom.Category(scheme=gdata.docs.service.DATA_KIND_SCHEME, 
                                             term=gdata.docs.service.DOCUMENT_KIND_TERM)
        self._entry.category.append(self._category)
        self.handle    = None
        
    #content    
    def get_title(self):
        return self._content
    def set_title(self, value):
        self._title = value
        self._entry.title = gdata.atom.Title(text=value)
    
    title = property(get_title, set_title,'The title of the document')
    
    def get(self):
        '''
        Synopsis:
            Gets the content of a document
        Arguments:
        Exceptions:
        Returns:
        '''
        pass
    
    def post(self,session):
        '''
        Synopsis:
            Creates a new document
        Arguments:
            session
        Exceptions:
        Returns:
        '''
        try:
            self.handle = session.client.Post(self._entry,'/feeds/documents/private/full')
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to create document'
            return False
    
    def put(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def delete(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True

class GCalendarService(CalendarService):
    '''
    '''
    def __init__(self):
        '''
        '''
        self.webaddress     = None   
        #Outside this domain - set user ability
        #By default, calendars are not shared outside this domain. 
        #Select the highest level of sharing that you want 
        #to allow for your users.
        # FREEBUSY,ALL,ALL_WRITE
        self.public_sharing = None
        #Within this domain - set default
        #Users will be able to change this default setting.
        # NONE,FREEBUSY,ALL
        self.domain_sharing = None
        #this is a dictionary with the page form
        #hidden attributes that we're reading here
        #to increase efficienct
        self._hidden_input_dict = None
    
    def get(self,session):
        '''
        Synopsis:
            Gets the info
        Arguments:
        Exceptions:
        Returns:
        '''
        ###################################################################
        #  Getting Doc Setting page
        ###################################################################
        #setting the uri
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/CalendarSettings'        
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + str(ex.reason)
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()                     
        #asserting we're on the right place
        pattern = 'Calendar settings'
        if len(re.findall(pattern, content))== 0 :
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s using pattern %s in content %s' % (uri,pattern,content)
            return False
        ###################################################################
        #Parsing content with BeautifulSoup
        ###################################################################
        try:
            html = BeautifulSoup(content)
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nException message: ' + ex.message
            return False
        ########################################################################
        #Scraping the page
        ########################################################################
        self.webaddress = str(html.findAll('a',{'id':'calendarLink'})[0].string)
        inputs= html.findAll('input',{'type':'radio', 'checked':None})
        #inputs= html.findAll('input')
        for input in inputs:
            if input.has_key('checked'):
                if   input['name']=='intraDomainSharing':
                    self.domain_sharing = input['value']
                elif input['name']=='extraDomainSharing':
                    self.public_sharing = input['value']
                else: 
                    self.error = 'Problem while scraping the page'
                    return False
        ########################################################################
        #retrieving hidden attributes
        ########################################################################
        inputs= html.findAll('input',{'type':'hidden'})
        if len(inputs)<>0:
            self._hidden_input_dict = {}
            for input in inputs:
                self._hidden_input_dict[input['name']]=input['value']
        return True

    def put(self,session, webaddress=None,public_sharing = None, domain_sharing = None):
        '''
        Synopsis:
            updates the calendar service
        Arguments:
        Exceptions:
        Returns:
        '''
        if webaddress is not None:
            if not GHServiceHelper.post_webaddress(session, 'cal', webaddress):
                return False
        if public_sharing is not None or domain_sharing is not None: 
            if public_sharing is not None:
                if string.upper(public_sharing) not in ['FREEBUSY','ALL','ALL_WRITE']:
                    self.error = 'Expected "FREEBUSY","ALL","ALL_WRITE" and received "%s"' % domain_sharing
                    return False 
            if domain_sharing is not None:
                if string.upper(domain_sharing) not in ['NONE','FREEBUSY','ALL']:
                    self.error = 'Expected "NONE","FREEBUSY","ALL" and received "%s"' % domain_sharing
                    return False        
            if not self.get(session):
                return False
            else:
                if self.public_sharing == public_sharing and \
                   self.domain_sharing == domain_sharing:
                    self.error = 'Update values are the same as current values'
                    return False
                else:
                    self.public_sharing = public_sharing
                    self.domain_sharing = domain_sharing
        ###################################################################
        #Posting value
        ###################################################################
        #setting uri   
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/CalendarSettings'
        #setting the headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #setting body
        data = {}
        for key in self._hidden_input_dict.keys():
            data[key] = self._hidden_input_dict[key]
        data['extraDomainSharing'] = self.domain_sharing
        data['intraDomainSharing'] = self.public_sharing
        #there's already a hidden attribute with this name
        #data['actionInput.CONTINUE'                    ] = 'Continue &raquo;'        
        #defining the request
        request = urllib2.Request(uri, data=urllib.urlencode(data),headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
        else:
            content = response.read() 
        ########################################################
        # Check for any errors
        ########################################################
        return True
    
    def delete(self):
        '''
        Synopsis:
            Deactivates the service
        Arguments:
        Exceptions:
        Returns:
        '''
        return True

class GCalendar(Calendar):
    '''
    '''
    def __init__(self):
        pass

    def get(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True

    def post(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def put(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True
    
    def delete(self):
        '''
        Synopsis:
            updates an existing site
        Arguments:
        Exceptions:
        Returns:
        '''
        return True

class GSiteService (SiteService):
    '''
    This class represents the service that allows
    a user to create websites.
    '''
    def __init__(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        super(GSiteService,self).__init__()
        self.webaddress                  = None
        self.is_no_collab_outside_domain = None
        self.is_allow_collab_with_warn   = None 
        self.is_allow_collab             = None
        self.us_allow_users_public       = None
        self.site_list                   = None
    
    def get(self, session,list_sites=None):
        '''
        Synopsis:
            Returns the site service configurations and 
            it can return the list of sites associated 
            with the account. For performance reasons,
            it also add the hidden attributes.
        Arguments:
            Deep - determines if sites data will be passed
        Exceptions:
        Returns:
        '''
        ###################################################################
        #  Getting to CPanel Service Site Settings
        ###################################################################
        #setting the uri
        uri='https://www.google.com/a/cpanel/' + session.domain_name + '/SitesSettings'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        #Parsing content with BeautifulSoup
        ###################################################################
        try:
            html = BeautifulSoup(content)
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nException message: ' + ex.message
            return False
        ########################################################################
        #Scraping the page
        ########################################################################
        self.webaddress = str(html.findAll('a',{'id':'sitesLink'})[0].string)
        inputs= html.findAll('input',{'type':'radio'})
        #inputs= html.findAll('input')
        for input in inputs:
            if input.has_key('checked'):
                if   input['name']=='intraDomainSharing':
                    self.domain_sharing = input['value']
                elif input['name']=='extraDomainSharing':
                    self.public_sharing = input['value']
                else: 
                    self.error = 'Problem while scraping the page'
                    return False
        ########################################################################
        #retrieving hidden attributes
        ########################################################################
        inputs= html.findAll('input',{'type':'hidden'})
        if len(inputs)<>0:
            self._hidden_input_dict = {}
            for input in inputs:
                self._hidden_input_dict[input['name']]=input['value']
        return True
            
            
    def _get_sites(self,session):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        #setting the uri
        uri='https://sites.google.com/a/' + session.domain_name + '/?tab=c3'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()

        ###################################################################
        #  Returning the list of sites
        ###################################################################
        pattern = '<h3>My sites in '+session.domain_name+'</h3>.*?<ul>(.*?)</ul>'
        results = re.findall(pattern, content, re.S)
        if len(results)==0: 
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        else:
            pattern='<li>.*?<a.*?>(.*?)</a>.*?<a.*?>(.*?)</a>.*?<span.*?>(.*?)</span>.*?<span.*?>(.*?)</span>.*?</li>'
            results = re.findall(pattern, results[0], re.S)
            if len(results)==0:
                self.error = 'no sites found'
                return True
            else:
                for result in results:
                    my_site = GSite()
                    my_site.name=string.strip(result[0])
                    my_site.template=string.strip(result[1])
                    if string.find(result[2],'world')<>-1: my_site.is_public=True
                    my_site.description=string.strip(result[3])
                    if deep:
                        if not my_site.get(session, deep=deep):
                            self.error = my_site.error
                            return False
                    self.site_list.append(my_site)
            return True


    def put(self,session,webaddress=None):
        '''
        Synopsis:
            Changes the configuration of the site
            service.
        Arguments:
        Exceptions:
        Returns:
        '''
        if webaddress is not None:
            if not GHServiceHelper.post_webaddress(session, 'jotspot', webaddress):
                return False
        if public_sharing is not None or domain_sharing is not None: 
            if public_sharing is not None:
                if string.upper(public_sharing) not in ['FREEBUSY','ALL','ALL_WRITE']:
                    self.error = 'Expected "FREEBUSY","ALL","ALL_WRITE" and received "%s"' % domain_sharing
                    return False 
            if domain_sharing is not None:
                if string.upper(domain_sharing) not in ['NONE','FREEBUSY','ALL']:
                    self.error = 'Expected "NONE","FREEBUSY","ALL" and received "%s"' % domain_sharing
                    return False        
            if not self.get(session):
                return False
            else:
                if self.public_sharing == public_sharing and \
                   self.domain_sharing == domain_sharing:
                    self.error = 'Update values are the same as current values'
                    return False
                else:
                    self.public_sharing = public_sharing
                    self.domain_sharing = domain_sharing
        ###################################################################
        #Posting value
        ###################################################################
        #setting uri   
        uri = 'https://www.google.com/a/cpanel/' + session.domain_name + '/CalendarSettings'
        #setting the headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #setting body
        data = {}
        for key in self._hidden_input_dict.keys():
            data[key] = self._hidden_input_dict[key]
        data['extraDomainSharing'] = self.domain_sharing
        data['intraDomainSharing'] = self.public_sharing
        #there's already a hidden attribute with this name
        #data['actionInput.CONTINUE'                    ] = 'Continue &raquo;'        
        #defining the request
        request = urllib2.Request(uri, data=urllib.urlencode(data),headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
        else:
            content = response.read() 
        ########################################################
        # Check for any errors
        ########################################################
        return True
        

    def delete(self):
        '''
        Synopsis:
            Innactivates the Sites Service 
        Arguments:
        Exceptions:
        Returns:
        '''
        pass

class GSiteHelper():
    '''
    Synopsis:
        This class contains all the GSite helper methods.
        It's no included into a GSite class because there
        is more than once class.
    '''
    
    @staticmethod
    def _set_jotxtok(session):
        '''
        Synopsis:
            This method sets the first jotxtok in case the
            session hasn't done yet.  This is done automatically
            without user intervention.
        '''
        ###################################################################
        #
        #  Step 1 - Getting to Sites Service Dashboard
        #
        ###################################################################
        #setting the uri
        uri='https://sites.google.com/a/' + session.domain_name + '/?tab=c3'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        # assess current page
        ###################################################################
        pattern = '<h3>My sites in '+session.domain_name+'</h3>.*?<ul>(.*?)</ul>'
        results = re.findall(pattern, content, re.S)
        if len(results)==0: 
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable certify uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False
        else:
            return True
    
    @staticmethod
    def _get_jotxtok(session):
        '''
        Synopsis:
            determines if the jotxtok is set.  In case it is
            not calls _set_jotxtok, and call recursevelly the
            _get_jotxtok.
        Returns:
            jotxtok
        ''' 
        for cookie in session.cookiejar:
            if cookie.name == 'jotxtok': 
                return cookie.value
        if GSiteHelper._set_jotxtok(session):
            for cookie in session.cookiejar:
                if cookie.name == 'jotxtok': 
                    return cookie.value
                    
    @staticmethod
    def _set_uri_token(session, original_uri):
        '''
        Synopsis:
            Adds to an URI the "jotxtok" token.
        '''
        jotxtok = GSiteHelper._get_jotxtok(session)
        return string.join([original_uri,'jot.xtok=' + urllib.quote(jotxtok,'')],'?')
    
    @staticmethod
    def _set_json(dict):
        '''
        Synopsis:
            Correctly sets the JSON call.
        Note: changed to quote('',safe=''), i.e., no characters
              safe because of page.post JSON calls
        '''
        #return 'json=' + urllib.quote(string.replace(jsonpickle.encode(dict),' ',''),safe='')
        return 'json=' + urllib.quote(GSiteHelper._rm_space(jsonpickle.encode(dict)),safe='')
    
    @staticmethod
    def _rm_space(dict):
        '''
        Synopsis:
            Remove the extra spaces in a dict
            a) { "
            b) " :|, "
            d) "  }
        '''
        dict = string.strip(dict)
        pattern = '{\s+?"'
        repl    = '{"'
        dict = re.sub(pattern, repl, dict)
        pattern = '"\s+?:\s+?"'
        repl    = '":"'
        dict = re.sub(pattern, repl, dict)
        pattern = '"\s+?,\s+?"'
        repl    = '","'
        dict = re.sub(pattern, repl, dict)
        pattern = '"\s*?}'
        repl    = '"}'
        dict = re.sub(pattern, repl, dict)
        return dict


class GSiteComponent(SiteComponent):
    '''
    Synopsis:
        Represents a GoogleSite Nav 
    '''
    def __init__(self,generate=False):
        '''
        constructor
        type: '/system/app/components/min-navigation',
              '/system/app/components/min-textbox',
              '/system/app/components/min-countdown'
        '''
        super(GSiteComponent,self).__init__()
        self._type            = None
        self.is_show_recents  = None
        self.dynamic_depth    = None
        self.is_show_site_map = None
        self.navigation_tree  = None  #[{"id":"wuid:gx:ffefa98919eca61","title":"Home","path":"/home"}]
        self._content         = None
        self.event            = None
        self.from_date_utc    = None  #How many milliseconds there are from 1970/01/01 to current date
        self.component_list   = None
        self.indent_image     = None
        self.outdent_image    = None
        self.operation        = None
        
        #generates a number 75058737428045
        if generate:
            self.id = token = ''.join(random.choice(string.digits) for i in xrange(15))
        
    #content    
    def get_content(self):
        return self._content
    def set_content(self, value):
        self._content = '<DIV DIR=\"ltr\">%s</DIV>' % value
    
    content = property(get_content, set_content,'Content to add to the text component')


    #type    
    def get_type(self):
        return self._type
    def set_type(self, value):
        '''
        Synopsis:
            if value is the complete string, then it gets replaced.
        '''
        if value is not None:
            value = re.sub('/system/app/components/', '', value)
            if value in ['sidebar','min-navigation','min-textbox','min-countdown']:
                self._type = '/system/app/components/' +  value
            else:
                raise Exception('Unexpected component type: ' + value)
    
    type = property(get_type, set_type,'Type of component')



class GSite(Site):
    '''
    Synopsis:
        Represents a GoogleSite
    '''
    def __init__(self):
        '''
        constructor
        '''
        super(GSite,self).__init__()
        self.theme                 = ''
        self.is_show_site_title    = False   #Show site name at top of pages
        self.landing_page          = ''
        self.is_analytics_enable   = False   #is webanalytics enableded
        self.analytics_account_id  = ''      #webanalytics
        self.webmaster_meta_tag    = ''      #webmaster tools
        self.web_address_mapping   = ''
        #self.locale                = '' 
        self.admin_list            = None    #[{"uid":"17627929225826748628","email":"fpinto@filipe-pinto.com"},
                                             #{"uid":"13543395615464981804","email":"nealwalters@nealwalters.com"}];
        self.collab_list           = None   
        self.viewer_list           = None        
        self.collab_list_sr        = None   
        self.viewer_list_sr        = None        
        self.attachments           = None
        self.pages                 = None    # list of GSitePage objects
        self.logo                  = None
        self.components            = None    #{'textbox'      : {'title:'bio',
                                             #                   'content':'blabah'},
                                             # 'countdown'    : {'title':'BPM exam',
                                             #                   'date':'12/09/2010'}
                                             # 'nav'          : {'title':'nav',
                                             #                   'display':True,
                                             #                   'org_automatic':True,
                                             #                   'show_level_number':2,
                                             #                   'show_sitemap: True
                                             #                   'show_rec_ativity: False}
        self.width            = None
        self.sidebar_width    = None
        self.url_changed      = None    #this flag will be True if during site creation
                                             #the site url was changed. For example is there
                                             #are spaces in the orginal name, Google Sites will
                                             #replace it.
        self.search           = None
        self.header_height    = None
        self.version          = None
        self.body_id          = None
        self.sidebar_ref      = None
    
    def get(self,session,type='info'):
        '''
        Synopsis:
            Returns all the details of a website, by scraping
            the data from the different tabs
        Arguments:
            session : 
            type    :  info, sharing, layout, attachments, all
        Exceptions:
        Returns:
        '''
        # Checkign mandatory fields
        if self.url =='':
            self.error = 'Please define site uri'
            return False
        # Determining the type of query        
        if   type=='info'       : return self._get_info(session)
        elif type=='sharing'    : return self._get_sharing(session)
        elif type=='layout'     : return self._get_layout(session)
        elif type=='attachments': return self._get_attachments(session)
        elif type=='all':
            if not self._get_info(session)       : return False
            if not self._get_sharing(session)    : return False
            if not self._get_layout(session)     : return False
            if not self._get_attachments(session): return False
            return True

    def _get_info(self,session):
        '''
        '''
        ###################################################################
        #
        #  Step 1 - Getting Site General Tab
        #
        ###################################################################
        #defining the uri
        uri='https://sites.google.com/a/'+session.domain_name+'/'+\
             self.url + '/system/app/pages/admin/settings'
        #definng the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + str(ex.reason)
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        #
        # Scraping information
        #        
        #{"config/siteTags"              :["tag_1","tag_2","tag_3","tag_4","tag_5","tag_6"],
        # "config/enableAnalytics"       :true,
        # "config/siteTitle"             :"OneCloud_test",
        # "config/showSiteTitle"         :true,
        # "config/siteDescription"       :"This is the Filipe Pinto's oneCloud Professional 1",
        # "config/siteLocale"            :"en",
        # "config/webmasterToolsMetaTag" :"verify-v1|IHk8prUJGoHm3wa9moW5saIp6akmqDdLc2qMXsfaocb6g=",
        # "config/analyticsAccountId"    :"UA-12345-12",
        # "config/landingPage"           :"/home",
        # "config/admins"                :["17627929225826748628","13543395615464981804"],
        # "sys/webspace/matureWebspace"  :false,
        # "sys/hidden"                   :true};
        #
        ###################################################################
        #searching for origWsConfig_
        pattern = 'origWsConfig_\s*=\s*(.*?);'
        content = re.findall(pattern, content)
        if len(content)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unable to retrieve '%s' pattern in content '%s':" % (pattern,content)            
            return False
        content = string.replace(content[0], '\'', '')
        try:
            config  = jsonpickle.decode(content)
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "\nUnable to decode JSON '%s' " % (content) + \
                         '\nException: '  +  ex.message
            return False
        
        #assigniments
        self.title                 = config['config/siteDescription']
        self.is_show_site_title    = config['config/showSiteTitle']
        self.tags                  = config['config/siteTags']
        self.description           = config['config/siteDescription']
        self.landing_page          = config['config/landingPage']
        self.is_analytics_enable   = config['config/enableAnalytics']
        self.locale                = config['config/siteLocale']
        if config.has_key('config/analyticsAccountId'):
            self.analytics_account_id = config['config/analyticsAccountId']
        if config.has_key('config/webmasterToolsMetaTag'):
            self.webmaster_meta_tag  = config['config/webmasterToolsMetaTag']

        return True
    
    def _get_sharing(self,session): 
        '''
        Synopsis:
            Getting Site Sharing Tab
                self.owner      : [{"uid":"17627929225826748628","email":"fpinto@filipe-pinto.com"}],
                self.collborator: []
                self.viewer     : []
        Arguments:
        Exceptions:
        Returns:
        '''
        #defining the uri
        uri='https://sites.google.com/a/'+session.domain_name+'/'+\
             self.url + '/system/app/pages/admin/sharing'
        #definng the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        #
        # Scraping information
        #
        #  var adminList  = [{"uid":"17627929225826748628","email":"fpinto@filipe-pinto.com"},{"uid":"13543395615464981804","email":"nealwalters@nealwalters.com"}];
        #  var collabList = [{"uid":"08598595239741952641","email":"patricia@patricia-hughes.com"}];
        #  var viewerList = [{"uid":"05711560405127345140","email":"diego.moses@gmail.com"}];
        #
        #  var collabListSR = [];
        #  var viewerListSR = ["#public"];
        #
        ###################################################################
        if not self._get_sharing_info(content,'adminList'   ): return False
        if not self._get_sharing_info(content,'collabList'  ): return False
        if not self._get_sharing_info(content,'viewerList'  ): return False
        if not self._get_sharing_info(content,'collabListSR'): return False
        if not self._get_sharing_info(content,'viewerListSR'): return False  
        return True
        
    def _get_sharing_info(self,content,list_string):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
            list
            success
        '''
        #searching for adminList
        pattern = list_string + '\s*=\s*(.*?);'
        content = re.findall(pattern, content)
        if len(content)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unable to retrieve '%s' pattern in content '%s':" % (pattern,content)            
            return False
        try:
            list= jsonpickle.decode(content[0])
            if   list_string=='adminList'   : self.admin_list     = list
            elif list_string=='collabList'  : self.collab_list    = list
            elif list_string=='viewerList'  : self.viewer_list    = list
            elif list_string=='viewerListSR': self.viewer_list_sr = list
            elif list_string=='collabListSR': self.collab_list_sr = list
            
            return True
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "\nUnable to decode JSON '%s' " % (content) + \
                         '\nException: '  +  ex.message
            return False
    
    def _get_layout(self,session):
        '''
        Synopsis:
            Getting Site Layout Tab
        Arguments:
        Exceptions:
        Returns:
        '''    
        #defining the uri
        uri='https://sites.google.com/a/'+session.domain_name+'/'+\
             self.url + '/system/app/pages/admin/appearance/pageElements'
        #definng the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        # Scraping information
        # var origAppConfig_ = {"config/sidebarRef"            :"30bf",
        #                       "component/30bf/type"          :"/system/app/components/sidebar",
        #                       "config/siteWidth"             :null,
        #                       "component/2bd/showRecents"    :false,
        #                       "component/2bd/navDynamicDepth":2,
        #                       "config/version"               :"20",
        #                       "component/30bf/items"         :["2bd"],
        #                       "component/2bd/type"           :"/system/app/components/min-navigation",
        #                       "config/bodyId"                :"goog-ws-left",
        #                       "component/2bd/navigationTree" :"{\"children\":[{\"id\":\"wuid:gx:7641eef7626e769e\",\"title\":\"Home\",\"path\":\"/home\"}]}","component/2bd/hideTitle":"true","config/activeTheme":"iceberg","config/logoPath":"DEFAULT_LOGO","config/headerHeight":null,"config/landingPage":"wuid:gx:7641eef7626e769e",
        #                       "component/2bd/showSiteMap"    :true,
        #                       "config/sidebarWidth"          :"150",
        #                       "sys/hidden"                   :true};
        ###################################################################
        #searching for origWsConfig_
        pattern = 'origAppConfig_\s*=\s*(.*);'
        content = re.findall(pattern, content)
        if len(content)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unable to retrieve '%s' pattern in content '%s':" % (pattern,content)            
            return False        
        #assigniments        
        pattern = '"((?:component|config|sys)/.*?)":(.*?)(?=(?:,"(?:component|config|sys)/.*?":)|}$)'
        results = re.findall(pattern, content[0])
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "\nUnable to find pattern '%s' in content '%s'" % (pattern,content) 
            return False            
        for result in results:
            if   result[0]=='confg/siteWidth':
                self.width = eval(result[1])
            elif result[0]=='config/activeTheme':
                self.theme = eval(result[1])
            elif result[0]=='config/search/settings/default':
                self.search = eval(result[1])
            elif result[0]=='config/headerHeight':
                self.header_height = jsonpickle.decode(result[1])
            elif result[0]=='config/headerHeight':
                self.header_height = eval(result[1])
            elif result[0]=='config/bodyId':
                self.body_id = eval(result[1])
            elif result[0]=='config/sidebarWidth':    
                self.sidebar_width = eval(result[1])                
            elif result[0]=='config/logoPath':    
                self.logo = eval(result[1])                
            elif result[0]=='config/sidebarRef':    
                self.sidebar_ref = eval(result[1])
            elif result[0]=='config/landingPage':    
                self.landing_page = eval(result[1])
            elif result[0]=='config/version':    
                self.version = eval(result[1])
            # Processing components
            elif string.find(result[0],'component')==0:
                pattern = 'component/(.*?)/(.*)'
                results = re.findall(pattern, result[0])
                found = False
                #Checking if object was already created
                if self.components is not None:
                    for i in range(len(self.components)):
                        if self.components[i].id == results[0][0]:
                            index=i
                            found = True
                            break
                else:
                    self.components = []
                    index = 0
                #Creating object
                if not found:             
                    component = GSiteComponent()
                    component.id = results[0][0]
                    self.components.append(component)
                    index = len(self.components)-1
                #pupulating the component
                if   results[0][1] == 'type':
                    self.components[index].type = jsonpickle.decode(result[1])  
                elif   results[0][1] == 'title':
                    self.components[index].title = jsonpickle.decode(result[1])  
                elif results[0][1] ==  'showSiteMap':
                    self.components[index].is_show_site_map = jsonpickle.decode(result[1])   
                elif results[0][1] ==  'navigationTree':
                    self.components[index].navigation_tree = jsonpickle.decode(result[1])  
                elif results[0][1] ==  'content':
                    self.components[index].content = re.findall('<div dir="ltr">(.*?)</div>',jsonpickle.decode(result[1]),re.I)[0]                      
                elif results[0][1] ==  'event':
                    self.components[index].event = jsonpickle.decode(result[1])  
                elif results[0][1] ==  'fromDateUTC':
                    self.components[index].from_date_utc = jsonpickle.decode(result[1])  
                elif results[0][1] ==  'showRecents':
                    self.components[index].date = jsonpickle.decode(result[1])  
                elif results[0][1] ==  'items':
                    self.components[index].component_list = jsonpickle.decode(result[1]) 
                elif results[0][1] ==  'indentImgSrc':
                    self.components[index].indent_image = jsonpickle.decode(result[1])
                elif results[0][1] ==  'outdentImgSrc':
                    self.components[index].outdent_image = jsonpickle.decode(result[1])                    
                    
        return True       
    
    def _get_attachments(self,session):
        '''
        Synopsis:
            Gets site attachements
        Arguments:
        Exceptions:
        Returns:
        '''
        #defining the uri
        uri='https://sites.google.com/a/'+session.domain_name+'/'+\
             self.url + '/system/app/pages/admin/attachments'
        #definng the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        #Parsing HTML
        ###################################################################
        pattern = SoupStrainer('table', {'id':'sites-admin-attach-table'})
        try:
            node = BeautifulSoup(WebTools.rm_script_tag(content), parseOnlyThese=pattern)
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nException message: ' + ex.message
            return False
        if node==None:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to parse uri %s - content %s' % (self.uri,content)
            return False
        
        ########################################################################
        #looking for files
        ########################################################################
        tbody_node  = node.findAll('tbody')[0]
        self.attachments=[]
        for tr in tbody_node:
            if not isinstance(tr, unicode):
                file={}
                index = 0
                for td  in tr:
                    if not isinstance(td, unicode):
                        index = index + 1
                        if   index==2:
                            file['name']= string.strip(td.a.span.string)
                            #wuid:gx:75e65f41f70a87be
                            file['id'  ]= re.findall('(wuid:gx:.*)', td.a.span['id'])[0]
                        elif index ==3:
                            if td.a is not None:
                                file['location']= string.strip(td.a.string)
                            else:
                                file['location']= '/'
                        elif index ==4:
                            file['size']= string.strip(td.string)
                self.attachments.append(file)
        return True

    def post(self,session):
        '''
        Synopsis:
            Creates a new site
        Arguments:
        Exceptions:
        Returns:
        '''
        #defining the uri
        uri='https://sites.google.com/a/'+session.domain_name+\
                 '/sites/system/app/pages/meta/dashboard/create-new-site'
        #definng the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##################################################################
        #asserting correct page
        ##################################################################
        pattern='Create new site'
        results = re.findall(pattern, content)      
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s using pattern %s in content %s' % (uri,pattern,content)
            return False
        ###################################################################
        #
        #  Calling WS to normalize the site url.
        #
        #  Example: all spaces in the url will be replaced with a dashes
        #              
        ################################################################### 
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/sites/system/services/gateway' )
        #building the json request
        #json={"string":"test88","hasDelimiter":true,"service":"Asciify"}
        #json=%7B%22string%22%3A%22%22%2C%22hasDelimiter%22%3Atrue%2C%22service%22%3A%22Asciify%22%7D
        dict = {'string':self.url,'hasDelimiter':True,'service':'Asciify'}
        #defining the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting the request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##################################################################
        # Checking webservice reply
        # Expected reply {"string":"test_333"} or {"string":""}
        ##################################################################
        try:
            ws_result = jsonpickle.decode(string.strip(content))
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         '\n@line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to unpickle JSON reply from Gateway WS to normalize URI.' +\
                         '\nRaw message retrieved: ' + content +\
                         '\nException: ' + ex.message
            return False
        else:
            if not ws_result.has_key('string'):
                self.error = self.__class__.__name__+'.'+ \
                             sys._getframe().f_code.co_name + \
                            ' @line:' + str(sys._getframe().f_lineno) + \
                            'WS returned unexpected reply "%s" while looking for {"string":"normalized_uri"}.' % content
                return False
            else:
                if self.url <> ws_result['string']:
                    self.url = ws_result['string']
                    self.site_url_changed = True
        ###################################################################
        #
        #  Calling WS Create Site
        #
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+session.domain_name+\
                                                 '/sites/system/services/createSite' )
        #building the json structure
        #json={"wsName":"test88","opt_title":"test88","opt_writeUsers":["#domain"],
        #      "opt_readUsers":["#public"],"opt_theme":"iceberg","opt_desc":"sitedescription",
        #      "opt_categories":["cat1","cat2","cat3"],"opt_matureFlag":null}
        dict={'wsName'        :self.url,
              'opt_title'     :self.name,
              'opt_writeUsers':['#domain'], 
              'opt_readUsers' :['#public'],
              'opt_theme'     :'iceberg',
              'opt_desc'      :self.description,
              'opt_categories':self.tags,
              'opt_matureFlag':None}
        #define headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting the request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##################################################################
        # Checking webservice reply
        # Expected reply: {"webspace":"test88"}
        ##################################################################        
        try:
            ws_result = jsonpickle.decode(string.strip(content))
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         'Unable to unpickle JSON reply from createSite WS.' +\
                         '\nRaw message retrieved: ' + content +\
                         '\nException: ' + ex.message
            return False
        else:            
            if not ws_result.has_key('webspace'):
                self.error= self.error = self.__class__.__name__+'.'+ \
                            sys._getframe().f_code.co_name + \
                            ' @line:' + str(sys._getframe().f_lineno) + \
                            'WS returned unexpected reply "%s" while looking for {"webspace":"xxxxx"}.' % content
                return False    
        ###################################################################
        #
        #  Calling verifyWebspaceExists WS
        #
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                        session.domain_name+'/sites/system/services/verifyWebspaceExists' )
        #building the json structure
        #json={"wsName":"test88","fromCopyOp":false}
        dict={'wsName':self.name,'fromCopyOp':False}
        #setting headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded' 
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##################################################################
        # Checking webservice reply
        # 
        # NOTE! Something strange happens here. Sometimes the WS returns 
        #       "yes" and others returns nothing.
        ##################################################################
        if string.find(content,'yes')==-1 and len(string.strip(content))<>0:   #doesn't find yes and it's not empty!
                self.error = 'WS returned %S when looking for "yes" or "empty string"' % content
                return False
        ###################################################################
        #
        #  verrifying the site was successfully created
        #  
        ###################################################################         
        uri = 'https://sites.google.com/a/'+ session.domain_name + '/' + self.url
        request = urllib2.Request(uri, headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            return True

    def put(self,type=None):
        '''
        Synopsis:
            Updates an existing site.
        Arguments:
            type: the subset of information to be updated:
                    - info
                    - sharing
                    - layout
                    - attachments
        Exceptions:
        Returns:
        '''
        # Checkign mandatory fields
        if self.url =='':
            self.error = 'Please define site uri'
            return False
        # Determining the type of query        
        if   type=='info'       : return self._get_info(session)
        elif type=='sharing'    : return self._get_sharing(session)
        elif type=='layout'     : return self._get_layout(session)
        elif type=='attachments': return self._get_attachments(session)

        return True
        
    def _put_info(self,session,
                       title                = None,
                       show_title           = None,
                       tags                 = None,
                       description          = None,
                       enable_analytics     = None,
                       analytics_account_id = None,
                       webmaster_meta_tag   = None,
                       locale               = None):
        '''
        Synopsis:
            Updates site general info. It first does
            a get_info to make sure that there's no loss
            of information.
        Arguments:
            Session              - authenticated session
            title                - None,
            show_title           - None,
            tags                 - None,
            description          - None,
            enable_analytics     - None,
            analytics_account_id - None,
            webmaster_meta_tag   - None,
            locale               - None
        Exceptions:
        Returns:
        '''
        ###################################################################
        #  Calling WS Create Site
        ###################################################################  
        if not self._get_info(session): return False
        ###################################################################
        #  Setting attributes that will change
        ###################################################################
        if title                is not None:
            self.title                = title
        if show_title           is not None:
            self.is_show_site_title   = show_title
        if tags                 is not None:
            self.tags                 = tags
        if description          is not None:
            self.description          = description
        if enable_analytics     is not None:
            self.is_analytics_enable  = enable_analytics
        if analytics_account_id is not  None:
            self.analytics_account_id = analytics_account_id  
        if webmaster_meta_tag   is not  None:
            self.webmaster_meta_tag   = webmaster_meta_tag 
        if locale               is not  None:
            self.locale               = locale
        ###################################################################
        #  Calling WS Create Site
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+self.url + \
                                         '/system/services/save' )        
        ################################################################################################
        #json={"path":"/config/WebspaceConfig",
        #      "properties":{
        #                    "config/siteTitle"    :"Project X, pROHECT J",
        #                    "config/showSiteTitle":false,
        #                    "config/siteTags"     :["tag1","tag2","tag3","tag4","tag5","tag6","tag 7"],
        #                    "config/siteDescription":"test site description",
        #                    "config/enableAnalytics":false,
        #                    "config/analyticsAccountId":"",
        #                    "config/webmasterToolsMetaTag":"",
        #                    "config/siteLocale":"en"
        #                    },
        #      "requestPath":"/a/filipe-pinto.com/projectx/system/app/pages/admin/settings"}
        ################################################################################################
        properties = {'config/siteTitle'            : self.title,
                      'config/showSiteTitle'        : self.is_show_site_title,
                      'config/siteTags'             : self.tags,
                      'config/siteDescription'      : self.description,
                      'config/enableAnalytics'      : self.is_analytics_enable,
                      'config/analyticsAccountId'   : self.analytics_account_id,
                      'config/webmasterToolsMetaTag': self.webmaster_meta_tag,
                      'config/siteLocale'           : self.locale}
        dict = {'path'        : '/config/WebspaceConfig',
                'requestPath' : '/a/' + session.domain_name + '/' + self.url + '/system/app/pages/admin/settings',
                'properties'  : properties}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        #
        #{"revision"  :3,
        # "time"      :"Sep 9, 2009 6:10 PM",
        # "path"      :"/config/WebspaceConfig",
        # "wuid"      :"wuid:gx:632c195b312de6c5",
        # "url"       :"/a/filipe-pinto.com/test_pro1cloud/config/WebspaceConfig",
        # "parentWuid":"wuid:gx:79dfc17f48ab8ad3"}
        ################################################################################################m
        return True

    def _put_sharing(self,session, role,list,operation, email= None):
        '''
        Synopsis:
            Changes the sharing configurations of the website. It first
            gets the current sharing configurations, and than processes
            the delta, add or removing users.
        Arguments:
            session    - authenticated session
            scope      - 'individual','domain_wide'
            role       - 'administrator','collaborator','viewer'
            send_email - whether to send email or not
            list       - list of email addresses with admin rights
            operation  - add,remove       
        Exceptions:
        Returns:        
        '''
        ###################################################################
        #  Get current charing configuration
        ###################################################################  
        if not self._get_sharing(session): return False
        ###################################################################
        #  Processing list
        ###################################################################
        if  list[0][0] <> '#':
            if operation == 'add':
                if not self._put_sharing_add(session,role,list,email): return False
            elif operation == 'remove':
                if not self._put_sharing_remove(session, role, list): return False
            elif operation not in ['add','remove']:
                self.error = 'Invalid admin list operation'
                return False
        #  Processing domain WideSharing
        else:
            if not self._put_sharing_domain_wide(session, role, operation): return False

           
        return True
            
    def _put_sharing_domain_wide(self,session,role,action):
        '''
        Synopsis:
            Calls the domain_wide webservice
        Arguments:
            session - authenticated session
            role    - ["administrator","guest",""]
            action  - ["add","remove"]
        Exceptions:
        Returns:        
        '''
        #checking the required attributes
        if role not in ['administrator','collaborator','guest']:
            self.error = 'The role "%s" is not valid. Please consult documentation' % role
            return False
        ###################################################################
        #  Calling WS Create Site
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+self.url + \
                                         '/system/services/domainWideSharing' )        
        ################################################################################################
        #json={"type"   :
        #      "action" :"ProcessInvites"}
        ################################################################################################
        dict = {'type'    : role,
                'action'  : action}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        #
        # Empty string
        ################################################################################################m
        if len(content)<> 0:
            self.error = 'There was an unexpected return from webservice - "%s"' % content
            return False
        else:
            return True

    def _get_list_user_ids(self,source_list,list):
        '''
        Synopsis:
            Searches the GSite sharing list and returns
            the uids of the emails passed in list. If
            no ids are found returns None
        Arguments:
            source list
            list
        Exceptions:
        Returns
            uids - uids corresponding to list
        '''
        uids = []
        for user in source_list:
            if user['email'] in list:
                uids.append(user['uid']) 
        if len(uids)==0: return None
        return uids

    def _put_sharing_remove(self,session,role,email_list):
        '''
        Synopsis:
            Removes the passed list from the sharing of the site.  Since
            the user passes a list of emails, and the webservice 
            requires user ids, there a lookup first done in self.
        Arguments:
            session        - authenticated session
            role           - "administrator","collaborator","viewer"
            email_list     - list of emails
        Exceptions:
        Returns:        
        '''
        #checking the required attributes
        if role not in ['administrator','collaborator','viewer']:
            self.error = 'The role "%s" is not valid. Please consult documentation' % role
            return False
        
        #checking if user exists in current list
        if   role == 'administrator' : uids=self._get_list_user_ids(self.admin_list ,email_list)
        elif role == 'collaborator'  : uids=self._get_list_user_ids(self.collab_list,email_list)
        elif role == 'viewer'        : uids=self._get_list_user_ids(self.viewer_list,email_list)
        if uids == None:
            self.error = 'No names in the supplied list were found as members'
            return False
        ###################################################################
        #  Calling WS Create Site
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+self.url + \
                                         '/system/services/deleteUsers' )        
        ################################################################################################
        #json={{"roles":["administrator"],
        #       "uids":["13543395615464981804"],
        #       "newRole":null}
        ################################################################################################
        dict = {'roles'        : [role],
                'uids'         : uids,
                'newRole'      : None}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        #
        #{"viewerList":[],
        # "collabList":[],
        # "adminList":[{"uid":"17627929225826748628","email":"fpinto@filipe-pinto.com"},
        #              {"uid":"13543395615464981804","email":"nealwalters@nealwalters.com"}]}
        ################################################################################################
        if content <> '{}':
            self.error = 'WS returned "%s when program expected {}' % content
        else: 
            return True

            
    def _put_sharing_add(self,session,role,email_list,email=None):
        '''
        Synopsis:
            Calls the webservice to process sharing changes
        Arguments:
            session        - authenticated session
            role           - "administrator","collaborator","viewer"
            email_list     - list of emails
            email          - GSITE_SHARING_EMAIL_DICT
        Exceptions:
        Returns:        
        '''
        #checking the required attributes
        if role not in ['administrator','collaborator','viewer']:
            self.error = 'The role "%s" is not valid. Please consult documentation' % role
            return False
        if email is not None: send_email = True
        else: send_email = False
        ###################################################################
        #  Calling WS Create Site
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+self.url + \
                                         '/system/services/gateway' )        
        ################################################################################################
        #json={"addrs"   :["nealwalters@nealwalters.com"],
        #      "role"    :"administrator",
        #      "sendMail":true,
        #      "subject" :"Project rt",
        #      "body"    :"I'm inviting you to become part of the website admins",
        #      "doCc"    :true,
        #      "service" :"ProcessInvites"}
        ################################################################################################
        dict = {'addrs'        : email_list,
                'role'         : role,
                'sendMail'     : send_email,
                'subject'      : email['subject'],
                'body'         : email['body'],
                'doCc'         : email['doCc'],
                'service'      : 'ProcessInvites'}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        #
        #{"viewerList":[],
        # "collabList":[],
        # "adminList":[{"uid":"17627929225826748628","email":"fpinto@filipe-pinto.com"},
        #              {"uid":"13543395615464981804","email":"nealwalters@nealwalters.com"}]}
        ################################################################################################m
        return True

    def _put_layout(self,session,
                         version       = None,
                         sidebar_width = None,
                         body_id       = None,
                         site_width    = None,
                         logo_path     = None,
                         header_height = None,
                         theme         = None,
                         landing_page  = None,
                         components    = None,    
                    ):
        '''
        Synopsis:
            Updates the site layout.  It first does
            a get of the current settings.
        Arguments:
             session       : authenticated session
             version       : None
             sidebar_width : None
             body_id       : None
             site_width    : None
             logo_path     : None
             header_height : None
             theme         : None
             landing_page  : None
             components    : list of components  
             operation     : 'add' or 'remove'  by default 'add'
        Exceptions:
        Returns
            success
        '''        
        #Getting the current data
        if not self._get_layout(session): return False
        
        ###################################################################
        #  Setting new values
        ###################################################################        
        if version      is not None:
            self.version = version
        if sidebar_width is not None:
            self.sidebar_width = sidebar_width
        if body_id       is not None:
            self.body_id = body_id
        if site_width    is not None:
            self.width = site_width
        if logo_path     is not None:
            self.logo = logo_path
        if header_height is not None:
            self.header_height = header_height
        if theme        is not None:
            self.theme = theme
        if landing_page is not None:
            self.landing_page = landing_page
            
        #identifying the index of the sidebarref
        for i in range(len(self.components)):
            if self.components[i].id == self.sidebar_ref: break
        sidebar_index = i
            
        #determining if components should be added or removed
        if components is not None:
            for put_component in components:
                if put_component.operation == 'add':
                    self.components.append(put_component)
                    self.components[i].component_list.append(put_component.id)
                elif put_component.operation == 'remove':
                    if   put_component.title is not None and put_component.type is not None: search = 1
                    elif put_component.id is not None: search = 2
                    elif put_component.event is not None: search =3
                    else:
                        self.error = 'Please either define "id" or "title" and "Type" to remove component'
                        return False
                    del_list=[]
                    for i in range(len(self.components)):
                        if   search ==1 :
                            if self.components[i].title == put_component.title and \
                               self.components[i].type  == put_component.type:
                                del_list.append({'index':i,'id':self.components[i].id})
                        elif search == 2:
                             if self.components[i].id == put_component.id:
                                 del_list.append({'index':i,'id':self.components[i].id})
                        elif search == 3:
                             if self.components[i].event == put_component.event:
                                 del_list.append({'index':i,'id':self.components[i].id})
                    #removing the components from the self.component list
                    time = 0
                    for item in del_list:
                        del self.components[item['index']-time]
                        time = time + 1
                        #removing the components from the sidebar
                        self.components[sidebar_index-time].component_list.remove(item['id'])
                else:  
                    self.error = 'Invalid operation. Received %s when expecting "add" or "remove"' % operation
                    return False

        ###################################################################
        #  Calling WS Create Site
        ###################################################################        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+self.url + \
                                         '/system/services/saveConfig' )        
        ################################################################################################
        #json=
        #{"path"      :"/config/app/appConfig",
        # "properties":{
        #                "config/version"               :"20",
        #                "config/sidebarWidth"          :"150",
        #                "config/bodyId"                :"goog-ws-left",
        #                "config/sidebarRef"            :"30bf",
        #                "config/siteWidth"             :null,
        #                "config/logoPath"              :"DEFAULT_LOGO",
        #                "config/headerHeight"          :null,
        #                "config/activeTheme"           :"iceberg",
        #                "config/landingPage"           :"wuid:gx:ffefa98919eca61",                        
        #                "sys/hidden"                   :true,
        # 
        #                "component/30bf/type"          :"/system/app/components/sidebar",                        
        #                "component/30bf/items"         :["2bd","3895508987321945","4989141843497884","11463227729236292"],
        #                
        #                "component/2bd/type"           :"/system/app/components/min-navigation",
        #                "component/2bd/hideTitle"      :"true",
        #                "component/2bd/showRecents"    :false,
        #                "component/2bd/navDynamicDepth":2,
        #                "component/2bd/showSiteMap"    :true,
        #                "component/2bd/navigationTree" :"
        #                    {
        #                     \"children\":
        #                        [
        #                        {\"id\":\"wuid:gx:ffefa98919eca61\",\"title\":\"Home\",\"path\":\"/home\"},
        #                        {\"id\":\"wuid:gx:488a63f06d7cc1ee\",\"title\":\"My Blog\",\"path\":\"/Blog\"},
        #                        {\"id\":\"wuid:gx:1ae9bc2984e63028\",\"title\":\"My Books\",\"path\":\"/Books\"},
        #                        {\"id\":\"wuid:gx:75cf2adff74b0e3f\",\"title\":\"My Expertise\",\"path\":\"/Expertise\"},
        #                        {\"id\":\"wuid:gx:642ff7f0596b538b\",\"title\":\"My Pictures\",\"path\":\"/Pictures\"},
        #                        {\"id\":\"wuid:gx:5f3966f7c236937d\",\"title\":\"My Resume\",\"path\":\"/Resume\"},
        #                        {\"id\":\"wuid:gx:3a2fe8124b334cad\",\"title\":\"My Social\",\"path\":\"/Social\"},
        #                        {\"id\":\"wuid:gx:11f1a96c63a59bd\",\"title\":\"My Videos\",\"path\":\"/Videos\"}
        #                        ]
        #                    }",
        #
        #
        #                "component/3895508987321945/type"          :"/system/app/components/min-navigation",
        #                "component/3895508987321945/navigationTree":"[]",
        #                
        #                "component/11463227729236292/type"         :"/system/app/components/min-countdown",
        #                "component/11463227729236292/event"        :"",
        #                "component/11463227729236292/fromDateUTC"  :"",
        #                
        #                "component/4989141843497884/type"          :"/system/app/components/min-textbox",
        #                "component/4989141843497884/title"         :"Bio"
        #                "component/4989141843497884/content"       :"<DIV DIR=\"ltr\">This is my bio</DIV>",
        #    },
        #    "requestPath":"/a/filipe-pinto.com/test_1cloudProEdiR1/system/app/pages/admin/appearance/pageElements"
        #}
        ################################################################################################
         
        properties = {
                      'config/version'        : self.version,
                      'config/sidebarWidth'   : self.sidebar_width,
                      'config/bodyId'         : self.body_id,
                      'config/sidebarRef'     : self.sidebar_ref,
                      'config/siteWidth'      : self.width,
                      'config/logoPath'       : self.logo,
                      'config/headerHeight'   : self.header_height,
                      'config/activeTheme'    : self.theme,
                      'config/landingPage'    : self.landing_page,           #'wuid:gx:ffefa98919eca61',                        
                      'sys/hidden'            : True
                      }
        
       
        #processing the component list
        for component in self.components:   
            if  component.type is not None:
                properties['component/'+component.id+'/type'] = component.type 
            if  component.title is not None:
                properties['component/'+component.id+'/title'] = component.title 
            if component.is_show_site_map is not None:
                properties['component/'+component.id +'/showSiteMap']  = component.is_show_site_map       
            if component.navigation_tree is not None: 
                properties['component/'+component.id +'/navigationTree'] = component.navigation_tree
            if component.content is not None: 
                properties['component/'+component.id +'/content'] = component.content                      
            if component.event is not None:
                properties['component/'+component.id +'/event'] = component.event 
            if component.from_date_utc is not None: 
                properties['component/'+component.id +'/fromDateUTC'] = component.from_date_utc 
            if component.is_show_recents is not None:  
                properties['component/'+component.id +'/showRecents'] = component.is_show_recents  
            elif component.component_list is not None:
                properties['component/'+component.id +'/items'] = component.component_list
              
        
        dict = {'path'        : '/config/app/appConfig',
                'requestPath' : '/a/' + session.domain_name + '/' + self.url + \
                              '/system/app/pages/admin/admin/appearance/pageElements',
                'properties'  : properties}
        
        print dict
        
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        #
        #{"revision":2,
        # "time":"Sep 17, 2009 2:43 PM",
        # "path":"/config/app/appConfig",
        # "wuid":"wuid:gx:226bfbc7972d4447",
        # "url":"/a/filipe-pinto.com/projectx/config/app/appConfig",
        # "parentWuid":"wuid:gx:5501ee0dd8e61815"}
        ################################################################################################m
        print content
        return True

    def _put_attachments(self,session,operation,file_name,page_path,content_type=None,uri=None):
        '''
        Synopsis:
            Adds or removes site attachements. 
        Arguments:
            session      : authenticated session
            operation    : 'upload', 'remove'
            file_name    : name of the file
            content_type : MIME type (example: png: image/x-png, old word: application/msword)
            uri          : file path
        Exceptions:
        Returns
            success
        '''
        if   operation == 'upload':
            if content_type is None:
                self.error = 'Please define the type of file'
                return False
            if uri is None:
                self.error = 'Please define the file path'
                return False
                
            self._put_attachment_add(session, content_type, file_name, uri, page_path)
            
        elif operation =='remove':
            self._put_attachment_remove(session, file_name, page_path)
            
        elif operation not in ['remove','upload']:
            self.error = 'Invalid operation. Received %s when expecting ["upload","remove"]' % operation
            return False
        
        return True
            

    def _put_attachment_remove(self,session,file_name,page_path):
        '''
        Synopsis:
            Removes an attachment from a website for a given
            page path.  It first retrieves the wuid of the 
            file. If it doesn't find it, returns false with
            error file not found.
        Arguments:
        Exceptions:
        Returns:
        '''
        #defining the current attachments
        if not self._get_attachments(session): return False
        ###################################################################
        #  getting the id of the file
        ###################################################################
        found = False
        for file in self.attachments:
            if file['name']==file_name:
                file_id = file['id']
                found = True
                break
        if not found:
            self.error = 'The file supplied was not found'
            return False
                        
        #setting the uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+self.url + \
                                         '/system/services/gateway' )        
        ################################################################################################
        #json={"wuids":["wuid:gx:75be7fa19888b396"],
        #      "service":"BulkDelete"}
        ################################################################################################
        dict = {'wuids'        : [file_id],
                'service'      : 'BulkDelete'}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        # {}
        ################################################################################################m
        if content <> '{}':
            self.error = 'Unexpected WS return code. Received %s when expecting "{}"' % content
            return False
        else:
            return True


    def _put_attachment_add(self,session,content_type,file_name,uri,page_path):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        #checking URI scheme
        pattern = '^(.*?)://'
        results = re.findall(pattern, uri)
        if len (results)==0:
            self.error = 'Please define the URI scheme'
            return False
        if results[0]=='file': 
            #checking file
            try:
                file = open(re.sub(pattern, '', uri),'rb')
                file_content = file.read()
            except Exception, ex:
                self.error = self.__class__.__name__+'.'+ \
                             sys._getframe().f_code.co_name + \
                             '@line:' + str(sys._getframe().f_lineno) + \
                             'Unable to open file.' +\
                             '\nException: ' + ex.message
                return False 
        if results[0] == 'http':
            headers=WebTools.firefox_headers()
            #defining the request
            request = urllib2.Request(uri, headers=headers)
            #submitting request
            try:
                response = session.urlopener.open(request)
            except IOError, ex:
                if hasattr(ex, 'reason'):
                    self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                    return False 
                elif hasattr(ex, 'code'):
                    self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                    return False
            except Exception,ex:
                self.error = "Unexpected error:" + ex.message
                return False
            else:
                file_content = response.read()            
        #defining the current attachments
        #if not self._get_attachments(session): return False
        #setting the uri
        uri = 'https://sites.google.com/a/'+ session.domain_name+'/'+self.url + \
              '/system/services/gateway-upload'        
        ################################################################################################
        #    -----------------------------7d92611a4e0e68
        #    Content-Disposition: form-data; name="userfile"; filename="C:\Documents and Settings\fpinto\Desktop\test2.html"
        #    Content-Type: text/html
        #    
        #    file.read()
        #    -----------------------------7d92611a4e0e68
        #    Content-Disposition: form-data; name="fileLocation"
        #    
        #    /
        #    -----------------------------7d92611a4e0e68
        #    Content-Disposition: form-data; name="pagePath"
        #    
        #    /
        #    -----------------------------7d92611a4e0e68
        #    Content-Disposition: form-data; name="json"
        #    
        #    {"service":"AttachFile"}
        #    -----------------------------7d92611a4e0e68
        #    Content-Disposition: form-data; name="jot.xtok"
        #    
        #    bMVck_YCt2LH3Im3eWG-hRN5_DY:1253396867185
        #    -----------------------------7d92611a4e0e68--
        ################################################################################################
        #IE token
        #token = '7d9' + ''.join(random.choice('0123456789abcdef') for i in xrange(11))
        #Firefox token
        token = ''.join(random.choice(string.digits) for i in xrange(15))
                
        NL                = '\r\n'
        http_content_type = 'multipart/form-data; boundary=' + ''.join('-' for i in xrange(27))+ token 
        file_location     = '/'
        service           = '{"service":"AttachFile"}'
        content_length    = str(len(file_content))
        separator         = NL + ''.join('-' for i in xrange(29))+ token + NL 
        
        #defining the body
        body = 'Content-Type: ' + http_content_type  + NL + \
               'Content-Length: ' + content_length + NL +\
                separator + \
               'Content-Disposition: form-data; name="userfile"; filename="' + file_name + '"' + NL +\
               'Content-Type: ' + content_type + NL + NL + \
               file_content +\
               separator  +\
               'Content-Disposition: form-data; name="fileLocation"' + NL + NL + \
               file_location +\
               separator + \
               'Content-Disposition: form-data; name="pagePath"' + NL +NL + \
               page_path + \
               separator + \
               'Content-Disposition: form-data; name="json"' + NL + NL + \
               service  +\
               separator + \
               'Content-Disposition: form-data; name="jot.xtok"' + NL +NL + \
               GSiteHelper._get_jotxtok(session) +\
               separator 
 
        #print body               
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = http_content_type
        #headers['Content-Type'] = 'multipart/form-data; ' + 'boundary=' + ''.join('-' for i in xrange(27))+ random_string 
        #defining the request
        request = urllib2.Request(uri, body, headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ################################################################################################
        # Assess WS response
        # {"remove"    :"Remove",
        #  "wuid"      :"wuid:gx:75be7fa19888b396",
        #  "cacheUrl"  :"/a/filipe-pinto.com/projectx/_/rsrc/1253543131845/load_test_2.txt",
        #  "attachVer" :"(version 7 / \u003Ca xmlns=\"http://www.w3.org/1999/xhtml\"
        #                 href=\"/a/filipe-pinto.com/projectx/system/app/pages/admin/revisions?wuid=wuid:gx:75be7fa19888b396\"
        #                \u003Eearlier versions\u003C\/a\u003E)","type":"text/plain",
        #  "url"       :"/a/filipe-pinto.com/projectx/load_test_2.txt?attredirects=0",
        #  "size"      :14,
        #  "displayNameOrEmail":"filipe pinto",
        #  "version"   :7,
        #  "timestamp" :1253543131831,
        #  "time"      :"Sep 21, 2009 7:25 AM",
        #  "title"     :"load_test_2.txt",
        #  "attachMsg" :"\u003Ca xmlns=\"http://www.w3.org/1999/xhtml\" href=\"/a/filipe-pinto.com/projectx/load_test_2.txt?attredirects=0\" dir=\"ltr\"\u003Eload_test_2.txt\u003C\/a\u003E 1k - on Sep 21, 2009 7:25 AM by filipe pinto",
        #  "path"      :"/load_test_2.txt",
        #  "parentPath":"/"}
        #
        ################################################################################################
        return True

    def delete(self,session):
        '''
        Synopsis:
            deletes an existing site
        Arguments:
            url needs to be populated
        Exceptions:
        Returns:
        '''
        #checkling for required attributes
        if self.url =='':
            self.error = 'Unable to delete site because URL was not defined'
            return False
        ###################################################################
        #
        #  Getting to Site General settings
        #
        ###################################################################          
        #defining uri
        uri = 'https://sites.google.com/a/'+ \
               session.domain_name + '/'   + \
               self.url                    + \
               '/system/app/pages/admin/settings'
        #defining headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #asserting correct page
        pattern='Delete this Site'
        results = re.findall(pattern, content)      
        if len(results)==0:
            #check whether Google returned any errors
            pattern = '<h2>(.*?)</h2>.*?<p>(.*)</p>'
            results = re.findall(pattern, content, re.S)
            if len(results)<>0:
                tmp_error = ''
                for result in results: tmp_error = tmp_error + '.' + result[0] + '.' + result[1]
                self.error = tmp_error
            else:
                self.error = self.__class__.__name__+'.'+ \
                             sys._getframe().f_code.co_name + \
                             ' @line:' + str(sys._getframe().f_lineno) + \
                             '\nUnable assert uri "%s" using pattern "%s" in content %s' % (uri,pattern,content)
            return False

        ###################################################################
        #
        #  Posting delete command
        #
        ###################################################################          
        #retrieving the sufix from the cookie jar
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                session.domain_name+'/'+self.url + '/system/services/deleteSite')
        '''
        uri_extension =''
        for cookie in session.cookiejar:
            if cookie.name == 'jotxtok': 
                uri_extension = cookie.value
                break
        uri = 'https://sites.google.com/a/'+session.domain_name+'/sites/system/services/deleteSite?jot.xtok=' + urllib.quote(uri_extension,'')
        '''
        #building json
        #json={"webspace":""}
        dict={'webspace':''}
        #defining the header
        headers['Content-Type'] = 'application/x-www-form-urlencoded' 
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting the request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##################################################################
        # Checking webservice reply
        # 
        # Expected result:  true 
        ##################################################################            
        if string.find(content,'true')==-1:   #doesn't find 'true'
            self.error = 'delete was not successful'
            return False
        else:
            return True

class GSitePage(SitePage):
    '''
    '''
    def __init__(self):
        super(GSitePage,self).__init__()
        self.type                   = 'text'
        self.is_show_page_title      = False
        self.is_show_sub_pages_links = False
        self.is_allow_attachments    = False
        self.is_allow_comments       = False
        self.layout                  = 'one-column'
        self.wuid                    = ''              #unique page identifier
        self.parent_wuid             = ''              #if NULL page in the root directory of the site
        self.revision                = None
        

        
    def _lock_page(self,session,site_url):
        '''
        Synopsis:
            Establishes a lock which is done by calling
            the "lockNode" webservice with the page's
            {"wuid":"wuid:gx:2a533374e74167e9"}.  This 
            will enforce that no one else is editing 
            the page of the same time.
        '''
        #veriufying mandatory attributes
        if self.wuid == '':
            self.error = 'Unable to establish a lock on the page because wuid is not defined'
            return False
        
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+\
                                         site_url +\
                                         '/system/services/lockNode' )        
        #building the json request
        #json={"wuid":"wuid:gx:2a533374e74167e9"}
        dict={'wuid':self.wuid}
        #define headers
        headers = WebTools.firefox_headers()
        #headers['Connection'  ] = 'keep-alive'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #headers['Referer'     ] = 'https://sites.google.com/a/'+ session.domain_name+'/'+\
        #                                 site_url + self.relative_uri
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #request = urllib2.Request(uri, jsonpickle.encode(data), headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ##################################################################
        # Checking webservice reply - returns a list
        #
        # [
        #  true,
        #  "ok",
        # {"revision" :1,
        #  "main/text":"\u003Ctable xmlns=\"http://www.w3.org/1999/xhtml\" cellspacing=\"0\" class=\"sites-layout-name-one-column sites-layout-hbox\"\u003E\u003Ctbody\u003E\u003Ctr\u003E\u003Ctd class=\"sites-layout-tile sites-tile-name-content-1 sites-layout-empty-tile\"\u003E \u003C\/td\u003E\u003C\/tr\u003E\u003C\/tbody\u003E\u003C\/table\u003E",
        #  "sys/layout":"one-column"}
        #  ]
        #
        ##################################################################        
        try:            
            list_items = string.split(content, ',')
            pattern='"(.*?)":"?(((?!"}|"$).)*)"?'
            ws_result={}
            for item in list_items[2:5]:
                tmp= re.findall(pattern,item)
                #ws_result[tmp[0][0]]=tmp[0][1].decode("unicode-escape")
                ws_result[tmp[0][0]]=tmp[0][1]
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         '\n@line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to unpickle JSON reply from Gateway WS to verify page creation request.' +\
                         '\nRaw message retrieved: ' + content +\
                         '\nException: ' + ex.message
            return False
        if string.find(list_items[0],'true')==-1:
            self.error = 'ws didn\'t return true'
            return False
        elif string.find(list_items[1],'ok')==-1:
            self.error = 'ws didn\'t return true'
            return False
        ###assigning values to the page
        self.content = ws_result['main/text']
        self.layout  = ws_result['sys/layout']
        self.revision= eval(ws_result['revision'])
        return True


    def _unlock_page(self,session,site_url):
        '''
        Synopsis:
            Releases a previously set lock (unlock)
            the "unlockNode" webservice with the page's
            {"wuid":"wuid:gx:2a533374e74167e9"}.
        '''
        #veriufying mandatory attributes
        if self.wuid == '':
            self.error = 'Unable to establish a lock on the page because wuid is not defined'
            return False
        
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+\
                                         site_url +\
                                         '/system/services/unlockNode' )        
        #building the json request
        #json={"wuid":"wuid:gx:2a533374e74167e9"}
        dict={'wuid':self.wuid}
        #define headers
        headers = WebTools.firefox_headers()
        #headers['Connection'  ] = 'keep-alive'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #headers['Referer'     ] = 'https://sites.google.com/a/'+ session.domain_name+'/'+\
        #                                 site_url + self.relative_uri
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #request = urllib2.Request(uri, jsonpickle.encode(data), headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ##################################################################
        # Checking webservice reply - returns a list
        #
        # false
        ##################################################################        
        if content <> 'false':
            self.error = 'unlock returned an expected result "%s" when looking for "false"' % content 
            return False
        else:
            return True

    def get(self,session,site_url):
        '''
        Synopsis:
            gets low level information of a page
        Arguments:
            session  - authenticated session
            site_url - site url
        Exceptions:
        Returns:
        '''
        #checking required attributes
        if self.relative_uri == '':
            self.error = 'Please define the relative uri'
            return False
        ###################################################################
        #
        #  Step 1 - Getting the page
        #
        ###################################################################
        #setting the uri
        uri='https://sites.google.com/a/' + session.domain_name + '/' +\
             site_url + self.relative_uri
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ###################################################################
        # assess current page
        ###################################################################
        pattern = 'webspace.page\s*?=\s*?(.*?);'
        results = re.findall(pattern, content)
        if len(results)==0: 
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable certify uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False
        else:
            try:
                webspace = jsonpickle.decode(results[0])
            except Exception,ex:
                self.error = self.__class__.__name__+'.'+ \
                             sys._getframe().f_code.co_name + \
                             '\n@line:' + str(sys._getframe().f_lineno) + \
                             '\nUnable to unpickle JSON webspace.' +\
                             '\nWebspace.page retrieved: ' + results[0] +\
                             '\nException: ' + ex.message
                return False
            else:
                try:
                    self.wuid         = webspace['wuid'    ]
                    self.revision     = webspace['revision']
                    self.title        = webspace['title'   ]
                    self.relative_uri = webspace['path'    ]
                    self.type         = webspace['type'    ]
                except Exception,ex:
                    self.error = self.__class__.__name__+'.'+ \
                                 sys._getframe().f_code.co_name + \
                                 '\n@line:' + str(sys._getframe().f_lineno) + \
                                 '\nUnable to assign results from dicitonary.' +\
                                 '\nWebspace.page retrieved: ' + results[0] +\
                                 '\nException: ' + ex.message
                else:                 
                    return True
            

    def post(self,session,site_url):
        '''
        Synopsis:
            Adds a page to the site passed.
            If the page already exists, the method returns False
        Arguments:
            session    : authenticated Google Hosted Account Session
            site_url   : the site's unique identifier (example: public)
        Exceptions:
        Returns:
            success
        '''      
        ###################################################################
        #
        #  Step 1 - checking section
        #           a) required attributes
        #           b) if page already exists
        #           c) if session already has the jot.xtok 
        #
        ###################################################################
        if self.get(session,site_url):
            self.error = 'Page already exists'
            return False
        #if GSiteHelper._is_jotxtok_definied(session)==-1:
        #    if not self._get_jotspot_token(session): return False
        ###################################################################
        #
        #  Step 2 - Getting to create new page 
        #
        ###################################################################         
        uri = 'https://sites.google.com/a/'+\
                   session.domain_name+'/'+site_url+\
                   '/system/app/pages/createPage?source=/home'
        #definng the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submiting GET
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #asserting correct page
        pattern='Create a new page'
        results = re.findall(pattern, content,re.IGNORECASE)      
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable certify uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False
        ###################################################################
        #
        #  Step 3 - Defining some of the page's metainfo.
        #
        ###################################################################        
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+\
                                         site_url +\
                                         '/system/services/gateway' )        
        #building the json request
        #json={"path"      :"/test",
        #      "properties":{"main/title":"test"},
        #      "pagetype":"text",
        #       "requestPath":"/a/filipe-pinto.com/test2/system/app/pages/createPage",
        #       "service":"CreateNode"}
        #
        #Notes:
        #   main/title represents the page name extracted from the uri (see regex below)
        dict={'path'       :self.relative_uri,
              'properties' :{'main/title':self.title},
              #'properties' :{'main/title':re.findall('/([^/]*?)$',self.relative_uri)[0]},
              'pagetype'   :self.type,
              'requestPath':'/a/' + session.domain_name + '/' + site_url+ '/system/app/pages/createPage', 
              'service'    :'CreateNode'}
        #define headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #request = urllib2.Request(uri, jsonpickle.encode(data), headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        ##################################################################
        # Checking webservice reply
        ##################################################################        
        try:
            ws_result = jsonpickle.decode(string.strip(content))
        except Exception,ex:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         '\n@line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to unpickle JSON reply from Gateway WS to verify page creation request.' +\
                         '\nRaw message retrieved: ' + content +\
                         '\nException: ' + ex.message
            return False
        else:   
            # reading the ws return values
            # {"revision":2,
            #  "time":"Aug 28, 2009 6:45 AM",
            #  "main/title":"test",
            #  "path":"/test",
            #  "wuid":"wuid:gx:2a533374e74167e9",
            #  "url":"/a/filipe-pinto.com/test2/test",
            #  "parentWuid":null}                         
            if not ws_result.has_key('wuid'):
                #look for errors in the page
                if ws_result.has_key('error'):
                    self.error = self.__class__.__name__+'.'+ \
                                 sys._getframe().f_code.co_name + \
                                '\n@line:' + str(sys._getframe().f_lineno) + \
                                '\n'+ws_result['error']
                else:
                    self.error=self.__class__.__name__+'.'+ \
                                 sys._getframe().f_code.co_name + \
                                '\n@line:' + str(sys._getframe().f_lineno) + \
                                '\nWS returned unexpected reply "%s" while looking for {"url":"normalized_uri"}.' % content
                return False
            else:
                #retrieveing page metadata
                self.wuid        = ws_result['wuid']
                self.parent_wuid = ws_result['parentWuid']             
        ###################################################################
        #    
        #  Step 4 - loading the new page just created.
        #        
        ###################################################################
        if not self.get(session,site_url):
            return False
        else:
            return True
        
    
    def put(self,session,site_url,content=None):
        '''
        Synopsis:
            updates an existing page.
        Arguments:
        Exceptions:
        Returns:
        '''   
        #checking for required attributes
        if self.wuid=='':
            self.error = 'you need wuid to change an existing page'
            return False
        if self.relative_uri =='':
            self.error = 'please define relative_uri'
            return False
        ###################################################################
        #    
        #  Step 1 - get a page lock
        #  
        ###################################################################            
        #setting uri
        if not self._lock_page(session,site_url):
            self.error = self.error + '\nUnable to establish a lock on the page'
            return False
          
        ###################################################################
        #    
        #  Step 2 - setting html
        #  
        ###################################################################            
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name + '/' + site_url + \
                                         '/system/services/editorSave' )   
        #################################################################################################        
        #building the json request
        #json ={"uri":"wuid:gx:5e29f75e6c7bf57a",
        #       "form":"/system/app/forms/DefaultForm",
        #       "properties":{"main/text":"<TABLE class=\"sites-layout-name-one-column ...</TBODY></TABLE>",
        #                     "main/title":"Home"},
        #       "requestPath":"/a/filipe-pinto.com/test33_url/home",
        #       "verifyLockRevision":1} 
        #################################################################################################
        page_properties = {'main/text'  : '<TABLE class=\"sites-layout-name-one-column sites-layout-hbox\" '+\
                                                  'cellSpacing=0 xmlns=\"http://www.w3.org/1999/xhtml\">\r\n'+\
                                                  '<TBODY>\r\n<TR>\r\n<TD class=\"sites-layout-tile sites-tile-name-content-1\" '+\
                                                  'id=sites-tile-name-content-1-editing>\r\n'+\
                                                  '<DIV dir=ltr>' + content + '</DIV></TD></TR>'+\
                                                  '</TBODY></TABLE>',
                           'main/title' : self.title}
        dict = {'uri'               : self.wuid,         
                'form'              : '/system/app/forms/DefaultForm',
                'properties'        : page_properties,
                'requestPath'       : '/a/'+session.domain_name+'/' + site_url + self.relative_uri,
                'verifyLockRevision': self.revision}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ##################################################################
        # Checking webservice reply by checking for the word error
        ##################################################################
        if string.find(content,'error')<>-1:
            self.error = content
            return False
        ###################################################################
        #    
        #  Step 3 - Set page settings
        #  
        ###################################################################  
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name + '/' + site_url + \
                                         '/system/services/savePageSettings' )         
        ####################################################################
        #building the json request        
        #json = {"wuid":"wuid:gx:774881fc656d78e2",
        #        "path":"/home",
        #        "navIds":[],
        #        "properties":{"config/showPageTitle":false,
        #                      "config/showComments":true,
        #                      "config/showAttachments":true,
        #                      "config/showSubpages":false}
        #       }
        ####################################################################            
        properties = {'config/showPageTitle'  : self.is_show_page_title,
                      'config/showComments'   : self.is_allow_comments,
                      'config/showAttachments': self.is_allow_attachments,
                      'config/showSubpages'   : self.is_show_sub_pages_links}
        dict = {'wuid'              : self.wuid,         
                'path'              : self.relative_uri,
                'navIds'            : [],
                'properties'        : properties}
        #define headers
        headers=WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #submitting request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ##################################################################
        # Checking webservice reply by checking for the word error
        # 
        # NOTE: Google doesn't return anything!!!!!
        ##################################################################
        if len(content)<>0:
            self.error = 'Expecting empty return, and instead received this ' + content
            return
        else:
            return True
    
    def delete(self,session,site_url,remove_children=True):
        '''
        Synopsis:
            deletes the current page and any associate 
            subpages.
        Arguments:
            session
            site_url
            remove_children
        Exceptions:
        Returns:
        '''
        #veriufying mandatory attributes
        if self.relative_uri== '':
            self.error = 'Unable to delete page without relative-uri defined'
            return False       
        ###########################################################################
        #
        # Step 1 - looking for subpages
        #
        #  json = {"path":"/test_page_7a","removeChildren":true}
        #
        ###########################################################################
        #setting uri
        uri = GSiteHelper._set_uri_token(session,'https://sites.google.com/a/'+\
                                         session.domain_name+'/'+\
                                         site_url +\
                                         '/system/services/delete' )        
        #building the json request
        dict={'path':self.relative_uri,'removeChildren':remove_children}
        #define headers
        headers = WebTools.firefox_headers()
        #headers['Connection'  ] = 'keep-alive'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, GSiteHelper._set_json(dict), headers=headers)
        #request = urllib2.Request(uri, jsonpickle.encode(data), headers=headers)
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = string.strip(response.read())
        ###########################################################################
        #
        # Asserting ws response (response equal to request minus 'json='
        #
        #  {"path":"/test_page_7a","removeChildren":true}
        #
        ###########################################################################            
        check_string = string.replace(jsonpickle.encode(dict),' ','')
        if content <> check_string:
            self.error = 'Delete page returned unexpcted message "%s" when looking for "%s"' %\
                          (content,check_string) 
            return False
        else:
            return True


class GOneCloudProfessional(OneCloudTemplate):
    '''
    Synopsis:
        This class represents the 3WC oneCloud
        Professional Edition Google site.
    '''    
    def __init__(self,email,password,root='Public',debug=False,over_write=False):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        super(GOneCloudProfessional,self).__init__()
        #private variables
        self._session          = GHSession(debug=debug)
        self._site             = GSite() 
        self.owner_email       = email
        self.owner_password    = password
        self.root              = root
        #getting a session
        self._session.email       = self.owner_email
        self._session.password    = self.owner_password
        if not self._session.get():
            raise Exception(self._session.error)
              
        #check if over write was defined. If so delete
        #existing site.
        if over_write:
            self._site.url = self.root
            self._site.delete(self._session)

        self.info = {'name'         :'oneCloud',
                     'edition'      :'Professional',
                     'release'      :1,
                     'logo'         :'http://3wcloud.com/images/logo/onecloud-individual-logo-thumb.png',
                     'provider'     : 'google'}
        
        self.pages = {'Home'     :
                     'Welcome to my oneCloud, my place on the web wide world.<br/>\
                      <br/><br/><br/><0br/><br/><br/><br/><br/>\
                      Powered by <a href="http://3wcloud.com"><img src=' + self.info['logo'] + '></a>',
                     'Blog'     :
                     '<a href="http://blog.filipe-pinto.com">My blog</a>',
                     'Books'    :
                     '',
                 'Calendar' :
                     '<iframe src="https://www.google.com/calendar/hosted/filipe-pinto.com/embed?height=600&amp;wkst=1&amp;bgcolor=%23FFFFFF&amp;src=filipe-pinto.com_6276hnh4liai1ivgtu2d3bgbj0%40group.calendar.google.com&amp;color=%23A32929&amp;ctz=America%2FNew_York" style=" border-width:0 " width="800" height="600" frameborder="0" scrolling="no"></iframe>',
                 'Expertise':
                     'Google App Engine <br/>\
                      Python <br/>\
                      Business Process Management <br/>\
                      Healthcare\
                      Market theory',
                 'Pictures' :
                     '<h1>My Pictures</h1>'  +\
                     '<h2>1994 - IST Graduation</h2>' +\
                     '<h2>1996 - 100,000 Vitaminas Activated for Vodafone</h2>' +\
                     '<h2>1998 - First successful billing cycle at Daleen Tech</h2>' +\
                     '<h2>2000 - Technical Project Manager at Daleen Tech</h2>' +\
                     '<h2>2001 - Director Customer Engineering</h2>' +\
                     '<h2>2004 - M2MSys comes to live</h2>' +\
                     '<h2>2005 - Best system in show for Healthcare</h2>' +\
                     '<h2>2007 - Market Management System takes shape</h2>' +\
                     '<h2>2009 - 3WCloud becomes a reality</h2>',
                 'Projects' :\
                     '<h1>My Projects</h1>'      +\
                     '<h2>3WCloud</h2>'          +\
                     '<h2>M2MSys</h2>'           +\
                     '<h2>SocialOrg</h2>'        +\
                     '<h2>HolisticThinkers</h2>',
                 'Resume'   :
                     '<h1><a name="TOC-Professional-Summary"></a>Professional Summary</h1>\
                      <p>Experienced information system architect, with over 17 years of professional\
                      experience, who increases the efficiency and effectiveness of the organization\
                      through the combination of technology and methodology. System Thinker intimately\
                      involved in the BPM industry as an architect, mentor, innovator</p>\
                      <p>For a copy of the resume in MS-Word please click here. For a detailed project\
                      list, please click here.',
                 'Social'   :\
                     '<a href="http://filipe-pinto.twitter.com">Twitter</a> <br/>\
                      <a href="http://filipe-pinto.slideshare.com">Slideshare</a><br/>\
                      <a href="http://filipepinto.delicious.com">Delicious</a><br/>\
                      <a href="http://filipepinto.LinkedIn.com">LinkedIn</a><br/>\
                      <a href="http://filipepinto.youtube.com">YouTube</a>',
                 'Videos'   :\
                     '<object width="425" height="344">\
                      <param name="movie" value="http://www.youtube.com/v/oBEWrlsl58Q&hl=en&fs=1&rel=0"></param>\
                      <param name="allowFullScreen" value="true"></param>\
                      <param name="allowscriptaccess" value="always"></param>\
                      <embed src="http://www.youtube.com/v/oBEWrlsl58Q&hl=en&fs=1&rel=0" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="425" height="344"></embed>\
                      </object>'
                 }

        
    def post(self,over_write=False):
        '''
        Synopsis:
            create site.
        '''
        ###################################################################
        #
        #Step 1 - create a new site
        #
        ###################################################################
        #create site
        self._site.description  = 'This is the %s %s\'s %s %s %s' % \
                                 (self.owner_first_name,self.owner_last_name,self.info['name'],self.info['edition'],self.info['release'])
        self._site.name         = 'OneCloud'
        self._site.is_public    = True
        self._site.tags         = self.tags
        self._site.twc_template = 'onecloud-Professional'
        self._site.google_theme = 'Iceberg' 
        success = self._site.post(self._session)
        if not success:
            self.error = self._site.error
            return False
        else:
            print 'successfully created site'
            
        ###################################################################
        #
        #Step 2 - configuring the site
        #
        ###################################################################        
        
        
        ###################################################################
        #
        #Step 2 - create the pages
        #
        ###################################################################        
        page = GSitePage()
        for key in self.pages.keys():
            
            page.relative_uri = '/'  + key 
            page.title        = 'My ' + key
            page.layout       = 'one-column'
            if key <> 'Home' : 
                success = page.post(self._session, self._site.url)
            else:
                success = page.get(self._session, self._site.url)
            #adding the correct content
            if success:
 
                page.is_allow_attachments    = False
                page.is_allow_comments       = False
                page.is_show_page_title      = False
                page.is_show_sub_pages_links = False
                success = page.put(self._session,self._site.url,content = self.pages[key])
                if not success:
                    self.error = page.error
                    return False
                else:
                    print 'Successfully created page: ' + key
            else:
                self.error = page.error
                return False

        ###################################################################
        #
        #Step 3 - Set site configurations
        #
        ###################################################################   
            
        return True     

        
if __name__ == '__main__':
    print 'Please revert to the test module'