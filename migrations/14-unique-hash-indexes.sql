/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

--
-- The unique constraint got left out of an earlier actioncounters migration,
-- so this schematic migration forcibly cleans up the few duplicates and adds
-- the unique constraint.
--
-- There should only be about 50 duplicates in 180000 or so production records.
--
CREATE TEMPORARY TABLE dup_actioncounter_hashes
    SELECT unique_hash
    FROM actioncounters_actioncounterunique
    GROUP BY unique_hash 
    HAVING count(unique_hash) > 1;

DELETE FROM actioncounters_actioncounterunique 
    WHERE unique_hash IN
        (SELECT unique_hash FROM dup_actioncounter_hashes);

DROP INDEX actioncounters_actioncounterunique_unique
    ON actioncounters_actioncounterunique;

ALTER TABLE actioncounters_actioncounterunique 
    ADD UNIQUE actioncounters_actioncounterunique_unique (unique_hash);
