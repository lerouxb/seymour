#!/usr/bin/env python

# next few lines copy from django.core.management so that DJANGO_SETTINGS_MODULE
# is not needed and so that you don't have to add tank to the path manually
import os
import os.path
import sys
#import settings
#project_directory = os.path.dirname(settings.__file__)
#project_name = os.path.basename(project_directory)
#sys.path.append(os.path.join(project_directory, '..'))
#os.environ['DJANGO_SETTINGS_MODULE'] = u'%s.settings' % project_name

from seymour.feeds.models import Feed, Item, fix_item_html

#feed_link = "http://opensores.za.tank.dev/feeds/atom/"
feed_link = "http://feeds.boingboing.net/boingboing/iBag"

feed = Feed.objects.get(link=feed_link)

feed.update(fix_html=True)

#for item in Item.objects.filter(feed=feed).order_by('-date_added')[:10]:
#     print fix_item_html(item.original_html)
