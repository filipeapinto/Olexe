'''
Created on Sep 2, 2009

@author: fpinto
'''

from BeautifulSoup import BeautifulSoup, SoupStrainer
import re
import string
import sys

##########################################
#
# LinkedIn tests
#
##########################################

file = open ('linkedin-invite.html')
content = file.read()

pattern = SoupStrainer('form', {'name':'invitation' })

node = BeautifulSoup(content, parseOnlyThese=pattern)

if node==None:
    print'there was an error finding the form'
else:
    uri = node.form['action']
    print 'URI:' + uri
    inputs  = node.findAll('input',{'type':'hidden'})
    data=dict()
    for input in inputs:  data[input['name']]=input['value']

        
print data
    

