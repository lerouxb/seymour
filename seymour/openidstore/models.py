"""
This is based on 
django-openid-consumer (http://code.google.com/p/django-openid-consumer/)
which is a fork of
django-openid (http://code.google.com/p/django-openid/)

with some patches from here:
http://code.google.com/p/django-openid/issues/detail?id=10

and some more patches to get that to work properly with openid 2 and django 1.0 
and then to be contained in one file.
"""

import time, base64, md5, operator
import openid.store
from openid.store.interface import OpenIDStore
from openid.association import Association as OIDAssociation
from django.conf import settings
from django.db import models
from django.db.models.query import Q


class Nonce(models.Model):
    nonce = models.CharField(max_length=8)
    server_url = models.CharField(max_length=255)
    timestamp = models.IntegerField()
    salt = models.CharField(max_length=40)
    
    def __unicode__(self):
        return u"Nonce: %s" % self.id        

class Association(models.Model):
    server_url = models.TextField(max_length=2047)
    handle = models.CharField(max_length=255)
    secret = models.TextField(max_length=255) # Stored base64 encoded
    issued = models.IntegerField()
    lifetime = models.IntegerField()
    assoc_type = models.TextField(max_length=64)
    
    def __unicode__(self):
        return u"Association: %s, %s" % (self.server_url, self.handle)
        
class DjangoOpenIDStore(OpenIDStore):    
    def storeAssociation(self, server_url, association):
        assoc = Association(
            server_url = server_url,
            handle = association.handle,
            secret = base64.encodestring(association.secret),
            issued = association.issued,
            lifetime = association.issued,
            assoc_type = association.assoc_type
        )
        assoc.save()
    
    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = Association.objects.filter(
                server_url = server_url, handle = handle
            )
        else:
            assocs = Association.objects.filter(
                server_url = server_url
            )
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, base64.decodestring(assoc.secret), assoc.issued,
                assoc.lifetime, assoc.assoc_type
            )
            if association.getExpiresIn() == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]
    
    def removeAssociation(self, server_url, handle):
        assocs = list(Association.objects.filter(
            server_url = server_url, handle = handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.delete()
        return assocs_exist

    def useNonce(self, server_url, timestamp, salt):               
        if not openid.store.nonce.checkTimestamp(openid.store.nonce.mkNonce(timestamp)):            
            return False
        
        query =[
                Q(server_url__exact=server_url),
                Q(timestamp__exact=timestamp),
                Q(salt__exact=salt),
        ]
        try:
            ononce = Nonce.objects.get(reduce(operator.and_, query))
        except Nonce.DoesNotExist:            
            ononce = Nonce(
                    server_url=server_url,
                    timestamp=timestamp,
                    salt=salt
            );
            ononce.save()            
            return True
    
        ononce.delete()
        
        return False    
    
    # haven't actually checked if these still work
    
    def cleanupNonce(self):
        Nonce.objects.filter(timestamp<int(time.time()) - nonce.SKEW).delete()

    def cleaupAssociations(self):
        Association.objects.extra(where=['issued + lifetimeint<(%s)' % time.time()]).delete()    
    
    def getAuthKey(self):
        # Use first AUTH_KEY_LEN characters of md5 hash of SECRET_KEY
        return md5.new(settings.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]

