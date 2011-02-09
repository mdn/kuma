-- Migrate watches from the old notifications_eventwatch table to the 2 new ones.
-- Took 2 minutes and 45 seconds for 120K rows on my laptop.

-- First, frob the collation of the email column to hugely speed things up:
ALTER TABLE notifications_watch MODIFY email varchar(75) NOT NULL COLLATE utf8_unicode_ci;
BEGIN;  -- MySQL stupidly commits when it hits an ALTER statement.

-- Next, do the filterless watches:

INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'question solved',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='solution';

INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'wiki edit document',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='edited';

-- 'post' type referring to wiki docs:
INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'kbforum thread',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='post' AND content_type_id=(SELECT id from django_content_type where model='document' and app_label='wiki');

-- 'post' type referring to forums:
INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'forum thread',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='post' AND content_type_id=(SELECT id from django_content_type where model='forum' and app_label='forums');

-- 'reply' type referring to questions:
INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'question reply',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='reply' AND content_type_id=(SELECT id from django_content_type where model='question' and app_label='questions');

-- 'reply' type referring to forum threads:
INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'thread reply',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='reply' AND content_type_id=(SELECT id from django_content_type where model='thread' and app_label='forums');

-- 'reply' type referring to kbforums:
INSERT INTO notifications_watch
    (event_type, content_type_id, object_id, is_active, email)
    SELECT 'kbthread reply',
           content_type_id,
           watch_id,
           1,
           email
        FROM notifications_eventwatch
        WHERE event_type='reply' AND content_type_id=(SELECT id from django_content_type where model='thread' and app_label='kbforums');


-- Migrate watches that in the new system have filters:

-- 'approved' type:
-- We do a little dance where we stick the old watch ID into the object_id
-- column temporarily and use it to find the old watch when inserting the new
-- watchfilter row.
INSERT INTO notifications_watch (event_type, is_active, email, object_id)
    SELECT 'approved wiki in locale',
           1,
           email,
           id
        FROM notifications_eventwatch
        WHERE event_type='approved';
INSERT INTO notifications_watchfilter (watch_id, name, value)
    SELECT notifications_watch.id,
           'locale',
           crc32(notifications_eventwatch.locale)
        FROM notifications_watch
        INNER JOIN notifications_eventwatch ON notifications_watch.object_id=notifications_eventwatch.id
        WHERE notifications_eventwatch.event_type='approved';
UPDATE notifications_watch SET object_id=NULL
    WHERE event_type='approved wiki in locale';

-- 'ready_for_review' type:
INSERT INTO notifications_watch (event_type, is_active, email, object_id)
    SELECT 'reviewable wiki in locale',
           1,
           email,
           id
        FROM notifications_eventwatch
        WHERE event_type='ready_for_review';
INSERT INTO notifications_watchfilter (watch_id, name, value)
    SELECT notifications_watch.id,
           'locale',
           crc32(notifications_eventwatch.locale)
        FROM notifications_watch
        INNER JOIN notifications_eventwatch ON notifications_watch.object_id=notifications_eventwatch.id
        WHERE notifications_eventwatch.event_type='ready_for_review';
UPDATE notifications_watch SET object_id=NULL
    WHERE event_type='reviewable wiki in locale';


-- Replace the emails with user IDs where they match:
UPDATE notifications_watch INNER JOIN auth_user ON notifications_watch.email=auth_user.email SET notifications_watch.user_id=auth_user.id, notifications_watch.email=NULL;
-- And put the email column's collation back the way we found it:
ALTER TABLE notifications_watch MODIFY email varchar(75) NOT NULL COLLATE utf8_general_ci;


-- Insert random secrets:
UPDATE notifications_watch SET secret=concat(
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)),
    char(round(rand() * 25) + (case when round(rand()) then 65 else 97 end)));
