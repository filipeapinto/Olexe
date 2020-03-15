'''
Created on Jul 14, 2009

@author: fpinto
'''

class CumulusObject(object):
    '''
    Represents the base class of all objects in the 
    cumulus system.
    '''
    def __init__(self):
        '''
        '''
        self.error = ''
        self.debug = False
