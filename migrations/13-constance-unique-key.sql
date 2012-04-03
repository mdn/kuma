--
-- django-constance uses manager.get(key=) but doesn't specify unique=True on the
-- key field. This migration fixes any duplicates and adds the unique constraint

CREATE TEMPORARY TABLE dup_constance_config_keys
    SELECT `key`, `value`
    FROM constance_config
    GROUP BY `key`
    HAVING count(`key`) > 1;

DELETE FROM constance_config
    WHERE `key` IN
        (SELECT `key` FROM dup_constance_config_keys);

ALTER TABLE constance_config
    ADD UNIQUE constance_config_key_unique(`key`(100));
