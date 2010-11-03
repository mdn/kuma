ALTER TABLE `notifications_eventwatch`
    ADD `locale` varchar(7) DEFAULT '';
CREATE INDEX `notifications_eventwatch_928541cb`
    ON `notifications_eventwatch` (`locale`);
ALTER TABLE notifications_eventwatch
    DROP KEY content_type_id;
ALTER TABLE notifications_eventwatch
        ADD UNIQUE (`content_type_id`,`watch_id`,`email`, `event_type`, `locale`);
