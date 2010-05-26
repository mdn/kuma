BEGIN;
CREATE TABLE `notifications_eventwatch` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type` varchar(100) NOT NULL,
    `watch_id` integer NOT NULL,
    `email` varchar(75) NOT NULL,
    UNIQUE (`content_type`, `watch_id`, `email`)
)
;
CREATE INDEX `notifications_eventwatch_content_type` ON `notifications_eventwatch` (`content_type`);
CREATE INDEX `notifications_eventwatch_watch_id` ON `notifications_eventwatch` (`watch_id`);
CREATE INDEX `notifications_eventwatch_email` ON `notifications_eventwatch` (`email`);
COMMIT;
