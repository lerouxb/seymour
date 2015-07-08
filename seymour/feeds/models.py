import re
import feedparser
import datetime
import urllib2
import sha
from PIL import Image
import cStringIO as StringIO
from django.db import models, connection
from django.template.defaultfilters import slugify
from _mysql_exceptions import IntegrityError

# NOTE: only reasonably well-formed img tags and attributes will be picked up. 
# If the attributes don't have double-quotes surrounding the attributes or if
# the attributes have double-quotes inside the attributes or if the html uses
# uppercase tags, then they will be ignored. Basically I'm working from the
# assumption that if the html is that bad, then rather just leave it alone.
re_img_tag = re.compile(r"<img .*?>")
re_a_tag = re.compile(r"<a .*?>")
re_attr = re.compile(r'([A-Za-z]+)\="([^"]+)"')

def slug_from_url(url):
    return slugify(url.replace('http://', '').replace('https://', '').replace('/', '-').replace('.', '-').rstrip('- '))

def make_identifier(feed_id, title, link):
    return sha.sha(str(feed_id)+link.encode('utf8')+title.encode('utf8')).hexdigest()

def get_image_dimensions(src):    
    fp = urllib2.urlopen(src)
    data = fp.read()

    sio = StringIO.StringIO(data)
    image = Image.open(sio)
    
    size = image.size
    
    return size    

def fix_item_html(html):
    def fix_img_tag(match):
        tag = match.group(0)
        attrs = dict(re_attr.findall(tag))
        #print attrs.keys()
        
        if attrs.has_key('src'): # ignore severely broken img tags
            if attrs.has_key('align'):
                # use align=left or align=right as class name if it is supplied
                cls = attrs['align']                
                
            else:
                try:
                    try:
                        # use width and height if it is already supplied
                        width, height = int(attrs['width']), int(attrs['height'])
                        
                    except KeyError, ValueError:
                        # if not, then load in the image so that we can get the
                        # width and height.
                        width, height = get_image_dimensions(attrs['src'])
                        
                    if width == 1 and height == 1:
                        cls = "hidden"
                    elif width <= 32:
                        cls = "tiny"
                    elif width < 400:
                        cls = "small"
                    else:
                        cls = "big"
                        
                except:                    
                    # if some weird network or other error occurred insid
                    # get_image_dimensions, then just ignore this image - this
                    # isn't all that mission critical anyway.
                    cls = ""
            
            # just remove unnecessary tags for good measure
            disallowed_attrs = ["border", "align", "width", "height", "hspace", "vspace"]
            for attr in disallowed_attrs:
                if attrs.has_key(attr):
                    del attrs[attr]
            
            if cls:
                attrs['class'] = cls # herein lies the magic!
                
            items = attrs.iteritems()
            attrs_str = u" ".join(['%s="%s"' % (k, v) for k, v in items])
            tag = u"<img %s />" % (attrs_str,)
            #print tag
        
        return tag
        
    def fix_a_tag(match):
        tag = match.group(0)
        attrs = dict(re_attr.findall(tag))
        
        if attrs.has_key('href'):
            attrs['class'] = 'external'
            attrs['target'] = '_blank'
            
            items = attrs.iteritems()
            attrs_str = u" ".join(['%s="%s"' % (k, v) for k, v in items])
            tag = u"<a %s>" % (attrs_str,)
        
        return tag
        
    html = re.sub(re_img_tag, fix_img_tag, html)
    html = re.sub(re_a_tag, fix_a_tag, html)
    
    return html


class Feed(models.Model):
    title = models.CharField('title', max_length=255, db_index=True)
    link = models.CharField('link', max_length=2048, db_index=True)
    page_link = models.CharField('associated page link', max_length=255, db_index=True, null=True)
    slug = models.CharField('slug', max_length=255, db_index=True, unique=True)
    last_updated = models.DateTimeField('date and time last updated', null=True, db_index=True)
    is_active = models.BooleanField('active', default=True, db_index=True) 
    
    class Meta:
        db_table = 'feeds'        
        ordering = ['title']
    
    def __unicode__(self):
        return self.link
    
    def get_unread_items(self, account):
        """Return unread items for this feed and account."""

        sql = """
SELECT items.id
FROM items
INNER JOIN accounts_feeds ON accounts_feeds.feed_id = items.feed_id
WHERE accounts_feeds.account_id = %s AND 
      accounts_feeds.feed_id = %s AND
      items.is_archived = 0 AND
      (items.date_added > accounts_feeds.latest_read OR accounts_feeds.latest_read IS NULL)      
        """ % (account.id, self.id)
        
        cursor = connection.cursor()
        cursor.execute(sql)
        
        item_ids = [row[0] for row in cursor.fetchall()]
        if not item_ids:
            item_ids = [-1]
            
        return Item.objects.filter(pk__in=item_ids)
    
    def update(self, fp=None, fix_html=False):
        if not self.is_active:
            return
        
        if not fp:
            fp = feedparser.parse(self.link)
        
        if fp.feed.has_key('link'):
            self.page_link = fp.feed.link
        
        try:
            if fp.status == 301:
                self.link = fp.href
            elif fp.status in (410, 404):
                self.is_active = False
                
        except AttributeError:
            pass
            
        
        if fp.feed.has_key('title') and fp.feed.title != self.title:
            self.title = fp.feed.title            
        
        for e in fp.entries:
            try:            
                title = e.title            
                link = e.link
                
                try:
                    identifier = e.id
                except AttributeError:
                    #identifier = link+title
                    identifier = make_identifier(self.id, title, link)
                
                if e.has_key('content'):
                    original_html = e.content[0].value
                elif e.has_key('summary'):
                    original_html = e.summary
                else:
                    original_html = ''
                    
                try:
                    date_updated_parsed = e.updated_parsed
                except AttributeError:
                    date_updated = None # default to None
                else:
                    d = date_updated_parsed
                    #year, month, day, hour, minute, second, microsecond, tzinfo = date_updated_parsed                    
                    #date_updated = datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo)
                    date_updated = datetime.datetime(d[0], d[1], d[2], d[3], d[4], d[5])
                
                try:
                    date_added_parsed = e.created_parsed
                except AttributeError:
                    if date_updated:
                        date_added = date_updated
                        date_updated = None
                    else:
                        date_added = datetime.datetime.now() # default to now
                else:
                    d = date_added_parsed
                    #year, month, day, hour, minute, second, microsecond, tzinfo = date_added_parsed                    
                    #date_added = datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo)
                    date_added = datetime.datetime(d[0], d[1], d[2], d[3], d[4], d[5])
                
            except AttributeError, err:
                print self.title.encode('utf8'), e.title.encode('utf8'), err, e.keys()
                continue
                
            else:
                try:
                    item = Item.objects.get(feed=self, identifier=identifier)
                
                except Item.DoesNotExist:
                    # insert 
                    try:
                        try:
                            item = Item(feed=self, identifier=identifier, title=title, link=link, original_html=original_html, date_added=date_added, date_updated=date_updated)
                            item.save()
                    
                        except IntegrityError, e:
                            # integrity errors every now and then..
                            item.identifier = make_identifier(self.id, title, link)
                            item.save()
                    
                    except Exception, e:
                        print type(e), e
                        
                    else:
                        if fix_html:
                            item.fixed_html = fix_item_html(item.original_html)
                            item.save()
                    
                else:                    
                    # existing item, so see if it got updated
                    if item.title != title or item.link != link or item.original_html != original_html:
                        # update (for now only update once)                        
                        if not date_updated:
                            date_updated = datetime.datetime.now()
                                                
                            item.title = title
                            item.link = link
                            item.original_html = original_html
                            item.fixed_html = None
                            item.date_updated = date_updated
                            item.is_archived = False
                            item.save()
                        
                            # clear all the "mark as reads" for this item so people
                            # get the updated version
                            # for now, don't do this. Too many feeds are broken
                            # to the point where they always look like they
                            # were updated and that's just incredibly annoying.
                            #item.account_set.clear()
                        
                            if fix_html:
                                item.fixed_html = fix_item_html(item.original_html)
                                item.save()
                            
                    elif fix_html and not item.fixed_html:                        
                        item.fixed_html = fix_item_html(item.original_html)
                        item.save()
        
        # archive old items (magic number!!)
        items = Item.objects.filter(feed=self, is_archived=False).order_by('-date_added')[20:]
        for item in items:
            item.is_archived = True
            item.save()
        
        self.last_updated = datetime.datetime.now()
        self.save()
    
    def save(self):
        self.slug = slug_from_url(self.link)
        super(Feed, self).save()
    

class Item(models.Model):
    feed = models.ForeignKey(Feed)
    identifier = models.CharField('identifier', max_length=255, db_index=True)
    title = models.CharField('title', max_length=255, db_index=True)
    link = models.CharField('link', max_length=2048, db_index=True)
    original_html = models.TextField('original html')
    fixed_html = models.TextField('fixed html', null=True)
    date_added = models.DateTimeField('date and time added', db_index=True)
    date_updated = models.DateTimeField('date and time updated', db_index=True)
    is_archived = models.BooleanField('archived', default=False, db_index=True)
    
    class Meta:
        db_table = 'items'        
        ordering = ['-date_added']
        unique_together = ('feed', 'identifier')
    
    def __unicode__(self):
        return self.link

    def get_body(self):
        if self.fixed_html:
            return self.fixed_html
        else:
            return self.original_html
    body = property(get_body)
    
class AccountFeed(models.Model):
    feed = models.ForeignKey(Feed)
    account = models.ForeignKey('accounts.Account')
    title = models.CharField('title', max_length=255, db_index=True)
    latest_read = models.DateTimeField('date and time added', db_index=True)
    
    class Meta:
        db_table = 'accounts_feeds'
        unique_together = ('feed', 'account')
    
    def delete(self):
        # TODO: delete from accounts_items
        super(AccountFeed, self).delete()

