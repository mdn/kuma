-- blob it
ALTER TABLE `upload_imageattachment`
  MODIFY COLUMN `file` blob
, MODIFY COLUMN `thumbnail` blob;
-- utf8 it
ALTER TABLE `upload_imageattachment`
  MODIFY COLUMN `file` varchar(250) CHARACTER SET utf8
, MODIFY COLUMN `thumbnail` varchar(250) CHARACTER SET utf8;

ALTER TABLE `upload_imageattachment`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;


-- blob it
ALTER TABLE `flagit_flaggedobject`
  MODIFY COLUMN `reason` blob
, MODIFY COLUMN `notes` blob;
-- utf8 it
ALTER TABLE `flagit_flaggedobject`
  MODIFY COLUMN `reason` varchar(64) CHARACTER SET utf8
, MODIFY COLUMN `notes` longtext CHARACTER SET utf8;

ALTER TABLE `flagit_flaggedobject`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;


-- blob it
ALTER TABLE `customercare_cannedcategory`
  MODIFY COLUMN `title` blob;
-- utf8 it
ALTER TABLE `customercare_cannedcategory`
  MODIFY COLUMN `title` varchar(255) CHARACTER SET utf8;

ALTER TABLE `customercare_cannedcategory`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;


-- blob it
ALTER TABLE `customercare_cannedresponse`
  MODIFY COLUMN `title` blob,
  MODIFY COLUMN `response` blob;
-- utf8 it
ALTER TABLE `customercare_cannedresponse`
  MODIFY COLUMN `title` varchar(255) CHARACTER SET utf8,
  MODIFY COLUMN `response` varchar(140) CHARACTER SET utf8;

ALTER TABLE `customercare_cannedresponse`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;


ALTER TABLE `customercare_categorymembership`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;


ALTER TABLE `customercare_tweet` DROP INDEX `customercare_tweet_928541cb`;

-- blob it
ALTER TABLE `customercare_tweet`
  MODIFY COLUMN `raw_json` blob,
  MODIFY COLUMN `locale` blob;
-- utf8 it
ALTER TABLE `customercare_tweet`
  MODIFY COLUMN `raw_json` longtext CHARACTER SET utf8,
  MODIFY COLUMN `locale` varchar(20) CHARACTER SET utf8;

ALTER TABLE `customercare_tweet`
    ADD INDEX `customercare_tweet_928541cb` (`locale`);

ALTER TABLE `customercare_tweet`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;
