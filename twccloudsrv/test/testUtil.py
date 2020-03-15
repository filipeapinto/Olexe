'''
Created on Aug 19, 2009

@author: fpinto

Synopsis:
    This module tests the util.py module from the
    twccloudsrv package.
    
    The test class doesn't derive from unittest. The reason
    is because we need to have tests that never run the same
    exact configuration twice.


Date      Author        Description
--------  ------------- -------------------------------------------------------
09-13-09  fpinto        Started editing the file accordingly to the 3WC testing
                        rules.   


'''
import unittest

from twccloudsrv.util import WebTools


class Test(unittest.TestCase):
    
    def testRemoveCookie(self):
        current_cookie = 'ASP.NET_SessionId=20jyiyrhwd2sie55n3fd4zbo;adc1=US;currency1=potableSourceStr=USD;flag1=cflag=us;currencypopin1=cdisplaypopin=false;traffic=cookies=1&referrer=https://www.godaddy.com/domains/register.aspx?ci=13686&sitename=www.godaddy.com&page=/domains/register.aspx&server=CORPWEB107&status=200 OK&querystring=ci=13686&shopper=4467367&privatelabelid=1&isc=&clientip=68.19.115.231&referringpath=&referringdomain=;gdMyaHubble1=ShopperID=pavhadqhqdjekahhejzandsjrjmgsdfh&Hubble=True;MemAuthId1=uiubfhgicjmeyhyhcfdacgxdyambqiihqamcldadwaldlcpjtagjnfqhmjtiwcga;ShopperId1=qdtelfwdravdqirenikdtdbjzafbbald;MemShopperId1=potableSourceStr=xcncdibcjawcbaidifzbciefeahejedj;MemPDC1=;MemPDCLoc1=;ASPSESSIONIDQQQRBDBT=DBCFIPMBJMEDBGIGLHECGLIM;'
        
        new_cookie = WebTools.remove_cookie(current_cookie,'ASP.NET_SessionId')
        
        new_cookie = WebTools.remove_cookie(new_cookie,'ASPSESSIONID',match='prefix')
        print new_cookie
        
        assert new_cookie=='adc1=US;currency1=potableSourceStr=USD;flag1=cflag=us;currencypopin1=cdisplaypopin=false;traffic=cookies=1&referrer=https://www.godaddy.com/domains/register.aspx?ci=13686&sitename=www.godaddy.com&page=/domains/register.aspx&server=CORPWEB107&status=200 OK&querystring=ci=13686&shopper=4467367&privatelabelid=1&isc=&clientip=68.19.115.231&referringpath=&referringdomain=;gdMyaHubble1=ShopperID=pavhadqhqdjekahhejzandsjrjmgsdfh&Hubble=True;MemAuthId1=uiubfhgicjmeyhyhcfdacgxdyambqiihqamcldadwaldlcpjtagjnfqhmjtiwcga;ShopperId1=qdtelfwdravdqirenikdtdbjzafbbald;MemShopperId1=potableSourceStr=xcncdibcjawcbaidifzbciefeahejedj;MemPDC1=;MemPDCLoc1=;', 'test failed'


    def testUpdateCookie(self):
        current_cookie = 'traffic=cookies=1&referrer=https://www.godaddy.com/domains/searchresults.aspx?ci=8962&sitename=www.godaddy.com&page=/domains/stack.aspx&server=CORPWEB177&status=200 OK&querystring=ci=13676&shopper=4467367&privatelabelid=1&isc=&clientip=68.211.86.79&referringpath=&referringdomain=;'
        new_cookie    = 'traffic=cookies=1&referrer=https://www.godaddy.com/domains/register.aspx?ci=13686&sitename=www.godaddy.com&page=/domains/register.aspx&server=CORPWEB177&status=200 OK&querystring=ci=13686&shopper=4467367&privatelabelid=1&isc=&clientip=68.211.86.79&referringpath=&referringdomain=; domain=godaddy.com; path=/'
        
        new_cookie = WebTools.normalize_cookie(new_cookie)
        
        
        assert WebTools.update_cookie(current_cookie, new_cookie) == new_cookie, "update cookie not working correctly"
        

def testCookieDict():
    import httplib
    httplib.debug = 1
    conn = httplib.HTTPSConnection('www.google.com')
    headers = WebTools.firefox_headers()
    uri = 'https://www.google.com/a/filipe-pinto.com/ServiceLogin?service=CPanel&continue=https%3A%2F%2Fwww.google.com%3A443%2Fa%2Fcpanel%2Ffilipe-pinto.com%2FDashboard&passive=true'
    conn.request("GET", uri ,headers=headers)
    httplib_resp = conn.getresponse()
    print httplib_resp.getheader('set-cookie')
    print str (WebTools.cookie_dict(httplib_resp.getheader('set-cookie')))
    
class TWebTools():
    
    def test_rm_script_tag(self):
        '''
        Synopsis:
            Opens a file that contains the html
        Arguments:
        Expected results:
        '''
        file = open('test_html.html','r')
        html = file.read()
        content = WebTools.rm_script_tag(html)
        print content

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    #unittest.main()
    #testCookieDict()
    
    t_webtools = TWebTools()
    t_webtools.test_rm_script_tag()
    