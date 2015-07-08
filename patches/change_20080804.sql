alter table feeds add page_link varchar(255) default null after link;
alter table accounts_feeds add `title` varchar(255) default null;
update accounts_feeds, feeds set accounts_feeds.title = feeds.title where accounts_feeds.feed_id=feeds.id;
alter table accounts_feeds modify title varchar(255) not null;
update items set identifier = sha(concat(feed_id,link,title)) where identifier = concat(link,title);

alter table items modify link varchar(2048) NOT NULL;
