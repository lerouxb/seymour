from django.conf import settings
from django.http import HttpResponseRedirect


class RedirectMiddleware(object):
    """
    Redirect if the app is accessed via the wrong domain.
    """
    
    def process_request(self, request):
        # lighttpd+fastcgi deployment hack
        request.path = request.path.replace('/main.fcgi', '')
        
        host = request.META.get('HTTP_HOST', '')        
        if host != settings.SEYMOUR_DOMAIN and host != 'm.'+settings.SEYMOUR_DOMAIN:        
            return HttpResponseRedirect('http://'+settings.SEYMOUR_DOMAIN+request.path)
