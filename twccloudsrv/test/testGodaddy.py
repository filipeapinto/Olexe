'''
Created on Aug 10, 2009

@author: fpinto

Synopsis: This module is intended to be run after
          any changes are made agains the the
          godaddy.py module.
'''

import jsonpickle
import unittest
from twccloudsrv.godaddy import *
from twccloudsrv.util import TimeTools
from time import *

#Global variables
DEFAULT_LOGING_NAME          = '****'
DEFAULT_LOGING_NAME_PASSWORD = '****'
DEFAULT_DOMAIN_NAME          = '****'
DEFAULT_FORWARDING_URI       = '****'

#class GodaddyServiceTestCase(unittest.TestCase):
class GodaddyServiceTestCase():
    
    def testPotencialdomainGet(self,debug = False,
                               domain_name=DEFAULT_DOMAIN_NAME):
        '''
        Test:
            Determines response from PotentialDomain.get()
            If no parameters are passed the method will use
            a domain known to be taken 'filipe-pinto.com'
        Expected results:
            If domain is NOT available needs to return a
            list with alternative names'''
    
        print self.testPotencialdomainGet.__doc__
        print 'Arguments:\n-debug: %s\n-domain: %s' % \
                          (str(debug),domain_name)
        p_domain = PotentialDomain()
        p_domain.debug       = debug
        p_domain.domain_name = domain_name
        start_time = time()
        success = p_domain.get()
        end_time = time()
        if success:
            if p_domain.is_available == False:
                print 'Results:\nThe domain %s is taken.  Here some alternative' % (domain_name)
                for domain in p_domain.alternative_names: print domain
            else:
                print 'Results:\n-%s is available' % (domain_name)
        print 'Duration:\n-' + TimeTools.duration(start_time, end_time)
        
        assert success and  \
               ((    p_domain.is_available and len(p_domain.alternative_names)==0) or \
                (not p_domain.is_available and len(p_domain.alternative_names)>0)), p_domain.error

    def testGdSessionGet(self,debug=False,
                         login_name=DEFAULT_LOGING_NAME, 
                         password=DEFAULT_LOGING_NAME_PASSWORD,):
        '''
        Synopsis:
            Godaddy session functionality
        Expected Results:
            Returns "Account Number" and "Account Name"
        '''

        print self.testGdSessionGet.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-debug : %s' % \
                  (login_name,password,str(debug))
        gd_session=GdSession(debug=debug)
        gd_session.login_name = login_name
        gd_session.password = password
        start_time = time()
        success = gd_session.get()
        end_time = time()
        if success:
            print 'Results\n-Acct: %s\n-Acct name: %s' %\
                    (gd_session.account_number,gd_session.account_name)
        print 'Duration:\n-' + TimeTools.duration(start_time,end_time)
        
        assert success, gd_session.error


    def testGdAccountGet(self,
                         debug = False,
                         deep  = False,
                         login_name=DEFAULT_LOGING_NAME,
                         password=DEFAULT_LOGING_NAME_PASSWORD):
        '''
        Synopsis:
            Retrieves the information of an already
            existing account.
        Expected Results:
            Dictionary with the account values.
        '''
        bt = time()
        print self.testGdAccountGet.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-deep: %s\n-debug: %s' % \
                  (login_name,password,str(deep),str(debug))
        gd_session=GdSession(debug=debug)
        gd_session.login_name = login_name
        gd_session.password   = password
        success = gd_session.get()
        if not success:
            error = gd_session.error
        else:
            my_account = GdAccount()
            success = my_account.get(gd_session,deep=deep)
            et= time()
            if not success:
                error = my_account.error
            else:
                print 'Results:\n-' + jsonpickle.encode(my_account)
        
        print 'test duration: ' + TimeTools.duration(bt,et)

        assert success, error
        
    def testGdAccountPost(self,first_name,last_name,email,debug=False):
        '''
        Synopsis:
            Creates a new Godaddy account
        Expected Results:
            Need to see the user_name and account_number
            of the created account.
        Notes:
            Apparently entering an already registered cell
            phone returns an error.  When i started coding
            this module, that was NOT the case.
        '''
    
        print self.testGdAccountPost.__doc__
        print 'Arguments:\n-first name: %s\n-last name: %s\n-email: %s\n-debug: %s' % \
                  (first_name,last_name,email,str(debug))        
        
        #creating a Godaddy provider
        my_account = GdAccount()
            
        #second method of creating an account
        my_account.first_name     = first_name
        my_account.last_name      = last_name
        my_account.address_1      = 'Canal Street #45' 
        my_account.city           = 'New York' 
        my_account.zip            = '10013' 
        my_account.state_province = 'NY' 
        my_account.country        = 'us' 
        my_account.password       = '*****'
        my_account.email          = email
        my_account.phone          = '******'
        my_account.mobile_phone   = '******'
        my_account.debug          = True

        #Creating godaddy account
        bt = time()
        success = my_account.post()
        et= time()
        if not success:
            error= my_account.error
        else:
            print TimeTools.duration(bt,et)
            print 'User Name     : ' + my_account.user_name 
            print 'Account Number: ' + my_account.account_number
    
        assert success, error      

    def testDomainGet(self,login_name = DEFAULT_LOGING_NAME,
                            password = DEFAULT_LOGING_NAME_PASSWORD,
                            domain_name = DEFAULT_DOMAIN_NAME,
                            deep = False,
                            debug = False):
        '''
        Synopsis:
            Retrieves information about the one specific domain.
        Expected Results:
            Domain information in JSON
        '''
    
        print self.testDomainGet.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-domain name: %s\n-deep: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(deep),str(debug))                
        #getting the session
        session=GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        start_time = time()
        success = session.get()
        end_time = time()
        print 'Session duration: ' + TimeTools.duration(start_time,end_time)
        if not success:
            error = session.error
        else:
            my_domain = Domain()
            my_domain.domain_name = domain_name
            start_time = time()
            success = my_domain.get(session, deep=deep)
            end_time = time()
            if not success:
                error = my_domain.error
            else:
                print 'Get duration: ' + TimeTools.duration(start_time,end_time)
                print jsonpickle.encode(my_domain)
                    
        assert success, error   
        
    def testDomainPost(self,domain_name ,
                            login_name = DEFAULT_LOGING_NAME,
                            password = DEFAULT_LOGING_NAME_PASSWORD,
                            debug = False):
        '''
        Synopsis:
            Creates a new domain.
        Expected Results:
            Invalid credit card message
        '''
        print self.testDomainPost.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-domain name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))                
        #getting the session
        session=GdSession(debug=True)
        session.login_name = login_name
        session.password   = password
        success = session.get()
        if not success:
            error = session.error
        else:
            new_domain = Domain()
            new_domain.domain_name=domain_name
            start_time =time() 
            success = new_domain.post(session)
            end_time = time()
            if not success:
                error = new_domain.error
            print 'Total Duration - ' + TimeTools.duration(start_time,end_time)
            
        assert success, error    

    def testDomainPut(self,forwarding_uri = DEFAULT_FORWARDING_URI,
                           login_name     = DEFAULT_LOGING_NAME,
                           password       = DEFAULT_LOGING_NAME_PASSWORD,
                           domain_name    = DEFAULT_DOMAIN_NAME,
                           debug          = False):                      
        '''
        Synopsis:
            Set domain forwarding.
        Expected Results:
            Invalid credit card message
        '''
        print self.testDomainPut.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-domain name: %s\n-forwarding uri: %s\n-debug: %s' % \
                  (login_name,password,domain_name,forwarding_uri,str(debug))                
        #getting the session
        session=GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        print 'Getting a session... please be patient'
        start_time = time()
        success = session.get()
        end_time = time()
        print 'Session get duration - ' + TimeTools.duration(start_time,end_time)
        if not success:
            error = session.error
        else:
            domain = Domain()
            domain.domain_name    = domain_name
            domain.forwarding_uri = forwarding_uri 
            start_time =time() 
            success = domain.put(session)
            end_time = time()
            if not success:
                error = domain.error
            print 'Domain Update Duration - ' + TimeTools.duration(start_time,end_time)
            
        assert success, error    


    def testShoppingCartDelete(self, login_name=DEFAULT_LOGING_NAME,
                                password=DEFAULT_LOGING_NAME_PASSWORD,debug=False):
        '''
        Synopsis: deletes all items from the shopping cart
        '''
        print self.testShoppingCartDelete.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-debug: %s' % \
                  (login_name,password,str(debug))
        
        #getting the session
        gd_session=GdSession()
        gd_session.login_name = login_name
        gd_session.password   = password
        success = gd_session.get()
        if not success:
            error = 'Session error : ' + gd_session.error
        else:
            start_time = time()
            cart = ShoppingCart()
            end_time= time()
            success = cart.delete(gd_session)
            if not success:
                error = 'Error deleting cart' + cart.error
        
        print TimeTools.duration(start_time,end_time)
        
        assert success, error


    def testShoppingCartGet(self, login_name=DEFAULT_LOGING_NAME,
                                password=DEFAULT_LOGING_NAME_PASSWORD,debug=False):
        '''
        Synopsis:
            gets the items in the shopping cart
        Expected results:
            returns a JSON of the cart items
        '''
        print self.testShoppingCartGet.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-debug: %s' % \
                  (login_name,password,str(debug))
        
        #getting the session
        gd_session=GdSession()
        gd_session.login_name = login_name
        gd_session.password   = password
        success = gd_session.get()
        if not success:
            error = 'Session error : ' + gd_session.error
        else:
            start_time = time()
            my_cart = ShoppingCart()
            end_time= time()
            success = my_cart.get(gd_session)
            if not success:
                error = 'Error deleting cart' + cart.error
            else:
                print jsonpickle.encode(my_cart)
        
        print TimeTools.duration(start_time,end_time)

    
    def testCnamePost(self, login_name=DEFAULT_LOGING_NAME,
                               password=DEFAULT_LOGING_NAME_PASSWORD,
                               domain_name = DEFAULT_DOMAIN_NAME,     
                               debug=False):
        '''
        Synopsis:
            Creates a DNS record.
        Expected results
        '''
        print self.testCnamePost.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-domain_name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))
        bt = time()
        #loging into Godaddy
        session = GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        success = session.get()
        if not success:
            error = self.error
        else:
                my_cname = DNSRecord()
                #my_cname.domain_name =  domain_name 
                my_cname.name        = 'test_10' 
                my_cname.rdata       = 'ghs.google.com'
                my_cname.type        = 5
                my_cname.debug       = True
                success = my_cname.post(session,domain_name)
                if not success:
                    error = my_cname.error
                else:
                    print 'NEW DNS CREATED!!!!!'
        et= time()
        print TimeTools.duration(bt,et)

        assert success,error

    def testCnameDelete(self, login_name=DEFAULT_LOGING_NAME,
                               password=DEFAULT_LOGING_NAME_PASSWORD,
                               domain_name = DEFAULT_DOMAIN_NAME,     
                               debug=False):
        '''
        Synopsis:
            Deletes a DNS record.
        Expected results
        '''
        print self.testCnameDelete.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-domain_name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))
        bt = time()
        #loging into Godaddy
        session = GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        success = session.get()
        if not success:
            error = session.error
        else:
                my_cname = DNSRecord()
                #my_cname.domain_name =  domain_name 
                my_cname.name        = 'imap' 
                my_cname.type        = 5
                success = my_cname.delete(session,domain_name)
                if not success:
                    error = my_cname.error
                else:
                    print 'Warning: ' + my_cname.error
        et= time()
        print TimeTools.duration(bt,et)

        assert success,error
    
    def testMxPost (self, login_name  = DEFAULT_LOGING_NAME,
                          password    = DEFAULT_LOGING_NAME_PASSWORD,
                          domain_name = DEFAULT_DOMAIN_NAME,     
                          debug       = False):
        '''
        Synopsis:
            Creates a MX DNS Record.
        '''
        print self.testMxPost.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-domain_name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))
        bt = time()
        #loging into Godaddy
        session = GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        success = session.get()
        if not success:
            error =  self.error
        else:
            my_mx = DNSRecord()
            my_mx.domain_name = DEFAULT_DOMAIN_NAME
            my_mx.name        = '@'
            my_mx.rdata       = 'ASPMX.L.GOOGLE.COM.'
            my_mx.priority    = 10
            my_mx.type        = 15
            my_mx.TTL         = 604800   #1 week
            my_mx.debug       = True
            success = my_mx.post(session,domain_name)
            if not success:
                error = my_mx.error
        et= time()
        print TimeTools.duration(bt,et)
        
        assert success,error

    def testGoogleMxConfiguration (self, login_name  = DEFAULT_LOGING_NAME,
                                         password    = DEFAULT_LOGING_NAME_PASSWORD,
                                         domain_name = DEFAULT_DOMAIN_NAME,     
                                        debug       = False):
        '''
        Synopsis:
            Creates a MX DNS Record.
        '''
        print self.testMxPost.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-domain_name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))
        bt = time()
        #loging into Godaddy
        session = GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        success = session.get()
        if not success:
            error =  self.error
        else:
            my_mx = DNSRecord()
            my_mx.domain_name = DEFAULT_DOMAIN_NAME
            my_mx.type        = 15
            my_mx.TTL         = 604800   #1 week
            ########################################
            #
            #   MX Record #1
            #
            ########################################
            my_mx.name        = '@'
            my_mx.rdata       = 'ASPMX.L.GOOGLE.COM.'
            my_mx.priority    = 10
            bt= time()
            success1 = my_mx.post(session)
            et= time()
            print TimeTools.duration(bt,et)
            if not success1: error1 = my_mx.error
            ########################################
            #
            #   MX Record #2
            #
            ########################################
            my_mx.name        = '@'
            my_mx.rdata       = 'ALT1.ASPMX.L.GOOGLE.COM.'
            my_mx.priority    = 20
            bt = time()
            success2 = my_mx.post(session)
            et= time()
            print TimeTools.duration(bt,et)
            if not success2: error2 = my_mx.error
            ########################################
            #
            #   MX Record #3
            #
            ########################################
            my_mx.name        = '@'
            my_mx.rdata       = 'ALT2.ASPMX.L.GOOGLE.COM.'
            my_mx.priority    = 30
            bt = time()
            success3 = my_mx.post(session)
            et= time()
            print TimeTools.duration(bt,et)
            if not success3: error3 = my_mx.error
            ########################################
            #
            #   MX Record #4
            #
            ########################################
            my_mx.name        = '@'
            my_mx.rdata       = 'ASPMX2.GOOGLEMAIL.COM.'
            my_mx.priority    = 40
            bt = time()
            success4 = my_mx.post(session)
            et= time()
            print TimeTools.duration(bt,et)
            if not success4: error4 = my_mx.error            
            ########################################
            #
            #   MX Record #4
            #
            ########################################
            my_mx.name        = '@'
            my_mx.rdata       = 'ASPMX3.GOOGLEMAIL.COM.'
            my_mx.priority    = 50
            bt = time()
            success5 = my_mx.post(session)
            et= time()
            print TimeTools.duration(bt,et)
            if not success5: error5 = my_mx.error         
        
        
        assert success,error

    def testMxDelete (self, login_name  = DEFAULT_LOGING_NAME,
                          password    = DEFAULT_LOGING_NAME_PASSWORD,
                          domain_name = DEFAULT_DOMAIN_NAME,     
                          debug       = False):
        '''
        Synopsis:
            Deletes a MX DNS Record.
        '''
        print self.testMxDelete.__doc__
        print 'Arguments:\n-login: %s\n-password: %s\n-domain_name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))
        bt = time()
        #loging into Godaddy
        session = GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        success = session.get()
        if not success:
            error =  self.error
        else:
            my_mx = DNSRecord()
            my_mx.domain_name = DEFAULT_DOMAIN_NAME
            my_mx.name        = '@'
            my_mx.rdata       = 'gooogle.mail.server.com'
            my_mx.priority    = 10
            my_mx.type        = 15
            my_mx.TTL         = 604800   #1 week
            my_mx.debug       = True
            success = my_mx.post(session)
            if not success:
                error = my_mx.error
        et= time()
        print 'Duration:' +  TimeTools.duration(bt,et)
        
        assert success,error 
        
    def testDeleteGdCnameMxDNSConfig(self,login_name = DEFAULT_LOGING_NAME,
                                    password = DEFAULT_LOGING_NAME_PASSWORD,
                                    domain_name = DEFAULT_DOMAIN_NAME,
                                    debug = False):
        '''
        Synopsis:
            This test gets all the DNS records
            and deletes them.
        '''
            
        print self.testDeleteGdCnameMxDNSConfig.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-domain name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))                
        #getting the session
        session=GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        start_time = time()
        success = session.get()
        end_time = time()
        print 'Get session:' + TimeTools.duration(start_time,end_time)
        if not success:
            error = session.error
        else:
            my_domain = Domain()
            my_domain.domain_name = domain_name
            start_time = time()
            success = my_domain.get(session,deep=True)
            end_time = time()
            print 'Get domains:' + TimeTools.duration(start_time,end_time)
            if not success:
                error = my_domain.error
            else:
                for rec in my_domain.dns_records:
                    if rec.type==5 or rec.type==15:
                        print 'Deleting DNS record - ' + str(rec.type) + rec.name + rec.rdata
                        start_time = time() 
                        success = rec.delete(session,my_domain.domain_name)
                        end_time = time()
                        print 'Delete:' + TimeTools.duration(start_time,end_time)
                        if not success:
                            error = rec.error
                            break
        assert success, error


    def testDNSZap(self,login_name = DEFAULT_LOGING_NAME,
                                    password = DEFAULT_LOGING_NAME_PASSWORD,
                                    domain_name = DEFAULT_DOMAIN_NAME,
                                    debug = False):
        '''
        Synopsis:
            This test gets all the DNS records
            and deletes them.
        '''
            
        print self.testDNSZap.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-domain name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))                
        #getting the session
        session=GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        start_time = time()
        success = session.get()
        end_time = time()
        print 'Get Session:' + TimeTools.duration(start_time,end_time)
        if not success:
            error = session.error
        else:
            my_dns = DNSRecord()
            start_time = time()
            success = my_dns._zap(session, domain_name)
            end_time = time()
            print 'Zap:' + TimeTools.duration(start_time,end_time)
            if not success:
                error = my_dns.error
            
        assert success, error
        
        
    def testConfigureOneCloud(self,login_name = DEFAULT_LOGING_NAME,
                                    password = DEFAULT_LOGING_NAME_PASSWORD,
                                    domain_name = DEFAULT_DOMAIN_NAME,
                                    debug = False):
        '''
        Synopsis:
            This test sets a domain ready for Google
            Hosted account, as defined in the oneCloud .
               
        oneCloud DNS configuration
        
        #MX RECORDS
        
        Priority   Host    Points to                    TTL
        ---------  ----    -------------------------    ------
        10         @       ASPMX.L.GOOGLE.COM.          1 week
        20         @       ALT1.ASPMX.L.GOOGLE.COM.     1 week
        30         @       ALT2.ASPMX.L.GOOGLE.COM.     1 week
        40         @       ASPMX2.GOOGLEMAIL.COM.       1 week
        50         @       ASPMX3.GOOGLEMAIL.COM.       1 week 
        
        CNAME
        
        CName        Address
        --------     ----------------
        www          ghs.google.com
        mail         ghs.google.com
        docs         ghs.google.com
        calendar     ghs.google.com
        sites        ghs.google.com
        blog         ghs.google.com     
        '''
        print self.testConfigureOneCloud.__doc__
        print 'Arguments:\n-login name: %s\n-password: %s\n-domain name: %s\n-debug: %s' % \
                  (login_name,password,domain_name,str(debug))  
        ##########################################################################
        #        
        #getting the session
        #
        ##########################################################################
        start_function = time()
        session=GdSession(debug=debug)
        session.login_name = login_name
        session.password   = password
        start_time = time()
        success = session.get()
        end_time = time()
        print 'Get Session:' + TimeTools.duration(start_time,end_time)
        if not success:
            error = session.error
        else:
            ##########################################################################
            #        
            #Zapping current CNAMES and MX records
            #
            ##########################################################################
            my_dns = DNSRecord()
            start_time = time()
            print 'Initiating DNS configuration ZAPPING... please be patient....'
            success = my_dns._zap(session, domain_name)
            end_time = time()
            print 'Zap:' + TimeTools.duration(start_time,end_time)
            if not success:
                error = my_dns.error
            else:
                error=''
                ########################################
                #
                #   ++++++++ M X   R E C O R D  ++++++++ 
                #
                ######################################## 
                my_mx = DNSRecord()
                my_mx.type        = 15
                my_mx.TTL         = 604800   #1 week
                ########################################
                #
                #   MX Record #1
                #
                ########################################
                my_mx.name        = '@'
                my_mx.rdata       = 'ASPMX.L.GOOGLE.COM.'
                my_mx.priority    = 10
                bt= time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success:
                    error = my_mx.error
                else:
                    print 'successfully created MX record:\n-CName: '+ \
                           my_mx.name+'\n-Address: ' + \
                           my_mx.rdata +'\n-Priority: ' + \
                           str(my_mx.priority)
                ########################################
                #
                #   MX Record #2
                #
                ########################################
                my_mx.name        = '@'
                my_mx.rdata       = 'ALT1.ASPMX.L.GOOGLE.COM.'
                my_mx.priority    = 20
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created MX record:\n-CName: '+ \
                           my_mx.name+'\n-Address: ' + \
                           my_mx.rdata +'\n-Priority: ' + \
                           str(my_mx.priority)
                ########################################
                #
                #   MX Record #3
                #
                ########################################
                my_mx.name        = '@'
                my_mx.rdata       = 'ALT2.ASPMX.L.GOOGLE.COM.'
                my_mx.priority    = 30
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created MX record:\n-CName: '+ \
                           my_mx.name+'\n-Address: ' + \
                           my_mx.rdata +'\n-Priority: ' + \
                           str(my_mx.priority)
                ########################################
                #
                #   MX Record #4
                #
                ########################################
                my_mx.name        = '@'
                my_mx.rdata       = 'ASPMX2.GOOGLEMAIL.COM.'
                my_mx.priority    = 40
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created MX record:\n-CName: '+ \
                           my_mx.name+'\n-Address: ' + \
                           my_mx.rdata +'\n-Priority: ' + \
                           str(my_mx.priority)
                ########################################
                #
                #   MX Record #4
                #
                ########################################
                my_mx.name        = '@'
                my_mx.rdata       = 'ASPMX3.GOOGLEMAIL.COM.'
                my_mx.priority    = 50
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created MX record:\n-CName: '+ \
                           my_mx.name+'\n-Address: ' + \
                           my_mx.rdata +'\n-Priority: ' + \
                           str(my_mx.priority)
                ########################################
                #
                #   ++++++++ C N A M E  ++++++++ 
                #
                ########################################            
                my_mx.type        = 5
                my_mx.TTL         = 3600   #1 HOUR
                ########################################
                #
                #   CNAME Record #1
                #
                ########################################
                my_mx.name        = 'www'
                my_mx.rdata       = 'ghs.google.com'
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created CNAME record:\n-CName: '\
                    + my_mx.name+'\n-Address: ' + my_mx.rdata  
                ########################################
                #
                #   CNAME Record #2
                #
                ########################################
                my_mx.name        = 'mail'
                my_mx.rdata       = 'ghs.google.com'
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created CNAME record:\n-CName: '+\
                     my_mx.name+'\n-Address: ' + my_mx.rdata  
                ########################################
                #
                #   CNAME Record #3
                #
                ########################################
                my_mx.name        = 'docs'
                my_mx.rdata       = 'ghs.google.com'
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created CNAME record:\n-CName: '+\
                     my_mx.name+'\n-Address: ' + my_mx.rdata  
                ########################################
                #
                #   CNAME Record #4
                #
                ########################################
                my_mx.name        = 'calendar'
                my_mx.rdata       = 'ghs.google.com'
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created CNAME record:\n-CName: '+\
                     my_mx.name+'\n-Address: ' + my_mx.rdata  
                ########################################
                #
                #   CNAME Record #5
                #
                ########################################
                my_mx.name        = 'sites'
                my_mx.rdata       = 'ghs.google.com'
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created CNAME record:\n-CName: '+\
                     my_mx.name+'\n-Address: ' + my_mx.rdata  
                ########################################
                #
                #   CNAME Record #6
                #
                ########################################
                my_mx.name        = 'sites'
                my_mx.rdata       = 'ghs.google.com'
                bt = time()
                success = my_mx.post(session,domain_name)
                et= time()
                print TimeTools.duration(bt,et)
                if not success: 
                    error = error + '\n' + my_mx.error
                else:
                    print 'successfully created CNAME record:\n-CName: '+\
                     my_mx.name+'\n-Address: ' + my_mx.rdata  
        
        end_function = time()
        print 'Total function duration was ' + TimeTools.duration(start_function, end_function)
        
        assert success, error



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    #unittest.main()
    my_test = GodaddyServiceTestCase()
    #my_test.testPotencialdomainGet(debug=False,domain_name='nealwalters-new')
    #my_test.testGdSessionGet()
    #my_test.testGdAccountGet(debug=False)
    #my_test.testDomainGet(domain_name='GOVERNMENTCLOUD.COM')
    #my_test.testDomainPost('franciscorocha.com')
    #my_test.testGdAccountPost('xpto1', 'xptp2', 'filipe.pinto@yahoo.com')
    #my_test.testShoppingCartDelete()
    #my_test.testShoppingCartGet()
    #my_test.testCnamePost(debug=True)
    #my_test.testMxPost(debug=True)
    #my_test.testCnameDelete(debug=True)
    #my_test.testGoogleMxConfiguration(debug=True)
    #my_test.testDeleteGdCnameMxDNSConfig(domain_name = 'BESTEMPLOYEEBENEFITSNOW.COM')
    #my_test.testDomainGet(domain_name='GOVERNMENTCLOUD.COM',deep=True)
    #my_test.testDNSZap(domain_name='EXTREMEBPM.COM')
    #my_test.testConfigureOneCloud(domain_name='HIMSGURU.COM')
    my_test.testDomainPut(domain_name='HIMSGURU.COM',debug=True)
    
