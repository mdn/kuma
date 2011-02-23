INSERT INTO `feeder_feed` (`id`, `shortname`, `url`, `enabled`, `keep`, `created`, `updated`) VALUES
(9, 'moz-hacks-comments', 'http://hacks.mozilla.org/comments/feed/', 1, 50, NOW(), NOW()),
(10, 'amo-blog', 'http://blog.mozilla.com/addons/feed/', 1, 50, NOW(), NOW()),
(11, 'amo-blog-comments', 'http://blog.mozilla.com/addons/comments/feed/', 1, 50, NOW(), NOW()),
(12, 'amo-forums', 'https://forums.addons.mozilla.org/feed.php', 1, 50, NOW(), NOW())
;

INSERT INTO `feeder_bundle_feeds` (`id`, `bundle_id`, `feed_id`) VALUES
(9, 6, 10);
