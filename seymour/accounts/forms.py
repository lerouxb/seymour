from django.conf import settings
from django import forms
from seymour.accounts.models import Account


__all__ = (
    'LoginForm', 'SignupForm', 
    'ResetPasswordForm', 'ConfirmResetPasswordForm', 
    'EditOpenIDProfileForm', 'EditEmailProfileForm'
)

    
class LoginForm(forms.Form):
    method = forms.ChoiceField(label='Login using', required=True, choices=(('email', 'Email & Password'), ('openid', 'OpenID')), widget=forms.RadioSelect())
    
    openid = forms.CharField(label='Your OpenID', max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    
    email = forms.EmailField(label='Email address', max_length=75, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    password = forms.CharField(label='Password', max_length=30, required=False, widget=forms.PasswordInput(attrs={'class': 'text'}))
    
    
    def clean(self):
        if self.cleaned_data['method'] == 'email':
            email = self.cleaned_data.get('email') 
            password = self.cleaned_data.get('password')
            
            # must I use a forms.ValidationError()? must this be a sequence?
            # the documentation isn't clear..
            if not email:
                self.errors['email'] = "This field is required."            
            if not password:
                self.errors['password'] = "This field is required."
            
            if email and password:        
                try:
                    account = Account.objects.get(email=email)                
                except Account.DoesNotExist:               
                    self.data['password'] = ''
                    raise forms.ValidationError("Please enter a correct email address and password. Note that both fields are case-sensitive.")
                
                if not account.check_password(password):
                    self.data['password'] = ''                
                    raise forms.ValidationError("Please enter a correct email address and password. Note that both fields are case-sensitive.")
                    
                if not account.is_active:
                    raise forms.ValidationError("This account is inactive.")
    
                self._account = account
                
                return self.cleaned_data
        
        else:
            # TODO: do some basic checks to make sure this is actually a URL..            
            return self.cleaned_data
    
    def get_openid(self):
        # for now handle it all inside the view
        return self.cleaned_data['openid']        
    
    def get_account(self):        
        if hasattr(self, '_account'):
            return self._account
        else:
            return None    


email_help = """Please use a valid email address as you will use this to log-in.
We will never sell your email address to anyone."""
password_help = """Password should be at least 6 characters."""
confirmation_help = """We sent you this in an email. If you clicked the link we
sent it should automatically be filled in."""

class SignupForm(forms.Form):
    method = forms.ChoiceField(label='Signup using', required=True, choices=(('email', 'Email & Password'), ('openid', 'OpenID')), widget=forms.RadioSelect())
    
    openid = forms.CharField(label='Your OpenID', max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'text'})) 
    
    firstname = forms.CharField(label='First name', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    lastname = forms.CharField(label='Last name', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    email = forms.EmailField(label='Email address', help_text=email_help, max_length=75, required=False, widget=forms.TextInput(attrs={'class': 'text'}))    
    password = forms.CharField(label='Password', help_text=password_help, initial='', max_length=30, required=False, widget=forms.PasswordInput(attrs={'class': 'text'}))
    confirm_password = forms.CharField(label='Re-type password', initial='', max_length=30, required=False, widget=forms.PasswordInput(attrs={'class': 'text'}))
    
    captcha = forms.CharField(label='Please type the word you see in the image', initial='', max_length=128, required=True, widget=forms.TextInput(attrs={'class': 'vTextField'}))

    def __init__(self, *args, **kwargs):
        self.word = kwargs['word']
        del kwargs['word']
        
        super(SignupForm, self).__init__(*args, **kwargs)        

    def clean_email(self):
        value = self.cleaned_data['email']
        
        try:
            account = Account.objects.get(email=value)
        except Account.DoesNotExist:
            pass
        else:
            raise forms.ValidationError("The email address is already used.")
            
        return value

    def clean_captcha(self):
        value = self.cleaned_data['captcha']
        if value != self.word:
            self.data['captcha'] = ''
            raise forms.ValidationError("Please fill in this code.")
        
        return value

    def clean(self):
        if self.cleaned_data['method'] == 'email':        
            email = self.cleaned_data.get('email')                
            password = self.cleaned_data.get('password')
            confirm_password = self.cleaned_data.get('confirm_password')
            
            # must I use a forms.ValidationError()? must this be a sequence?
            # the documentation isn't clear..
            if not email:
                self.errors['email'] = "This field is required."            
            if not password:
                self.errors['password'] = "This field is required."
            if not confirm_password:
                self.errors['confirm_password'] = "This field is required."
            
            if password or confirm_password:
                if password != confirm_password:                
                    self.data['password'] = ''
                    self.data['confirm_password'] = ''
                    raise forms.ValidationError("The Passwords don't match.")
                else:
                    if len(password) < 6:
                        self._errors['password'] = "Passwords must be at least 6 characters long."
                        self.data['password'] = ''
                        self.data['confirm_password'] = ''
            
            return self.cleaned_data
            
        else:
            # TODO: do some basic checks to make sure this is actually a URL..
            return self.cleaned_data
        
    def save(self):
        data = self.cleaned_data               
                    
        account = Account(
            firstname=data['firstname'],
            lastname=data['lastname'],            
            email=data['email'],
            is_active=True,
        )            
        account.set_password(data['password'])            
        account.save()
        
        # email the password to the user                
        from django.core.mail import send_mail
        from django.template import Template, Context, loader  
        context = Context({            
            'account': account,
            'password': data['password'],
            'sitename': settings.SITENAME,
            'seymour_domain': settings.SEYMOUR_DOMAIN            
        })
        
        subject = u"Welcome to %s" % (settings.SITENAME)
        t = loader.get_template('emails/account_added.email')            
        
        email_body = t.render(context)
        if settings.DEBUG:
            print "Subject: " + subject.encode('utf8')
            print "-"*80
            print email_body.encode('utf8')
        else:
            send_mail(subject, email_body, settings.EMAIL_FROM, [account.email], fail_silently=True)
        
        return account
        
    def get_openid(self):
        # for now handle it all inside the view
        return self.cleaned_data['openid']
        
class ResetPasswordForm(forms.Form):
    email = forms.EmailField(label='Email address', max_length=75, required=True, widget=forms.TextInput(attrs={'class': 'vTextField'}))
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:            
            try:                            
                account = Account.objects.get(email=email)
            except Account.DoesNotExist:
                raise forms.ValidationError("This email address is not on our system.")
                
            return email
        
    def save(self):        
        import sha
        import random
        
        confirmation_code = sha.new(str(random.random())).hexdigest()[:5].upper()
        
        email = self.cleaned_data['email']
        account = Account.objects.get(email=email)
        account.confirmation_code = confirmation_code
        account.save()
        
        # send email
        from django.core.mail import send_mail
        from django.template import Template, Context, loader  
        context = Context({
            'account': account, 
            'sitename': settings.SITENAME,
            'seymour_domain': settings.SEYMOUR_DOMAIN   
        })
                
        subject = u"[%s] Reset Password Confirmation" % (settings.SITENAME)
        t = loader.get_template('emails/reset_password_confirm.email')
        email_body = t.render(context)
        if settings.DEBUG:
            print "Subject: " + subject.encode('utf8')
            print "-"*80
            print email_body.encode('utf8')
        else:
            send_mail(subject, email_body, settings.EMAIL_FROM, [account.email], fail_silently=True)
    
class ConfirmResetPasswordForm(forms.Form):
    email = forms.EmailField(label='Email address', max_length=75, required=True, widget=forms.TextInput(attrs={'class': 'vTextField'}))
    confirmation_code = forms.CharField(label='Confirmation code', max_length=75, help_text=confirmation_help, required=True, widget=forms.TextInput(attrs={'class': 'vTextField'})) 

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:            
            try:                            
                account = Account.objects.get(email=email)
            except Account.DoesNotExist:
                raise forms.ValidationError("This email address is not on our system.")
                
            return email
    
    def clean(self):
        email = self.cleaned_data.get('email')
        confirmation_code = self.cleaned_data.get('confirmation_code')
        
        if email:            
            try:                            
                account = Account.objects.get(email=email)
                if account.confirmation_code != confirmation_code:
                    self._errors['confirmation_code'] = "Invalid confirmation code. Please try again. If you keep having problems, please contact support."
                
                return self.cleaned_data
                
            except Account.DoesNotExist:
                self._errors['email'] = "This email address is not on our system."
    
    def save(self):
        import sha
        import random
        
        email = self.cleaned_data['email']
        account = Account.objects.get(email=email)
        
        new_password = sha.new(str(random.random())).hexdigest()[:5].upper()
        account.confirmation_code = None
        account.set_password(new_password)        
        account.save()
        
        # send email
        from django.core.mail import send_mail
        from django.template import Template, Context, loader  
        context = Context({
            'account': account,
            'password': new_password,
            'sitename': settings.SITENAME,
            'seymour_domain': settings.SEYMOUR_DOMAIN
        })
                
        subject = u"[%s] Password Changed" % (settings.SITENAME)
        t = loader.get_template('emails/changed_password.email')
        email_body = t.render(context)
        if settings.DEBUG:
            print "Subject: " + subject.encode('utf8')
            print "-"*80
            print email_body.encode('utf8')
        else:
            send_mail(subject, email_body, settings.EMAIL_FROM, [account.email], fail_silently=True) 

class EditOpenIDProfileForm(forms.Form):
    firstname = forms.CharField(label='First name', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    lastname = forms.CharField(label='Last name', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    
    # TODO: allow changing OpenID (will probably require re-authentication, 
    # because otherwise you can't log back in..)
    
    def __init__(self, *args, **kwargs):
        self.update = kwargs['update']
        del kwargs['update']
        
        super(EditOpenIDProfileForm, self).__init__(*args, **kwargs)

    def save(self):
        data = self.cleaned_data               
        account = self.update
        
        account.firstname = data['firstname']
        account.lastname = data['lastname']
        
        account.save()


class EditEmailProfileForm(forms.Form):
    firstname = forms.CharField(label='First name', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    lastname = forms.CharField(label='Last name', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'text'}))
    email = forms.EmailField(label='Email address', max_length=75, required=True, widget=forms.TextInput(attrs={'class': 'text'}))    
    password = forms.CharField(label='Password', initial='', max_length=30, required=False, widget=forms.PasswordInput(attrs={'class': 'text'}))
    confirm_password = forms.CharField(label='Re-type password', initial='', max_length=30, required=False, widget=forms.PasswordInput(attrs={'class': 'text'}))
    
    def __init__(self, *args, **kwargs):
        self.update = kwargs['update']
        del kwargs['update']
        
        super(EditEmailProfileForm, self).__init__(*args, **kwargs)
    
    def clean_email(self):
        value = self.cleaned_data['email']
        
        if value == self.update.email:
            return value
        
        try:
            account = Account.objects.get(email=value)
        except Account.DoesNotExist:
            pass
        else:
            raise forms.ValidationError("The email address is already used.")
            
        return value

    def clean(self):
        email = self.cleaned_data.get('email')
                
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if password or confirm_password:
            if password != confirm_password:                
                self.data['password'] = ''
                self.data['confirm_password'] = ''
                raise forms.ValidationError("The Passwords don't match.")
            else:
                if len(password) < 6:
                    self._errors['password'] = "Passwords must be at least 6 characters long."
                    self.data['password'] = ''
                    self.data['confirm_password'] = ''
        
        return self.cleaned_data
        
    def save(self):
        data = self.cleaned_data               
        account = self.update
        
        account.email = data['email']
        account.firstname = data['firstname']
        account.lastname = data['lastname']
        
        if data['password']:
            account.set_password(data['password'])

        account.save()

