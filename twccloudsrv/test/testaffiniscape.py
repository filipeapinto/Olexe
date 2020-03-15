'''
Created on Sep 3, 2009

@author: fpinto

This module tests the Affiniscape API

'''

from twccloudsrv.affiniscape import *

DEFAULT_LOGIN_NAME = '*'
DEFAULT_PASSWORD   = '*'
DEFAULT_FIRST_NAME     = '*'
DEFAULT_LAST_NAME      = '*'
DEFAULT_ACCOUNT_NUMBER = '*'

class TestAffiniscape():


    def testAfSessionGet(self, login_name = DEFAULT_LOGIN_NAME,
                               password   = DEFAULT_PASSWORD,
                               debug      = False):
        '''
        Synopsis:
            returns a Affiniscape session
        '''
        print self.testAfSessionGet.__doc__
        print 'Arguments:\n-login:%s\n-password:%s\n-debug:%s' % \
                         (login_name,password,debug)
        session = AfSession(debug=debug)
        session.password   = password
        session.login_name = login_name
        success = session.get()
        if not success:
            error = session.error
            
        assert success, error


    def testAfAccountGet(self, login_name     = DEFAULT_LOGIN_NAME,
                               password       = DEFAULT_PASSWORD,
                               first_name     = DEFAULT_FIRST_NAME,
                               last_name      = DEFAULT_LAST_NAME,
                               account_number = DEFAULT_ACCOUNT_NUMBER, 
                               debug          = False):
        '''
        Synopsis:
            returns informaiton on an Affiniscape customer
        '''
        print self.testAfAccountGet.__doc__
        print 'Arguments:\n-login:%s\n-password:%s\n-debug:%s' % \
                         (login_name,password,debug)
        session = AfSession(debug=debug)
        session.password   = password
        session.login_name = login_name
        success = session.get()
        if not success:
            error = session.error
        else:
            account = AfAccount()
            account.first_name     = first_name
            account.last_name      = last_name
            account.account_number = account_number
            success = account.get(session)
            if not success:
                error = account.error
            else:
                print 'Email: ' + account.email
            
        assert success, error


if __name__ == '__main__':
    
    my_test = TestAffiniscape()
    #my_test.testAfSessionGet(debug=True)
    my_test.testAfAccountGet(debug=True)