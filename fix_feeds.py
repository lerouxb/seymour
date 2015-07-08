from django.db import connection
from seymour.feeds.models import AccountFeed


sql = """SELECT accounts_feeds.account_id, accounts_feeds.feed_id, max(items.date_added)
FROM accounts_feeds
INNER JOIN items ON items.feed_id = accounts_feeds.feed_id
INNER JOIN accounts_items ON accounts_items.account_id = accounts_feeds.account_id AND 
                            accounts_items.item_id = items.id
GROUP BY accounts_feeds.account_id, accounts_feeds.feed_id
"""

cursor = connection.cursor()
cursor.execute(sql)

for row in cursor.fetchall():
    account_id = row[0]
    feed_id = row[1]
    dt = row[2]
    
    try:
        af = AccountFeed.objects.get(account__pk=account_id, feed__pk=feed_id)    
        af.latest_read = dt
        af.save()
    except AccountFeed.DoesNotExist:
        pass
