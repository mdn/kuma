-- secret doesn't need to be a varchar:
ALTER TABLE notifications_watch MODIFY secret char(10);

-- Make event_type case sensitive:
ALTER TABLE notifications_watch MODIFY event_type varchar(30) CHARACTER SET ascii COLLATE ascii_bin NOT NULL;

-- name should be a varchar (and was meant to be); otherwise, MySQL pads it out
-- with nulls, and equality comparisons all fail.
ALTER TABLE notifications_watchfilter MODIFY name varchar(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL;
