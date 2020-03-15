'''
Created on Aug 23, 2009

@author: fpinto

Synopsis:
    This module was created to test the urllib2 functionality.
    It uses both automated redirection and cookie management,
    and manual management.
'''

import re
import sys
import string
from time import *
from twccloudsrv.util import duration
import urlparse
import httplib
import urllib
import urllib2
from cookielib import CookieJar 
from twccloudsrv.util import WebTools


class GDSession():
    '''
    '''
    def __init__(self):
        '''
        constructor
        '''
        self.account_number = ''
        self.account_name   = '' 
        self.login_name     = ''
        self.password       = ''
        self.cookiejar      = CookieJar()
        self.debug          = False
        self.error          = ''
        
    def get(self):
        '''
        Synopsis:
            Returns a cookie jar
        '''
        debug_level = 0
        if self.debug: debug_level = 1
    
        opener = urllib2.build_opener(
                            urllib2.HTTPHandler(debuglevel=debug_level),
                            urllib2.HTTPSHandler(debuglevel=debug_level),
                            urllib2.HTTPCookieProcessor(self.cookiejar))

        urllib2.install_opener(opener)
        
        uri = 'http://www.godaddy.com/default.aspx' 
        headers = WebTools.firefox_headers()
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            btm = time()
            response = urllib2.urlopen(request)
            etm = time()
            print 'GET - ' + duration(btm,etm) + ' uri = ' + uri
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + e.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', e.code
                return False
                print 
        except:
            self.error = "Unexpected error:", sys.exc_info()[0]

        #retrieving CORPWEB value
        response_headers = response.info()
        pattern='server=(CORPWEB[0-9]*?)&'
        details = re.findall(pattern,response_headers['set-cookie'])
        if len(details)== 0:
            error = 'Unable to determine CORPWEB'
            sys.exit()
        corp_web = details[0]            

        #Request uri
        scheme   = 'https'
        netloc   = 'idp.godaddy.com'
        url      = '/login.aspx'
        params   = ''  
        q1       = 'ci=9160'
        q2       = 'prog_id=GoDaddy'
        q3       = 'spkey=GDSWNET-'+ corp_web  
        q4       = 'signalnonorig=https://mya.godaddy.com/login_redirect.aspx' 
        query    = string.join([q1,q2,q3,urllib.quote(q4,safe='')],'&')
        fragment = ''
        #setting request headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #headers['Referer'     ] = response['content-location']
        headers['Host'        ] = netloc
        #setting uri
        uri = urlparse.urlunparse((scheme, netloc, url, params, query, fragment))
        #setting request body 
        data = dict()
        data['Login.x'    ] = '0'   
        data['Login.y'    ] = '0'
        data['login_focus'] = 'false'
        data['loginname'  ] = self.login_name
        data['pass_focus' ] = 'true'
        data['password'   ] = self.password
        data['validate'   ] = '1'
        
        #defining the request
        request = urllib2.Request(uri, data=urllib.urlencode(data),headers=headers)
        
        #submitting request
        try:
            btm = time()
            response = urllib2.urlopen(request)
            etm = time()
            print 'POST CREDENTIALS - ' + duration(btm,etm) + ' uri = ' + uri
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + e.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', e.code
                return False
                print 
        except:
            self.error = "Unexpected error:", sys.exc_info()[0]
                    
        headers.pop('Content-Type') 

        #asserting success
        pattern = '(User Name|Customer Number): <strong>(.*?)</strong>'
        details = re.findall(pattern, response.read(), re.S)
        if len(details)== 2:
            self.account_name   = details[0][1]
            self.account_number = details[1][1]
            return True
        else:
            return False


class VoidHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        return None



class DNSSession():
    '''
    Synopsis:
        Represents a TotalDNS system session.
    Methods:
        get
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        self.login_name    = ''
        self.password      = ''
        self.email         = ''
        self.dns_session   =''
        self.domain_name   =''
        self.gd_session    = None
        self.html          =''
        self.headers       = None
        self.error         = ''

    def get(self):
        '''
        Synopsis:
            Returns a session to the DNS System
        Arguments:
            domain_name
            godaddy_session
            debug
        Exceptions:
        Returns:
            Success:
        '''
        if self.domain_name =='' or self.gd_session is None:
            if self.current_domain=='':
                self.error = 'please define a domain'
                return False
            if self.gd_session is None:
                self.error = 'please get a godaddy login first' 
                return False
            
        #creating DNS Session cookiejar
        #self.cookiejar = cookielib.CookieJar
        
        #copying the cookie jar settins of GD Session to DNS Session
        self.cookiejar = self.gd_session.cookiejar
            
        debug_level = 0
        if self.debug: debug_level = 1
        
        opener = urllib2.build_opener(
                            urllib2.HTTPHandler(debuglevel=debug_level),
                            urllib2.HTTPSHandler(debuglevel=debug_level),
                            urllib2.HTTPCookieProcessor(self.cookiejar))

        urllib2.install_opener(opener)        

        headers = WebTools.firefox_headers()

        print '**************************************************'
        print '*'
        print '* Getting hidden fields from domain page to post to dNS'
        print '*'
        print '**************************************************'

        uri = 'https://dcc.godaddy.com/DomainDetails.aspx?domain=' + self.domain_name 
        #headers['cookie']= self.gd_session.session
        headers['Host'  ]= urlparse.urlparse(uri)[1]
        request = urllib2.Request(uri,headers=headers)
        
        #submitting GET request
        try:
            btm = time()
            response = urllib2.urlopen(request)
            etm = time()
            print 'GET - ' + duration(btm,etm) + ' uri = ' + uri
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + e.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', e.code
                return False
                print 
        except:
            self.error = "Unexpected error:", sys.exc_info()[0]        

        print '**************************************************'
        print '*'
        print '* Getting to DNS domain page'
        print '*'
        print '**************************************************'        

        uri = 'https://dcc.godaddy.com/DomainDetails.aspx?domain=' + self.domain_name
        #headers['cookie'] = self.gd_session.session
        headers['Host'  ] = urlparse.urlparse(uri)[1]
        #retrieving hidden attributes
        pattern = '<input type="hidden" name="(.*?)" id=".*?" (value="(.*?)"|value="")'
        fields = re.findall(pattern, response.read())
        if len(fields)==0 :
            self.error = 'could NOT find hidden fields'
            return False
        data = dict()
        for field in fields: data[field[0]]= field[2]
        data['SearchNewDomainText'                             ]= ''
        data['ctl00$cphMain$ctlDomainSearch$SearchNewDomainTLD']= re.findall('.*?\.(.*?)',self.domain_name)[0]
        data['ctl00$cphMain$hdnDeleteHostID'                   ]=''   
        data['ctl00$cphMain$hdnErrorDetails'                   ]=''   
        data['ctl00$cphMain$hdnErrorMessage1'                  ]=''    
        data['ctl00$cphMain$hdnErrorMessage2'                  ]=''    
        data['ctl00$cphMain$hdnErrorTitle'                     ]='' 
        data['ctl00$cphMain$hdnShowOkButton'                   ]=''   
        data['ctl00$hdnResizeColumnViewType'                   ]=''   
        data['ctl00$hdnTransferResizeColumns'                  ]=''    
        data['ctl00$txtDomainName'                             ]= self.domain_name
        data['__EVENTTARGET'                                   ]= 'ctl00$cphMain$lnkTotalDnsManager'
        #submit post
        headers['Referer'     ] = uri
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        request = urllib2.Request (uri,urllib.urlencode(data), headers=headers)
        
        #submitting POST request
        try:
            btm = time()
            response = urllib2.urlopen(request)
            etm = time()
            print 'Finalized POST Redirections - ' + duration(btm,etm) + ' uri = ' + uri
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + e.reason
                return False 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', e.code
                return False
                print 
        except:
            self.error = "Unexpected error:", sys.exc_info()[0] 

        print '**************************************************'
        print '*'
        print '* Asserting correct page'
        print '*'
        print '**************************************************'  
        btm = time()
        pattern = '<h2.*?class="pagetitle".*?>.*?' + self.domain_name + '.*?</h2>'
        results = re.findall(pattern, response.read(), re.S)
        etm = time()
        print 'Finalized ASSERTION of correct DNS page - ' + duration(btm,etm) + ' uri = ' + uri
        if len(results)==0:
            self.error = 'unable to determine whether login was successful'
            return False
        return True

if __name__=='__main__':
    
    print '**************************************************'
    print '*'
    print '* loging in to Godaddy'
    print '*'
    print '**************************************************'
    start_time = time()
    gd_session = GDSession()
    #gd_session.debug = True
    gd_session.login_name = '27484909'        #'nealwalters'
    gd_session.password   = 'salena1976'          #'godad21214'
    btm = time()
    success = gd_session.get()
    etm= time()
    if not success:
        print __name__ + 'test duration: ' + duration(btm,etm)
        print 'Godaddy Login failed'
        print 'Error :' + gd_session.error
    else:
        print 'LOGIN TO MAIN GODADDY ACCOUNT TOOK ------------>: ' + duration(btm,etm)
        print 'Account Name   : ' + gd_session.account_name
        print 'Account Number : ' + gd_session.account_number


        print '**************************************************'
        print '*'
        print '* loging in to DNSSession'
        print '*'
        print '**************************************************'
        dns_session = DNSSession()
        dns_session.debug = True
        dns_session.gd_session = gd_session
        dns_session.domain_name = 'hollyparrish.com'
        btm = time()
        success = dns_session.get()
        etm= time()
        if not success:
            print 'LOGIN TO DNS TOOK ------------>:' + duration(btm,etm)
            print 'Godaddy Login failed'
            print 'Error :' + dns_session.error
        else:
            print 'LOGIN TO DNS TOOK ------------>:' + duration(btm,etm)
            print 'success'
            end_time = time()
            print '\r\n\r\nOVERALL TEST TOOK:' + duration(start_time,end_time)
