#!/usr/bin/env python

# next few lines copy from django.core.management so that DJANGO_SETTINGS_MODULE
# is not needed and so that you don't have to add tank to the path manually
import os
import os.path
import sys

from django.conf import settings

from seymour.feeds.models import Feed

for f in Feed.objects.all():
    line = u"%s..." % (f.title,)
    print line.encode('utf8') 
    try:
        f.update(fix_html=True)
    except Exception, e:
        print e
    
print "done."
