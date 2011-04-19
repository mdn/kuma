--
-- Screenshot and demp package zip file path columns need to be longer
--
BEGIN;

ALTER TABLE `demos_submission` MODIFY COLUMN `screenshot_1` varchar(255);
ALTER TABLE `demos_submission` MODIFY COLUMN `screenshot_2` varchar(255);
ALTER TABLE `demos_submission` MODIFY COLUMN `screenshot_3` varchar(255);
ALTER TABLE `demos_submission` MODIFY COLUMN `screenshot_4` varchar(255);
ALTER TABLE `demos_submission` MODIFY COLUMN `screenshot_5` varchar(255);
ALTER TABLE `demos_submission` MODIFY COLUMN `demo_package` varchar(255);

COMMIT;
