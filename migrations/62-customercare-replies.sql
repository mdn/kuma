ALTER TABLE `customercare_tweet` ADD `reply_to` BIGINT NULL DEFAULT NULL ;
ALTER TABLE `customercare_tweet` ADD INDEX ( `reply_to` ) ;
