from django.db import connection
from django.conf import settings


def auth(request):
    try:
        return {
            'account': request.account,            
        }
    except AttributeError:
        return {}

def constants(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    host = request.META.get('HTTP_HOST', '')
    
    is_ie5 = "MSIE 5" in user_agent
    is_ie55 = "MSIE 5.5" in user_agent
    is_ie6 = "MSIE 6.0" in user_agent
    is_ie7 = "MSIE 7" in user_agent    
    is_firefox = 'Firefox' in user_agent
    
    is_ipod = 'iPod' in user_agent
    is_iphone = 'iPhone' in user_agent
    is_android = 'Android' in user_agent
    
    is_mobile_override = host[:2] == 'm.'
    #is_mobile_override = True # testing..
    
    #from django.db import connection
        
    d = {        
        'is_firefox': is_firefox,
        'is_ie5': is_ie5,
        'is_ie55': is_ie55,
        'is_ie6': is_ie6,
        'is_ie7': is_ie7,
        'is_ipod': is_ipod,
        'is_ipod': is_ipod,
        'is_iphone': is_iphone,
        'is_android': is_android,
        'is_mobile_override': is_mobile_override,
        'is_mobile': is_ipod or is_iphone or is_android or is_mobile_override,
        'sitename': settings.SITENAME,
        'sql_queries': connection.queries        
    }   
        
    return d
