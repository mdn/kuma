ALTER TABLE `notifications_watch`
    ADD `is_active` tinyint(1) NOT NULL DEFAULT 0;
CREATE INDEX `notifications_watch_2d27166b`
    ON `notifications_watch` (`is_active`);
