ALTER TABLE `notifications_eventwatch`
        ADD `event_type` varchar(20);
CREATE INDEX `notifications_eventwatch_event_type_idx`
        ON `notifications_eventwatch` (`event_type`);
ALTER TABLE notifications_eventwatch
        DROP KEY content_type_id;
ALTER TABLE notifications_eventwatch
        ADD UNIQUE (`content_type_id`,`watch_id`,`email`, `event_type`);
UPDATE notifications_eventwatch
        SET event_type = 'reply';
