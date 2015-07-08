from django.conf import settings
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    # static files (images, css, js)
    # it is recommended that you setup your webserver to serve these files
    # this is just handy as a fallback for the dev server.
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    
    # accounts    
    (r'^login/openid/$', 'seymour.accounts.views.login_openid_callback'),
    (r'^login/$', 'seymour.accounts.views.login'),
    (r'^signup/openid/$', 'seymour.accounts.views.signup_openid_callback'),
    (r'^signup/$', 'seymour.accounts.views.signup'),    
    (r'^reset/$', 'seymour.accounts.views.reset_password'),
    (r'^confirm-reset/((?P<email>[^/]+)/?)?((?P<code>[^/]+)/)?$', 'seymour.accounts.views.confirm_reset'),
    (r'^profile/$', 'seymour.accounts.views.profile'),
    (r'^captcha/(?P<hexhash>[^/]+)/', 'seymour.accounts.views.captcha'),
    
    # feeds        
    (r'^feeds/unread/$', 'seymour.feeds.views.unread_feeds'),
    (r'^feeds/manage/$', 'seymour.feeds.views.manage_feeds'),
    (r'^feeds/export/$', 'seymour.feeds.views.export_feeds'),    
    (r'^feeds/add/', 'seymour.feeds.views.add_feed'),
    (r'^feeds/(?P<slug>[^/]+)/edit/', 'seymour.feeds.views.edit_feed'),
    (r'^feeds/(?P<slug>[^/]+)/', 'seymour.feeds.views.view_feed'),
    (r'^feeds/$', 'seymour.feeds.views.feeds'),
    (r'^$', 'seymour.feeds.views.home'),
)
