ALTER TABLE `gallery_video`
    ADD `webm` varchar(100) NULL,
    ADD `ogv` varchar(100) NULL,
    ADD `flv` varchar(100) NULL;

ALTER TABLE `gallery_video` DROP `file`;
