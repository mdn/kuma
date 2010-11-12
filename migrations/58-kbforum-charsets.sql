-- kbforums_post
ALTER TABLE `kbforums_post`
    MODIFY COLUMN `content` BLOB;
ALTER TABLE `kbforums_post`
    MODIFY COLUMN `content` LONGTEXT CHARACTER SET utf8 NOT NULL;
ALTER TABLE `kbforums_post`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;
ALTER TABLE `kbforums_post`
    ENGINE=InnoDB;

-- kbforums_thread
ALTER TABLE `kbforums_thread`
    MODIFY COLUMN `title` BLOB;
ALTER TABLE `kbforums_thread`
    MODIFY COLUMN `title` VARCHAR(255) CHARACTER SET utf8 NOT NULL;
ALTER TABLE `kbforums_thread`
    CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;
ALTER TABLE `kbforums_thread`
    ENGINE=InnoDB;
