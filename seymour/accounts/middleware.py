from django.conf import settings
from django.http import HttpResponseRedirect
from seymour.accounts.models import Account


class AuthMiddleware(object):
    """
    Make sure the user is logged in before he tries to access the app.
    """
    
    def process_request(self, request):        
        # lighttpd+fastcgi deployment hack
        request.path = request.path.replace('/main.fcgi', '')
        
        open_urls = "/static/ /login/ /signup/ /reset/ /confirm-reset/ /captcha/".split( )
        def is_sub_url(path, urls):
            for url in urls:
                if path[:len(url)] == url:
                    return True
            return False
        
        if not is_sub_url(request.path, open_urls):
            account_id = request.session.get('account_id', False)
            if account_id:
                try:
                    request.account = Account.objects.select_related().get(id__exact=account_id)
                except Account.DoesNotExist:
                    request.account = None
                    request.session['account_id'] = None
                    request.session['account'] = None
                    if request.path != '/':
                        return HttpResponseRedirect('/login/')
            else:
                request.account = None
                request.session['account_id'] = None
                request.session['account'] = None
                if request.path != '/':
                    return HttpResponseRedirect('/login/')
                    
    def process_response(self, request, response):
        # Never cache for now. This should probably not be on all pages..
        import time
        response['Expires'] = 'Mon, 15 Jul 1981 00:00:00 GMT'
        response['Last-Modified'] = time.ctime()+' GMT'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'        
        response['Pragma'] = 'no-cache'
                
        return response
