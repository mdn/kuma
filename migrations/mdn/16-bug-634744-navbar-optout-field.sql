--
-- bug 634744: Adding a field to allow opt-out of navbar and iframe
--
BEGIN;

ALTER TABLE `demos_submission` ADD COLUMN (
  `navbar_optout` tinyint(1) DEFAULT 0 NOT NULL
);

COMMIT;
