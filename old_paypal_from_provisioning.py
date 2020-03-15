
#This is a big chunk of code removed form provision.py in the SubmitOrder routine. 

# After dealing more with Paypal, discovered that it 99% not likely to be used. 


     #the following might go in config file 
     imageURL = "http://3wcloud.com/images/PaypalLogo.png" 
     business = "nwalters@sprynet.com"   #account on Paypal where payment will be sent 
     returnURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalSuccess'))
     cancelReturnURL =  str(atom.url.Url('http', settings.HOST_NAME, path='/PaypalFailure'))



     #TODO = lookup serviceTypeDescription from ServiceType table 

     serviceTypeDescription = "oneCloud-Individual" 

     #TODO = lookup these fields in RatePlan corresponding to ServiceType 
     recurringAmount = 12 
     onetimeAmount = 25 
     billingPeriod = "M" 
     billingInterval = 1 
     numberOfPayments = 0 

     onetimePaymentDict = {
          'a1':onetimeAmount,
          'p1':'1',
          't1':'D',
          'on1': 'One Time Setup Fee',
          'os1': '$25 one time setup fee charged first day'
          }
    
     recurringPaymentDict = {
          'cmd': "_xclick-subscriptions",
          'image_url': imageURL,
          'business': business, 
          'item_name': serviceTypeDescription,
          'a3': recurringAmount,
          'p3': billingInterval,
          't3': billingPeriod,
          'src': '1',
          'sra': '1',
          'on0': 'Subscription Option:',
          'os0': 'Monthly Membership ',      #might want to put $xx in front of this  
          'no_note': '1',
          'return': returnURL,
          'rm':'2',                          #specifies full data via Post when Paypal returns 
          'cancel': cancelReturnURL,
          'currency_code': 'USD',
          'upload': '1'
          }


     #some services may have onetime amount, others might not
     #  if both exist, copy in the oneTimePayment dictionary into the larger existing recurringPaymentDict 
     if onetimeAmount > 0 and recurringAmount: 
        recurringPaymentDict.update(onetimePaymentDict) 

     #TODO - need slightly different cmd= and post if we have a fixed amount and NO recurring amount 
     #       and other variables will be slightly different - no immediate need to code this 

     import urllib 
     from google.appengine.api import urlfetch

     #paypalData = urllib.urlencode(recurringPaymentDict)   #urlencode always acts on a dictionary 

     #http-post body from fiddler: cmd=_xclick-subscriptions&image_url=http%3A%2F%2F3wcloud.com%2Fimages%2FPaypalLogo.png&item_name=oneCloud-Individual&a3=12.00&p3=1&t3=M&a1=25.00&p1=1&t1=D&src=1&sra=1&on0=Subscription+Option%3A&os0=%2412+monthly+membership+&on1=One+Time+Setup+Fee&os1=%2425+one+time+setup+fee+charged+first+day+&no_note=1&return=http%3A%2F%2F3wcloud.com%2FPaypalPaid&cancel_return=http%3A%2F%2F3wcloud.com%2FPaypalCancelled&business=nwalters@sprynet.com&currency_code=USD&upload=1&submit.x=92&submit.y=9
     #paypalForm = paypalForm.replace(&os1",formatCurrency(fixedAmt) + " one time setup fee charged first day") 



     # The change request required that we now go to home page. 
     # This requires full login of that user as if he had enter the login page 
     # (which he skipped because he filled out user/pass on an order form). 
     # Retrieve session row based on email/password so myHome page will display everything properly 

     query = db.GqlQuery("SELECT * FROM Subscriber WHERE userEmail = :1 ", session.userEmail)   
     LIMIT = 2 
     subscriberList = query.fetch(LIMIT,offset=0);

     if len(subscriberList) == 0: 
        signinError = "ERROR: Username " + session.userEmail + " not found in Subscriber database after SubmitOrder" 
        self.renderPage('templates/customer/signin.html', 
                     {"postback": "Y", 
                      "action": "login", 
                      "signinError": signinError,
                      "now": datetime.datetime.now()
                      }
                     ) 
        log = CumulusLog()    #log invalid signins  
        log.category  = "OneCloudSetupIndivSubmit:Get" 
        log.message   = signinError 
        log.ipaddress = self.request.remote_addr 
        log.put() 
        return   #return now so the redirect below doesn't go back to MyHome
                 #thus losing the signinError message 
     else:        
        mySession['subscriberkey'] = subscriberList[0].key()  
        mySession['username'] = session.userEmail 
        subscriber = subscriberList[0] 
        if subscriber.isAdmin: 
           mySession['isAdmin'] = True 
        else:
           mySession['isAdmin'] = False 

     mySession['OneCloudStatus'] = "Inactive"   #don't show the mail/docs/calendar links on myHome 

     templateDictionaryLocal = {"userMessage": "",
                                "debugText": debugText,
                                "showUserPass": showUserPass, 
                                "dynamicHTML": dynamicHTML, 
                                "returnURL":returnURL, 
                                "now": datetime.datetime.now()
                               }

     serviceCode = ""
     page = ""
     templateDictionaryGeneral = getSharedTemplateDictionary(self.request.path,self.request.url, forms, serviceCode, page)
     templateDictionaryLocal.update(templateDictionaryGeneral)
     self.renderPage('templates/customer/home.html', templateDictionaryLocal)
