INSERT INTO `feeder_bundle` (`id`, `shortname`) VALUES 
(6, 'updates-addons'),
(5, 'updates-apps'),
(7, 'updates-mobile'),
(8, 'updates-web');

INSERT INTO `feeder_bundle_feeds` (`id`, `bundle_id`, `feed_id`) VALUES 
(7, 7, 6),
(8, 8, 1);
