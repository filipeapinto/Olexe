'''
Created on Aug 18, 2009

@author: fpinto
'''

import string
import urllib


def test_string_format():

    error=''

    domain_name='sddsdfusfs'

    parsed_domain =string.split(domain_name,'.')

    if len(parsed_domain)<>2:
        error = 'domain name not well configured %s' % (domain_name)
    if len(parsed_domain[1]) not in (2,3):
        error = 'domain name has incorrect domain %s'  % (domain_name)
            
    print 'Error: ' + error
    
def test_comprehensions():
    
    data = {}  
    data['ctl00$MainContent$ucRegisterDomains$ddlRegistrationLengthForAll'] = '1'
    data['ctl00$MainContent$CustomizeOrCart'                              ] = 'rbToCart'      # by looking at Fiddler body
    data['ctl00$MainContent$ucDomainTestimonials$collapse1_ClientState'   ] = 'false'         # by looking at Fiddler body
    data['ctl00$MainContent$ucRegisterDomains$hfDomainsListView'          ] = ''
    data['__EVENTTARGET'                                                  ]= 'ctl00$MainContent$lbContinue'
    data['rbgCertifiedDomainForAll'                                       ]= '0'           # by looking at Fiddler body
    data['rbgAddSmartSpace'                                               ]= '6577'        # by looking at Fiddler body 
    
    
    #creating the request body
    #request_body =string.join([string.join([k,v],'=') for k, v in data.iteritems()],'&')
    print request_body
    request_body = urllib.urlencode(request_body)
    print request_body
        
        
        

if __name__ == '__main__':
    
    test_comprehensions()