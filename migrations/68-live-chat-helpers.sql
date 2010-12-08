ALTER TABLE users_users
    MODIFY login varchar(30) COLLATE utf8_unicode_ci;

INSERT IGNORE INTO auth_group(id, name)
    VALUES (NULL, 'Live Chat helpers');

INSERT IGNORE INTO auth_user_groups (user_id, group_id)
  SELECT auth_user.id, (
        SELECT id FROM auth_group
        WHERE name = 'Live Chat helpers'
    )
  FROM auth_user JOIN users_users ON
          (auth_user.username = users_users.login),
       users_usergroups
  WHERE users_users.userId = users_usergroups.userId
        AND users_usergroups.groupName = 'Live Chat helpers';
