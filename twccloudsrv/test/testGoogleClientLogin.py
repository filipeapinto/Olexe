'''
Created on Aug 23, 2009

@author: fpinto
'''

import urllib
import urllib2
import httplib2


#defining the uri
uri = 'https://www.google.com/accounts/ClientLogin'
#defining the headers
#headers = WebTools.firefox_headers()
headers = {}
headers['content-type']= 'application/x-www-form-urlencoded'
#defining the body
data = dict()  
data['Email'      ] = self.email
data['Passwd'     ] = self.password
data['accountType'] = 'HOSTED_OR_GOOGLE'
data['source'     ] = 'cumulus'
data['service'    ] = 'writely'

#submitting the request
if env is None:
    self.error = 'env is not defined'
    return False
elif env == 'httplib2':        
    client = httplib2.Http()
    try:
        response, content = client.request (uri, 'POST', urllib.urlencode(data), headers= headers)
    except Exception, ex:
        self.error = ex.message
        return False
elif env=='urlfetch':
    self.error = 'env not yet implemented'
    return False
elif env=='urllib2':
    request = urllib2.Request(uri,data=urllib.urlencode(data),headers=headers)
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError, ex:
        self.error = ex.message            
        return False
    print 'Response Status : ' + str(response.code)
    print 'Headers         : ' + str(response.info())
    print 'Content         : ' + response.read()
    print 'URL             : ' + response.geturl()
    return False
    
#moving to step 2

print 'Content: ' + content