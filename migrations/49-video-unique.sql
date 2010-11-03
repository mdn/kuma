CREATE UNIQUE INDEX `gallery_image_locale_title`
        ON `gallery_image` (`locale`, `title`);
CREATE UNIQUE INDEX `gallery_video_locale_title`
        ON `gallery_video` (`locale`, `title`);
