'''
Created on Jun 27, 2009

@author: fpinto

This package contains all the super classes for the cloud
service package.  Different cloud operators have different ways
to implement their services but at a minimum all classes will
have a minimum of functionality.


Date      Author        Description
--------  ------------- ------------------------------------------
09-09-09  fpinto        Added locale to Site
09-13-09  fpinto        Added TwcSiteTemplate and TwcOneCloudTemplate
09-21-09  fpinto        Added SiteComponent class

'''
import cookielib


class CumulusCloudObject(object):
    '''
    Represents a generic OSS objects.
    All OSS classes derive from this class
    '''
    def __init__(self):
        '''
        constructor
        '''
        self.error = ''
        self.debug = False
        
class Provider(CumulusCloudObject):
    '''
    Represents a generic service provider
    '''
    def __init__(self):
        '''
        '''
        super(Provider, self).__init__()
        name = ''
        url  = ''   

class ProviderSession(CumulusCloudObject):
    '''
    Represents a service provider session
    
    TODO: implement a CookieJar
    '''
    def __init__(self):
        '''
        '''
        super(ProviderSession, self).__init__()
        self.login_name = ''
        self.password   = ''
        self.email      = ''
        self.cookiejar  = cookielib.CookieJar()

class ProviderAccount(CumulusCloudObject):
    '''
    Represents a Provider Account under which all services 
    are provisioned (services reside on the cloud in an account.
    The credentials associated with services are centralized 
    at the level of the Provider Account. No other login functions 
    will be allowed. A SERVICE in the cloud needs an account 
    to exist. The same ACCOUNT can have multiple services.
    '''
    def __init__(self):
        '''
        constructor
        '''
        super(ProviderAccount, self).__init__()
        self.password       = ''
        self.user_name      = ''
        self.account_number = ''
        self.password_hint  = ''
        self.first_name     = ''
        self.last_name      = ''
        self.email          = ''
        self.pin            = ''
        self.debug          = False
        self.services       = []


class ProviderShoppingCart(CumulusCloudObject):
    '''
    Represents a service provider session
    '''
    def __init__(self):
        '''
        '''
        super(ProviderShoppingCart, self).__init__()
        self.items = []

class ProviderPotentialDomain(CumulusCloudObject):
    '''
    Synopsis:
        Represents a domain that has yet to be claimed
        by anyone, or that has POTENTIAL to become a 
        real domain service.
    '''
    def __init__(self):
        super(ProviderPotentialDomain,self).__init__()
        self.domain_name       = ''
        self.is_available      = None
        self.alternative_names = []


class Service(CumulusCloudObject):
    '''
    '''
    def __init__(self):
        '''
        '''
        super(Service, self).__init__()

class ServiceResource(CumulusCloudObject):
    '''
    Represents a generic a resource that is
    managed by the service 
    '''
    def __init__(self):
        '''
        '''
        super(ServiceResource, self).__init__()
        self.name        = ''
        self.description = ''
        self.type        = ''
        #self.uri         = ''
        self.template    = ''
        self.is_public   = None

class ServiceComponent(CumulusCloudObject):
    '''
    Represents a generic a component of a service
    '''
    def __init__(self):
        '''
        '''
        super(ServiceComponent, self).__init__()
        self.description = None
        self.type        = None
        self.id          = None

class DNSRecord(CumulusCloudObject):
    '''
    This class represents DNS record.        
    '''
    def __init__(self):
        '''
        constructor 
        '''
        super(DNSRecord, self).__init__()
        self.priority   = None    #priority - if '-1' then it's not defined 
        self.name       = ''      #Name of the node to which this record pertains
        self.type       = None    #Type of record: A=1,CNAME=5,MX=15
        self.class_code = ''      #Class code
        self.TTL        = None    #Signed time in seconds that RR stays valid (-1 means not set)
        self.rdata      = ''      #Additional Resource Record-specific data

    @staticmethod
    def _dns_type(type):
        '''
        Synopsis:
            Returns the numeric type associated with the
            DNS record type passed as argument
        Arguments:
            type: string
        Exceptions:
        Returns:
            type  : numeric type
        '''
        if string.lstrip(line[0]) == 'A':
            type = 1
        else:
            if string.lstrip(line[0]) == 'CNAME':
                type = 5
            else:
                if string.lstrip(line[0]) == 'MX':
                    type = 15
                else:
                    if string.lstrip(line[0]) == 'NS':
                        type = 2

     
class DomainService(Service):
    '''
    Represents a domain services, which contains
    a list of name servers, and a list of 
    DNS records.
    '''
    
    def __init__(self):
        super(DomainService, self).__init__()
        self.domain_name           = ''
        self.registration_date     = ''
        self.expiration_date       = ''
        self.status                = ''
        self.is_forwarding         = None
        self.forwarding_uri        = ''
        self.is_private            = None
        self.dns_records           = list()


class HostedDomainService(Service):
    '''
    Represents the ability to host a domain
    '''
    def __init__(self):
        '''
        constructor
        '''
        super(HostedDomainService,self).__init__()
        self.domain_name = ''


class DocumentService(Service):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(DocumentService, self).__init__()
        max_quota=''
        
class Document(ServiceResource):
    '''
    represents a document that can be word, excel, powerpoint
    '''
    def __init__(self):
        '''
        Constructor
        '''
        super(Document, self).__init__()


class VideoService(Service):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(VideoService, self).__init__()
        max_quota=''

class Video(ServiceResource):
    '''
    represents a video
    '''
    pass

        
class EmailService(Service):
    '''
    Represents a generic email account
    '''
    
    def __init__(self):
        '''
        '''
        super(EmailService, self).__init__()
        self.max_storage=''
        
class Email(ServiceResource):
    '''
    represents an email
    '''
    pass

    
class BlogService(Service):
    '''
    Represents a generic blog account.
    '''
    
    def __init__(self):
        '''
        '''
        super(BlogService, self).__init__()


class BlogEntry(ServiceResource):
    '''
    Represents a generic blog entry.
    '''
    
    def __init__(self):
        '''
        '''
        super(BlogEntry, self).__init__()
    

class MicroBlogService(Service):
    '''
    Represents a generic blog account.
    '''
    
    def __init__(self):
        '''
        '''
        super(MicroBlogService, self).__init__()


class MicroBlogEntry(ServiceResource):
    '''
    Represents a generic blog entry.
    '''
    
    def __init__(self):
        '''
        '''
        super(MicroBlogEntry, self).__init__()

    
class PhotoService(Service):
    '''
    Represents a generic photo account.
    '''
    
    def __init__(self):
        super(PhotoService, self).__init__()
        
        
class Photo(ServiceResource):
    '''
    Represents a photo.
    '''    
    def __init__(self):
        '''
        '''
        super(Photo, self).__init__()
    
class CalendarService(Service):
    '''
    Represents a generic calendar service.
    '''
    
    def __init__(self):
        '''
        '''
        super(CalendarService, self).__init__()
        
class Calendar(ServiceResource):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(Calendar, self).__init__()        
    
class SiteService(Service):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(SiteService, self).__init__()
        
class Site(ServiceResource):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(Site, self).__init__()
        self.url                = ''
        self.locale             = ''
        self.name               = ''
        self.description        = ''
        self.title              = ''
        self.tags               = []    

class SitePage(ServiceResource):
    '''
    Represents a generic a site page.
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        super(SitePage, self).__init__()
        self.relative_uri = ''             #relative path to the root example - /books
        self.title        = ''
        self.description  = ''
        self.tags         = []
        self.content      = ''
        self.attachments  = []

class SiteComponent(ServiceComponent):
    '''
    Represents a generic a site navigation menu.
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        super(SiteComponent, self).__init__()
        self.title         = None
        self.is_hide_title = None


class SiteTemplate(CumulusCloudObject):
    '''
    Synopsis:
        Represents a website template
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        super(SiteTemplate,self).__init__()
        self._tags = None

class OneCloudTemplate(SiteTemplate):
    '''
    Synopsis:
        Represents a 3WC OneCloud Basic Site that 
        should be able to be provisioned in any
        type of provider that enables website service
    '''
    def __init__(self):
        '''
        constructor
        '''
        super(OneCloudTemplate,self).__init__()
        self.root             = ''
        self.owner_first_name = ''
        self.owner_last_name  = ''
        self.owner_email      = ''
        self.owner_password   = ''
    
    #Tags    
    def get_tags(self):
        return self._tags
    def set_tags(self, value):
        if type(value) is list:
            self._tags = value
        else:
            raise Exception('sorry on list assignments can be performed')
    tags = property(get_tags, set_tags,'tags to be associated with the site')
        
class ChatService(Service):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(ChatService, self).__init__()
        
class Chat(ServiceResource):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(Chat, self).__init__()               


class SocialConnectionService(Service):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(SocialConnectionService, self).__init__()
        
class SocialConnection(ServiceResource):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(SocialConnection, self).__init__()
        self.first_name = ''
        self.last_name  = ''
        self.email      = ''
                      

class QuestionService(Service):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(QuestionService, self).__init__()
        
class Question(ServiceResource):
    '''
    Represents a generic site service.
    '''
    
    def __init__(self):
        '''
        '''
        super(Question, self).__init__()               



'''
Main
'''
if __name__=='__main__':
    pass
    print '<please see cumulus.oss.xxx.test> module to perform any tests'  