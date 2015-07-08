import feedparser
import feedfinder
from django import forms
from seymour.feeds.models import Feed, Item, AccountFeed


class SelectFeedForm(forms.Form):
    link = forms.CharField(label='Link', max_length=255, required=False, widget=forms.HiddenInput())
    feed = forms.ChoiceField(label='Choose a feed', initial='', required=True, widget=forms.RadioSelect())
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs['account']
        del kwargs['account']
        
        self.link = kwargs['link']
        del kwargs['link']
        
        self.feeds = kwargs['feeds']
        del kwargs['feeds']
        
        super(SelectFeedForm, self).__init__(*args, **kwargs)
        feed_choices = []
        for f in self.feeds:
            title = 'unknown'
            fp = feedparser.parse(f)
            try:
                title = fp.feed.title
            except:
                title = f
            version = fp.version
            if version:
                title += ' [' + version + ']'
            else:
                title += ' [unknown]'
            feed_choices.append((f, title))            
        self.fields['feed'].choices = feed_choices
        
        self.fields['feed'].help_text = u'<span class="feed-link">%s</span> contains more than one feed. Please select one.' % (self.link,)
        
    def save(self):
        feed_link = self.cleaned_data['feed']
        try:
            feed = Feed.objects.get(link=feed_link)
        except Feed.DoesNotExist:            
            fp = feedparser.parse(feed_link)
            feed = Feed(title=fp.feed.title, link=feed_link, last_updated=None, is_active=True)
            feed.save()
            feed.update()
                
        #self.account.feeds.add(feed)
        try:        
            AccountFeed(account=self.account, feed=feed, title=feed.title).save()
        except:
            pass
        
        return feed

class ManageFeedsForm(forms.Form):
    feeds = forms.MultipleChoiceField(label='Feeds', required=False, widget=forms.CheckboxSelectMultiple())
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs['account']
        del kwargs['account']
        
        if kwargs.has_key('feeds'):
            self.feeds = kwargs['feeds']
            del kwargs['feeds']
        else:
            self.feeds = self.account.get_all_feeds() 
        
        super(ManageFeedsForm, self).__init__(*args, **kwargs)
        
        self.fields['feeds'].choices = [(af.feed.id, af.title) for af in self.feeds]        
        
    def delete(self):
        feed_ids = [int(fid) for fid in self.cleaned_data['feeds']]
        if feed_ids:
            feeds = Feed.objects.filter(pk__in=feed_ids)
            for f in feeds:
                #self.account.feeds.remove(f)
                try:
                    af = AccountFeed.objects.get(account=self.account, feed=f)
                except AccountFeed.DoesNotExist:
                    pass
                else:
                    af.delete()

class EditAccountFeedForm(forms.Form):
    title = forms.CharField(label='Title', max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'long_text'}))

    def __init__(self, *args, **kwargs):
        self.update = kwargs['update']
        del kwargs['update']

        super(EditAccountFeedForm, self).__init__(*args, **kwargs)
        
    def save(self):
        title = self.cleaned_data['title']
        af = self.update
        
        af.title = title
        af.save()
        
        return af
        
    def delete(self):
        af = self.update
        af.delete()
