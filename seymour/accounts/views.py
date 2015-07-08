import random
from sha import sha
import datetime
from Captcha.Visual import Text, Backgrounds, Distortions, ImageCaptcha
from Captcha import Words
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext 
from django.http import HttpResponseRedirect, Http404, HttpResponse

from openid.consumer.consumer import Consumer, \
    SUCCESS, CANCEL, FAILURE, SETUP_NEEDED
from openid.consumer.discover import DiscoveryFailure

from seymour.openidstore.models import DjangoOpenIDStore
from seymour.accounts.models import Account
from seymour.accounts.forms import *

    
class CustomTest(ImageCaptcha):
    def __init__(self, *args, **kwargs):
        self.word = kwargs['word']
        del kwargs['word']
        super(CustomTest, self).__init__(*args, **kwargs)
        self.addSolution(self.word)
        
    def getLayers(self):
        return [
            Backgrounds.SolidColor(),
            Backgrounds.Grid(size=10),            
            Distortions.SineWarp(amplitudeRange=(3, 5.0)),
            Text.TextLayer(self.word, borderSize=0),            
            Backgrounds.RandomDots(dotSize=2, numDots=800),
            Distortions.SineWarp(amplitudeRange=(3, 6.0)),
        ]

def login(request):
    "Display the login form and handle the login action."
    
    try:       
        del request.session['account_id']
    except KeyError:
        # request.session did not have a has_key() last I checked...
        pass
    
    just_signed_up = False
    openid_failure = ''
    
    if request.POST:
        data = request.POST.copy()
        
        # don't validate fields that the user might have filled in before
        # changing the type..
        if data.get('method', 'email') == 'email':            
            data['openid'] = ''
        else:
            data['email'] = ''
            data['password'] = ''
            data['confirm_password'] = ''
            
        form = LoginForm(data)
        if form.is_valid():
            if data.get('method', 'email') == 'email':
                account = form.get_account()
                request.session['account_id'] = account.id
                account.last_login = datetime.datetime.now()
                account.save()
                return HttpResponseRedirect('/feeds/unread/')
            
            else:
                openid = form.get_openid()
                
                consumer = Consumer(request.session, DjangoOpenIDStore())
                try:
                    auth_request = consumer.begin(openid)
                except DiscoveryFailure:
                    openid_failure = "The OpenID was invalid"
                else:
                    trust_root = 'http://'+settings.SEYMOUR_DOMAIN + '/'
                    redirect_to = 'http://'+settings.SEYMOUR_DOMAIN+'/login/openid/'                
                    redirect_url = auth_request.redirectURL(trust_root, redirect_to)
                    return HttpResponseRedirect(redirect_url)
    
    else:
        initial = {'method': 'email'}        
        form = LoginForm(initial=initial)

    return render_to_response('accounts/login.html', {
        'form': form,
        'just_signed_up': just_signed_up,
        'openid_failure': openid_failure,
        'section': 'login',
        'method': request.POST.get('method', 'email')
    }, context_instance=RequestContext(request))

def login_openid_callback(request):
    consumer = Consumer(request.session, DjangoOpenIDStore())
    #trust_root = 'http://'+settings.SEYMOUR_DOMAIN + '/'
    redirect_to = 'http://'+settings.SEYMOUR_DOMAIN+'/login/openid/'                
    #redirect_url = auth_request.redirectURL(trust_root, redirect_to)
    openid_response = consumer.complete(dict(request.GET.items()), redirect_to)
    
    if openid_response.status == SUCCESS:        
        try:
            account = Account.objects.get(openid=openid_response.identity_url)
        except Account.DoesNotExist:
            error_msg = "No account using that OpenID found."
        else:
            request.session['account_id'] = account.id
            account.last_login = datetime.datetime.now()
            account.save()
        
            return HttpResponseRedirect('/feeds/unread/')
        
    elif openid_response.status == CANCEL:
        error_msg = "The request was cancelled"
    elif openid_response.status == FAILURE:
        error_msg = openid_response.message
    elif openid_response.status == SETUP_NEEDED:
        error_msg = "Setup needed"
    else:
        error_msg = "Bad openid status: %s" % openid_response.status
    
    return render_to_response('accounts/login_error.html', {
        'error_msg': error_msg,
        'section': 'login',
    }, context_instance=RequestContext(request))        
      

def captcha(request, hexhash):
    "Display the captcha image."
    
    state = request.session.get('state', '')    
    word = request.session.get('word', '')
    if not (state and word):
        raise Http404
    
    random.setstate(state)
    
    if request.session.get(hexhash, False):
        g = CustomTest(word=word)
        i = g.render(size=(200, 50))
        
        response = HttpResponse(mimetype="image/png")
        i.save(response, "PNG")
        random.seed() # is this necessary?
        return response
        
    else:
        raise Http404

def signup(request):
    "Display the sign-up form and handle registration."
    
    word = Words.defaultWordList.pick()
    state = random.getstate()
    hexhash = sha(word+settings.SECRET_KEY).hexdigest()
    
    openid_failure = ''
    
    form = None
    if request.POST:
        data = request.POST.copy()
        
        # don't validate fields that the user might have filled in before
        # changing the type..
        if data.get('method', 'email') == 'email':
            data['openid'] = ''
        else:
            data['email'] = ''
            data['password'] = ''
            data['confirm_password'] = ''
        
        oldword = request.session.get('word', '')
        if oldword:
            del request.session['word']
            
        form = SignupForm(data, word=oldword)
        if form.is_valid():
            if data.get('method', 'email') == 'email':
                account = form.save()
                request.session['account_id'] = account.id
                account.last_login = datetime.datetime.now()
                account.save()
                return HttpResponseRedirect('/feeds/unread/')
                
            else:
                openid = form.get_openid()
                                
                consumer = Consumer(request.session, DjangoOpenIDStore())
                try:
                    auth_request = consumer.begin(openid)
                except DiscoveryFailure:
                    openid_failure = "The OpenID was invalid"
                else:
                    trust_root = 'http://'+settings.SEYMOUR_DOMAIN + '/'
                    redirect_to = 'http://'+settings.SEYMOUR_DOMAIN+'/signup/openid/'                
                    redirect_url = auth_request.redirectURL(trust_root, redirect_to)
                    return HttpResponseRedirect(redirect_url)                           
    
    if not form:
        initial = {'method': 'email'}
        form = SignupForm(initial=initial, word=word)

    request.session['state'] = state
    request.session['word'] = word
    request.session[hexhash] = True

    return render_to_response('accounts/signup.html', {
        'hexhash': hexhash,
        'form': form,
        'openid_failure': openid_failure,
        'section': 'signup',
        'method': request.POST.get('method', 'email')
    }, context_instance=RequestContext(request))

def signup_openid_callback(request):
    consumer = Consumer(request.session, DjangoOpenIDStore())    
    redirect_to = 'http://'+settings.SEYMOUR_DOMAIN+'/signup/openid/'
    openid_response = consumer.complete(dict(request.GET.items()), redirect_to)
    
    if openid_response.status == SUCCESS:
        try:
            account = Account.objects.get(openid=openid_response.identity_url)
        except Account.DoesNotExist:
            account = Account(openid=openid_response.identity_url, last_login=datetime.datetime.now(), is_active=True)
            account.save()
            request.session['account_id'] = account.id
            return HttpResponseRedirect('/feeds/unread/')
        else:
            error_msg = "An account for that openid already exists."        
    elif openid_response.status == CANCEL:
        error_msg = "The request was cancelled"
    elif openid_response.status == FAILURE:
        error_msg = openid_response.message
    elif openid_response.status == SETUP_NEEDED:
        error_msg = "Setup needed"
    else:
        error_msg = "Bad openid status: %s" % openid_response.status
    
    return render_to_response('accounts/signup_error.html', {
        'error_msg': error_msg,
        'section': 'signup',
    }, context_instance=RequestContext(request))

def reset_password(request):
    "Display the reset password form and send the confirmation email."
    
    if request.POST:
        data = request.POST.copy()
        form = ResetPasswordForm(data)
        if form.is_valid():
            form.save()            
            return HttpResponseRedirect('/confirm-reset/')
        
    else:
        form = ResetPasswordForm()
        
    return render_to_response('accounts/reset_password.html', {        
        'form': form,
        'section': 'reset',
    }, context_instance=RequestContext(request))
    
def confirm_reset(request, email='', code=''):
    """
    Display the confirm password reset form, reset the password and send the
    new password in an email.
    """
        
    if request.POST:
        data = request.POST.copy()
        form = ConfirmResetPasswordForm(data)
        if form.is_valid():
            form.save()            
            request.session['new_email'] = data['email']
            return HttpResponseRedirect('/login/')
        
    else:
        initial = {
            'email': email,
            'confirmation_code': code
        }
        form = ConfirmResetPasswordForm(initial=initial)
        
    return render_to_response('accounts/confirm_reset.html', {
        'form': form,
        'section': 'reset',
    }, context_instance=RequestContext(request))
    
def profile(request):
    "View/edit the logged in user's profile"
    
    account = request.account
    
    if account.email:
        if request.POST:
            data = request.POST.copy()
            form = EditEmailProfileForm(data, update=account)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/feeds/unread/')
            
        else:
            initial = account.__dict__.copy()
            initial['password'] = ''
            initial['confirm_password'] = ''
            
            form = EditEmailProfileForm(initial=initial, update=account)
            
    else:
        if request.POST:
            data = request.POST.copy()
            form = EditOpenIDProfileForm(data, update=account)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/feeds/unread/')
            
        else:
            initial = account.__dict__.copy()                        
            form = EditOpenIDProfileForm(initial=initial, update=account)
    
    feeds = account.get_unread_feeds()

    return render_to_response('accounts/edit_profile.html', {
        'form': form,
        'feeds': feeds,        
        'section': 'profile',
        'collapse_sidebar': True
    }, context_instance=RequestContext(request))
    
