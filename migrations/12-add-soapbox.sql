/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

BEGIN;
DROP TABLE IF EXISTS `soapbox_message`;

CREATE TABLE `soapbox_message` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `message` longtext NOT NULL,
    `is_global` bool NOT NULL,
    `is_active` bool NOT NULL,
    `url` varchar(255)
)
;
COMMIT;
