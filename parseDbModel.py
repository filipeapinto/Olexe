
#
#  attempt to build django form from dbModel 
#

import re 
import string 
#The parser reads a variable dbModelCode.  I keep old models handy by leaving them here in 
#for future re-use testing in other variables names such as dbModelCode2,3,4,... 

def firstLetterLower(text): 
  #make the first letter only lower case 
  text = text[0:1].lower() + text[1:]
  return text
def firstLetterUpper(text): 
  #make the first letter only lower case 
  text = text[0:1].upper() + text[1:]
  return text

#this goes at the top of report and updateForm (allows you to inherit some base template) 
formFrontMatter = """
{%extends "baseMain.html"%}
{%block body%}
"""

dbModelCode = """
class Feedback(db.Model):
  submittedDateTime        = db.DateTimeProperty(auto_now=True)
  subscriber               = db.ReferenceProperty(Subscriber, collection_name='subscriber_feedback') #formDisplay=lastname #reportLookup:firstname,lastname,state,country 
  rating                   = db.IntegerProperty()    #5-star rating: number between 1 to 5 (5=best, 1=worst)
  comments                 = db.TextProperty()       #free form paragraph text         #reportDetail 
  relatedURL               = db.StringProperty()     #page where feedback originated   
  feedbackType             = db.StringProperty(choices=('feedback','defect','ticket'),default='feedback')
  department               = db.StringProperty(choices=('software','billing','resources','support','website'),default='website')
#checkbox fields available when users choose 1=bad or 2=poor on rating 
  isDefect                 = db.BooleanProperty(default=False)
  isCumbersome             = db.BooleanProperty(default=False)
  isUgly                   = db.BooleanProperty(default=False)
  isImStuck                = db.BooleanProperty(default=False)
#the following fields are set by internal admins only, user will probably not see these
  adminStatus              = db.StringProperty(choices=('software','billing','resources','support'))
  adminPriority            = db.IntegerProperty()  #number between 1-10, 10 is highest priority 
"""

dbModelCodeTest1 = """
class Document(db.Model):
  docId                  = db.StringProperty()                 #formReadOnly
  docName                = db.StringProperty()   
  keywords               = db.ListProperty(db.Key)             #formSkip 
  title                  = db.StringProperty()   
  subtitle               = db.StringProperty()   
  summary                = db.StringProperty() 
  authorName             = db.StringProperty()  
  authorEmail            = db.StringProperty() 
                            #could use MIME media type as well?   http://www.iana.org/assignments/media-types/
  mediaType              = db.StringProperty(choices=('blog','audio','video','picture','link'))
  isGDoc                 = db.BooleanProperty(default=False) 
  isExternalLink         = db.BooleanProperty(default=False) 
  externalLink           = db.StringProperty() 
  language               = db.StringProperty()   #English,Spanish, etc... 
                            #could potentiall have "length" attribute to show user approximate size of article 
  dateTimePublished       = db.DateTimeProperty(auto_now=False)
  dateTimeCreated         = db.DateTimeProperty(auto_now=False)  #formReadOnly 
  dateTimeLastModified    = db.DateTimeProperty(auto_now=True)   #formReadOnly
  userEmailCreated        = db.StringProperty()                  #formReadOnly
  userEmailLastModified   = db.StringProperty()                  #formReadOnly
"""

dbModelCodeTest2 = """
class Book(db.Model):
  name                   = db.StringProperty()
  keywordPrefix          = db.StringProperty() 
  appliesTo              = db.StringProperty(choices=('ALL','serviceType')) 
  serviceType            = db.ReferenceProperty(ServiceType, collection_name='ServiceType_Book') #formDisplay=name#
"""

#colonParts = dbModelCode.split(":") 
#print "left=" + colonParts[0] 
#print "right=" + colonParts[1] 

#tablename = "Document".lower()  #Todo Parse this instead of typing it here 
tablename = "temp" 


lines = dbModelCode.split("\n") 
print "num lines = " + str(len(lines))
dbvars = [] 
for line in lines: 
  
  print line 

  #skip any lines that start with a comment symbol 
  if line.strip()[0:1] == "#": 
     print "skip comment line" 
     continue 

  if "db.Model" in line:
        print "found db.model, looking for tablename with regex" 
        pattern = "class (.+?)\(db\.Model\):"
        regexMatch = re.findall(pattern, line, re.IGNORECASE)
        if len(regexMatch) < 1: 
           raise Exception("Error looking for tableName parsing pattern=" + pattern + " number of matches = " + str(len(regexMatch)))
        tablename = regexMatch[0]
        print "tablename = '" + tablename + "'" 

  if "=" in line:

     #print "line=" + line 
     parts = line.split("=") 
     var1 = parts[0].strip()
     print "var1='" + var1 + "'" 
     referenceTablename = None
     referenceTableFieldname = None 
     if "db.ReferenceProperty" in line:
        print "found db.ReferenceProperty, looking for tablename with regex" 
        fieldType = "db.ReferenceProperty" 
        #NOTE: escape character before real parentheses, other parentheses are for extracting groups f
        pattern = "db.ReferenceProperty\((.+?), collection_name='.+?'\) #formDisplay=(.+?)#"
        regexMatch = re.findall(pattern, line, re.IGNORECASE)
        if len(regexMatch) < 1: 
           #for (counter,item) in enumerate(regexMatch):
           #for item in regexMatch: 
           #   print "Match  value=" + str(item)
           raise Exception("Error parsing pattern=" + pattern + " number of matches = " + str(len(regexMatch)) + "\n\n perhaps you need to add the #formDisplay tag to this line") 
        referenceTablename = regexMatch[0][0]
        referenceTableFieldname = regexMatch[0][1] 
        print "referenceTablename='" + referenceTablename + "'" 
        print "referenceTableFieldname='" + referenceTableFieldname + "'" 
        #x = 0/0 # - stop to see results 

     if "db.BooleanProperty" in line:
        fieldType = "db.BooleanProperty" 

     if "db.StringProperty" in line:
        fieldType = "db.StringProperty" 

     if "db.IntegerProperty" in line:
        fieldType = "db.IntegerProperty" 

     if "db.TextProperty" in line:
        fieldType = "db.TextProperty" 

     if "db.DateTimeProperty" in line:
        fieldType = "db.DateTimeProperty" 

     if "#formReadOnly" in line: 
        readOnly = True 
     else:
        readOnly = False 

     if "#formSkip" in line: 
        skip = True 
     else:
        skip = False 

     keyword = "#reportLookup"
     reportLookupFieldnames = [] 
     if keyword in line: 
        #sample tag:  #reportLookup:firstname,lastname,state,country 
        pos = line.find(keyword)
        print "pos=" + str(pos) 
        if pos > 0: 
           textAfterReportLookup = string.strip(line[pos+1+len(keyword):])
           reportLookupFieldnames = textAfterReportLookup.split(",")
           print "Number of lookupFieldnames found=" + str(len(reportLookupFieldnames))
           for item in reportLookupFieldnames:
              print "   lookupFieldname=" + item 
           
        print "textAfterReportLookup='" + textAfterReportLookup + "'" 

        

     #choices=('blog','audio','video','picture','link')
     if "choices=" in line:
        choices = True 
        parts = line.split("choices=") 
        choiceList = parts[1].replace(")","") 
        choiceList = choiceList.replace('"','')
        choiceList = choiceList.replace('(','')
        choiceValues = choiceList.split(",") 
        for choiceValue in choiceValues: 
            print "choice=" + choiceValue
        #build a Python code file - to help display these values on a form 
        code = "class " + firstLetterUpper(var1) + "Choices(db.Model): #this table is never stored \n"
        code += "    value    = db.StringProperty() \n" 
        code += "    selected = db.BooleanProperty() \n" 
        code += " \n"
        code += var1 + "Choices = []\n" 
        for choiceValue in choiceValues: 
           choiceValue = choiceValue.replace("'","")
           code += var1 + "Choices.append(" + firstLetterUpper(var1) + 'Choices(value="' + choiceValue + '",selected=False)) \n'
        code += " \n"

        #now build code to be used later in updateTablename 
	#to properly handle the above lists... 
        lookupArrays = ""
	lookupArrays += """

	for item in &var1 + Choices:
           if item.value == &tablenameLower.appliesTo: 
              item.selected = True 
           else: 
              item.selected = False 
	"""
	lookupArrays = lookupArrays.replace("&var1",var1) 


        filename = firstLetterUpper(tablename) + "_" + firstLetterUpper(var1) + "Choices.py"
        FILE = open(filename,"w") 
        FILE.writelines(code) 
        FILE.close()
        print "Wrote code to filename=" + filename 

     else:
        choices = False 
     dbvars.append({"fieldName":var1,
                    "fieldType":fieldType,
                    "readOnly": readOnly, 
                    "skip": skip,
                    "choices": choices,
                    "referenceTablename": referenceTablename,
                    "referenceTableFieldname": referenceTableFieldname,
                    "reportLookupFieldnames": reportLookupFieldnames
                    })

print '===============SUMMARY=================================='
for dbvar in dbvars:    
    print dbvar['fieldName'] + " type=" + dbvar['fieldType']
print '========================================================'


#-----------------------------------------------------------------
# Build Update form left/right columnName = Fieldname format 
#-----------------------------------------------------------------
print "=====STARTING TO BUILD UPDATE FORM====="
html = formFrontMatter 
html += "<h3>Update " + tablename + "</h3>\n" 
html += "<form action=/upd" + firstLetterUpper(tablename) + " method=post>\n" 
html += "<table border=1>\n"
for dbvar in dbvars: 
  print "Fieldname=" + dbvar['fieldName']
  if not dbvar['skip']:
    html += "<tr>\n"
    html += '  <td>&nbsp;'+ firstLetterUpper(dbvar['fieldName']) + ':</td>\n'
    #TODO - handle other types here, such as Boolean 
    html += '  <td>\n'
    if dbvar['choices']:
       html += '   <select id="' + dbvar['fieldName'] + '" name="' + dbvar['fieldName'] + '"> \n'
       html += '     <option value="">Select One</option> \n' 
       html += '     {% for item in ' + dbvar['fieldName'] + 'Choices %} \n'
       html += '     <option value="{{item.value}}" {% if item.selected %} selected {% endif %}>{{item.value}}</option>   \n'
       html += '     {% endfor %} \n'
       html += '   </select> \n'
    elif dbvar['fieldType'] == "db.ReferenceProperty":
       print "handling ReferenceProperty with referenceTablename = " +  str(dbvar['referenceTablename'])
       html += '   <select id="' + dbvar['fieldName'] + '" name="' + dbvar['fieldName'] + '"> \n'
       html += '     <option value="">Select One</option> \n' 
       html += '     {% for item1 in ' + dbvar['referenceTablename'] + 'List %} \n'
       html += '     <option value="{{item1.key}}" {% ifequal item1.' + dbvar['referenceTableFieldname'] + " " +  dbvar['referenceTablename'] +'.' + dbvar['fieldName']  + ' %} selected {% endifequal %}>{{item1.' + dbvar['referenceTableFieldname'] + '}}</option>   \n'
       html += '     {% endfor %} \n'
       html += '   </select> \n'
    elif dbvar['fieldType'] == "db.BooleanProperty":
       html += ' &nbsp;True: <input type=radio name=' + dbvar['fieldName'] + ' value="True" \n'
       html += '  {%if ' + firstLetterLower(tablename) + "." + dbvar['fieldName'] + '%} checked {% endif %}>\n' 
       html += ' &nbsp;&nbsp;False: <input type=radio name=' + dbvar['fieldName'] + ' value="False" \n' 
       html += '  {%if not ' + firstLetterLower(tablename) + "." + dbvar['fieldName'] + '%} checked {% endif %}> \n' 
    else: 
       #Assume for now, everthing that is not boolean is string, TODO - add other types here 
       if dbvar['readOnly']:
          html += '  &nbsp;{{' + firstLetterLower(tablename) + '.' + dbvar['fieldName'] + '}}\n'
       else:
          html += '  &nbsp;<input type=text name=' + dbvar['fieldName'] + ' size=24 value="{{' + firstLetterLower(tablename) + '.' + dbvar['fieldName'] + '}}">\n'
    html += '  </td>\n'
    html += "</tr>\n"

html += "</tr>\n"
#final row with submit button 
html += "\n<tr>\n" 
html += "   <td>&nbsp;</td>\n" 
html += '   <td><input type=submit value="Update"</td>\n'
html += "<tr>\n" 
html += "</table>\n" 
html += '<input type="hidden" name="key" value="{{' + tablename + '.key}}">\n' 
html += "</form>\n" 
html += "<br/><br/><br/>\n" 
html += "{%endblock%}\n"
print html 

filename = "update" + firstLetterUpper(tablename) + ".html" 
FILE = open(filename,"w") 
FILE.writelines(html) 
FILE.close()
print "Wrote html to filename=" + filename 

#-----------------------------------------------------------------
# Build Python update statements in this format: 
# document.subtitle = self.request.get('subtitle') 
#-----------------------------------------------------------------

print "=====Writing Python Code to Update this Table ====="
code = ""

#NOTE: we will use .replace statements to change the &xxx variables in the code below 
#TODO - should read this in from a file 
code +=   """
class Update&tablenameCap(webapp.RequestHandler):

  def renderPage(self, fileName, values):
    path = os.path.join(os.path.dirname(__file__),fileName)
    self.response.out.write(template.render(path, values)) 

  def get(self):
    mySession = Session() 
    command = self.request.get("cmd") 

    key = self.request.get('key')
    if key <= " " and command != "ADD":
          self.response.out.write("<h3>Missing ?key= parameter on URL</h3>") 
          return 

    &tablenameLower = &tablenameCap() 
    if key > " ":
        &tablenameLower = &tablenameCap.get(self.request.get('key')) 
        if not &tablenameLower:
           self.response.out.write("<h3>&tablenameCap not found with key=" + key + "</h3>") 


    templateDictionaryLocal = {"&tablenameLower":&tablenameLower
&lookupArrays
                              }
                               
    templateDictionaryGeneral = getSharedTemplateDictionary("",self.request.url, [], '', 0)  
    templateDictionaryLocal.update(templateDictionaryGeneral)
    self.renderPage('templates/update&tablenameCap.html', templateDictionaryLocal)

  def post(self):
     debugText = "" 
     mySession = Session()
     params = {}
     params = commonUserCode(params,self.request.url)
     currentUser = "Temp" 
     if 'username' in mySession:
        currentUser = mySession['username'] 

     key = self.request.get('key')

     &tablenameLower = &tablenameCap()   #create new object (in case we are doing an ADD instead of Modify) 
     #&tablenameLower.dateTimeCreated = datetime.datetime.now() 
     #&tablenameLower.userCreated = currentUser
     #above two fields will be reset if we are doing modified and have the key below...

     if key > ' ': 
        &tablenameLower = &tablenameCap.get(key) 
        if not &tablenameLower:
           self.response.out.write("<h3>&tablenameCap not found with key=" + key + "</h3>") 


&updateFieldsCode 
     &tablenameLower.put()      
     self.redirect("/report&tablenameCap")    


"""

updateFieldsCode = "" 
indent = "     "
for dbvar in dbvars:

   if dbvar['readOnly'] or dbvar['skip']: 
      comment = "#"    #generate the syntax, but leave it commented-out 
   else:
      comment = "" 

   #boolean must be converted back from string "True" or "False"
   if dbvar['fieldType'] == "db.BooleanProperty": 
      cast1 = "eval(" 
      cast2 = ") #use eval() not bool() " 
   else: 
      cast1 = "" 
      cast2 = "" 
   updateFieldsCode += (comment + indent + firstLetterLower(tablename) + "." + dbvar['fieldName'] + 
           " = " + cast1 + "self.request.get('" + dbvar['fieldName']  + "')" + cast2 + " \n") 
   #document.subtitle = self.request.get('subtitle') 


code = code.replace("&updateFieldsCode" ,updateFieldsCode)
code = code.replace("&lookupArrays"     ,lookupArrays)
code = code.replace("&tablenameLower",firstLetterLower(tablename)) 
code = code.replace("&tablenameCap"  ,firstLetterUpper(tablename)) 




filename = "Update" + firstLetterUpper(tablename) + ".py"
FILE = open(filename,"w") 
FILE.writelines(code) 
FILE.close()
print "Wrote code to filename=" + filename 

  
#-----------------------------------------------------------------
# Build Report Format - columns across top, fields under 
#-----------------------------------------------------------------
formatInputOrDisplay = "Display" 
print "=====STARTING TO BUILD REPORT FORMAT====="
html = formFrontMatter 
html += "<h3>" + tablename + "Report</h3>" 
html += "<a href='/upd" + tablename + "cmd=ADD'>Add new " + tablename + "</a> <br/>\n" 
html += "<table border=1>\n"
html += "<tr>\n"
html += "  <th>Row</th>\n"
for dbvar in dbvars:
   if dbvar['fieldType'] == "db.ReferenceProperty":
      if len(dbvar['reportLookupFieldnames']) > 0: 
         for item in dbvar['reportLookupFieldnames']: 
             suffix = "<br/>" + item   #example book.serviceType.name  where ".name" is the suffix 
             html += "  <th>" + firstLetterUpper(dbvar['fieldName']) + suffix + "</th>\n" 
   else:
      html += "  <th>" + firstLetterUpper(dbvar['fieldName']) + "</th>\n" 
html += "</tr>\n"
html += "{%for " + firstLetterLower(tablename) + " in " + firstLetterLower(tablename) + "List%} \n" 
html += "<tr>\n"
#special row for row/counter link 

html += "<td><a href='/upd" + tablename + "?key={{" + firstLetterLower(tablename) + ".key}}'>&nbsp;{{forloop.counter}}&nbsp;</a></td>"


for dbvar in dbvars: 
   suffix = "" 
   print "var=" + dbvar['fieldName']

   if dbvar['fieldType'] == "db.ReferenceProperty":
      if len(dbvar['reportLookupFieldnames']) > 0: 
         #suffix = "." + dbvar['referenceTableFieldname']   #example book.serviceType.name  where ".name" is the suffix 
         for item in dbvar['reportLookupFieldnames']: 
           suffix = "." + item   #example book.serviceType.name  where ".name" is the suffix 
           if formatInputOrDisplay == "Display": 
             html += '    <td>{{' + firstLetterLower(tablename) + '.' + dbvar['fieldName'] + suffix + '}}</td>\n'
           else:
             html += '    <td><input type=text name=' + dbvar['fieldName'] + ' value="{{' + firstLetterLower(tablename) + '.' + dbvar['fieldName'] + suffix + '}}"></td>\n'
   else: 
      if dbvar['fieldType'] == "db.DateTimeProperty":
         formatString = '|date:_("m/d/y h:i:s")'
      else: 
         formatString = ''

      if formatInputOrDisplay == "Display": 
         html += '    <td>{{' + firstLetterLower(tablename) + '.' + dbvar['fieldName'] + suffix + formatString + '}}</td>\n'
      else: 
         html += '    <td><input type=text name=' + dbvar['fieldName'] + ' value="{{' + firstLetterLower(tablename) + '.' + dbvar['fieldName'] + suffix + formatString + '}}"></td>\n'

html += "</tr>\n"
html += "{%endfor%}\n" 
#final row with submit button 
html += "<!--Add or Remove this submit button as needed " 
html += "<tr>\n" 
html += '   <td><input type=submit value="Update"></td>\n'
for dbvar in dbvars: 
   html += "<td>&nbsp;</td>\n" 
html += "/<tr>\n" 
html += "-->"
html += "</table>\n" 
html += "<br/><br/><br/>\n" 
html += "{%endblock%}\n"
print html 

filename = "report" + firstLetterUpper(tablename) + "s.html" 
FILE = open(filename,"w") 
FILE.writelines(html) 
FILE.close()
print "Wrote html to filename=" + filename 


