import datetime
from django.db import models, connection
from seymour.feeds.models import Feed, Item, AccountFeed


class Account(models.Model):
    openid = models.CharField('openid', max_length=255, null=True)
    firstname = models.CharField('first name', max_length=100, null=True)
    lastname = models.CharField('last name', max_length=100, null=True)
    email = models.EmailField('e-mail address', null=True)
    date_joined = models.DateTimeField('date joined', default=datetime.datetime.now, db_index=True)
    last_login = models.DateTimeField('last login', null=True, db_index=True)
    password_salt = models.CharField('password salt', max_length=100, null=True)
    password_hash = models.CharField('password hash', max_length=100, null=True)
    confirmation_code = models.CharField('confirmation code', max_length=50, null=True, db_index=True)
    is_active = models.BooleanField('active', default=True, db_index=True)    
    
    class Meta:
        db_table = 'accounts'
        unique_together = (('email', 'openid'),)
        ordering = ['email', 'openid']
        
    def get_fullname(self):
        if self.firstname or self.lastname:            
            return u"%s %s" % (self.firstname, self.lastname)
        else:
            return None
    fullname = property(get_fullname)
        
    def set_password(self, raw_password):
        import random
        import sha
                        
        salt = sha.new(str(random.random())).hexdigest()[:5]        
        hsh = sha.new(salt+raw_password).hexdigest()
        self.password_salt = salt
        self.password_hash = hsh        

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct.
        """

        import random
        import sha
                
        hsh = sha.new(self.password_salt+raw_password).hexdigest()
        return self.password_hash == hsh
        
    def get_all_feeds(self):
        """Return all feeds associated with this account"""
                
        return self.accountfeed_set.select_related().filter().order_by('feeds.title')
    
    def get_unread_feeds(self):
        """Return a list of unread feeds for this account. Each feed has 
           unread_total filled in."""

        sql = """
SELECT items.feed_id, count(*)
FROM items
INNER JOIN accounts_feeds ON accounts_feeds.feed_id = items.feed_id
WHERE accounts_feeds.account_id = %s AND 
      (items.date_added > accounts_feeds.latest_read OR accounts_feeds.latest_read IS NULL)
GROUP BY items.feed_id
        """ % (self.id,)
        
        cursor = connection.cursor()
        cursor.execute(sql)
        
        feed_totals = {}
        for row in cursor.fetchall():
            feed_id, total_items = row             
            feed_totals[feed_id] = total_items
        
        feed_ids = feed_totals.keys()
        
        if feed_ids:            
            accountfeeds = AccountFeed.objects.select_related().filter(account=self, feed__id__in=feed_ids).order_by('feeds.title')
            for af in accountfeeds:
                af.feed.unread_total = feed_totals[af.feed.id]

            return accountfeeds
            
        else:
            return []
            
    def save(self):
        # TODO: What would be the best standard exception here?
        #       (This should be picked up by form validation already)
        
        if self.email and self.openid:
            raise Exception() 
        if not self.email and not self.openid:
            raise Exception()            
        if self.openid and (self.password_salt or self.password_hash):
            raise Exception()
        if self.email and not (self.password_salt and self.password_hash):
            raise Exception()
            
        super(Account, self).save()
