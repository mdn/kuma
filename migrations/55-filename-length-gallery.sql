-- Extend the length of the filename columns to 250

ALTER TABLE `gallery_video`
  MODIFY COLUMN `thumbnail` varchar(250),
  MODIFY COLUMN `webm` varchar(250),
  MODIFY COLUMN `flv` varchar(250),
  MODIFY COLUMN `ogv` varchar(250);

ALTER TABLE `gallery_image`
  MODIFY COLUMN `file` varchar(250),
  MODIFY COLUMN `thumbnail` varchar(250);
