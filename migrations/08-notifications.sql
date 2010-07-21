CREATE TABLE `notifications_eventwatch` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer NOT NULL,
    `watch_id` integer NOT NULL,
    `email` varchar(75) NOT NULL,
    UNIQUE (`content_type_id`, `watch_id`, `email`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `notifications_eventwatch` ADD CONSTRAINT `content_type_id_refs_id_1b6122ce` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE INDEX `notifications_eventwatch_content_type_id` ON `notifications_eventwatch` (`content_type_id`);
CREATE INDEX `notifications_eventwatch_watch_id` ON `notifications_eventwatch` (`watch_id`);
CREATE INDEX `notifications_eventwatch_email` ON `notifications_eventwatch` (`email`);

-- django_content_type and auth_permission entries are made in 10-create-questions-app.sql due to an historical deployment contingency.
