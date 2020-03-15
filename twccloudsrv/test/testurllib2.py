'''
Created on Aug 26, 2009

@author: fpinto

This module should be used to thest the urllib2 library


'''
import re
import urllib
import cookielib
import urllib2
from twccloudsrv.util import WebTools 


class GDSession():
    '''
    '''
    def __init__(self, debug=False):
        '''
        constructor
        '''
        self.account_number = ''
        self.account_name   = '' 
        self.login_name     = ''
        self.password       = ''
        self.cookiejar      = cookielib.CookieJar()
        self.error          = ''
        self.debug          = None
        self.urlopener      = urllib2.OpenerDirector()
        
        debug_level = 0
        if debug:
            debug_level = 1
            self.debug = debug
        
        #building the urllib2 session opener
        try:
            self.urlopener.add_handler(urllib2.HTTPHandler(debuglevel=debug_level))
            self.urlopener.add_handler(urllib2.HTTPSHandler(debuglevel=debug_level))
            self.urlopener.add_handler(urllib2.HTTPRedirectHandler())
            self.urlopener.add_handler(urllib2.HTTPErrorProcessor())
            self.urlopener.add_handler(urllib2.HTTPCookieProcessor(self.cookiejar))
        except Exception, ex:
            self.error = 'unexpected error while defining session uri opener' + ex.message
            raise Exception(ex.message)
        
    def get(self):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''

        #setting the uri
        uri = 'https://www.google.com/a/filipe-pinto.com/ServiceLogin'
        
        #setting the headers
        headers = WebTools.firefox_headers()
       
        #defining the urllib2.opener
        
        '###################################################################'
        '#'
        '#  Getting to login form'
        '#'
        '###################################################################'

        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = self.urlopener.open(uri)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + e.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', e.code
                return False
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()

        '###################################################################'
        '#'
        '#  Asserting correct page'
        '#'
        '###################################################################'
                     
        #asserting we're on the right place
        pattern = '@'+self.domain_name
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False

        '###################################################################'
        '#'
        '#  Posting credentials'
        '#'
        '###################################################################'        
        
        #retrieve uri and hidden fields
        pattern = '<form id="gaia_loginform".*?</form>'
        form_html = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('gaia_loginform',pattern,content)
            return False
        #setting the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #retrieving uri
        pattern = 'action="(.*?)".*?method="post"'
        results = re.findall(pattern, content, re.S)
        if len(pattern)==0:
            self.error = 'Unable to find POSTing uri with %s in %s' % (pattern,content)
            return False
        else:
            uri = results[0]
        #Retrieving hidden attributes
        pattern='input.*?type=["|\']hidden["|\'].*?name=["|\'](.*?)["|\'].*?(id=["|\'].*?["|\'])*value=["|\'](.*?)["|\']'
        hidden_inputs = re.findall(pattern,form_html[0], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2]
        #for verification, these are the current hidden fields
        #data['GALX'           ] = 'NmJNLzKfR3g'
        #data['asts'           ] = ''
        #data['rmShown'        ] = '1'     
        data['Email'           ] = self.login_name
        data['Passwd'          ] = self.password
        data['PersistentCookie'] = 'yes'                #check box to stay signed in
        data['continue'        ] = 'https://www.google.com:443/a/cpanel/' + self.domain_name +'/Dashboard'
        data['service'         ] = 'CPanel'
        data['signIn'          ] = 'Sign in'        
        #defining the request
        request = urllib2.Request(uri, data=urllib.urlencode(data),headers=headers)
        try:
            response = self.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + e.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', e.code
                return False
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
        else:
            content = response.read()

        '###################################################################'
        '#'
        '#  Asserting correct page'
        '#'
        '###################################################################'
        
        pattern = 'id="CPanelMenuDashboard"'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        else:
            return True         
        
if __name__=='__main__':
    
    
    my_session = GDSession(debug=True)
    my_session.debug       = True
    my_session.login_name  = '*****'
    my_session.email       = '******'
    my_session.password    = '******'
    my_session.domain_name = '******'   
    success = my_session.get()
    if success:
        print 'SUCCESS!!!!!'
    else:
        print 'FAILED :-('
    
    
    