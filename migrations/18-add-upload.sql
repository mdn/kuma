BEGIN;
-- Application: upload
-- Model: ImageAttachment
ALTER TABLE `upload_imageattachment`
        MODIFY `id` integer AUTO_INCREMENT;
ALTER TABLE `upload_imageattachment`
        MODIFY `file` varchar(100);
ALTER TABLE `upload_imageattachment`
        MODIFY `thumbnail` varchar(100);
ALTER TABLE `upload_imageattachment`
        MODIFY `object_id` integer UNSIGNED;
COMMIT;
