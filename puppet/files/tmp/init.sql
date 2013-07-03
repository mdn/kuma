/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

-- Open mysql root up to host machine, no password. Seems scary, but maybe
-- change the password after provisioning
grant all on *.* to 'root'@'192.168.10.1' identified by '';

drop database if exists kuma;
create database kuma;
grant all privileges on kuma.* to kuma@'%' identified by 'kuma';
grant all privileges on kuma.* to kuma@localhost identified by 'kuma';
grant all privileges on kuma.* to kuma@10.0.2.15 identified by 'kuma';
