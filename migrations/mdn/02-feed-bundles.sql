INSERT INTO `feeder_bundle` (`id`, `shortname`) VALUES 
(1, 'twitter-web'),
(2, 'twitter-mobile'),
(3, 'twitter-addons'),
(4, 'twitter-apps');

INSERT INTO `feeder_bundle_feeds` (`id`, `bundle_id`, `feed_id`) VALUES 
(1, 1, 2),
(2, 1, 3),
(3, 1, 5),
(4, 2, 4),
(5, 3, 7),
(6, 4, 8);
