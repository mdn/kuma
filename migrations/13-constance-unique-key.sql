/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

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
