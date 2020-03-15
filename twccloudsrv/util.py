'''
Created on Aug 25, 2009

@author: fpinto


Synopsis:
    This is the util class for the 3wc-cloudservices
    package


Date      Author        Description
--------  ------------- -------------------------------------------------------
09-13-09  fpinto        Started editing with 3WC best practices.
                        Added rm_script_tag(html)to remove script tags from html.

'''

import re
import string
import urlparse
import urllib

class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None
 
    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
 
        return cls.instance

class TimeTools():
    '''
    '''
    
    @staticmethod
    def duration(strt,end):
        '''
        Synopsis:
            Calculates the duration in minutes
            between two events
        Arguments
            strt : start time
            end  : end time
        Exceptions:
        Returns: duration in minutes    
        '''
        duration = end - strt
        minutes = int(duration/60)
        seconds = duration - (minutes*60)
        return '%d:%d' % (minutes, seconds)


class WebTools():
    '''
    Synopsis:
        This class assists with web scraping
    '''
    
    @staticmethod
    def firefox_headers():
        '''
        Synopsis:
            Simulates Mozilla browser headers
        Arguments:
            None
        Exceptions:
            None
        Returns:
            Firefox http headers dictionary
        '''
        headers = dict()
        headers['User-agent'     ]= 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1'
        headers['Accept'         ]= 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers['Accept-Language']= 'en-us,en;q=0.5'
        #headers['Accept-Encoding']= 'gzip,deflate'
        headers['Accept-Charset' ]= 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
        return headers

    @staticmethod
    def rm_script_tag(html):
        '''
        Synopsis:
            Removes script tags from HTML
        Arguments:
            None
        Exceptions:
            None
        Returns:
            Firefox http headers dictionary
        '''
        p = re.compile('<script.*?>.*?</script>', re.S)
        return p.sub('', html)

    
if __name__=='__main__':
    print 'This is not a testing module'
