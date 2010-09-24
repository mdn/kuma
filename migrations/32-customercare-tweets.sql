BEGIN;
CREATE TABLE `customercare_tweet` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `tweet_id` bigint NOT NULL,
    `raw_json` longtext NOT NULL,
    `locale` varchar(20) NOT NULL,
    `created` datetime NOT NULL
)
;
CREATE INDEX `customercare_tweet_928541cb` ON `customercare_tweet` (`locale`);
CREATE INDEX `customercare_tweet_3216ff68` ON `customercare_tweet` (`created`);
COMMIT;
