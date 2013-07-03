/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

--
-- MDN Kuma anonymization / sanitization
--
-- Run this on a COPY of a production DB - NEVER ON THE REAL THING!
-- This nukes all kinds of data from orbit.
--
-- See also: https://mana.mozilla.org/wiki/display/SECURITY/Database+Sanitization+Policy+-+Draft
--
-- Confidential, private or personal data is any data that contains the
-- following:
-- 
--     First Name
--     Last Name
--     Physical Address Information
--     IP Addresses
--     Passwords and/or Password Hashes
--     Ages
--     Gender
--     Any database record or data which could be tied to the identity of an
--         individual
-- 
-- When exporting this data, referred as Personally Identifiable Information
-- (PII) data must be removed such that no data would be specifically tied to
-- an individual. 

SET @common_hash_secret=rand();

SET FOREIGN_KEY_CHECKS=0;

TRUNCATE actioncounters_actioncounterunique;
TRUNCATE auth_message;
TRUNCATE authkeys_key;
TRUNCATE authkeys_keyaction;
TRUNCATE contentflagging_contentflag;
TRUNCATE django_admin_log;
TRUNCATE django_session;
TRUNCATE djcelery_crontabschedule;
TRUNCATE djcelery_intervalschedule;
TRUNCATE djcelery_periodictask;
TRUNCATE djcelery_periodictasks;
TRUNCATE djcelery_taskstate;
TRUNCATE djcelery_workerstate;
TRUNCATE notifications_eventwatch;
TRUNCATE notifications_watch;
TRUNCATE notifications_watchfilter;
TRUNCATE threadedcomments_freethreadedcomment;
TRUNCATE threadedcomments_threadedcomment;
TRUNCATE threadedcomments_testmodel;
TRUNCATE users_emailchange;
-- `user_profiles` is the real profiles table, not this. I know, it's weird.
TRUNCATE users_profile;
TRUNCATE users_registrationprofile;

UPDATE auth_user SET
    -- username left alone, because it's public info
    password = NULL, 
    email = CONCAT('user-', id, '@example.com'),
    first_name = ROUND(RAND()*1000000), 
    last_name = ROUND(RAND()*1000000);

-- Does this table need more scrubbing? It's profile data made intentionally
-- public by users.
UPDATE user_profiles SET
    location = ROUND(RAND()*1000000),
    homepage = ROUND(RAND()*1000000);

SET FOREIGN_KEY_CHECKS=1;
