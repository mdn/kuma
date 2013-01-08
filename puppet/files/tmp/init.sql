-- Open mysql root up to host machine, no password. Seems scary, but maybe
-- change the password after provisioning
grant all on *.* to 'root'@'192.168.10.1' identified by '';

drop database if exists kuma;
create database kuma;
grant all privileges on kuma.* to kuma@'%' identified by 'kuma';
grant all privileges on kuma.* to kuma@localhost identified by 'kuma';
grant all privileges on kuma.* to kuma@10.0.2.15 identified by 'kuma';
