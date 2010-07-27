BEGIN;
-- Application: upload
-- Model: ImageAttachment
CREATE TABLE `upload_imageattachment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `file` varchar(100) NOT NULL,
    `thumbnail` varchar(100) NOT NULL,
    `creator_id` integer NOT NULL,
    `content_type_id` integer NOT NULL,
    `object_id` integer UNSIGNED NOT NULL
)
;
ALTER TABLE `upload_imageattachment` ADD CONSTRAINT `creator_id_refs_id_c6b152a0` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `upload_imageattachment` ADD CONSTRAINT `content_type_id_refs_id_e616c0dc` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE INDEX `upload_imageattachment_f97a5119` ON `upload_imageattachment` (`creator_id`);
CREATE INDEX `upload_imageattachment_e4470c6e` ON `upload_imageattachment` (`content_type_id`);
COMMIT;
