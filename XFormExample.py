class XForm(webapp.RequestHandler):
 
  def get(self):
      self.response.headers['Content-Type'] = "text/xml"
      ### <submission action="http://localhost:8080/xformsubmit"
      self.response.out.write("""
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xforms="http://www.w3.org/
2002/xforms">
  <head>
    <title>A sample XHTML+XForms document</title>
<model xmlns="http://www.w3.org/2002/xforms" id="p1">
  <instance>
    <task xmlns="">
      <function/>
      <taskCode/>
      <issues/>
      <resultFlag/>
    </task>
  </instance>
<submission xmlns="http://www.w3.org/2002/xforms"
  id="s0" method="post"
action="http://localhost:8080/xformsubmit"/>

</model>

</head>


<body>

<input xmlns="http://www.w3.org/2002/xforms"
  model="p1" ref="function" class="edit" value="StartTask" type="hidden">
</input>
<br/>

<input xmlns="http://www.w3.org/2002/xforms"
  xmlns:ev="http://www.w3.org/2001/xml-events"
  model="p1" ref="issues" class="edit" 
  ev:event="DOMActivate" ev:handler="#speak">
  <label>Issue(s)</label>
  <help>What issues, if any, did you have with this step? (Help)</help>
  <hint>What issues, if any, did you have with this step? (Hint)</hint>
</input>
<br/>

<select1 xmlns="http://www.w3.org/2002/xforms"
  ref="resultFlag" appearance="full" accesskey="R">
  <label>Results:</label>
  <item>
    <label>Success</label>
    <value>0</value>
  </item>
  <item>
    <label>Issue(s)</label>
    <value>1</value>
  </item>
  <item>
    <label>ShowStopper</label>
    <value>2</value>
  </item>
</select1>

<submit xmlns="http://www.w3.org/2002/xforms"
  submission="s0"><label>Submit</label>
</submit>


</body>
</html>
""")

  def post(self):
     self.response.out.write(
      "1 Python found your submitted value = " + 
         self.request.get('s')
     )

class XFormSubmit(webapp.RequestHandler):

  def post(self):
    # self.response.out.write(
    #  "Post: Python found your submitted value = " + 
    #     self.request.get('s')
    # )


        #Thus, the following should work (untested!):
        #from: http://markmail.org/message/5eimlxspdyxcgcpo#query:HTTP%20RAW%20POST%20-php%20python+page:1+mid:muliwierakgyi55i+state:results
        #import cgi, sys, cStringIO
        #copyInput = cStringIO.StringIO(sys.stdin.read())
        #fieldStorage = cgi.FieldStorage(copyInput)
        #The raw posted data are now available as the string returned
        #by calling copyInput.getvalue(), and are also parsed by cgi to
        #obtain fieldStorage.

     self.response.out.write(
         "My New Heading<BR/>" 
          )

     data = self.request.body
     fixline = data.replace("<","&lt;");
     fixline = fixline.replace(">","&gt;");
     self.response.out.write(
       "Post3: Python found your submitted value = " + 
          fixline + "<BR/>" 
        )

     #data = sys.stdin.readlines()
     
     #for eachline in data:
     #  self.response.out.write(
     #    "Post2: Python found your submitted value = " + 
     #       fixline + "<BR/>" 
     #     )


