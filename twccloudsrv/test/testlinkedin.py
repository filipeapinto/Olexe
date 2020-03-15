'''
Created on Aug 28, 2009

@author: fpinto
'''
import unittest
from twccloudsrv.linkedin import *

DEFAULT_LOGIN_NAME = '*****'
DEFAULT_PASSWORD   = '*****' 

class TestLinkedIn():


    def testLiGetSession(self, login_name = DEFAULT_LOGIN_NAME,
                               password   = DEFAULT_PASSWORD,
                               debug      = False):
        '''
        Synopsis:
            returns a LinkedIn session
        '''
        print self.testLiGetSession.__doc__
        print 'Arguments:\n-login:%s\n-password:%s\n-debug:%s' % \
                         (login_name,password,debug)
        session = LiSession(debug=debug)
        session.password   = password
        session.login_name = login_name
        success = session.get()
        if not success:
            error = session.error
            
        assert success, error 
        
    def testLiAccountGet(self):
        '''
        Synopsis: get the account information 
        '''
        pass
    
    def testLiAccountPost(self):
        '''
        Synopsis: creates a new LinkedIn Account
        '''
        pass
    
    def testLiConnectionPost(self,first_name,
                                  last_name,
                                  email,
                                  login_name = DEFAULT_LOGIN_NAME,
                                  password   = DEFAULT_PASSWORD,
                                  debug      = False):
        '''
        Synopsis:
            Creates a new connection to current
            logged LinkedIn subscriber
        '''
        print self.testLiConnectionPost.__doc__
        print 'Arguments:\n-first_name:%s\n-last_name:%s\n-email:%s\n-login_name:%s\n-password:%s\n-debug:%s' % \
                         (first_name,last_name,email,login_name,password,debug)
        session = LiSession(debug=debug)
        session.password   = password
        session.login_name = login_name
        success = session.get()
        if not success: error = session.error
        else:
            connection = LiConnection()
            connection.first_name = first_name 
            connection.last_name  = last_name
            connection.email      = email
            success = connection.post(session)
            if not success: error = connection.error           
            
        assert success, error 
    
    def tesLiMicroBlogPostPost(self):
        '''
        Synopsis: create a microblog post
        '''
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    #unittest.main()
    my_test = TestLinkedIn()
    #my_test.testLiGetSession(debug=True) 
    my_test.testLiConnectionPost('Mario','Ceu','maria.ceu@newzelandporatal.nz',debug=True)