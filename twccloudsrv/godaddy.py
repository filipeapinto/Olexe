'''
Created on Jul 3, 2009

@author: fpinto

This modules contains the classes that will allow
to create and update the Godaddy services.

TODO:

Date      Author        Description
--------  ------------- -------------------------------------------------------
10-05-09  fpinto        Removed from the file the defaulst that now are loaded
                        from the provisioning engine (client)
10-05-09  fpinto        Corrected defects spotted through unit testing.
                        Started using BeautifulSoup to parse HTML
                        
                        

'''

#cumulus imports\
from twccloudsrv.base import ProviderPotentialDomain
from twccloudsrv.base import ProviderShoppingCart
from twccloudsrv.base import ProviderSession
from twccloudsrv.base import ProviderAccount
from twccloudsrv.base import DomainService
from twccloudsrv.base import DNSRecord as DNSRecordBase
from twccloudsrv.util import WebTools

#built-in imports
import uuid
import string
import random
import re
import urlparse
import os
import logging
import time
import urllib2
import sys
import urllib
import httplib
import jsonpickle
import cookielib

from BeautifulSoup import BeautifulSoup,SoupStrainer

#3WC CONSTANTS
TWC_FIRST_NAME     = '*'
TWC_LAST_NAME      = '*'
TWC_MOBILE_PHONE   = '*'
TWC_PAYMENT_NUMBER = '*'
TWC_PAYMENT_M_EXP  = '*'
TWC_PAYMENT_Y_EXP  = '*'
TWC_PAYMENT_TYPE   = '*'
TWC_ADDRESS1       = '*'
TWC_CITY           = '*'
TWC_ZIP            = '*' 
TWC_EMAIL          = '*'
#GODADDY CONSTANTS
GODADDY_3WC_MOBILE_PHONE_PROVIDER =['1'] #other in the drop down
GODADDY_PASSWORD_HINT             = 'Please use your onecloud password'
GODADDY_DOMAIN_MAX_RECS           = 5
#GODADDY_SESSION_FILTER =['gdMyaHubble1','MemAuthId1','ShopperId1','MemShopperId1','ASP.NET_SessionId']
GODADDY_DOMAIN_RESERVATION_PERIOD = '1'  #1 year
#ONECLOUD CONSTANTS
ONECLOUD_DEFAULT_DOMAIN='com'


class GdSession(ProviderSession):
    '''
    Synopsis:
        Represents a Godaddy session
    Methods:
        get
    '''
    def __init__(self,debug=False):
        '''
        '''
        super(GdSession, self).__init__()
        self.account_name   = ''
        self.account_number = ''
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
        uri = 'http://www.godaddy.com/default.aspx'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
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
            return False
        else:
            content = response.read()
            
        ###################################################################'
        #'
        #  Posting credentials'
        #'
        ###################################################################'  
        
        #retrieve uri and hidden fields
        pattern = '<form.*?id="pchFL".*?action="(.*?)"(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('gaia_loginform',pattern,content)
            return False
        else:
            uri     = string.replace(results[0][0],';','&')
            content = results[0][1]
        #Retrieving hidden attributes
        pattern='input.*?type=["|\']hidden["|\'].*?name=["|\'](.*?)["|\'].*?(id=["|\'].*?["|\'])*value=["|\'](.*?)["|\']'
        hidden_inputs = re.findall(pattern,content, re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2]
        #data['validate'   ] = '1'      #hidden attribute
        #data['login_focus'] = 'false'  #hidden attribute
        #data['pass_focus' ] = 'true'
        data['Login.x'    ] = '0'   
        data['Login.y'    ] = '0'
        data['loginname'  ] = self.login_name
        data['password'   ] = self.password
        #setting request headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri,urllib.urlencode(data), headers=headers)
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
        ###################################################################'
        #'
        #  Asserting correct page'
        #'
        ###################################################################'
        pattern = '(User Name|Customer Number): <strong>(.*?)</strong>'
        details = re.findall(pattern, content, re.S)
        if len(details)== 2:
            self.account_name   = details[0][1]
            self.account_number = details[1][1]      
            return True
        else:
            pattern = 'Authentication failed. Please try again.'
            result = re.findall(pattern, content)
            if len(result) == 1:
                self.error = 'authentication Failed'
                return False
            else:
                self.error = 'Unable to assert why login failed'
                return False                 


class PotentialDomain(ProviderPotentialDomain):
    '''
    Synopsis:
        Represents a domain that has yet to be claimed
        by anyone, or that has POTENTIAL to become a 
        real domain service.
    Methods:
        get
    '''
    def __init__(self):
        super(PotentialDomain,self).__init__()
        self.cookiejar = cookielib.CookieJar()

    def get(self):
        '''
        Synopsis:
            Determines whether a domain is available. If
            not available and user passed suggestions []
            it will return a list with suggestions
        Arguments:
        Exceptions:
        Returns
            success : boolean
        '''
        debug_level=0
        if self.debug: debug_level = 1
        
        
        opener = urllib2.build_opener(
                            urllib2.HTTPHandler(debuglevel=debug_level),
                            urllib2.HTTPSHandler(debuglevel=debug_level),
                            urllib2.HTTPCookieProcessor(self.cookiejar))

        urllib2.install_opener(opener)
        
        headers = WebTools.firefox_headers()
        
        #######################################################
        #
        # Getting Godaddy home page
        #
        #######################################################
        
        #defining uri
        uri = 'http://www.godaddy.com/default.aspx' 
        
        #defining request
        request = urllib2.Request(uri,headers=headers)
        
        #submitting GET request
        try:
            response = urllib2.urlopen(request)
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

        #######################################################
        #
        # Submitting the domain name using form name pchFS
        #
        #######################################################
        content = response.read()
        #Retrieve form
        pattern = '<form.*?name="pchFS".*?</form>' 
        form_html = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        #retrieving uri
        pattern='<input.*?type="hidden".*?name="pch_sdomain_action".*?value="(.*?)"'
        results = re.findall(pattern,content, re.S)
        if len(results) == 0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        uri = string.replace(results[0],';','&')
        #Retrieving hidden attributes
        pattern='input.*?type="hidden".*?name="(pch.*?)".*?value="(.*?)"'
        hidden_inputs = re.findall(pattern,form_html[0], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden field with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[1]         
        data['domainToCheck'            ]= self.domain_name
        
        #getting current on the right page       
        headers['Referer'     ] = uri
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Host'        ] = urlparse.urlparse(uri)[1]

        #defining the request
        request = urllib2.Request(uri,urllib.urlencode(data), headers=headers)

        #submitting GET request
        try:
            response = urllib2.urlopen(request)
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
    
        #######################################################
        #
        # Asserting domain availability
        #
        #######################################################
        content = response.read()
        pattern = '<(span|b) class="(red|black)">(.*?) is (.*?).</(span|b)>'
        results = re.findall(pattern, content, re.IGNORECASE)
        if len(results) == 0:
            self.error = 'Unable to see if domain is taken or not'
            return False
        elif len(results[0]) <= 3:
            self.error = 'Wrong page?'
            return False
        elif results[0][3] =='available':
            self.is_available = True
            return True
        if results[0][3]=='already taken':
            self.is_available = False
            #checking for alternative domain names
            pattern = 'id="ctl00_MainContent_ucVerticalStripMall2_rptCrossCheckDomains_ctl[0-9]{2}_hfDomain".*?value="(.*?)\|'
            results = re.findall(pattern,content,re.S)
            if len(results)== 0:
                self.error= 'Unable to parse alternative domain names'
                return False
            else:
                self.alternative_names = results
                return True

class ShoppingCart(ProviderShoppingCart):
    '''
    Synopsis:
        Represents a shopping cart
    Methods:
        Delete
    '''
    def __init__(self):
        '''
        constructor
        '''
        super(ShoppingCart,self).__init__()
    
    def get(self,session):
        '''
        Synopsis:
        Arguments:
        Exceptions:
        Returns:
        '''

        #Setting the uri
        uri = 'https://cart.godaddy.com/Basket.aspx'        
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri,headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
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
        ###################################################################
        #
        #  Asserting correct page
        #
        ################################################################### 
        pattern = '<title>.*?GoDaddy.com : Shopping Cart.*?</title>'
        results = re.findall(pattern, content, re.S)
        if len(results)==0:
            self.error = 'Unable to reach the Shopping Cart page'
            return False
        
        pattern = '<div class="cellPadd ItemName t12">(.*?)<'
        details  = re.findall(pattern, content, re.S)
        if len(details)==0:
            return True
        else:
            for detail in details : self.items.append(detail)
            return True

    def delete(self,session):
        '''
        Synopsis:
            Removes from the shopping cart all domains.
        Arguments:
            session : current active session
        Exceptions:
        Returns:
            Success: whether operation was successful
            Error  : list of errors from POST method
        '''        
        #Setting the uri
        uri = 'https://cart.godaddy.com/Actions/EmptyCart.aspx'
        #setting headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'  ] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri,{},headers=headers)
        #submitting POST request
        try:
            response = session.urlopener.open(request)
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

        ###################################################################
        #
        #  Asserting cart is empty
        #
        ################################################################### 
        pattern = 'Your Shopping Cart is Empty'
        results = re.findall(pattern, content, re.S)
        if len(results)>0 :
            return True
        else:
            self.error = 'Unable to confirm that the cart was deleted'
            return False       

class GdDNSRecord(DNSRecordBase):
    '''
    Synopsis:
        This class represents a DNS record
    '''
    def __init__(self,values=None):
        '''
        Creates a new DNS Record
        '''
        super(GdDNSRecord, self).__init__()
        #self.uid = ''
        #self.domain_name=''
        
    @staticmethod
    def _dns_type(type):
        '''
        Synopsis:
            Returns the DNS type based on the Godaddy
            total DNS definition
        Arguments:
            Type  : string
        Exceptions:
        Returns:
            The DNS type
        '''
        if type == 'CNAMES (Aliases)' or type=='CNAME':
            return 5
        elif type == 'MX (Mail Exchange)' or type=='MX':
            return 15
        elif type == 'NS (Name Servers)':
            return 2
        elif type == 'A (Host)' or type =='ARecord':
            return 1
        elif type == 'TXT (Text)':
            return 16
        elif type == 'SRV (Service)':
            return 33
        elif type == 'AAAA':
             return 28
         
    def _get_current(self,session,domain_name):
        '''
        Synopsis:
            This function logs into the DNS record system.
        Arguments:
        Exception:
        Returns:
            Boolean
            response.read
        '''
        ##################################################################
        #
        # Step 1 - getting current on the domains page
        #
        ##################################################################
        #setting the uri
        uri = 'https://dcc.godaddy.com/DomainDetails.aspx?domain=' + domain_name
        #setting the headders
        headers = WebTools.firefox_headers()
        #setting the request
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
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message 
            return False
        else:
            content = response.read()
        ##################################################################
        #
        # Step 2 - loging into the DNS record system
        #
        ##################################################################
        #retrieving hidden attributes
        pattern = '<input type="hidden" name="(.*?)" id=".*?" (value="(.*?)"|value="")'
        fields = re.findall(pattern, content)
        if len(fields)==0 :
            self.error = 'could NOT find hidden fields'
            return False
        data = dict()
        for field in fields: data[field[0]]= field[2]
        data['SearchNewDomainText'                             ]= ''
        data['ctl00$cphMain$ctlDomainSearch$SearchNewDomainTLD']= re.findall('.*?\.(.*?)',domain_name)[0]
        data['ctl00$cphMain$hdnDeleteHostID'                   ]=''   
        data['ctl00$cphMain$hdnErrorDetails'                   ]=''   
        data['ctl00$cphMain$hdnErrorMessage1'                  ]=''    
        data['ctl00$cphMain$hdnErrorMessage2'                  ]=''    
        data['ctl00$cphMain$hdnErrorTitle'                     ]='' 
        data['ctl00$cphMain$hdnShowOkButton'                   ]=''   
        data['ctl00$hdnResizeColumnViewType'                   ]=''   
        data['ctl00$hdnTransferResizeColumns'                  ]=''    
        data['ctl00$txtDomainName'                             ]= domain_name
        data['__EVENTTARGET'                                   ]= 'ctl00$cphMain$lnkTotalDnsManager'
        #submit post
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
        #submitting GET request
        try:
            response = session.urlopener.open(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                self.error= 'Failed to reach a server. ' + 'Reason: ' + ex.reason
                return False, None 
            elif hasattr(ex, 'code'):
                self.error= 'Server couldn\'t fulfill the request. ' + 'Error code: ', ex.code
                return False, None
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False, None
        else:
            return True, response.read()         
    
    def post(self,session,domain_name,overwrite=False):
        '''
        Synopsis:
            creates a new DNS Record, or due to performance reasons
            a list of DNS records.
        Arguments:
           domain_name : domain name (example: filipe-pinto.com)
           overwrite   : boolean - determines if record is overwritten
        Returns:
            success
        '''
        #checking authorized updates
        if self.type not in (5,15):
            self.error = 'API not currently updating that DNS record'
            return False
        ##################################################################
        #
        # Step 1 - Getting current in DNS system
        #
        ##################################################################
        success, content = self._get_current(session,domain_name)
        if not success: return False
        ##################################################################
        #
        # Step 2 - Checking if domain already exists
        #
        ##################################################################
        if self.type == 5:
            pattern = '<td class=\'rr\'.*?>' + self.name + '</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?'
            results = re.findall(pattern, content, re.S)
            if len(results)> 0 and not overwrite:
                self.error = 'DNS record with that name already exists. Please update or delete the existing record'
                return False
        #checking TTL
        if self.TTL == -1:
            self.TTL = 3600
        ##################################################################
        #
        # Step 3 - Creating DNS Record
        #
        ##################################################################
        #setting uri
        uri = 'https://tdns.secureserver.net/doAction.php'
        #setting headers
        headers = WebTools.firefox_headers()
        headers['Content-Type']= 'application/x-www-form-urlencoded'
        #setting body
        if   self.type ==  5 : form_name = 'cnameedit'
        elif self.type == 15 : form_name = 'mxrecordedit' 
        html = re.findall('<form name="'+form_name+'".*?</form>',content, re.S)
        fields = re.findall('input type="hidden" name="(.*?)" id=".*?" (value=""|value="(.*?)")',html[0])
        data = dict()
        for field in fields: data[field[0]]=field[2]
        if self.type == 5:             #CNAME
            #retrieve hidden fields
            data['cdata'     ]= self.rdata
            data['chost'     ]= self.name
            data['cttl'      ]='3600'
            data['cok.x'     ]='12'
            data['cok.y'     ]='10'
        elif self.type == 15:            #MX record
            data['mdata'     ]= self.rdata
            data['mhost'     ]= self.name
            data['mpriority' ]= str(self.priority)
            data['mttl'      ]= str(self.TTL)
            data['mok.x'     ]='22'
            data['mok.y'     ]='5'
            data['mpselect'  ]= str(self.priority)
        #posting
        #submit post
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()         
        #assert if DNS record was properly created
        results = re.findall(self.name,content)
        if len(results)>0 :
            return True
        else:
            self.error = 'DNS record was NOT created'
            return False

    def delete(self,session,domain_name):
        '''
        Synopsis:
            Deletes a DNS Record 
        '''
        #checking authorized updates
        if self.type not in (5,15):
            error = 'API not currently deleting that DNS type record'
            return False
        ##################################################################
        #
        # Step 1 - Getting current in DNS system
        #
        ##################################################################
        success, content = self._get_current(session,domain_name)
        if not success: return False
        ##################################################################
        #
        # Step 2 - Deleting DNS record
        #
        ##################################################################        
        #setting uri
        uri = 'https://tdns.secureserver.net/doDelete.php'
        #setting body 
        if self.type ==  5:
            string = 'cname'
            pattern = '<td class=\'rr\'.*?>'+self.name+'</td>.*?<form name="cdel_(.*?)".*?value="'+ string +'".*?</form>'
        elif self.type == 15:
            string = 'mxrecord'
            pattern = '<td class=\'rr\'.*?>'+self.rdata+'</td>.*?<form name="mdel_(.*?)".*?value="'+ string +'".*?</form>'
        html = re.findall(pattern,content,re.S)
        if len(html)==0:
            if self.type==5 : self.error = 'CNAME record %s was not found with pattern %s in content %s!' % (self.name,pattern,content)
            if self.type==15: self.error = 'MX record %s was not found with pattern %s in content %s!' % (self.rdata,pattern,content)
            return False
        data = dict()
        data['dtype']=string
        data['did'  ]=html[0]
        #setting the headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()         
        #assert if DNS record was properly deleted
        pattern = '<td class=\'rr\'.*?>'+self.name+'</td>.*?<em>Pending Removal</em>.*?</tr>'
        results = re.findall(pattern,content,re.S)
        if len(results)>0:
            self.error = 'Delete is pending removal'
            return True
        else:
            self.error = 'Record was NOT deleted and it is still listing as valid.'
            return False

    def _zap(self,session,domain_name):
        '''
        Synopsis:
            Deletes all CNAMES and MX Records of 
            a domain
        Arguments:
            domain name
        Exceptions:
        Returns:
        '''
        ##################################################################
        #
        # Step 1 - Getting current in DNS system
        #
        ##################################################################
        success, content = self._get_current(session,domain_name)
        if not success: return False
        ##################################################################
        #
        # Step 2 - getting the list of DNS records
        #
        ##################################################################
        #retrieving complete domain information
        pattern='<td class=\'rrHeading\' width.*?>(MX \(Mail Exchange\)|CNAMES \(Aliases\))</td>.*?<table.*?>(.*?)</table>'
        servers =re.findall(pattern, content, re.S)
        for server in servers:
            if not server[0]=='MX (Mail Exchange)':
                pattern='<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?'
            else:
                pattern='<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>'
            recs=re.findall(pattern, server[1], re.S)
            
            ##################################################################
            #
            # Step 3 - Deleting DNS record
            #
            ##################################################################        
            for rec in recs:
                if  server[0]=='CNAMES (Aliases)':
                    string = 'cname'
                    pattern = '<td class=\'rr\'.*?>'+rec[0]+'</td>.*?<form name="cdel_(.*?)".*?value="'+ string +'".*?</form>'
                elif server[0]=='MX (Mail Exchange)':
                    string = 'mxrecord'
                    pattern = '<td class=\'rr\'.*?>'+rec[2]+'</td>.*?<form name="mdel_(.*?)".*?value="'+ string +'".*?</form>'
                #setting uri
                uri = 'https://tdns.secureserver.net/doDelete.php'
                #setting body 
                html = re.findall(pattern,content,re.S)
                if len(html)==0:
                    if self.type==5 : self.error = 'CNAME record %s was not found with pattern %s in content %s!' % (self.name,pattern,content)
                    if self.type==15: self.error = 'MX record %s was not found with pattern %s in content %s!' % (self.rdata,pattern,content)
                    return False
                data = dict()
                data['dtype']=string
                data['did'  ]=html[0]
                #setting the headers
                headers = WebTools.firefox_headers()
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                #defining the request
                request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
                        print 
                except Exception,ex:
                    self.error = "Unexpected error:" + ex.message
                    return False
                else:
                    content = response.read()         
                #assert if DNS record was properly deleted
                pattern = '<td class=\'rr\'.*?>'+self.name+'</td>.*?<em>Pending Removal</em>.*?</tr>'
                results = re.findall(pattern,content,re.S)
                if len(results)==0:
                    self.error = 'Record was NOT deleted and it is still listing as valid.' 
                    return False
        return True

class GdDomain(DomainService):
    '''
    Synopsis:
        This class represents a domain
    Methods:
        POST - creates a new domain
        PUT  - updates certain information of a domain
        GET  - gets certain information on the domain
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        super(GdDomain, self).__init__()
        #Godaddy specific attributes
        self.domain_public_id = ''
        self.message          = ''
        
    def get(self, session, deep=False):
        '''
        Synopsis:
            Returns domain informaiton.
        Arguments:
            deep    : indicates if the get goes into the TotalDNS system
        Exceptions:
        Returns:
            success : boolean
        '''
        #verifying required attributes
        if self.domain_name=='':
            self.error = 'Please define domain name'
            return False
        #Request uri
        uri = 'https://dcc.godaddy.com/DomainDetails.aspx?domain=' + self.domain_name
        #setting the headders
        headers = WebTools.firefox_headers()
        #setting the request
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
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message 
            return False
        else:
            content = response.read()
        #getting the domain information
        items = '(DomainCreateDate|DomainExpirationDate|Forwarding|DomainStatus)'
        pattern = 'span id="ctl00_cphMain_lbl(' + items + ')">(.*?)</span>'
        domain_items = re.findall(pattern, content, re.S)
        if len(domain_items) ==0 :
            self.error = 'unable to parse domain information with ' + pattern + ' for domain ' + self.domain_name
            return False
        self.registration_date = domain_items[0][2]
        self.expiration_date   = domain_items[1][2]
        self.status            = domain_items[2][2]
        self.forwarding        = domain_items[3][2]
        
        ###################################################
        #getting the dns records information
        ###################################################
        if not deep:
            pattern = '<td.*?>(ARecord|MX|CNAME)</td>.*?<td.*?>(.*?)</td>.*?<td>(.*?)</td>'
            dns_recs = re.findall(pattern, content, re.S)
            if len(dns_recs) == 0:
                self.error = 'unable to parse DNS records information with pattern ' + pattern + ' for domain ' + self.domain_name
                return False,             
            for dns_rec in dns_recs:
                rec = DNSRecord()
                rec.name = dns_rec[1]
                rec.type = DNSRecord._dns_type(dns_rec[0])
                rec.rdata = dns_rec[2]
                self.dns_records.append(rec)
            #################################################################
            #    
            #  Getting Name servers info
            #
            #################################################################
            pattern = 'span id="ctl00_cphMain_lblNameservers" title="(.*?)">'
            name_servers = re.findall(pattern, content,re.S)
            if len(name_servers)==0 :
                self.error = self.error = 'unable to parse pattern ' + pattern
                return False
            name_servers = string.rsplit(name_servers[0],'\r\n') 
            for name_server in name_servers:
                rec = DNSRecord()
                rec.type = 2
                rec.rdata = str(name_server)
                self.dns_records.append(rec)
        ###################################################
        #
        #getting complete (deep) DNS record information
        #
        ###################################################
        else:
            dns_tmp= DNSRecord()
            success,content =  dns_tmp._get_current(session, self.domain_name)
            if not success:
                self.error = dns_tmp.error
                return False       
            #retrieving complete domain information
            pattern='<td class=\'rrHeading\' width.*?>(.*?)</td>.*?<table.*?>(.*?)</table>'
            servers =re.findall(pattern, content, re.S)
            for server in servers:
                if not server[0]=='MX (Mail Exchange)':
                    pattern='<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?'
                else:
                    pattern='<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>'
                recs=re.findall(pattern, server[1], re.S)
                for rec in recs:
                    dns_rec = DNSRecord()
                    dns_rec.type  = DNSRecord._dns_type(string.lstrip(server[0]))
                    if not server[0]=='MX (Mail Exchange)':
                        dns_rec.name  = rec[0]
                        dns_rec.rdata = rec[1]
                        dns_rec.TTL   = string.lstrip(rec[2])
                    else:
                        dns_rec.priority = rec[0]
                        dns_rec.name     = rec[1]
                        dns_rec.rdata    = rec[2]
                        dns_rec.TTL      = string.lstrip(rec[3])                        
                    self.dns_records.append(dns_rec)
        return True

    def post(self, session):
        '''
        Synopsis:
            Creates a new domain.
        Arguments:
            session     :
        Exceptions:
        Returns:
            success : boolean
        '''        
        if self.domain_name=='': 
            self.error = 'Domain name not set'
            return False
        
        ################################################################################'
        #'
        # Step 0 - Empty shopping cart'
        #'
        ################################################################################'
        #emptying the shopping card
        cart = ShoppingCart()
        success = cart.delete(session)
        if not success:
            self.error = cart.error
            return False

        ################################################################################'
        #'
        # Step 1 - Getting current on home page
        #'
        ################################################################################'
        #setting uri
        uri = 'https://mya.godaddy.com/default.aspx'
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
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
        
        ################################################################################'
        #'
        # Step 2 - Checking domain availability'
        #'
        ################################################################################'
        #retrieving uri
        pattern = '<input.*?name="pch_sdomain_action".*?value="(.*?)">'
        results = re.findall(pattern, content, re.S)
        if len(results)== 0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('pchFS',pattern,content)
            return False
        else:
            uri = string.replace(results[0], 'amp;', '')
            #print '--------------------> : ' + uri
            
            
        #Retrieving uri and hidden fields
        form = 'pchFS'
        pattern = SoupStrainer('form', {'id':form})
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
            
        '''            
        #Retrieving hidden fields
        pattern = '<form.*?name="pchFS" id="pchFS".*?</form>'
        form_html = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('pchFS',pattern,content)
            return False
        #Retrieving hidden fields
        pattern='<input type="hidden" name="(.+?)".*?id=".+?".*?value="(.*?)">'
        hidden_inputs = re.findall(pattern,form_html[0], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden field with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[1] 
        '''
         
        #setting form variables
        data['domainToCheck'  ]= self.domain_name
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        # Checking if domain is available
        pattern = '<(?:span|b) class="black">(.*?)</(?:span|b)>'
        results = re.findall(pattern, content, re.S)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find pattern "%s" in content \n:%s' % (pattern,content)
            return False
        if string.find(results[0],'already taken')<>-1:
            self.error = 'Domain %s is NOT available' % (self.domain_name)
            return False

        ################################################################################
        #
        # Step 3 - Adding Domain Name to Shopping cart'
        #
        # 10-06-09 - Godaddy decided to change the uri that was called.  Currently
        #            scraping a jscript to get the URI.
        #
        ################################################################################
        #determining the uri
        pattern='addSelectedDomains\(\'/domains/stack.aspx?(.*?)\'\)'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find pattern %s in %s' % \
                         (pattern,content)
            return False
        #Retrieving the uri
        uri = 'https://www.godaddy.com/domains/stack.aspx' + results[0]
        #Retrieving uri and hidden fields
        form = 'aspnetForm'
        pattern = SoupStrainer('form', {'id':form})
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
            

              
        #Setting form inputs
        data['ctl00$MainContent$btnProceedToCheckout2ndATC.x'                           ]= '36'   #button X 
        data['ctl00$MainContent$btnProceedToCheckout2ndATC.y'                           ]= '8'    #button Y
        data['ctl00$MainContent$ddlVSM2DotType'                                         ]= 'COM'  #pulldown (nothing to do with code)
        data['ctl00$MainContent$ucVerticalStripMall2$rptTopSellers$ctl01$cbSelectDomain']= 'on'   #check box (nothing to do wiht code)
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        # Asserting we are upsell page - STOP!
        pattern = '<strong class="red">STOP!.*?</strong>'
        results = re.findall(pattern, content, re.S)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nPage assertion failed when loooking for %s in %s' % (pattern,content)
            return False

        ################################################################################'
        #'
        # Step 4 - Rejecting all add-ones'
        #'
        ################################################################################'
        #Retrieve hidden uri and fields
        pattern = '<form name="aspnetForm".*?action="(.*?)".*?>(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        else:
            uri = 'https://www.godaddy.com/domains/' + results[0][0]
            #print 'Step 4 - Rejecting all add-ones----------------->' + uri
        #Retrieving hidden attributes
        pattern='input type="hidden" name="(.+?)" id=".+?"( value="(.*?)")* '
        hidden_inputs = re.findall(pattern,results[0][1], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden field with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= string.replace(input[2],'&quot;','"')  
        #Setting form inputs
        data['ctl00$MainContent$lbContinueToCheckout.x' ]= '65'   #button X
        data['ctl00$MainContent$lbContinueToCheckout.y' ]= '8'    #button Y
        data['ctl00$MainContent$txtStackCodeNo'         ]= 'web_a_no_netorginfonetorginfousmobi'
        #defining the headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        # Asserting we're "Registration and Checkout Options"
        pattern = '<div class="t20 color_reg b">Registration and Checkout Options</div>'
        results = re.findall(pattern, content)
        if len (results)==0:
            self.error = 'Page assertion failed when loooking for %s in %s' % (pattern,content)
            return False
       
        ################################################################################'
        #'
        # Step 5 - Definifing domain reservation length'
        #'
        ################################################################################' 
        #Retrieve hidden uri and fields
        pattern = '<form name="aspnetForm".*?action="(.*?)".*?>(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        else:
            uri = 'https://www.godaddy.com/domains/' + results[0][0]
            #print 'Step 5 - Definifing domain reservation length----------------->' + uri
        #Retrieving hidden attributes
        pattern='input type="hidden" name="(.+?)" id=".+?"( value="(.*?)")* '
        hidden_inputs = re.findall(pattern,results[0][1], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden field with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2] 
        #setting form values
        data['ctl00$MainContent$ucRegisterDomains$ddlRegistrationLengthForAll'] = GODADDY_DOMAIN_RESERVATION_PERIOD  
        data['ctl00$MainContent$CustomizeOrCart'                              ] = 'rbToCart'      # by looking at Fiddler body
        data['ctl00$MainContent$ucDomainTestimonials$collapse1_ClientState'   ] = 'false'         # by looking at Fiddler body
        data['ctl00$MainContent$ucRegisterDomains$hfDomainsListView'          ] = ''
        data['__EVENTTARGET'                                                  ]= 'ctl00$MainContent$lbContinue'
        #data['rbgCertifiedDomainForAll'                                       ]= '0'           # by looking at Fiddler body
        #data['rbgAddSmartSpace'                                               ]= '6577'        # by looking at Fiddler body 
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        # Asserting we are upsell page - STOP!
        pattern = '<b>Review Your Shopping Cart</b>'
        results = re.findall(pattern, content, re.S)
        if len (results)==0:
            self.error = 'Page assertion failed when loooking for %s in %s' % (pattern,content)
            return False          

        ################################################################################'
        #'
        # Step 6 - Setting payment method'
        #'
        ################################################################################'                       
        #Retrieve hidden uri and fields
        pattern = '<form name="aspnetForm".*?action="(.*?)".*?>(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        else:
            uri = 'https://cart.godaddy.com/' + results[0][0]
            #print 'Step 6 - Setting payment method----------------->' + uri
        #Retrieving hidden attributes
        pattern='input type="hidden" name="(.+?)" id=".+?"( value="(.*?)")* '
        hidden_inputs = re.findall(pattern,results[0][1], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden field with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= string.replace(input[2],'&quot;','"')
        #setting the form input parameters
        data['chkAgree1'                                                  ] = 'UniversalTerms'
        data['chkAgree2'                                                  ] = 'DomainRegistration' 
        data['ctl00$MainContent$Footer1$Agreements1$imgContinueShopping.x'] = '73'   #button X
        data['ctl00$MainContent$Footer1$Agreements1$imgContinueShopping.y'] = '5'    #button Y
        data['ctl00$MainContent$Footer1$PaymentOptions1$Payment'          ] = 'optCreditCard'
        data['ctl00$MainContent$ctl00$basketRepeater$ctl01$ctl00$Scope'   ] = 'optPublic'
        data['ctl00$MainContent$ctl00$basketRepeater$ctl02$ctl00$Scope'   ] = 'optPublic'
        data['topLevelDomain'                                             ]= '.info'
        data['ctl00_ScriptManager1_HiddenField'                           ]= ''
        data['myLogin'                                                    ]= ''
        data['myPass'                                                     ]= ''
        data['mydomainToCheck'                                            ]= ''
        data['promoCode'                                                  ]= ''
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        # Asserting we're on the "Enter your billing information"
        pattern = 'Enter your billing information'
        results = re.findall(pattern, content)
        if len (results)==0:
            self.error = 'Page assertion failed when loooking for %s in %s' % (pattern,content)
            return False   

        ################################################################################'
        #'
        # Step 7 - Checkout'
        #'
        ################################################################################'                      
        #Retrieve hidden uri and fields
        pattern = '<form name="aspnetForm".*?action="(.*?)".*?>(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(form_html)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        else:
            uri = 'https://cart.godaddy.com/' + results[0][0]
            #print 'Step 7 - Checkout----------------->' + uri
        #Retrieving hidden attributes
        pattern='input type="hidden" name="(.+?)" id=".+?"( value="(.*?)")* '
        hidden_inputs = re.findall(pattern,results[0][1], re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden field with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= string.replace(input[2],'&quot;','"')         
        #setting the form input parameters    
        control1 = 'ctl00$MainContent$BillingInformation1$'
        data['CreditCardInfo_CCNumberPreviousValue'                                ] = ''                #by observation
        data['CreditCardInfo_CardNameForReValidation'                              ] = TWC_PAYMENT_TYPE
        data['CreditCardInfo_IsCCNumberMaskReady'                                  ]= '1'                #by observation
        data['SupportingControls_PaymentControls_ValueAddedTax_VatExemptRegionsDDL']='Select a region'   #by observation
        data['VatType'                                                             ] = 'vatPersonal'     #by observation
        data[control1 + 'BillingInfo1$CountrySelect1$drpCountry'     ]='226'                             #by observation
        data[control1 + 'BillingInfo1$txtAddress1'                   ]= TWC_ADDRESS1
        data[control1 + 'BillingInfo1$txtAddress2'                   ]=''    
        data[control1 + 'BillingInfo1$txtCity'                       ]= TWC_CITY
        data[control1 + 'BillingInfo1$txtEmail'                      ]= TWC_EMAIL
        data[control1 + 'BillingInfo1$txtExtension'                  ]=''    
        data[control1 + 'BillingInfo1$txtFaxNumber'                  ]=''
        data[control1 + 'BillingInfo1$txtFirstName'                  ]= TWC_FIRST_NAME
        data[control1 + 'BillingInfo1$txtHomePhone'                  ]=''
        data[control1 + 'BillingInfo1$txtLastName'                   ]= TWC_LAST_NAME
        data[control1 + 'BillingInfo1$txtOrganization'               ]=''
        data[control1 + 'BillingInfo1$txtProvince'                   ]=''
        data[control1 + 'BillingInfo1$txtWorkPhone'                  ]= TWC_MOBILE_PHONE
        data[control1 + 'BillingInfo1$txtZipCode'                    ]= TWC_ZIP
        data[control1 + 'CreditCardInfo1$disableCC'                  ]=''    
        data[control1 + 'CreditCardInfo1$drpCCType'                  ]= TWC_PAYMENT_TYPE
        data[control1 + 'CreditCardInfo1$drpMonth'                   ]= TWC_PAYMENT_M_EXP
        data[control1 + 'CreditCardInfo1$drpYears'                   ]= TWC_PAYMENT_Y_EXP
        data[control1 + 'CreditCardInfo1$txtCCNumber'                ]= TWC_PAYMENT_NUMBER
        data[control1 + 'CreditCardInfo1$txtName'                    ]= string.join([TWC_FIRST_NAME,TWC_LAST_NAME],' ')
        data[control1 + 'GiftCard1$accountList'                      ] =''   
        data[control1 + 'ValueAddedTax1$txtTaxID'                    ]=''
        data[control1 + 'imgContinue.x'                              ]='99'                            #by observation
        data[control1 + 'imgContinue.y'                              ]='14'                            #by observation
        data['ctl00$MainContent$frmPost'                                              ]='0'            #by observation
        data['ctl00_MainContent_BillingInformation1_BillingInfo1_StateSelect1_StateID']=''             #by observation
        data['ctl00_ScriptManager1_HiddenField'                                       ]=''             #by observation
        data['gc_count'                                                               ]='1'            #by observation
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        # Asserting if payment was successful
        if response.geturl()=='https://cart.godaddy.com/CheckoutErrors.aspx':
            pattern = '<span id="ctl00_MainContent_errorRepeater_ctl[0-9]{2}_Label2">(.*?)</span>'
            errors = re.findall(pattern, content, re.S)
            if len(errors)>0:
                self.error = string.join(errors,';')
            else:
                self.error = 'Unable to find checkour errors with pattern %s in %s' % (pattern,content)
            return False
        else:
            pattern='<div class="subText conf_data">.*?Order Number:.*?<b class="red">(.*?)</b>'
            results = re.findall(pattern, content, re.S)
            if len(results)==0:
                self.error = 'Unable to determine why order was not success in uri %s, \
                              with pattern %s in content %s' % (uri,pattern,content)
                return False 
            else:
                self.message = 'Order number: ' + results[0]
                return True     

    def put (self,session):
        '''
        Synopsis:
            Changes domain configurations.  Currently
            the only function allowed is setting 
            domain forward
        Arguments:
        Exceptions:
        Returns:
        '''
        if self.forwarding_uri == '':
            self.error = 'Please define the forwarding uri'
            return False
        
        ##########################################################################
        #
        #  Step 1 - Getting Current on Domain page
        #
        ##########################################################################
        #Request uri
        uri = 'https://dcc.godaddy.com/DomainDetails.aspx?domain=' + self.domain_name
        #setting the headders
        headers = WebTools.firefox_headers()
        #setting the request
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
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message 
            return False
        else:
            content = response.read()
            
        #asserting correct page & saving current uri because it contains domain id
        pattern = 'Domain Information'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error = 'Failed page assessment test with pattern %s and content %s in uri %s' % \
                          (pattern,content,uri)
        else:
            pattern = 'input type="hidden" name="hdnCurrentDomainId" id="hdnCurrentDomainId" value="(.*?)"'
            uri = response.geturl()
            results = re.findall(pattern, content)
            if len(results)==0:
                self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to get domain id using pattern %s in content %s' % (pattern,content)
                return False
            else:
                domain_id = results[0]    #required for a future posting hidden field
                orig_uri  = uri           #required for a future posting hidden field
        ##########################################################################
        #
        #  Step 2 - Getting the pop-up window
        #
        ########################################################################## 
        guid = uuid.uuid1()
        uri='https://dcc.godaddy.com/DropinLoad_Domain.aspx?controlRequest=ActionForwarding&guid='+ str(guid)
        #setting the headders
        headers = WebTools.firefox_headers()
        #setting the request
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
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         "Unexpected error:" + ex.message 
            return False
        else:
            content = response.read()
            
        #asserting the correct reply
        pattern = 'form name="aspnetForm".*?action="DropinLoad_Domain.aspx\?controlRequest=ActionForwarding&amp;guid='+str(guid)
        results = re.findall(pattern, content, re.S)
        if len(results)==0:
            self.error = 'Error asserting correct page with pattern %s in contect %s' % (pattern,content)
            return False
        ##########################################################################
        #
        #  Step 3 - Posting (don't really now why... following the script)
        #
        ##########################################################################        
        #retrieving hidden attrbibutes
        pattern = '<form.*?name="aspnetForm".*?>(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        else:
            form_content = results[0]
        #Retrieving 1st set hidden attributes
        pattern='input type="hidden" name="(.*?)".*?value="(.*?)"'
        hidden_inputs_1 = re.findall(pattern,form_content, re.S)
        if len(hidden_inputs_1)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         'Unable to find hidden fields with pattern %s in %s' % (pattern,form_content)
            return False
        #Retrieving 2nd set hidden attributes
        pattern='input name="(.*?)" type="hidden" id=".*?" (value="(.*?)")*'
        hidden_inputs_2 = re.findall(pattern,form_content, re.S)
        if len(hidden_inputs_2)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs_1: data[input[0]]= input[1]
        for input in hidden_inputs_2: data[input[0]]= input[2]        
        #adding values set by javascript - values set by using Fiddler
        data['ctl00$hdnParentURL'      ] = orig_uri 
        data['ctl00$hdnSelectedDomains'] = domain_id + '|'
        data['ctl00$hdnSelectedAction' ] = 'ActionForwarding'
        data['__EVENTTARGET'           ] = 'ctl00_btnLoadIt'
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        #asserting request was successful
        pattern = 'domainaction_domainForwardingWS'
        results = re.findall(pattern, content,re.IGNORECASE)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to to find jscript %s in content %s' % (pattern,content)
            return False
        ##########################################################################
        #
        #  Step 4 - Posting the forwarding form
        #
        ##########################################################################            
        uri='https://dcc.godaddy.com/DropinLoad_Domain.aspx?controlRequest=ActionForwarding&guid='+ str(guid)
        #retrieving hidden attrbibutes
        pattern = '<form.*?name="aspnetForm".*?>(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find form %s with pattern %s in %s' % ('aspnetForm',pattern,content)
            return False
        else:
            form_content = results[0] 
        #Retrieving 1st set hidden attributes
        pattern='input type="hidden" name="(.*?)".*?value="(.*?)"'
        hidden_inputs_1 = re.findall(pattern,form_content, re.S)
        if len(hidden_inputs_1)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find hidden fields with pattern %s in %s' % (pattern,form_content)
            return False
        #Retrieving 2nd set hidden attributes
        pattern='input name="(.*?)" type="hidden" id=".*?" (value="(.*?)")*'
        hidden_inputs_2 = re.findall(pattern,form_content)
        if len(hidden_inputs_2)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to find hidden fields with pattern %s in %s' % (pattern,form_content)
            return False
        data = dict()
        for input in hidden_inputs_1: data[input[0]]= input[1]
        for input in hidden_inputs_2: data[input[0]]= input[2]        
        #adding values set by javascript - values set by using Fiddler
        data['__EVENTTARGET'           ] = 'ctl00_cphAction1_dccForwarding_btnOK'
        #form variables
        p_uri = urlparse.urlparse(self.forwarding_uri)
        data['ctl00$cphAction1$dccForwarding$ddlProtocol'                       ] = p_uri[0] + '://' 
        data['ctl00$cphAction1$dccForwarding$txtForwardingURL'                  ] = p_uri[1]
        data['ctl00$cphAction1$dccForwarding$chkUpdateNS'                       ] = 'on'
        data['ctl00$cphAction1$dccForwarding$hdnValidated'                      ] = '1'
        data['ctl00$cphAction1$dccForwarding$divGrayBorder$ForwardPreference'   ] = '1'
        data['ctl00$cphAction1$dccForwarding$divGrayBorder$ddlRedirectType'     ] = '301'
        data['ctl00$cphAction1$dccForwarding$divGrayBorder$ForwardPreference'   ] = '1'
        data['ctl00$cphAction1$dccForwarding$divGrayBorder$txtMaskedTitle'      ] = 'Masked title'
        data['ctl00$cphAction1$dccForwarding$divGrayBorder$txtMaskedDescription'] = 'Description'
        data['ctl00$cphAction1$dccForwarding$divGrayBorder$txtMaskedKeywords'   ] = 'tag1'        
        #setting request headers
        headers = WebTools.firefox_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data),headers=headers)
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
        #asserting request was successful
        pattern = 'Your changes have been submitted.  Please allow a few minutes for the changes to take effect.'
        results = re.findall(pattern, content,re.IGNORECASE)
        if len(results)==0:
            self.error = self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable to to find jscript %s in content %s' % (pattern,content)
            return False
        else:
            return True
        
          
class GdAccount(ProviderAccount):
    '''
    Synopsis:
        Represents a GoDaddy account to which many services can
        be added, including DomainService.  
    Methods
        POST - creates a new account
        PUT  - updates certain information on the account
        GET  - gets the account details
    '''

    def __init__(self):
        '''
        Synopsis:
            Constructor
        Arguments:
        Exceptions:
        Returns:
        '''
        super(GdAccount,self).__init__()       
        self.first_name            = ''
        self.last_name             = ''
        self.address_1             = ''
        self.address_2             = ''
        self.city                  = ''
        self.state_province        = ''
        self.zip                   = ''
        self.country               = ''
        self.phone                 = ''
        self.mobile_phone          = ''
        self.mobile_phone_provider = ''
        self.email                 = ''


    def get(self,session,deep=False, type=None, max_recs = GODADDY_DOMAIN_MAX_RECS):
        '''
        Synopsis:
            Gets info on Godaddy account by populating the
        Arguments
            session     : current login session
            deep        : True for listing services, and service details
            type        : type of service list to retrieve
            max_recs    : maximum number of services to retrieve
            debug       : whether httplib2 will debub
        Exceptions:
        Returns:
            success :
        '''  
        #setting the uri                                   )       
        uri = 'https://mya.godaddy.com/Account/AccountSettings/AccountSettings.aspx?ci=11262&sa='
        #setting the headders
        headers = WebTools.firefox_headers()
        #setting the request
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
        #  Asserting the account details
        #
        ###################################################################        
        pattern = '<input name="ctl00\\$cphM\\$cntrlDetailAccountSettingsOwnerInfo\\$(.*?)".*?value="(.*?)"'
        details = re.findall(pattern, content)
        if len(details)==0:
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        
        for detail in details:
            
            if    detail[0] == 'Shopper_email'        : self.email      = detail[1]
            #elif  detail[0] == 'Shopper_company'      : self.company    = detail[1]   #future use
            #elif  detail[0] == 'Shopper_fax'          : self.fax        = detail[1]   #future use
            elif  detail[0] == 'Shopper_FirstName'    : self.first_name = detail[1]
            #elif  detail[0] == 'shopper_gender'       : self.gender = detail[1]      #future use
            elif  detail[0] == 'Shopper_LastName'     : self.last_name  = detail[1]
            elif  detail[0] == 'Shopper_loginname'    : self.user_name    
            #elif  detail[0] == 'Shopper_middle_name'  : self.middle_name = detail[1] #future use 
            elif  detail[0] == 'Shopper_Phone1'       : self.phone          = detail[1]
            #elif  detail[0] == 'Shopper_phone2'       : self.phone_2       = detail[1] #future use    
            elif  detail[0] == 'Shopper_Address1'      : self.address_1      = detail[1]
            elif  detail[0] == 'Shopper_Address2'      : self.address_2      = detail[1]
            elif  detail[0] == 'Shopper_City'         : self.city           = detail[1]
            elif  detail[0] == 'Shopper_state'        : self.state_province = detail[1]
            elif  detail[0] == 'Shopper_Zip'          : self.zip            = detail[1]
            elif  detail[0] == 'Shopper_country'      : self.country        = detail[1]
            #elif  detail[0] == 'txtCallinPin'         : self.pin            = detail[1]
            elif  detail[0] == 'Shopper_mobileCarrier': self.phone_carrier  = detail[1]
            elif  detail[0] == 'Shopper_mobilePhone'  : self.phone          = detail[1]
            #elif  detail[0] == 'txtWorkExtension'     : self.work_ext      = detail[1]
            #elif  detail[0] == 'Shopper_password'     : self.password          = detail[1]
            elif  detail[0] == 'Shopper_password_hint': self.password_hint  = self.password_hint
            #elif  detail[0] == 'txtShopperBirthday'            ]=''
            #optional fields   
            #elif  detail[0] == 'Shopper_mktg_ENews'            : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'Shopper_mktg_Radio'            : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'Shopper_mktg_blog'             : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'Shopper_mktg_email'            : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'Shopper_mktg_mail'             : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'Shopper_nonpromotional_notices': self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'optinBusinessEmail'            : self.phone_2       = detail[1] #future use      
            #elif  detail[0] == 'rbOptinBusEmailNo'             : self.phone_2       = detail[1] #future use      
            #elif  detail[0] == 'rbOptinSMSCommYes'             : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'rblBulkWhoisThirdParty'        : self.phone_2       = detail[1] #future use  
            #elif  detail[0] == 'ddlMarketingSurvey'            : self.phone_2       = detail[1] #future use  

        #getting the service information
        if deep:
            if type=='domains':
                success = self._get_domains(session,max_recs = max_recs, deep=deep)
                if not success:
                    return False
            if type is None:  #if not type if define retrieve all types of services
                success = self._get_domains(session,max_recs = max_recs, deep=deep)
                if not success:
                    self.error = self.__class__.__name__+'.'+ \
                                 sys._getframe().f_code.co_name + \
                                 ' @line:' + str(sys._getframe().f_lineno) + \
                                 '\n' + self.error
                                 
                    return False
        return True


    def post(self):
        '''
        Synopsis:
            creates a new godaddy account. The following defaults are used
            to create the account when the value is not defined:
            login name: firstnamelastname
            PIN       : random 4 digits 
            password  : firstname+lastname+4 random digits
            
            Other indications:
            country code - 2 letter abbreviation of the country
        Arguments: 
        Exceptions:
        Returns:
            success: whether call was succesful
        '''
        
        ###################################################################
        #Checking for defaults
        ###################################################################
        if self.user_name =='':
            self.user_name = string.join([self.first_name,self.last_name],'')
        if self.pin =='':
            self.pin = ''.join(random.choice(string.digits) for i in xrange(4))
        if self.mobile_phone_provider == '':
            self.mobile_phone_provider = GODADDY_3WC_MOBILE_PHONE_PROVIDER
        if self.mobile_phone == '':
            self.mobile_phone = TWC_MOBILE_PHONE
        if self.password =='':
            password    = string.join([self.first_name,\
                                       self.last_name,
                                       ''.join(random.choice(string.digits) for i in xrange(4))])            
        if self.password_hint =='':    
            self.password_hint= GODADDY_PASSWORD_HINT
                    
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
        #  Step 1 - Getting to the main page.
        #
        #  Note: the reason we don't go directly to the new customer
        #        page is because GD has the concept of server of the day
        #        which is a server name to which the result will be posted.
        #
        ###################################################################        
        #defining uri
        uri = 'http://www.godaddy.com/default.aspx'
        #creating a firefox browser
        headers = WebTools.firefox_headers()    
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submitting the request
        try:
            response = urllib2.urlopen(request)
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
            
        ###################################################################
        #
        #  Step 2 - Getting to the create account page.
        #
        ###################################################################        
        #Getting the uri for the create account page
        pattern = '<a href="(https://idp.godaddy.com/shopper_new.aspx\?.*?)".*?>Create Account</a>'
        results = re.findall(pattern, content, re.S)
        if len(results)==0:
            self.error =  'Unable to find form pattern %s in %s' % (pattern,content)
            return False
        else:
            uri = string.replace(results[0],'&amp;','&')
        #setting the headers
        headers['Host']= urlparse.urlparse(uri)[1]
        #determining request
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
                print 
        except Exception,ex:
            self.error = "Unexpected error:" + ex.message
            return False
        else:
            content = response.read()  
        #asserting we're on the right page
        pattern='Create A New Customer Account'
        if len(re.findall(pattern, content))== 0 :
            self.error = 'Unable to find form pattern %s in %s' % (pattern,content)
            return False        
        ###################################################################
        #
        #  Step 3 - Filling the form
        #
        ###################################################################        
        #Getting the uri for the create account page
        uri = response.geturl()
        #retrieve form content
        pattern = '<form.*?name="Form1"(.*?)</form>'
        results = re.findall(pattern,content, re.S)
        if len(results)==0:
            self.error = 'Unable to find form %s with pattern %s in %s' % ('Form1',pattern,content)
            return False
        #Retrieving hidden attributes
        pattern='input.*?type=["|\']hidden["|\'].*?name=["|\'](.*?)["|\'].*?(id=["|\'].*?["|\'])*value=["|\'](.*?)["|\']'
        hidden_inputs = re.findall(pattern,content, re.S)
        if len(hidden_inputs)==0:
            self.error = 'Unable to find hidden fields with pattern %s in %s' % (pattern,content)
            return False
        data = dict()
        for input in hidden_inputs: data[input[0]]= input[2]         
        #setting form values
        data['__SCROLLPOSITIONX'             ]='0'
        data['__SCROLLPOSITIONY'             ]='1423'        
        #defining form fields
        data['CreateAccountImageButton.x'    ]='161'
        data['CreateAccountImageButton.y'    ]='13'
        #
        data['ddlBirthday'                   ]=''
        data['shopper_bdmonth'               ]= ''
        data['shopper_email'                 ]= self.email
        data['confirm_shopper_email'         ]= self.email
        data['shopper_company'               ]= ''
        data['shopper_fax'                   ]= ''
        data['shopper_first_name'            ]= self.first_name
        data['shopper_gender'                ]='n'
        data['shopper_last_name'             ]= self.last_name
        data['shopper_loginname'             ] = self.user_name
        data['shopper_middle_name'           ]= '' 
        data['shopper_phone1'                ]= self.phone
        data['shopper_phone2'                ]= ''    
        data['shopper_street1'               ]= self.address_1
        data['shopper_street2'               ]= self.address_2
        data['shopper_city'                  ]= self.city
        data['shopper_state'                 ]= self.state_province
        #this was addded while trying to create an account
        #from Morocco
        data['shopper_other_state'           ]= self.state_province
        data['shopper_zip'                   ]= self.zip
        data['shopper_country'               ]= self.country
        data['txtCallinPin'                  ]= self.pin
        data['shopper_mobileCarrier'         ]= self.mobile_phone_provider
        data['shopper_mobilePhone'           ]= self.mobile_phone
        data['txtWorkExtension'              ]=''
        data['shopper_password'              ]= password
        data['shopper_password2'             ]= password
        data['shopper_password_hint'         ]= self.password_hint
        data['txtShopperBirthday'            ]=''
        #optional fields   
        data['shopper_mktg_ENews'            ]='ENews_no'
        data['shopper_mktg_Radio'            ]='Radio_no'
        data['shopper_mktg_blog'             ]='Blog_no'
        data['shopper_mktg_email'            ]='mktg_email_no'
        data['shopper_mktg_mail'             ]='mktg_mail_yes'
        data['shopper_nonpromotional_notices']='promo_yes'
        data['optinBusinessEmail'            ]=''    
        data['rbOptinBusEmailNo'             ]='optinSMS'    
        data['rbOptinSMSCommYes'             ]=''
        data['rblBulkWhoisThirdParty'        ]='0'
        data['ddlMarketingSurvey'            ]=''
        #defining the headers
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #defining the request
        request = urllib2.Request(uri, urllib.urlencode(data), headers=headers)
        #submitting the request
        try:
            response = urllib2.urlopen(request)
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
        #asserting success
        pattern = '(User Name|Customer Number):.*?<strong>(.*?)</strong>'
        results = re.findall(pattern, content, re.S)
        if len(results)==2:
            self.user_name      = results[0][1] 
            self.account_number = results[1][1]
        elif len(results)==0:
            pattern = '<span id="ErrorLabel">(.+?)<br />'
            results = re.findall(pattern,content,re.S)
            if len(results)==0:
                self.error = 'Unable to determine why account was not created'
                return False
            else:
                self.error = string.join(results,';')
                #print content
                return False

        #checks if any services are being created also
        for service in self.services:
            success, error = service.post(session)
            if not success: results['service']=error
            
        return True
    
    def put(self):
        '''
        updates certain aspects of the Godaddy account.
        '''
        pass
        
    def _get_domains(self,session,max_recs = GODADDY_DOMAIN_MAX_RECS,deep=False):
        '''
        Synopsis:
            Populates the services attributes with the
            domains services. By default it only retrieves
            MAX_RECS 
        Arguments:
            session     :validated logon
            deep        :determines whether to retrieve all info
            max_recs    :max number of records to be retrieved. If -1 retrieve all.
        Exceptions:
        Returns:
            success  : whether operation was successful
        '''
        #setting the uri
        uri = 'https://dcc.godaddy.com/default.aspx'
        #setting the headers
        headers = WebTools.firefox_headers()
        #defining the request
        request = urllib2.Request(uri, headers=headers)
        #submitting the request
        try:
            response = session.urlopener.open(request)
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

        #Retrieving all domains
        pattern = 'id="ctl00_cphMain_DomainList_gvDomains_([0-9]*)_btnDomainName" title="(.*?)"'
        domains = re.findall(pattern, content, re.S)
        if len(domains)== 0:
            self.error = 'Unable to find pattern %s in %s' % (pattern,content)
            return False
        counter = 0
        for domain in domains:
            counter +=1
            domain_service = DomainService()
            domain_service.domain_name = domain[1]
            domain_service.domain_public_id = domain[0] 
            domain_service.debug = self.debug
            if deep:
                success = domain_service.get(session,deep=deep)
                if success:
                    self.services.append(domain_service)
                else:
                    self.error = domain_service.error
                    return False
            if counter == max_recs: break
        return True
     
'''
Main
'''
if __name__=='__main__':
    pass
    print '<please see cumulus.cloud.godaddy.test> module to perform any tests'