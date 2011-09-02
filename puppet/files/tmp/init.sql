-- Open mysql root up to host machine, no password. Seems scary, but maybe
-- change the password after provisioning
grant all on *.* to 'root'@'192.168.10.1' identified by '';

drop database if exists wikidb;
create database wikidb;
grant all privileges on wikidb.* to wikiuser@'%' identified by '2yeOr7ByBUMBiB4z';
grant all privileges on wikidb.* to wikiuser@localhost identified by '2yeOr7ByBUMBiB4z';
grant all privileges on wikidb.* to wikiuser@10.0.2.15 identified by '2yeOr7ByBUMBiB4z';

drop database if exists kuma;
create database kuma;
grant all privileges on kuma.* to kuma@'%' identified by 'kuma';
grant all privileges on kuma.* to kuma@localhost identified by 'kuma';
grant all privileges on kuma.* to kuma@10.0.2.15 identified by 'kuma';

drop database if exists phpbb;
create database phpbb;
grant all privileges on phpbb.* to phpbb@'%' identified by 'phpbb';
grant all privileges on phpbb.* to phpbb@localhost identified by 'phpbb';
grant all privileges on phpbb.* to phpbb@10.0.2.15 identified by 'phpbb';
