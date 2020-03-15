'''
Created on Aug 7, 2009

@author: fpinto


Synopsis:
    This module is an API to the Affiniscape system 

'''

import re
import urllib
import sys
import string
import urllib2
import cookielib
from twccloudsrv.util import WebTools
from twccloudsrv.base import ProviderAccount, ProviderSession

class AfSession(ProviderSession):
    '''
    Synopsis:
        Affiniscape session
    Methods:
        get
    '''
    def __init__(self,debug=False):
        '''
        '''
        super(AfSession, self).__init__()
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
            self.urlopener.add_handler(urllib2.HTTPRedirectHandler())
            self.urlopener.add_handler(urllib2.HTTPErrorProcessor())
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
        uri = 'http://www.abpmp.org/displaycommon.cfm?an=22'
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
        pattern = 'Please Login'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable certify uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False 
        ###################################################################'
        #'
        #  Posting credentials
        #'
        ###################################################################'  
        #setting the uri
        uri = 'http://www.abpmp.org/displaycommon.cfm?an=22'
        #retrieve uri and hidden fields
        data={}
        data['CallingPage']= 'displaycommon.cfm'
        data['btnLogin'   ]= 'Login'
        data['cpass'      ]= self.password
        data['cuser'      ]= self.login_name
        data['loggingin'  ]= 'loggingin'
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
        # Getting uri for redirection
        pattern = 'Welcome to the secure members'
        results = re.findall(pattern, content, re.S)
        if len(results)== 0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable redirect login using pattern %s in content %s' % (pattern,content)
            return False
        else:
            return True      



class AfAccount(ProviderAccount):
    '''
    Synopsis:
        Represents an Affiniscape customer
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        super(AfAccount,self).__init__()
    
    def get(self,session):
        '''
        Synopsis:
            Retrieves the details of a customer
            account.
        '''
        #checking mandatory attributes
        if self.first_name == '' or self.last_name =='' or self.account_number =='':
            self.error = 'First name,last name and account # are mandatory'
            return False
        
        ######################################################
        #
        #getting admin page
        #
        ######################################################
        #setting the uri
        uri='http://www.abpmp.org/adminmanagemembers.cfm'
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
        #asserting correct page
        pattern = 'Manage Member Records'
        results = re.findall(pattern, content)
        if len(results)==0:
            self.error =  self.__class__.__name__+'.'+ \
                         sys._getframe().f_code.co_name + \
                         ' @line:' + str(sys._getframe().f_lineno) + \
                         '\nUnable certify uri %s id using pattern %s in content %s' % (uri,pattern,content)
            return False

        ######################################################
        #
        # getting info
        #
        ######################################################
        param=[]
        param.append('jumpfield=9')
        param.append('selSearchField=')
        param.append('btnAddField=')
        param.append('btnSearch=Search')
        param.append('selSearchOperator7=1')
        param.append('txtSearchValue7='+self.first_name)
        param.append('selSearchOperator9=1')
        param.append('txtSearchValue9='+ string.replace(self.last_name, ' ', '%20'))
        param.append('txtSearchFieldIds=9%2C7')
        param.append('selToggleSerach=Yes')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('quicktask=')
        param.append('txtPage=0')
        all_parms = string.join(param,'&') 
        uri='http://www.abpmp.org/adminmanagemembers.cfm?' + all_parms
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
        #check if the right member was found
        pattern='<a href="#" onclick="return displayMemberPopup\(([0-9]*?)\);'
        member_numbers = re.findall(pattern, content)
        found = False
        if len(member_numbers)==0:
            self.error = 'Customer NOT found'
            return False
        else:
            for number in member_numbers:
                if self.account_number == self.account_number:
                    found = True
                    break
        #retrieving information
        if found:
            pattern = '<a href="mailto:(.*?)">'
            emails = re.findall(pattern,content)
            if len(emails) == 0 :
                self.error = 'no email defined'
                return True
            else:
                if len(emails)== 1 or len(emails)==2:
                    self.email = emails[0]
                    return True
                else:
                    if len (emails)>2:
                        self.error ='multiple emails for :' + self.first_name + ' ' + self.last_name + ' ' + str(emails)
                        return False
        else:
            self.error = 'Customer NOT found'
            return False
            
    
