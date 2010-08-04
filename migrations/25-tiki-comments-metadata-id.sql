-- Django cannot do composite primary keys, so we're adding and id column
-- to this table.

ALTER TABLE tiki_comments_metadata DROP PRIMARY KEY;

CREATE UNIQUE INDEX
    threadId_name
ON
    tiki_comments_metadata(threadId, name);

ALTER TABLE
    tiki_comments_metadata
ADD
    id INT NOT NULL AUTO_INCREMENT KEY;


-- Rename FakeUser to something more friendly
UPDATE
    users_users
SET
    login = 'AnonymousUser'
WHERE
    login = 'FakeUser';


UPDATE
    auth_user
SET
    username = 'AnonymousUser'
WHERE
    username = 'FakeUser';
