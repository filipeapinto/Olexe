from google.appengine.ext import webapp
from dbModels import ServiceType

class StoreBundle(webapp.RequestHandler):

     
  def get(self):

     query = ServiceType.gql("")  #no where clause needed
     LIMIT = 1000
     serviceList = query.fetch(LIMIT,offset=0)
     if len(serviceList) > 0: 
        self.response.out.write("""
            <h1><font color='red'>StoreRows Aborted - ServiceTypes already exist on database</font></h1><br>
            """)
        return 

     serviceType8 = ServiceType(); 
     serviceType8.code                = 'GSite-oneCloud' 
     serviceType8.name                = 'GoogleSite-Public-OneCloud'
     serviceType8.description         = 'This is your OneCloud site' 
     serviceType8.infrastructureName  = '' 
     serviceType8.isSellable          = False  
     serviceType8.isBillingOnly       = False  
     serviceType8.isProvisioningOnly  = True 
     serviceType8.put()

     serviceType9 = ServiceType(); 
     serviceType9.code                = 'GSite-Test' 
     serviceType9.name                = 'GoogleSite-Test'
     serviceType9.description         = '' 
     serviceType9.infrastructureName  = '' 
     serviceType9.isSellable          = False  
     serviceType9.isBillingOnly       = False  
     serviceType9.isProvisioningOnly  = True 
     serviceType9.isSellable      = False  
     serviceType9.put()

     serviceType7 = ServiceType(); 
     serviceType7.code                = 'GoogleSites' 
     serviceType7.name                = 'Google-Sites'
     serviceType7.description         = 'Allows easy-to-customize web sites' 
     serviceType7.infrastructureName  = '' 
     serviceType7.isSellable          = False  
     serviceType7.isBillingOnly       = False  
     serviceType7.isProvisioningOnly  = True 
     serviceType7.children = [serviceType8.key(), serviceType9.key()] 
     serviceType7.put()


     serviceTypeAA = ServiceType(); 
     serviceTypeAA.code                = 'GApp-Base'
     serviceTypeAA.name                = 'Google-App-Base'
     serviceTypeAA.description         = '' 
     serviceTypeAA.infrastructureName  = '' 
     serviceTypeAA.isSellable          = False  
     serviceTypeAA.isBillingOnly       = False  
     serviceTypeAA.isProvisioningOnly  = True 
     serviceTypeAA.put()


     serviceType11 = ServiceType(); 
     serviceType11.code                = 'Mail'
     serviceType11.name                = 'Google-Email'
     serviceType11.description         = 'Complete suite of email tools' 
     serviceType11.infrastructureName  = 'GMail' 
     serviceType11.isSellable          = False  
     serviceType11.isBillingOnly       = False  
     serviceType11.isProvisioningOnly  = True 
     serviceType11.put()


     serviceType12 = ServiceType(); 
     serviceType12.code                = 'Calendar'
     serviceType12.name                = 'Calendar'
     serviceType12.description         = 'Complete calendar tools' 
     serviceType12.infrastructureName  = 'Google-Calendar' 
     serviceType12.isSellable          = False  
     serviceType12.isBillingOnly       = False  
     serviceType12.isProvisioningOnly  = True 
     serviceType12.put()

     serviceType13 = ServiceType(); 
     serviceType13.code                = 'Docs'
     serviceType13.name                = 'Docs'
     serviceType13.description         = 'Word Processing, Spreadsheets, Presentations' 
     serviceType13.infrastructureName  = 'Google-Docs' 
     serviceType13.isSellable          = False  
     serviceType13.isBillingOnly       = False  
     serviceType13.isProvisioningOnly  = True 
     serviceType13.put()


     serviceType4 = ServiceType(); 
     serviceType4.code                = 'GoogApp' 
     serviceType4.name                = 'Google-App-Account'
     serviceType4.description         = 'The oneCloud-organization for businesses and non-profits' 
     serviceType4.infrastructureName  = 'Google-App-Account' 
     serviceType4.isSellable          = False  
     serviceType4.isBillingOnly       = False  
     serviceType4.isProvisioningOnly  = True 
     serviceType4.children = [serviceTypeAA.key(), 
                                         serviceType7.key(), 
                                         serviceType11.key(),
                                         serviceType12.key(),
                                         serviceType13.key()
					 ] 
     serviceType4.put()


     serviceType14 = ServiceType(); 
     serviceType14.code                = 'GAcctProfile'
     serviceType14.name                = 'Google Account Profile'
     serviceType14.description         = ''
     serviceType14.infrastructureName  = 'Google Account Profile' 
     serviceType14.isSellable          = False  
     serviceType14.isBillingOnly       = False  
     serviceType14.isProvisioningOnly  = True 
     serviceType14.put()


     serviceType15 = ServiceType(); 
     serviceType15.code                = 'Blog'
     serviceType15.name                = 'Blogging Tool'
     serviceType15.description         = 'Create/Publish your own blogs'
     serviceType15.infrastructureName  = 'Blogger.com' 
     serviceType15.isSellable          = False  
     serviceType15.isBillingOnly       = False  
     serviceType15.isProvisioningOnly  = True 
     serviceType15.put()


     serviceType16 = ServiceType(); 
     serviceType16.code                = 'Videos'
     serviceType16.name                = 'Video Channel'
     serviceType16.description         = 'Post your own videos to your video-channel' 
     serviceType16.infrastructureName  = 'YouTube-Video' 
     serviceType16.isSellable          = False  
     serviceType16.isBillingOnly       = False  
     serviceType16.isProvisioningOnly  = True 
     serviceType16.put()
     
     serviceType16B = ServiceType(); 
     serviceType16B.code                = 'Photos'
     serviceType16B.name                = 'Photo-Sharing'
     serviceType16B.description         = 'Post and share your photos' 
     serviceType16B.infrastructureName  = 'Picasa-Photos' 
     serviceType16B.isSellable          = False  
     serviceType16B.isBillingOnly       = False  
     serviceType16B.isProvisioningOnly  = True 
     serviceType16B.put()
     
     serviceType16C = ServiceType(); 
     serviceType16C.code                = 'RSS-Reader'
     serviceType16C.name                = 'RSS-Reader'
     serviceType16C.description         = 'RSS Feed-Reader' 
     serviceType16C.infrastructureName  = 'Google-Reader' 
     serviceType16C.isSellable          = False  
     serviceType16C.isBillingOnly       = False  
     serviceType16C.isProvisioningOnly  = True 
     serviceType16C.put()

     serviceType16D = ServiceType(); 
     serviceType16D.code                = 'Alerts'
     serviceType16D.name                = 'News-Alerts'
     serviceType16D.description         = 'Get emails on news relating to your tags' 
     serviceType16D.infrastructureName  = 'Google-Alerts' 
     serviceType16D.isSellable          = False  
     serviceType16D.isBillingOnly       = False  
     serviceType16D.isProvisioningOnly  = True 
     serviceType16D.put()

     serviceType17 = ServiceType(); 
     serviceType17.code                = 'Analytics'
     serviceType17.name                = 'Web-Analytics'
     serviceType17.description         = 'Track web site usage'
     serviceType17.infrastructureName  = 'Google-Analytics' 
     serviceType17.isSellable          = False  
     serviceType17.isBillingOnly       = False  
     serviceType17.isProvisioningOnly  = True 
     serviceType17.put()

     
     serviceType18 = ServiceType(); 
     serviceType18.code                = 'WMTools'
     serviceType18.name                = 'WebMasterTools'
     serviceType18.description         = ''
     serviceType18.infrastructureName  = 'Google WebMasterTools' 
     serviceType18.isSellable          = False  
     serviceType18.isBillingOnly       = False  
     serviceType18.isProvisioningOnly  = True 
     serviceType18.put()


     serviceType19 = ServiceType(); 
     serviceType19.code                = '3WC-KB'
     serviceType19.name                = '3WCloud-Knowledgebase'
     serviceType19.description         = 'Answers, documentsion, videos, how-to guides'
     serviceType19.infrastructureName  = '3WCloud KB' 
     serviceType19.isSellable          = False  
     serviceType19.isBillingOnly       = False  
     serviceType19.isProvisioningOnly  = True 
     serviceType19.put()

     serviceType5 = ServiceType(); 
     serviceType5.code                = 'GoogleAccount' 
     serviceType5.name                = 'Google-Account'
     serviceType5.description         = 'The oneCloud-organization for businesses and non-profits' 
     serviceType5.infrastructureName  = 'Google-Account' 
     serviceType5.isSellable          = False  
     serviceType5.isBillingOnly       = False  
     serviceType5.isProvisioningOnly  = True 
     serviceType5.children = [serviceType14.key(), 
                                         serviceType15.key(), 
                                         serviceType16.key(),
                                         serviceType16B.key(),
                                         serviceType16C.key(),
                                         serviceType16D.key(),
                                         serviceType17.key(),
                                         serviceType18.key()
					 ] 

     serviceType5.put()

     serviceType23 = ServiceType(); 
     serviceType23.code                = '1CloudVideoL' 
     serviceType23.name                = 'oneCloud-Video-Live'
     serviceType23.description         = 'One-minute video, recorded in Atlanta with text/animation added' 
     serviceType23.infrastructureName  = '' 
     serviceType23.isSellable          = True  
     serviceType23.isBillingOnly       = False  
     serviceType23.isProvisioningOnly  = False 
     serviceType23.put()
     

     serviceType24 = ServiceType(); 
     serviceType24.code                = '1CloudVideoP' 
     serviceType24.name                = 'oneCloud-Video-Photos'
     serviceType24.description         = 'One-minute video, you send several photos, voice, text, animation added' 
     serviceType24.infrastructureName  = '' 
     serviceType24.isSellable          = True  
     serviceType24.isBillingOnly       = False  
     serviceType24.isProvisioningOnly  = False 
     serviceType24.put()


     serviceType25 = ServiceType(); 
     serviceType25.code                = 'BlogAMonth'
     serviceType25.name                = 'Blog-a-Month'
     serviceType25.description         = 'Our writers provide one custom blog per month, written to your keywords/topics'
     serviceType25.infrastructureName  = '' 
     serviceType25.isSellable          = True  
     serviceType25.isBillingOnly       = False  
     serviceType25.isProvisioningOnly  = False 
     serviceType25.put()

     # -------------- One-Cloud products --------------
     serviceType1 = ServiceType(); 
     serviceType1.code                = '1CloudI' 
     serviceType1.name                = 'oneCloud-Individual'
     serviceType1.description         = 'The oneCloud-Individual for personal promotion and knowledge management' 
     serviceType1.infrastructureName  = '' 
     serviceType1.isSellable          = True  
     serviceType1.isBillingOnly       = False  
     serviceType1.isProvisioningOnly  = False 
     serviceType1.children = [serviceType4.key(), serviceType5.key(),
                                         serviceType19.key()]
     serviceType1.upsells  = [serviceType23.key(), serviceType24.key(),
                                         serviceType25.key()]
     serviceType1.put()


     serviceType2 = ServiceType(); 
     serviceType2.code                = '1CloudOrg' 
     serviceType2.name                = 'oneCloud-Organization'
     serviceType2.description         = 'The oneCloud-organization for businesses and non-profits' 
     serviceType2.infrastructureName  = '' 
     serviceType2.isSellable          = True  
     serviceType2.isBillingOnly       = False  
     serviceType2.isProvisioningOnly  = False 
     serviceType2.children = [serviceType4.key(), serviceType5.key(), 
                                         serviceType19.key()]
     serviceType2.upsells             = [serviceType23.key(), serviceType24.key(),
                                         serviceType25.key()]
     serviceType2.put()


     serviceType3 = ServiceType(); 
     serviceType3.code                = '1CloudFam' 
     serviceType3.name                = 'oneCloud-Family'
     serviceType3.description         = 'The oneCloud-organization for families' 
     serviceType3.infrastructureName  = '' 
     serviceType3.isSellable          = True  
     serviceType3.isBillingOnly       = False  
     serviceType3.isProvisioningOnly  = False 
     serviceType3.children             = [serviceType4.key(), serviceType5.key(),
                                         serviceType19.key()]
     serviceType3.put()
     

     

     #db.run_in_transaction(self.storeData) 

     self.response.out.write("""
          <h1>StoreRows Completed - Use Admin Tool to View Rows</h1><br>
	  <a href='http://localhost:8081/_ah/admin/datastore'>Admin Tool</a><br>
          <a href='menu'>Back to Menu</a>&nbsp;&nbsp;
          <a href='reportBundle'>Report Bundle</a>&nbsp;&nbsp;
      """)


  