BEGIN;

ALTER TABLE `demos_submission` ADD COLUMN (
    `comments_total` integer DEFAULT 0 NOT NULL
);

COMMIT;
