'''
Created on Aug 20, 2009

@author: fpinto
'''
import unittest


class Test(unittest.TestCase):


    def testName(self):
        import poplib

        M = poplib.POP3('mail.3wcloud.com')
        M.user('oss@3wcloud.com')
        M.pass_('kmlus.6765')
        numMessages = len(M.list()[1])
        for i in range(numMessages):
            for j in M.retr(i+1)[1]:
                print j


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()