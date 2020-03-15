'''
Created on Jul 17, 2009

@author: fpinto
'''


import sys
import re
import os
import string
from BeautifulSoup import BeautifulSoup
import jsonpickle

#file = open ('url-forwarding.html')
#content = file.read()

#pattern='<td class=\'rrHeading\' width.*?>(.*?)</td>.*?<table.*?>(.*?)</table>'
#lines=re.findall(pattern, content, re.S)
#for line in lines:
#    print line[0]
#    pattern='<td class=\'rr\'.*?>(.*?)</td>'
#    lines=re.findall(pattern, line[1], re.S)
#    for line in lines: print line

#pattern='<td class=\'rrHeading\' width.*?>(.*?)</td>.*?<table.*?>(.*?)</table>'
#servers=re.findall(pattern, content, re.S)
#for server in servers:
#    print server[0]
#    if not server[0]=='MX (Mail Exchange)':
#        pattern='<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?'
#    else:
#        pattern='<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>.*?<td class=\'rr\'.*?>(.*?)</td>'
#    lines=re.findall(pattern, server[1], re.S)
#    for line in lines: print line

#pattern = '(User Name|Customer Number):.*?<strong>(.*?)</strong>'
#subscriber_data = re.findall(pattern, content, re.S)
#print subscriber_data

'''
pattern='input type="hidden" name="(.*?)".*?value="(.*?)"'
hidden_inputs_1 = re.findall(pattern,content, re.S)
if len(hidden_inputs_1)==0:
    self.error = self.__class__.__name__+'.'+ \
                 sys._getframe().f_code.co_name + \
                 ' @line:' + str(sys._getframe().f_lineno) + \
                 '\nUnable to find hidden fields with pattern %s in %s' % (pattern,form_content)
print str(hidden_inputs_1)
'''
'''
Provider: ?????????
#Retrieving 2nd set hidden attributes
pattern='input name="(.*?)" type="hidden" id=".*?" (value="(.*?)")*'
hidden_inputs_2 = re.findall(pattern,content)
if len(hidden_inputs_2)==0:
    self.error = self.__class__.__name__+'.'+ \
                 sys._getframe().f_code.co_name + \
                 ' @line:' + str(sys._getframe().f_lineno) + \
                 '\nUnable to find hidden fields with pattern %s in %s' % (pattern,form_content)
for field in hidden_inputs_2:
    print str(field)
    
'''

text = '<div class="alert success"> \n\
            <p><strong>Invitation to Adalbero Jasmin (adaberto.jasmin@portcall.pt) sent.</strong></p>\
            <span class="dismiss" id="global-error-dismiss"></span>'

'''
first_name = 'Adalbero'
last_name  = 'Jasmin'
email      = 'adaberto.jasmin@portcall.pt'

pattern = 'Invitation to %s %s \(%s\) sent' % (first_name, last_name, email)

print pattern
results = re.findall(pattern, text) 
print results
'''
'''
#google sites ws return
content ='[true,"ok",{"revision":1,"main/text":"\u003Ctable xmlns=\"http://www.w3.org/1999/xhtml\" cellspacing=\"0\" class=\"sites-layout-name-one-column sites-layout-hbox\"\u003E\u003Ctbody\u003E\u003Ctr\u003E\u003Ctd class=\"sites-layout-tile sites-tile-name-content-1 sites-layout-empty-tile\"\u003E \u003C\/td\u003E\u003C\/tr\u003E\u003C\/tbody\u003E\u003C\/table\u003E","sys/layout":"one-column"}]'
list_items = string.split(content, ',')
pattern='"(.*?)":"?(((?!"}|"$).)*)"?'
ws_result={}
for item in list_items[2:5]:
    tmp= re.findall(pattern,item)
    print tmp
    ws_result[tmp[0][0]]=tmp[0][1].decode("unicode-escape")
print ws_result
'''

#pattern = '\[true,"ok",{(.*?)}\]'
#pattern='\[(.*?),(.*?),{("(.*?)":["]?(.*?)["|,]?)*}\]'
#content ='{"revision":1,"main/text":"\u003Ctable xmlns=\"http://www.w3.org/1999/xhtml\" cellspacing=\"0\" class=\"sites-layout-name-one-column sites-layout-hbox\"\u003E\u003Ctbody\u003E\u003Ctr\u003E\u003Ctd class=\"sites-layout-tile sites-tile-name-content-1 sites-layout-empty-tile\"\u003E \u003C\/td\u003E\u003C\/tr\u003E\u003C\/tbody\u003E\u003C\/table\u003E","sys/layout":"one-column"}'
#pattern = '(?<={|,)"(.*?)":(?!\\) 
#results = re.findall(pattern, content)
#for match in results:
# print match
#print results
#dict = results[0]
#print 'Dict: '+ str(dict)
#ws_results={}
#pairs = string.split(dict, ',')
#pattern = '"(.*?)":"?(.*)'
#for i in pairs:
#    print i
#    results = re.findall(pattern, i)
#    print str(results[0][0]) + ':                    :' + str(results[0][1])
#    #ws_results[eval(i[0])]=eval(i[1])

#pattern = '"(.*?)":(.*?),'
#list_values = string.split(content,',',2)
#dict_pairs = string.split(list_values[2],',')
#ws_result = {}
#for pair in dict_pairs:
#    print pair
#    pattern = '.*?"(.*?)":"(.*)"'
#    key_value = re.findall(pattern, pair)
#    #print pair_value
#    ws_result[key_value[0][0]] = key_value[0][1]
    
#print ws_result

#results =  string.split(content, ',',2)
#print results[2]
    
#results = results[2].decode("unicode-escape")
#print results 

#json = jsonpickle.decode(results[2])

#pattern = '"(.*?)":(.*),'
#pair_values = string.split(results[2], ',') 
#pair_values = re.findall(pattern, results[2])
#for pair in pair_values:
#    print pair

string = '{"component/4989141843497884/type":"/system/app/components/min-textbox","component/2bd/indentImgSrc":"/system/app/images/icon_right.gif","component/3895508987321945/showSiteMap":false,"config/search/settings/default":"search-site","component/3895508987321945/navigationTree":"{\"children\":[{\"id\":\"wuid:gx:ffefa98919eca61\",\"title\":\"Home\",\"path\":\"/home\"},{\"id\":\"wuid:gx:488a63f06d7cc1ee\",\"title\":\"My Blog\",\"path\":\"/Blog\"},{\"id\":\"wuid:gx:1ae9bc2984e63028\",\"title\":\"My Books\",\"path\":\"/Books\"},{\"id\":\"wuid:gx:75cf2adff74b0e3f\",\"title\":\"My Expertise\",\"path\":\"/Expertise\"},{\"id\":\"wuid:gx:642ff7f0596b538b\",\"title\":\"My Pictures\",\"path\":\"/Pictures\"},{\"id\":\"wuid:gx:5f3966f7c236937d\",\"title\":\"My Resume\",\"path\":\"/Resume\"},{\"id\":\"wuid:gx:3a2fe8124b334cad\",\"title\":\"My Social\",\"path\":\"/Social\"},{\"id\":\"wuid:gx:11f1a96c63a59bd\",\"title\":\"My Videos\",\"path\":\"/Videos\"}]}","component/11463227729236292/event":"Certification A","config/sidebarRef":"30bf","component/3895508987321945/navDynamicDepth":999,"component/30bf/type":"/system/app/components/sidebar","config/siteWidth":"100%","component/11463227729236292/type":"/system/app/components/min-countdown","component/3895508987321945/indentImgSrc":"/system/app/images/icon_right.gif","component/3895508987321945/type":"/system/app/components/min-navigation","component/2bd/navigationTree":"{\"children\":[{\"id\":\"wuid:gx:ffefa98919eca61\",\"title\":\"Home\",\"path\":\"/home\"},{\"id\":\"wuid:gx:488a63f06d7cc1ee\",\"title\":\"My Blog\",\"path\":\"/Blog\"},{\"id\":\"wuid:gx:1ae9bc2984e63028\",\"title\":\"My Books\",\"path\":\"/Books\"},{\"id\":\"wuid:gx:75cf2adff74b0e3f\",\"title\":\"My Expertise\",\"path\":\"/Expertise\"},{\"id\":\"wuid:gx:642ff7f0596b538b\",\"title\":\"My Pictures\",\"path\":\"/Pictures\"},{\"id\":\"wuid:gx:5f3966f7c236937d\",\"title\":\"My Resume\",\"path\":\"/Resume\"},{\"id\":\"wuid:gx:3a2fe8124b334cad\",\"title\":\"My Social\",\"path\":\"/Social\"},{\"id\":\"wuid:gx:11f1a96c63a59bd\",\"title\":\"My Videos\",\"path\":\"/Videos\"}]}","component/5737448586549224/content":"\u003Cdiv dir=\"ltr\"\u003Ethis is a text\u003C\/div\u003E","config/activeTheme":"iceberg","config/logoPath":"DEFAULT_LOGO","config/headerHeight":"90","component/11463227729236292/fromDateUTC":"1254283200000","component/4989141843497884/title":"Bio","component/5737448586549224/type":"/system/app/components/min-textbox","component/2bd/title":"NAV1","component/2bd/outdentImgSrc":"/system/app/images/icon_left.gif","component/2bd/showRecents":false,"component/2bd/navDynamicDepth":2,"component/3895508987321945/outdentImgSrc":"/system/app/images/icon_left.gif","config/version":"20","component/3895508987321945/title":"NAV2","component/4989141843497884/content":"\u003Cdiv dir=\"ltr\"\u003EThis is my bio\u003C\/div\u003E","component/2bd/type":"/system/app/components/min-navigation","component/30bf/items":["2bd","3895508987321945","4989141843497884","11463227729236292","5737448586549224"],"config/bodyId":"goog-ws-left","component/2bd/hideTitle":true,"component/3895508987321945/showRecents":false,"config/landingPage":"wuid:gx:ffefa98919eca61","component/3895508987321945/hideTitle":false,"component/5737448586549224/title":"Bio","component/2bd/showSiteMap":false,"config/sidebarWidth":"180","sys/hidden":true}'
#pattern = '"component/(.*?)/(.*?)":.*?(?=(?:,"component/.*?/.*?":"))'
#pattern = '"(component/.*?)":(.*?)(?=(?:,"component/.*?":"))'
pattern = '"((?:component|config|sys)/.*?)":(.*?)(?=(?:,"(?:component|config|sys)/.*?":)|}$)'
results = re.findall(pattern, string)
for result in results:
    print result

print '  -----------------------> END'