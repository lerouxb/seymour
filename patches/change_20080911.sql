alter table accounts add openid varchar(255) DEFAULT NULL after id;
alter table accounts modify `firstname` varchar(100) DEFAULT NULL;
alter table accounts modify `lastname` varchar(100) DEFAULT NULL;
alter table accounts modify `email` varchar(75) DEFAULT NULL;
alter table accounts modify `password_salt` varchar(100) DEFAULT NULL;
alter table accounts modify `password_hash` varchar(100) DEFAULT NULL;
alter table accounts drop key email;
alter table accounts add unique (email, openid);
