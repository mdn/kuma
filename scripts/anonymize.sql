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

SET @common_hash_secret := rand();

SET FOREIGN_KEY_CHECKS=0;

-- Unmodified Tables
-- attachments_attachment
-- attachments_attachmentrevision
-- attachments_documentattachment
-- attachments_trashedattachment
-- auth_group
-- auth_group_permissions
-- auth_permission
-- auth_user_groups
-- auth_user_user_permissions
-- django_content_type
-- django_migrations
-- django_site
-- search_filter
-- search_filtergroup
-- search_index
-- search_outdatedobject
-- taggit_tag
-- taggit_taggeditem
-- waffle_flag
-- waffle_flag_groups
-- waffle_flag_users
-- waffle_sample
-- waffle_switch
-- wiki_document
-- wiki_documentdeletionlog
-- wiki_documenttag
-- wiki_editortoolbar
-- wiki_localizationtag
-- wiki_localizationtaggedrevision
-- wiki_reviewtag
-- wiki_reviewtaggedrevision
-- wiki_revision
-- wiki_taggeddocument

TRUNCATE account_emailconfirmation;
TRUNCATE celery_taskmeta;
TRUNCATE celery_tasksetmeta;
TRUNCATE core_ipban;
TRUNCATE django_admin_log;
TRUNCATE django_session;
TRUNCATE djcelery_crontabschedule;
TRUNCATE djcelery_intervalschedule;
TRUNCATE djcelery_periodictask;
TRUNCATE djcelery_periodictasks;
TRUNCATE djcelery_taskstate;
TRUNCATE djcelery_workerstate;
TRUNCATE socialaccount_socialaccount;
TRUNCATE socialaccount_socialapp;
TRUNCATE socialaccount_socialapp_sites;
TRUNCATE socialaccount_socialtoken;
TRUNCATE tidings_watch;
TRUNCATE tidings_watchfilter;

-- Old tables
DROP TABLE IF EXISTS wiki_documentzone;

UPDATE account_emailaddress SET
    email = CONCAT(MD5(CONCAT(email, @common_hash_secret)), '@example.com');

UPDATE auth_user SET
    -- username left alone, because it's public info
    password = '!',
    email = CONCAT(MD5(CONCAT(email, @common_hash_secret)), '@example.com'),
    first_name = '',
    last_name = '',
    homepage = '';
UPDATE auth_user SET
    title = CONCAT("Title ", MD5(CONCAT(fullname, @common_hash_secret)))
    WHERE title != "";
UPDATE auth_user SET
    fullname = CONCAT("Fullname ", MD5(CONCAT(fullname, @common_hash_secret)))
    WHERE fullname != "";
UPDATE auth_user SET
    organization = CONCAT("Organization ", MD5(CONCAT(organization, @common_hash_secret)))
    WHERE organization != "";
UPDATE auth_user SET
    irc_nickname = CONCAT("irc_", MD5(CONCAT(irc_nickname, @common_hash_secret)))
    WHERE irc_nickname != "";
UPDATE auth_user SET
    location = CONCAT("Location ", MD5(CONCAT(location, @common_hash_secret)))
    WHERE location != "";
UPDATE auth_user SET
    bio = CONCAT("Bio ", MD5(CONCAT(bio, @common_hash_secret)))
    WHERE bio != "";
UPDATE auth_user SET
    facebook_url = CONCAT("https://facebook.com/", MD5(CONCAT(facebook_url, @common_hash_secret)))
    WHERE facebook_url != "";
UPDATE auth_user SET
    discourse_url = CONCAT("https://discourse.mozilla.org/u/", MD5(CONCAT(discourse_url, @common_hash_secret)))
    WHERE discourse_url != "";
UPDATE auth_user SET
    github_url = CONCAT("https://github.com/", MD5(CONCAT(github_url, @common_hash_secret)))
    WHERE github_url != "";
UPDATE auth_user SET
    linkedin_url = CONCAT("https://www.linkedin.com/in/", MD5(CONCAT(linkedin_url, @common_hash_secret)))
    WHERE linkedin_url != "";
UPDATE auth_user SET
    mozillians_url = CONCAT("https://mozillians.org/u/", MD5(CONCAT(mozillians_url, @common_hash_secret)))
    WHERE mozillians_url != "";
UPDATE auth_user SET
    stackoverflow_url = CONCAT("https://stackoverflow.com/users/1/", MD5(CONCAT(stackoverflow_url, @common_hash_secret)))
    WHERE stackoverflow_url != "";
UPDATE auth_user SET
    twitter_url = CONCAT("https://twitter.com/", MD5(CONCAT(twitter_url, @common_hash_secret)))
    WHERE twitter_url != "";
UPDATE auth_user SET
    website_url = CONCAT("https://example.com/", MD5(CONCAT(website_url, @common_hash_secret)))
    WHERE website_url != "";
UPDATE auth_user SET stripe_customer_id = "";

UPDATE wiki_revisionip SET
    ip = CONCAT('192.168.', SUBSTRING_INDEX(ip, '.', -2))
    WHERE ip != "";
UPDATE wiki_revisionip SET
    user_agent = CONCAT('Mozilla 1.0 (', @common_hash_secret, ')')
    WHERE user_agent != "";
UPDATE wiki_revisionip SET
    referrer = CONCAT("https://example.com/", MD5(CONCAT(referrer, @common_hash_secret)))
    WHERE referrer != "";
UPDATE wiki_revisionip SET data = null;

UPDATE users_userban SET
    reason = MD5(reason)
    WHERE reason != "";

SET FOREIGN_KEY_CHECKS=1;
