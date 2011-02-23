INSERT INTO `feeder_feed` (`id`, `shortname`, `url`, `enabled`, `keep`, `created`, `updated`) VALUES
(13, 'about-mozilla', 'http://blog.mozilla.com/about_mozilla/feed/atom/', 1, 50, NOW(), NOW())
;

INSERT INTO `feeder_bundle_feeds` (`id`, `bundle_id`, `feed_id`) VALUES
(10, 5, 13);
