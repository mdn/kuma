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
-- feeder_bundle
-- feeder_bundle_feeds
-- feeder_entry
-- feeder_feed
-- search_filter
-- search_filtergroup
-- search_index
-- search_outdatedobject
-- soapbox_message
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
-- wiki_documentzone
-- wiki_editortoolbar
-- wiki_localizationtag
-- wiki_localizationtaggedrevision
-- wiki_reviewtag
-- wiki_reviewtaggedrevision
-- wiki_revision
-- wiki_revisionakismetsubmission
-- wiki_taggeddocument

TRUNCATE account_emailconfirmation;
TRUNCATE authkeys_key;
TRUNCATE authkeys_keyaction;
TRUNCATE celery_taskmeta;
TRUNCATE celery_tasksetmeta;
TRUNCATE constance_config;
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

-- Should be dropped
DROP TABLE IF EXISTS auth_message; -- Removed in Django 1.4
DROP TABLE IF EXISTS django_cache; -- Legacy, 0 records in prod
DROP TABLE IF EXISTS tagging_tag;  -- Not in production
DROP TABLE IF EXISTS tagging_taggeditem;  -- Not in production

-- To be dropped in bug 1184470, August 2015
DROP TABLE IF EXISTS badger_award;
DROP TABLE IF EXISTS badger_badge_prerequisites;
DROP TABLE IF EXISTS badger_badge;
DROP TABLE IF EXISTS badger_deferredaward;
DROP TABLE IF EXISTS badger_nomination;
DROP TABLE IF EXISTS badger_progress;
DROP TABLE IF EXISTS banishments;
DROP TABLE IF EXISTS dashboards_wikidocumentvisits;
DROP TABLE IF EXISTS devmo_calendar;
DROP TABLE IF EXISTS devmo_event;
DROP TABLE IF EXISTS gallery_image;
DROP TABLE IF EXISTS gallery_video;
DROP TABLE IF EXISTS notifications_eventwatch;
DROP TABLE IF EXISTS notifications_watch;
DROP TABLE IF EXISTS notifications_watchfilter;
DROP TABLE IF EXISTS schema_version;
DROP TABLE IF EXISTS south_migrationhistory;
DROP TABLE IF EXISTS teamwork_policy;
DROP TABLE IF EXISTS teamwork_policy_groups;
DROP TABLE IF EXISTS teamwork_policy_permissions;
DROP TABLE IF EXISTS teamwork_policy_users;
DROP TABLE IF EXISTS teamwork_role;
DROP TABLE IF EXISTS teamwork_role_permissions;
DROP TABLE IF EXISTS teamwork_role_users;
DROP TABLE IF EXISTS teamwork_team;
DROP TABLE IF EXISTS threadedcomments_freethreadedcomment;
DROP TABLE IF EXISTS threadedcomments_testmodel;
DROP TABLE IF EXISTS threadedcomments_threadedcomment;

-- To be dropped in bug 1180208, August 2015
DROP TABLE IF EXISTS user_profiles;

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

UPDATE wiki_documentspamattempt SET data = null;

UPDATE users_userban SET
    reason = MD5(reason)
    WHERE reason != "";

SET FOREIGN_KEY_CHECKS=1;
