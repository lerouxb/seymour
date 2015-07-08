alter table accounts_feeds add `latest_read` datetime DEFAULT NULL;
-- after update script:
-- drop table accounts_items;
