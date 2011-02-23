--
-- bug 634390 - some search queries cause exceptions with non-UTF8 charset in mysql
-- see also: http://wolfram.kriesing.de/blog/index.php/2007/convert-mysql-db-to-utf8
--
ALTER TABLE `actioncounters_actioncounterunique` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `contentflagging_contentflag` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_group` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_group_permissions` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_message` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_permission` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_user` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_user_groups` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `auth_user_user_permissions` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `demos_submission` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_admin_log` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_content_type` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_session` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `django_site` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `feeder_bundle` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `feeder_bundle_feeds` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `feeder_entry` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `feeder_feed` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `schema_version` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `tagging_tag` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `tagging_taggeditem` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `threadedcomments_freethreadedcomment` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `threadedcomments_testmodel` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `threadedcomments_threadedcomment` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `user_profiles` CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;

