drop database if exists wikidb;
create database wikidb;
grant all privileges on wikidb.* to wikiuser@'%' identified by '9wHAW21eT3yuQlc3';
grant all privileges on wikidb.* to wikiuser@localhost identified by '9wHAW21eT3yuQlc3';
grant all privileges on wikidb.* to wikiuser@10.0.2.15 identified by '9wHAW21eT3yuQlc3';

drop database if exists kuma;
create database kuma;
grant all privileges on kuma.* to kuma@'%' identified by 'kuma';
grant all privileges on kuma.* to kuma@localhost identified by 'kuma';
grant all privileges on kuma.* to kuma@10.0.2.15 identified by 'kuma';
