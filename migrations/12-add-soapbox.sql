BEGIN;
CREATE TABLE `soapbox_message` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `message` longtext NOT NULL,
    `is_global` bool NOT NULL,
    `is_active` bool NOT NULL,
    `url` varchar(255)
)
;
COMMIT;
