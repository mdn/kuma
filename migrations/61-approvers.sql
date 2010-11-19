INSERT IGNORE INTO auth_group(id, name)
    VALUES (NULL, 'Reviewers');

INSERT IGNORE INTO auth_user_groups (id, user_id, group_id)
  SELECT NULL, users_users.userId, (
        SELECT id FROM auth_group
        WHERE name = 'Reviewers'
    )
  FROM users_users, users_usergroups
  WHERE users_users.userId = users_usergroups.userId
        AND users_usergroups.groupName = 'Approvers';
