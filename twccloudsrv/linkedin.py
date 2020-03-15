'''
Created on Aug 7, 2009

@author: fpinto

Date      Author        Description
--------  ------------- ------------------------------------------


'''

from twccloudsrv.base import (ProviderSession,
                              ProviderAccount,
                              SocialConnectionService,SocialConnection,
                              QuestionService        , Question,
                              MicroBlogService       , MicroBlogEntry)
                              
from twccloudsrv.util import WebTools
import urllib2
import urllib
import re
import string
import sys
import cookielib
from BeautifulSoup import BeautifulSoup,SoupStrainer

#DEFAULTS
LI_DEFAULT_CONNECTION_SUBJECT = 'Invitation to connect to knowledge network'
LI_DEFAULT_CONNECTION_BODY    = 'I hope you\'re having a great day.\n because we have common\
                                 goals, I would like to add you to my network.\n\n\ If at\
                                 this time, you prefer not to accept my invitation,\
                                 please click \'ignore\' this request.\n\
                                 Thank you.'

class LiSession(ProviderSession):
    '''
    Synopsis:
        Represents a LinkedIn session
    Methods:
        get
    '''
    def __init__(self,debug=False):
        '''
        '''
        super(LiSession, self).__init__()
        self.cookiejar    = cookielib.CookieJar()
        self.urlopener    = urllib2.OpenerDirector()

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
            Returns a valid urlopener necessary for the 
            other classes to work.
        Arguments:
        Exceptions:
        Returns:
            success   : Boolean
        '''
        #checking for required attributes
        if   self.login_name=='':
             self.error = 'Please define login name'
             return False
        elif self.password=='':
             self.error = 'Please define password'
             return False
        
        ###################################################################'
        #
        #  Getting to login form'
        #
        ###################################################################'
        #setting the uri
        uri = 'https://www.linkedin.com/secure/login?trk=hb_signin'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = self.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #asserting correct page
        pattern = '<h1>Sign In to LinkedIn</h1>'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False 
        ###################################################################'
        #'
        #  Posting credentials
        #'
        ###################################################################'  
        #retrieve uri and hidden fields
        pattern = '<form action="(.*?)".*?name="login">'
        results = re.findall(pattern,content)
        if len(results)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('login',pattern,content)
            return False
        else:
            uri     = results[0]
        #retrieving cookie attributes
        for cookie in self.cookiejar:
            if cookie.name == 'JSESSIONID': session_id = cookie.value        
        #setting payload
        s1 = 'csrfToken='        + urllib.quote(session_id,safe='')
        s2 = 'session_key='      + self.login_name   
        s3 = 'session_password=' + self.password
        s4 = 'session_login='    + 'Sign+In'
        s5 = 'session_login='
        s6 = 'session_rikey='
        data = string.join([s1,s2,s3,s4,s5,s6],'&')
        #setting request headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri,data, headers=headers)
        try:
            response = self.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        # Getting uri for redirection
        pattern = '<a href="(.*?)" id="manual_redirect_link">'
        results = re.findall(pattern, content, re.S)
        if len(results)== 0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable redirect login using pattern %s in content %s' % (pattern,content)
            return False
        ###################################################################'
        #
        #  Manually redirecting
        #
        ###################################################################'
        uri = results[0]
        #setting the headers
        headers = WebTools.firefox_headers()
        headers['connection']='Keep-Alive'
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = self.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        #asserting correct page
        pattern = '<title>Home | LinkedIn</title>'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False
        return True      
        
class Account(ProviderAccount):
    '''
    Synopsis:
        Represents a LinkedIn account
    Arguments:
    Exceptions:
    Returns:
    '''
    
    def __init__(self):
        '''
        '''
        super(ProviderAccount,self).__init__()
        self.linked_connection=[]
        
    
    def post(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        pass
    
    def put(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''

class LiConnectionService(SocialConnectionService):
    '''
    Synopsis:
        Represents the configuration parameters
        of the configuration service.  Usually
        all connections establish to somewhat user
        configured parameters.
    '''
    def __init__(self):
        '''
        '''
        super(LiConnectionService,self).__init__()
        
    def put(self):
        '''
        Synopsis:
            Alters the defaults with which the 
            service is created by default.
        '''
        pass
    
class LiConnection(SocialConnection):
    '''
    Synopsis:
        Represents a connection
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        super(LiConnection,self).__init__()
        
    def get(self):
        '''
        Synopsis:
            Returns the details of one connection,
            usually should return the details of
            the connection, and a pointer to the
            account of the connection.
        '''
        pass
    
    def post(self,session,
             email_subject = LI_DEFAULT_CONNECTION_SUBJECT,
             email_body    = LI_DEFAULT_CONNECTION_BODY):
        '''
        Synopsis:
            Creates a new connection
        '''
        #############################################################################
        #
        # Step 1 - getting current on email invitations page
        #
        #############################################################################
        uri = 'https://www.linkedin.com/invite'
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
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        # Getting uri for redirection
        pattern = '<a href="(.*?)" id="manual_redirect_link">'
        results = re.findall(pattern, content, re.S)
        if len(results)== 0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable redirect login using pattern %s in content %s' % (pattern,content)
        #redirecting
        uri = results[0]
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
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()        
        #asserting correct page
        pattern = '<h1>Send Invitation</h1>'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False
        #############################################################################
        #
        # Step 2 - getting current on email invitations page
        #
        #############################################################################
        #retrieving uri and hidden attributes 
        form = 'invitation'
        pattern = SoupStrainer('form', {'name':form})
        node = BeautifulSoup(content, parseOnlyThese=pattern)
        if node==None:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find form % in content %s' % (form,content)
            return False
        else:
            #uri = node.form['action']
            inputs  = node.findAll('input',{'type':'hidden'})
            data=dict()
            for input in inputs:  data[input['name']]=input['value']
        '''
        Post:
        contentTemplateID    std_inv_9                  ->hidden
        csrfToken            ajax:3803862878444879164   ->hidden
        emailAddress         test2@test35.com           ->FORM
        firstName            test2                      ->FORM
        from                 default                    ->hidden
        greeting             email message              ->FORM
        invite               Send                       ->hidden
        inviteeID                                       ->hidden
        isMessageOptional    false                      ->hidden
        lastName             test3                      ->FORM
        subject              Subject                    ->FORM
        '''
        data['emailAddress']= self.email
        data['firstName'   ]= self.first_name
        data['lastName'    ]= self.last_name
        data['subject'     ]= email_subject
        data['greeting'    ]= email_body
        data['invite'      ]= 'send'
        #setting the headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri,urllib.urlencode(data),headers=headers)
        #submitting POST request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()
        '''
        confirmation message
        Invitation to test2 test3 (test2@test35.com) sent.
        '''
        #asserting correct page
        pattern = 'Invitation to %s %s \(%s\) sent' % (self.first_name, self.last_name, self.email)
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable assert uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False
        else:
            return True

class LiQuestionService(QuestionService):
    '''
    Synopsis:
        Represents the questions services
    '''
    pass

class LiQuestion(Question):
    '''
    Synopsis:
        Represents a Linkedin question
    '''
    
    def __init__(self):
        '''
        '''
        super(LiQuestion,self).__init__()
        
    
    def post(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        pass    

class LiGroup():
    '''
    Synopsis:
        Represents a LinkedIn Group
    Arguments:
    Exceptions:
    Returns:
    '''
    
    def __init__(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        pass
    
    def post(self):
        '''
        Synopsis:
            Creates a new connection between the 
            owner of the account, and a new email
            address and name
        Arguments:
        Exceptions:
        Returns:
        '''
        pass

class LiProfessionalExperience():
    '''
    Synopsis:
    Arguments:
    Exceptions:
    Returns:
    '''
    
    def __init__(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''
        pass
    
    def post(self):
        '''
        Synopsis:
            Creates a new connection between the 
            owner of the account, and a new email
            address and name
        Arguments:
        Exceptions:
        Returns:
        '''
        pass
     


class LiMicroBlogEntry(MicroBlogEntry):
    '''
    '''
    def __init__(self):
        '''
        '''
        super(LiMicroBlogEntry,self).__init__()
        

if __name__=='__main__':
    print 'hello'