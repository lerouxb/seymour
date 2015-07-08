import feedfinder
import feedparser
from django.shortcuts import render_to_response
from django.template import RequestContext 
from django.http import HttpResponseRedirect, Http404, HttpResponse
from seymour.feeds.models import Feed, Item, AccountFeed
from seymour.feeds.forms import SelectFeedForm, ManageFeedsForm, EditAccountFeedForm


def home(request):    
    return render_to_response('home.html', {
    }, context_instance=RequestContext(request))

def feeds(request):
    return HttpResponseRedirect('/feeds/unread/')

def unread_feeds(request):
    account = request.account
    feeds = account.get_unread_feeds()
    
    try:
        error = request.session['error']
        del request.session['error']
        
    except KeyError:
        error = ''
    
    return render_to_response('feeds/unread.html', {
        'error': error,
        'feeds': feeds,  
    }, context_instance=RequestContext(request))

def view_feed(request, slug):
    account = request.account
    feeds = account.get_unread_feeds()
    
    try:
        af = AccountFeed.objects.select_related().get(account=account, feed__slug=slug)
    except AccountFeed.DoesNotExist:
        raise Http404
    
    items = af.feed.get_unread_items(account)
    
    if request.POST and request.POST.has_key('item_id'):
        try:
            item_id = int(request.POST.get('item_id'))
            latest_item = items.get(pk=item_id)
        except (ValueError, Item.DoesNotExist):
            return HttpResponseRedirect('/feeds/unread/')        
        af.latest_read = latest_item.date_added
        af.save()
        return HttpResponseRedirect('/feeds/unread/')
        
    return render_to_response('feeds/view.html', {
        'feeds': feeds,
        'af': af,
        'item': items[0],
        'items': items,
        'collapse_sidebar': True
    }, context_instance=RequestContext(request))
    
def add_feed(request):
    account = request.account
    unread_feeds = account.get_unread_feeds()
    
    if request.POST and request.POST.has_key('link'):
        data = request.POST.copy()
        
        try:
            fp = feedparser.parse(data['link'])
            if fp.has_key('feed') and fp.feed.has_key('title'):            
                feeds = [data['link']]
            else:
                feeds = feedfinder.feeds(data['link'])
            if not feeds:                
                request.session['error'] = "No feeds found."
                return HttpResponseRedirect('/feeds/unread/')
            
            elif len(feeds) == 1:                
                try:
                    feed = Feed.objects.get(link=feeds[0])
                    
                except Feed.DoesNotExist:
                    # add the feed to the db
                    fp = feedparser.parse(feeds[0])
                    feed = Feed(title=fp.feed.title, link=feeds[0], is_active=True)
                    feed.save()
                    feed.update()
                    
                else:
                    pass # already added                       
                    
                try:
                    AccountFeed(account=account, feed=feed, title=feed.title).save()
                except:
                    pass
                
                return HttpResponseRedirect("/feeds/%s/" % (feed.slug,))
                
            else:                
                if data.has_key('feed'):
                    form = SelectFeedForm(data, account=account, link=data['link'], feeds=feeds)
                    if form.is_valid():
                        feed = form.save()
                        return HttpResponseRedirect("/feeds/%s/" % (feed.slug,))
                else:
                    initial = {
                        'link': data['link'],
                        'feed': feeds[0]
                    }
                    form = SelectFeedForm(initial=initial, account=account, link=data['link'], feeds=feeds)
                
                return render_to_response('feeds/select.html', {                    
                    'feeds': unread_feeds,
                    'form': form,
                    'collapse_sidebar': True
                }, context_instance=RequestContext(request))
        except UnicodeDecodeError:
            request.session['error'] = """
Encoding error.
<a href="http://feedparser.org/">Universal Feed Parser</a>
threw an exception while trying to make sense of the feed.
When this happens it is almost certainly the feed's fault.
            """.strip().replace('\n', ' ')
        except feedfinder.TimeoutError:
            request.session['error'] = "Timeout"
            # TODO: handle properly
            return HttpResponseRedirect('/feeds/unread/')

def edit_feed(request, slug):
    account = request.account
    feeds = account.get_all_feeds()
    
    try:
        af = AccountFeed.objects.select_related().get(account=account, feed__slug=slug)
    except AccountFeed.DoesNotExist:
        raise Http404
        
    if request.POST:        
        data = request.POST.copy()
        form = EditAccountFeedForm(data=data, update=af)
        if form.is_valid():
            if request.POST.has_key('delete'):
                form.delete()
            else:
                form.save()
            return HttpResponseRedirect('/feeds/manage/')
            
    else:
        initial = {'title': af.title}
        form = EditAccountFeedForm(initial=initial, update=af)
        
    return render_to_response('feeds/edit.html', {
        'form': form,        
        'feeds': feeds,
        'af': af,
        'collapse_sidebar': True
    }, context_instance=RequestContext(request))    

def manage_feeds(request):
    account = request.account
    feeds = account.get_all_feeds()
    
    if request.POST:
        data = request.POST.copy()
        form = ManageFeedsForm(data, account=account, feeds=feeds)
        if form.is_valid():
            form.delete()
            return HttpResponseRedirect('/feeds/unread/')
    
    else:
        form = ManageFeedsForm(account=account, feeds=feeds)
    
    return render_to_response('feeds/manage.html', {
        'form': form,        
        'feeds': feeds,        
    }, context_instance=RequestContext(request))     
    
def export_feeds(request):
    pass

