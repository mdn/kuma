-- Application: notifications
-- Model: EventWatch
ALTER TABLE `notifications_eventwatch`
	ADD `hash` varchar(40);
CREATE INDEX `hash` ON `notifications_eventwatch` (`hash`);
