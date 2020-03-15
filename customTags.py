from google.appengine.ext.webapp import template
register = template.Library() 

def floatcomma(value):
    """
    Converts a float to a string containing commas every three digits.
    For example, 3000.65 becomes '3,000.65' and -45000.00 becomes
'-45,000.00'.
    """
    orig = force_unicode(value)
    intpart, dec = orig.split(".")
    intpart = intcomma(intpart)
    return ".".join([intpart, dec])

floatcomma.is_safe = True
register.filter(floatcomma)