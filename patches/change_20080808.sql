update accounts_feeds, feeds set accounts_feeds.title = feeds.title  where accounts_feeds.feed_id=feeds.id and accounts_feeds.title = '';

