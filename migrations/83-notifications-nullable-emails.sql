-- Oops. Migration 82 made notifications_watch not nullable.

ALTER TABLE notifications_watch MODIFY email varchar(75) COLLATE utf8_general_ci;

-- Migration 82 set email to '' where it should have been NULL:
UPDATE notifications_watch SET email=NULL WHERE email='';
