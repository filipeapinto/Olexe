class PaypalSuccess(webapp.RequestHandler):
  """
  When we send a customer to Paypal, we pass a returnURL /PaypalSuccess, and Paypal posts
  data back to this page (see documentation for a sample). 
  This allows us to flag the order as paid and store the appropriate ServiceRatePlan table. 
  """

  def get(self):
     self.response.out.write("<H1>PayPal Success/GET</H1>") 
     for item in self.request.arguments():
         self.response.out.write("<BR>" + item + " value=" + self.request.get(item)) 

  def post(self):
     mySession = Session() 
     self.response.out.write("<H1>PayPal Success/POST</H1>") 
     paypalIPN = PaypalIPN() 
     strData = ""
     for item in self.request.arguments():
        #paypalIPN.item.append(item) 
        #paypalIPN.itemValue.append(self.request.get(item)) 
        strData += item + "=" + self.request.get(item) + "&" 
        #self.response.out.write("<BR>" + item + " value=" + self.request.get(item)) 
     paypalIPN.dataReceived = strData
     paypalIPN.put()     #create an audit record of exactly what Paypal sends us
                             #we might drop this in the future, but for the first few 
                             #weeks/months of testing, this could be useful. 

     #we passed the id (not the key) to Paypal 
     id = int(self.request.get("invoice")) 
     order = Order.get_by_id(id)            #retrieve existing non-paid order 
     if not order: 
        self.response.out.write("<h3>order not found with id=" + id + "<h3>") 
        return 

     serviceRatePlan = ServiceRatePlan() 
     #TODO - the following is BAD - if order has many services - this could cause big problems.
     #probably need to pass rateplan key to Paypal and back 
     serviceRatePlan.ratePlan = order.services[0].serviceType.ratePlan
     serviceRatePlan.order = order 

     #for first test, assume order just has one service.
     #TODO: might have to pass the service key and order key both to Paypal in the invoice
     #then split them apart... 
     #TODO: also consider that the ratePlan assigned to a serviceType can change 
     #over time.  What if user starts order with one RatePlan, then the RatePlan 
     #is changed by Admin.  Can user still order under old RatePlan? 
     #Or do we also need to pass the RatePlan key to Paypal as another 
     #part of the invoice...and split it back out here?  

     serviceRatePlan.ratePlan = order.services[0].serviceType.ratePlan 
     serviceRatePlan.dateTimeCreated = datetime.datetime.now() 
     serviceRatePlan.paymentType     = "Paypal"

     #the following fields are all posted to this page from Paypal
     serviceRatePlan.payerEmail      = self.request.get("payer_email")
     serviceRatePlan.payerId         = self.request.get("payer_id")
     serviceRatePlan.auth            = self.request.get("auth")
     serviceRatePlan.subscriptionId  = self.request.get("subscr_id")
     serviceRatePlan.put() 

     #because of redirect below - these two messages should not display 
     self.response.out.write("<h2>ServiceRatePlanStored </h2>") 

     order.financialStatus = "PayPal.paid"
     order.put() 
     self.response.out.write("<h2>FinancialStatus updated on Order Record </h2>") 

     objKeyValuePair = KeyValuePair() 
     #this message can be changed by Admin using the interface to the KeyValuePair database 
     mySession['myHomeMessage'] = objKeyValuePair.getValueFromKey("msgPaypalPaid") 
     self.redirect("/myHome")


